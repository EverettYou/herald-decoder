#!/usr/bin/env python3
"""A7 LER runner: frozen Lab 006 artifact decoder, with batched BP only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pymatching
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from artifact_backend import MAX_BP_ITERATIONS, _cached_decoder, warm_numba_kernels
from herald_decoder.lattice_model import honeycomb_graph, square_graph
from numba_fusion_decoder import GROUP_IRREPS, group_fusion_distribution
from sun_fusion_bp import Graph

GROUPS = ("None", "U1", "SU2", "SU3")
ARMS = ("no_herald", "syndrome_only", "representation_herald")
TRIVIAL = {"None": "1", "U1": "0", "SU2": "1", "SU3": "1"}
SCORING_RULE = "final-correction-v2: residual syndrome clear AND trivial logical parity; BP convergence diagnostic only"


def final_decoder_failure(residual: np.ndarray, logical_parity: bool) -> bool:
    """Score only the final two-stage decoder output, never BP convergence."""
    return bool(np.any(residual)) or bool(logical_parity)


def context(lattice: str, size: int):
    model = square_graph(size) if lattice == "square" else honeycomb_graph(size)
    observed = tuple(vertex for vertex, edges in enumerate(model.incident_edges) if edges)
    row = {vertex: index for index, vertex in enumerate(observed)}
    detector_rows = np.asarray([row[vertex] for vertex in model.detector_vertices], dtype=np.int64)
    boundary_rows = tuple(index for index, vertex in enumerate(observed) if not model.vertices[vertex].detector)
    graph = Graph(tuple(f"v{vertex}" for vertex in observed), tuple((f"v{tail}", f"v{head}") for tail, head in model.edges))
    return model, graph, detector_rows, boundary_rows


def select(channel: dict[str, float], u: float) -> str:
    total = 0.0
    for label, probability in channel.items():
        total += probability
        if u <= total:
            return label
    return next(reversed(channel))


@njit(cache=True)
def _generate_records_numba(errors, uniforms, incident_edges, incident_degrees,
                            boundary, cdf, label_codes):
    """Sample m and R from finite pretabulated local fusion channels."""
    batch, vertices = uniforms.shape
    labels = np.empty((batch, vertices), dtype=np.int8)
    m = np.zeros((batch, vertices), dtype=np.uint8)
    for sample in range(batch):
        for vertex in range(vertices):
            pattern = 0
            active = 0
            for position in range(incident_degrees[vertex]):
                if errors[sample, incident_edges[vertex, position]]:
                    pattern |= 1 << position
                    active += 1
            if boundary[vertex] == 0:
                m[sample, vertex] = active & 1
            selected = label_codes[vertex, pattern, label_codes.shape[2] - 1]
            for output in range(label_codes.shape[2]):
                if uniforms[sample, vertex] <= cdf[vertex, pattern, output]:
                    selected = label_codes[vertex, pattern, output]
                    break
            labels[sample, vertex] = selected
    return m, labels


def _record_tables(graph: Graph, boundary_rows: tuple[int, ...], group: str):
    """Turn every vertex/subset fusion channel into compact Numba lookup tables."""
    incident = graph.incident
    max_degree = max(len(leaves) for leaves in incident)
    outputs = max(len(group_fusion_distribution(group, tuple(
        "fund" if rep == "3" else "anti" for _, rep in leaves
    ))) for leaves in incident)
    incident_edges = np.zeros((len(incident), max_degree), dtype=np.int64)
    incident_degrees = np.zeros(len(incident), dtype=np.int64)
    boundary = np.zeros(len(incident), dtype=np.uint8)
    cdf = np.ones((len(incident), 1 << max_degree, outputs), dtype=np.float64)
    label_codes = np.zeros((len(incident), 1 << max_degree, outputs), dtype=np.int8)
    codes = {label: code for code, label in enumerate(GROUP_IRREPS[group])}
    boundary_set = set(boundary_rows)
    for vertex, leaves in enumerate(incident):
        incident_degrees[vertex] = len(leaves)
        for position, (edge, _) in enumerate(leaves):
            incident_edges[vertex, position] = edge
        boundary[vertex] = int(vertex in boundary_set)
        for pattern in range(1 << len(leaves)):
            if boundary[vertex]:
                channel = {TRIVIAL[group]: 1.0}
            else:
                active = tuple(
                    ("fund" if leaves[position][1] == "3" else "anti")
                    for position in range(len(leaves)) if pattern & (1 << position)
                )
                channel = group_fusion_distribution(group, active)
            total = 0.0
            last = codes[next(reversed(channel))]
            for output, (label, probability) in enumerate(channel.items()):
                total += probability
                cdf[vertex, pattern, output] = total
                label_codes[vertex, pattern, output] = codes[label]
                last = codes[label]
            for output in range(len(channel), outputs):
                cdf[vertex, pattern, output] = 1.0
                label_codes[vertex, pattern, output] = last
    return incident_edges, incident_degrees, boundary, cdf, label_codes


def _generate_records_legacy(errors, uniforms, graph: Graph, boundary_rows: tuple[int, ...]):
    count = errors.shape[0]
    m = np.zeros((count, len(graph.vertices)), dtype=np.uint8)
    labels = {group: np.empty((count, len(graph.vertices)), dtype=np.int8) for group in GROUPS}
    codes = {group: {label: code for code, label in enumerate(GROUP_IRREPS[group])} for group in GROUPS}
    for sample in range(count):
        for vertex, leaves in enumerate(graph.incident):
            active = tuple("fund" if rep == "3" else "anti" for edge, rep in leaves if errors[sample, edge])
            if vertex not in boundary_rows:
                m[sample, vertex] = len(active) & 1
            for group in GROUPS:
                label = TRIVIAL[group] if vertex in boundary_rows else select(group_fusion_distribution(group, active), uniforms[sample, vertex])
                labels[group][sample, vertex] = codes[group][label]
    return m, labels


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return float(centre - half), float(centre + half)


def run_cell(lattice: str, size: int, p: float, shots: int, seed: int, batch_size: int,
             *, optimized: bool = True) -> list[dict]:
    model, graph, detector_rows, boundary_rows = context(lattice, size)
    # This is topology-only.  Reusing it changes neither the artifact decoder
    # nor any correction; it removes an accidental sparse-matrix rebuild from
    # every Monte-Carlo shot.
    check_matrix = model.check_matrix
    decoders = {}
    for group in GROUPS:
        for arm, use_irrep in ((arm, arm == "representation_herald") for arm in ARMS if arm != "no_herald"):
            decoder = _cached_decoder(graph, group=group, orientation_mode="directed", use_irrep=use_irrep,
                                       p=p, damping=.5, boundary_factor_rows=boundary_rows,
                                       measure_boundary_representation=False, algorithm="sum_product")
            decoder.matrix = check_matrix
            decoders[group, arm] = decoder
    uniform_matching = pymatching.Matching.from_check_matrix(
        check_matrix, weights=np.full(len(graph.edges), np.log((1 - p) / p)),
    )
    tables = {group: _record_tables(graph, boundary_rows, group) for group in GROUPS} if optimized else None
    outcomes = {(group, arm): {"logical": 0, "logical_parity": 0, "invalid": 0, "nonconverged": 0} for group in GROUPS for arm in ARMS}
    rng = np.random.default_rng(seed)
    for start in range(0, shots, batch_size):
        count = min(batch_size, shots - start)
        errors = (rng.random((count, len(graph.edges))) < p).astype(np.uint8)
        uniforms = rng.random((count, len(graph.vertices)))
        if optimized:
            generated = [_generate_records_numba(errors, uniforms, *tables[group]) for group in GROUPS]
            m = generated[0][0]
            labels = {group: generated[index][1] for index, group in enumerate(GROUPS)}
            if any(not np.array_equal(m, record[0]) for record in generated[1:]):
                raise AssertionError("group-specific record generators disagree on m")
        else:
            m, labels = _generate_records_legacy(errors, uniforms, graph, boundary_rows)
        matching_m = m[:, detector_rows]
        for group in GROUPS:
            # Standard MWPM is the no-herald arm. It shares the exact detector record.
            if "no_herald" in ARMS:
                corrections = uniform_matching.decode_batch(matching_m).astype(np.uint8) if optimized else None
                for sample in range(count):
                    correction = corrections[sample] if optimized else uniform_matching.decode(matching_m[sample]).astype(np.uint8)
                    residual = matching_m[sample] ^ (np.asarray(check_matrix @ correction).ravel().astype(np.uint8) & 1)
                    if np.any(residual):
                        outcomes[group, "no_herald"]["invalid"] += 1
                        outcomes[group, "no_herald"]["logical"] += 1
                    elif model.logical_parity(errors[sample] ^ correction):
                        outcomes[group, "no_herald"]["logical_parity"] += 1
                        outcomes[group, "no_herald"]["logical"] += 1
            for arm in (arm for arm in ARMS if arm != "no_herald"):
                decoder = decoders[group, arm]
                marginals, converged, _, _ = decoder.infer_batch(m, labels[group])
                for sample in range(count):
                    clipped = np.clip(marginals[sample], 1e-12, 1 - 1e-12)
                    matching = pymatching.Matching.from_check_matrix(check_matrix, weights=np.log((1 - clipped) / clipped))
                    correction = matching.decode(matching_m[sample]).astype(np.uint8)
                    residual = matching_m[sample] ^ (np.asarray(check_matrix @ correction).ravel().astype(np.uint8) & 1)
                    # BP supplies soft edge weights to the second-stage matcher.
                    # Its numerical convergence flag is diagnostic only: matching
                    # still produces a correction from the final available beliefs.
                    logical_parity = bool(model.logical_parity(errors[sample] ^ correction))
                    failed = final_decoder_failure(residual, logical_parity)
                    outcomes[group, arm]["nonconverged"] += int(not bool(converged[sample]))
                    outcomes[group, arm]["invalid"] += int(bool(np.any(residual)))
                    outcomes[group, arm]["logical_parity"] += int(logical_parity)
                    if failed:
                        outcomes[group, arm]["logical"] += 1
    rows = []
    for group in GROUPS:
        for arm in ARMS:
            result = outcomes[group, arm]
            lo, hi = wilson(result["logical"], shots)
            rows.append({"lattice": lattice, "L": size, "p": p, "shots": shots, "group": group, "arm": arm,
                         "logical_failures": result["logical"], "ler": result["logical"] / shots,
                         "logical_parity_failures": result["logical_parity"],
                         "wilson95": [lo, hi], "bp_nonconverged": result["nonconverged"], "invalid_correction": result["invalid"]})
    return rows


def render(rows: list[dict], destination: Path, title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    colors = {"no_herald": "#64748b", "syndrome_only": "#2563eb", "representation_herald": "#d34f8d"}
    labels = {"no_herald": "No herald", "syndrome_only": "Interior m only", "representation_herald": "Interior (m,R)"}
    for axis, group in zip(axes.ravel(), GROUPS, strict=True):
        for lattice, marker in (("square", "o"), ("honeycomb", "s")):
            for arm in ARMS:
                series = sorted((row for row in rows if row["group"] == group and row["lattice"] == lattice and row["arm"] == arm), key=lambda row: (row["L"], row["p"]))
                for size in sorted({row["L"] for row in series}):
                    curve = [row for row in series if row["L"] == size]
                    axis.errorbar([row["p"] for row in curve], [row["ler"] for row in curve],
                                  yerr=[[row["ler"] - row["wilson95"][0] for row in curve], [row["wilson95"][1] - row["ler"] for row in curve]],
                                  color=colors[arm], marker=marker, linestyle="-" if size == 5 else "--", alpha=.85,
                                  label=f"{labels[arm]}, {lattice}, L={size}")
        axis.set_title(group.replace("U1", "U(1)").replace("SU", "SU(" ) + (")" if group.startswith("SU") else ""))
        axis.set_xlabel("physical edge-error rate p"); axis.set_ylabel("logical error rate")
        axis.set_ylim(-.02, 1.02); axis.grid(alpha=.25)
    handles, labels_out = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels_out, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(title); fig.tight_layout(rect=(0, .10, 1, .95)); fig.savefig(destination, dpi=180); plt.close(fig)


def render_convergence(rows: list[dict], destination: Path, title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    colors = {"syndrome_only": "#2563eb", "representation_herald": "#d34f8d"}
    for axis, group in zip(axes.ravel(), GROUPS, strict=True):
        for lattice, marker in (("square", "o"), ("honeycomb", "s")):
            for arm in ("syndrome_only", "representation_herald"):
                series = sorted((row for row in rows if row["group"] == group and row["lattice"] == lattice and row["arm"] == arm), key=lambda row: (row["L"], row["p"]))
                for size in sorted({row["L"] for row in series}):
                    curve = [row for row in series if row["L"] == size]
                    axis.plot([row["p"] for row in curve], [row["bp_nonconverged"] / row["shots"] for row in curve],
                              color=colors[arm], marker=marker, linestyle="-" if size == 5 else "--", alpha=.85,
                              label=f"{arm.replace('_', ' ')}, {lattice}, L={size}")
        title_group = "U(1)" if group == "U1" else (group.replace("SU", "SU(") + ")" if group.startswith("SU") else group)
        axis.set_title(title_group); axis.set_xlabel("physical edge-error rate p"); axis.set_ylabel("BP nonconvergence fraction")
        axis.set_ylim(-.02, 1.02); axis.grid(alpha=.25)
    handles, labels_out = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels_out, loc="lower center", ncol=2, fontsize=8)
    fig.suptitle(title); fig.tight_layout(rect=(0, .10, 1, .95)); fig.savefig(destination, dpi=180); plt.close(fig)


def render_four_size(rows: list[dict], destination: Path, title: str, *, convergence: bool = False) -> None:
    """Readable eight-panel view for four distances; used by merged sweeps."""
    fig, axes = plt.subplots(4, 2, figsize=(13, 14), sharex=True, sharey=True)
    colors = {"no_herald": "#64748b", "syndrome_only": "#2563eb", "representation_herald": "#d34f8d"}
    arm_labels = {"no_herald": "No herald", "syndrome_only": "Interior m only", "representation_herald": "Interior (m,R)"}
    sizes = sorted({row["L"] for row in rows})
    styles = {size: style for size, style in zip(sizes, ("-", "--", ":", "-"), strict=False)}
    for row_index, group in enumerate(GROUPS):
        for column, lattice in enumerate(("square", "honeycomb")):
            axis = axes[row_index, column]
            for arm in ARMS:
                if convergence and arm == "no_herald":
                    continue
                for size in sizes:
                    curve = sorted((row for row in rows if row["group"] == group and row["lattice"] == lattice and row["arm"] == arm and row["L"] == size), key=lambda row: row["p"])
                    if convergence:
                        axis.plot([row["p"] for row in curve], [row["bp_nonconverged"] / row["shots"] for row in curve], color=colors[arm], linestyle=styles[size], marker="o", markersize=3)
                    else:
                        axis.errorbar([row["p"] for row in curve], [row["ler"] for row in curve], yerr=[[row["ler"] - row["wilson95"][0] for row in curve], [row["wilson95"][1] - row["ler"] for row in curve]], color=colors[arm], linestyle=styles[size], marker="o", markersize=3, alpha=.9)
            if row_index == 0:
                axis.set_title(lattice)
            axis.set_ylabel(f"{group if group != 'U1' else 'U(1)'}\n" + ("BP nonconvergence" if convergence else "logical error rate"))
            axis.set_ylim(-.02, 1.02); axis.grid(alpha=.25)
            if row_index == len(GROUPS) - 1:
                axis.set_xlabel("physical edge-error rate p")
    arm_handles = [Line2D([0], [0], color=colors[arm], lw=2, label=arm_labels[arm]) for arm in (ARMS[1:] if convergence else ARMS)]
    size_handles = [Line2D([0], [0], color="#334155", lw=2, linestyle=styles[size], label=f"L={size}") for size in sizes]
    fig.legend(handles=arm_handles + size_handles, loc="lower center", ncol=len(arm_handles) + len(size_handles), fontsize=9)
    fig.suptitle(title); fig.tight_layout(rect=(0, .055, 1, .97)); fig.savefig(destination, dpi=180); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=20000)
    parser.add_argument("--sizes", type=int, nargs="+", default=[5, 7, 9, 11])
    parser.add_argument("--rates", type=float, nargs="+", default=[round(.02 * index, 2) for index in range(1, 16)])
    parser.add_argument("--tag", default="production")
    parser.add_argument("--legacy", action="store_false", dest="optimized", help="use the retained pre-optimization runner for regression comparison")
    parser.set_defaults(optimized=True)
    parser.add_argument("--resume", action="store_true", help="reuse completed cells from the tag's JSON checkpoint")
    args = parser.parse_args()
    warm_numba_kernels()
    results = HERE.parent / "results"
    json_path = results / f"a7-ler-{args.tag}.json"
    rows = []
    if args.resume and json_path.is_file():
        existing = json.loads(json_path.read_text())
        if existing.get("scope", {}).get("shots_per_cell") != args.shots or existing.get("scope", {}).get("sizes") != args.sizes or existing.get("scope", {}).get("rates") != args.rates or existing.get("scope", {}).get("scoring_rule") != SCORING_RULE:
            raise ValueError("checkpoint scope differs from requested acquisition")
        rows = existing["rows"]
    completed = {(row["lattice"], row["L"], row["p"]) for row in rows}
    cell = 0
    for lattice in ("square", "honeycomb"):
        for size in args.sizes:
            for p in args.rates:
                if (lattice, size, p) not in completed:
                    rows.extend(run_cell(lattice, size, p, args.shots, 800000 + cell, 256, optimized=args.optimized))
                    partial = {"protocol": "lab006-a7-frozen-artifact-ler", "tag": args.tag,
                               "status": "running", "scope": {"shots_per_cell": args.shots, "batch_size": 256, "sizes": args.sizes, "rates": args.rates, "scoring_rule": SCORING_RULE,
                                         "runner": "numba-record-generation+fixed-weight-pymatching-decode-batch" if args.optimized else "legacy",
                                         "decoder": "artifact default: directed sum-product, damping 0.5, 300 iterations, tolerance 1e-10, no rough-boundary m/R"},
                               "rows": rows}
                    json_path.write_text(json.dumps(partial, indent=2) + "\n")
                cell += 1
    result = {"protocol": "lab006-a7-frozen-artifact-ler", "tag": args.tag,
              "scope": {"shots_per_cell": args.shots, "batch_size": 256, "sizes": args.sizes, "rates": args.rates, "scoring_rule": SCORING_RULE,
                        "runner": "numba-record-generation+fixed-weight-pymatching-decode-batch" if args.optimized else "legacy",
                        "decoder": "artifact default: directed sum-product, damping 0.5, 300 iterations, tolerance 1e-10, no rough-boundary m/R"},
              "rows": rows}
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    render(rows, results / f"a7-ler-{args.tag}.png", f"Lab 006 LER — {args.tag}; {args.shots} shots/cell")
    render_convergence(rows, results / f"a7-bp-nonconvergence-{args.tag}.png", f"Lab 006 BP nonconvergence — {args.tag}; {args.shots} shots/cell")


if __name__ == "__main__":
    main()
