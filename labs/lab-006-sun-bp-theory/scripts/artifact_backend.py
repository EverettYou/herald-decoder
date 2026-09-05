#!/usr/bin/env python3
"""Numba-backed data endpoint for the Lab 006 fusion workbench."""
from __future__ import annotations

from pathlib import Path
import importlib
import sys
from time import perf_counter
from threading import RLock
from itertools import combinations

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numba_fusion_decoder as _decoder_module

# The dashboard hot-reloads this endpoint module but Python otherwise retains
# its sibling decoder module.  Refresh a pre-None registry exactly once so a
# live Artifact cannot validate controls against a stale group list.
if "None" not in _decoder_module.GROUP_IRREPS:
    _decoder_module = importlib.reload(_decoder_module)

from numba_fusion_decoder import (
    FastFusionBeliefMatchingDecoder,
    MinSumFusionBeliefMatchingDecoder,
    UndirectedFusionBeliefMatchingDecoder,
    GeneralizedSyndrome,
    GROUP_IRREPS,
    group_fusion_distribution,
)
from herald_decoder.lattice_model import honeycomb_graph, square_graph
from sun_fusion_bp import Graph
from sun_fusion_bp import IRREP_DIM, SU3_MULTIPLICITIES

COLORS = {
    "None": {},
    "U1": {"+1": "#0f9d8a", "-1": "#d34f8d", "+2": "#596bd6", "-2": "#df6975", "+3": "#8b5cf6", "-3": "#ef6f6c", "+4": "#2563eb", "-4": "#be185d"},
    "SU2": {"2": "#0f9d8a", "3": "#e4a031", "4": "#596bd6", "5": "#8b5cf6"},
    "SU3": {"3": "#0f9d8a", "3bar": "#d34f8d", "8": "#e4a031", "6": "#596bd6", "6bar": "#df6975", "10": "#2563eb", "10bar": "#be185d", "15": "#7c3aed", "15bar": "#db2777", "15prime": "#4338ca", "15primebar": "#9d174d", "24": "#0891b2", "24bar": "#c2418c", "27": "#b7791f"},
}
TRIVIAL = {"None": "1", "U1": "0", "SU2": "1", "SU3": "1"}
DISPLAY = {"None": "None", "U1": "U(1)", "SU2": "SU(2)", "SU3": "SU(3)"}
RULES = {
    "None": "R = 1 (no symmetry record)",
    "U1": "q1 x q2 = q1 + q2",
    "SU2": "2 x 2 = 1 + 3; 2 is self-conjugate",
    "SU3": "3 x 3̄ = 1 + 8; 3 x 3 = 6 + 3̄",
}
IRREP_DIMENSIONS = {
    "None": {"1": 1},
    "U1": {"0": 1, **{f"{charge:+d}": 1 for charge in range(-4, 5) if charge}},
    "SU2": {str(dimension): dimension for dimension in range(1, 6)},
    "SU3": IRREP_DIM,
}


def _irrep_sort_key(group: str, label: str) -> tuple:
    if group == "U1":
        charge = int(label)
        return (1, abs(charge), charge < 0, charge)
    return (IRREP_DIMENSIONS[group][label], label)


def _sort_fusion_rules(group: str, entries: list[dict]) -> list[dict]:
    for entry in entries:
        entry["outputs"].sort(key=lambda output: _irrep_sort_key(group, output["label"]))
    return sorted(
        entries,
        key=lambda entry: tuple(_irrep_sort_key(group, label) for label in entry["inputs"]),
    )

# A likelihood bank depends on topology, group, orientation model and whether
# R is observed—not on p, damping, seed, or the sampled record.  Retaining it
# makes interactive control changes call the preallocated Numba kernel instead
# of rebuilding Python fusion tables on every slider event.
_DECODER_CACHE: dict[tuple, FastFusionBeliefMatchingDecoder] = {}
_DECODER_CACHE_LOCK = RLock()
_MAX_CACHED_DECODERS = 48
MAX_BP_ITERATIONS = 300


def _cached_decoder(graph: Graph, *, group: str, orientation_mode: str,
                    use_irrep: bool, p: float, damping: float,
                    boundary_factor_rows: tuple[int, ...],
                    measure_boundary_representation: bool, algorithm: str):
    Decoder = MinSumFusionBeliefMatchingDecoder if algorithm == "min_sum" else (FastFusionBeliefMatchingDecoder if orientation_mode == "directed" else UndirectedFusionBeliefMatchingDecoder)
    key = (graph.vertices, graph.edges, group, orientation_mode, use_irrep,
           measure_boundary_representation, algorithm)
    decoder = _DECODER_CACHE.get(key)
    if decoder is None:
        if len(_DECODER_CACHE) >= _MAX_CACHED_DECODERS:
            _DECODER_CACHE.pop(next(iter(_DECODER_CACHE)))
        decoder = Decoder(graph, group=group, p=p, use_irrep=use_irrep,
            max_iterations=MAX_BP_ITERATIONS, damping=damping, tolerance=1e-10,
            **({"undirected": orientation_mode == "undirected"} if algorithm == "min_sum" else {}))
        # Rough-boundary m has no stabilizer measurement.  The UI records it
        # as 0 but this factor must marginalize it, rather than impose even
        # parity.  The optional trapped-R record is retained only when chosen.
        for factor in boundary_factor_rows:
            if measure_boundary_representation:
                decoder.bank[factor, 0] = decoder.bank[factor, 0] + decoder.bank[factor, 1]
            else:
                decoder.bank[factor, 0] = 1.0
        if hasattr(decoder, "costs"):
            decoder.costs = np.where(decoder.bank > 0.0, -np.log(np.maximum(decoder.bank, 1e-300)), 1e100)
        _DECODER_CACHE[key] = decoder
    # These are scalars read by the compiled kernel; changing a slider does not
    # alter any Numba signature or the precomputed local-likelihood bank.
    decoder.p = p
    decoder.damping = damping
    decoder.max_iterations = MAX_BP_ITERATIONS
    return decoder


def warm_numba_kernels(_payload: dict | None = None) -> None:
    """Compile the binary and ternary BP kernels before an interactive request.

    Numba specializes on dtype and array rank, not the numerical dimensions of
    a graph.  A one-edge graph therefore warms the same binary and ternary
    kernels used for every supported lattice size and symmetry group.
    """
    graph = Graph(("a", "b"), (("a", "b"),))
    observation = GeneralizedSyndrome(
        np.zeros(2, dtype=np.uint8), ("1", "1"),
    )
    for Decoder in (FastFusionBeliefMatchingDecoder, UndirectedFusionBeliefMatchingDecoder):
        Decoder(graph, group="SU3", p=.1, max_iterations=1).infer(observation)


def _number(body, name, low, high, default=None):
    value = body.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not low <= value <= high:
        raise ValueError(f"{name} must lie in [{low}, {high}]")
    return value


def _soft_metrics(probabilities, truth):
    probabilities = np.clip(np.asarray(probabilities), 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    return {
        "log_loss": float(-np.mean(truth * np.log(probabilities) + (1 - truth) * np.log(1 - probabilities))),
        "brier": float(np.mean((probabilities - truth) ** 2)),
    }


def _dynamic_fusion_rules(group: str, active_configurations: list[tuple[str, ...]]) -> list[dict]:
    """Two-representation fusion rules used as steps in this sampled record."""
    if group == "U1":
        rules: dict[tuple[str, str], list[dict]] = {}

        def label(charge: int) -> str:
            return f"{charge:+d}" if charge else "0"

        for leaves in active_configurations:
            if len(leaves) < 2:
                continue
            charge = 1 if leaves[0] == "fund" else -1
            for leaf in leaves[1:]:
                increment = 1 if leaf == "fund" else -1
                rules[(label(charge), label(increment))] = [
                    {"label": label(charge + increment), "multiplicity": 1}
                ]
                charge += increment
        return _sort_fusion_rules(group, [
            {"inputs": list(inputs), "outputs": outputs}
            for inputs, outputs in sorted(rules.items())
        ])
    if group == "SU2":
        maximum = max((len(leaves) for leaves in active_configurations), default=0)
        rules = []
        if maximum >= 2:
            rules.append({"inputs": ["2", "2"], "outputs": [{"label": "3", "multiplicity": 1}, {"label": "1", "multiplicity": 1}]})
        if maximum >= 3:
            rules.append({"inputs": ["3", "2"], "outputs": [{"label": "4", "multiplicity": 1}, {"label": "2", "multiplicity": 1}]})
        if maximum >= 4:
            rules.append({"inputs": ["4", "2"], "outputs": [{"label": "5", "multiplicity": 1}, {"label": "3", "multiplicity": 1}]})
        return _sort_fusion_rules(group, rules)
    if group == "SU3":
        rules: dict[tuple[str, str], list[dict]] = {}

        def add(left: str, right: str, *outputs: str) -> None:
            rules[(left, right)] = [{"label": label, "multiplicity": 1} for label in outputs]

        for leaves in active_configurations:
            fund, anti = leaves.count("fund"), leaves.count("anti")
            if fund >= 2:
                add("3", "3", "6", "3bar")
            if anti >= 2:
                add("3bar", "3bar", "6bar", "3")
            if fund and anti:
                add("3", "3bar", "1", "8")
            if fund >= 2 and anti:
                add("6", "3bar", "15", "3")
            if fund and anti >= 2:
                add("6bar", "3", "15bar", "3bar")
            if fund >= 3:
                add("6", "3", "10", "8")
            if anti >= 3:
                add("6bar", "3bar", "10bar", "8")
            if fund >= 3 and anti:
                add("10", "3bar", "24", "6")
            if fund and anti >= 3:
                add("10bar", "3", "24bar", "6bar")
            if fund >= 4:
                add("10", "3", "15prime", "15")
            if anti >= 4:
                add("10bar", "3bar", "15primebar", "15bar")
            if fund >= 2 and anti >= 2:
                add("15", "3bar", "27", "10", "8")
                add("15bar", "3", "27", "10bar", "8")
        return _sort_fusion_rules(group, [
            {"inputs": list(inputs), "outputs": outputs}
            for inputs, outputs in sorted(rules.items())
        ])
    pair_configurations = {
        pair for leaves in active_configurations for pair in combinations(leaves, 2)
    }
    unique = sorted(pair_configurations)
    entries = []
    displayed = set()
    for leaves in unique:
        if group == "None":
            inputs, outputs = ("1",), [{"label": "1", "multiplicity": 1}]
        elif group == "U1":
            inputs = tuple("+1" if leaf == "fund" else "-1" for leaf in leaves)
            output = next(iter(group_fusion_distribution(group, leaves)))
            outputs = [{"label": output, "multiplicity": 1}]
        elif group == "SU2":
            inputs = tuple("2" for _ in leaves)
            channel = group_fusion_distribution(group, leaves)
            outputs = [
                {"label": label, "multiplicity": int(round(probability * 2 ** len(leaves) / int(label)))}
                for label, probability in channel.items()
            ]
        else:
            inputs = tuple("3" if leaf == "fund" else "3bar" for leaf in leaves)
            multiplicities = SU3_MULTIPLICITIES[(inputs.count("3"), inputs.count("3bar"))]
            outputs = [{"label": label, "multiplicity": multiplicity} for label, multiplicity in multiplicities.items()]
        signature = (inputs, tuple((item["label"], item["multiplicity"]) for item in outputs))
        if signature not in displayed:
            displayed.add(signature)
            entries.append({"inputs": list(inputs), "outputs": outputs})
    return _sort_fusion_rules(group, entries)


def artifact_payload(body: dict) -> dict:
    group = str(body.get("group", "SU3"))
    if group not in GROUP_IRREPS:
        raise ValueError("group must be None, U1, SU2, or SU3")
    lattice = str(body.get("lattice", "square"))
    if lattice not in {"square", "honeycomb"}:
        raise ValueError("lattice must be square or honeycomb")
    size = body.get("L", 5)
    seed = body.get("seed", 25)
    if isinstance(size, bool) or not isinstance(size, int) or not 3 <= size <= 15:
        raise ValueError("L must be an integer in [3, 15]")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be a uint32 integer")
    p = _number(body, "p", 0.0, 0.5)
    damping = _number(body, "damping", 0.0, 0.9, default=.5)
    algorithm = str(body.get("algorithm", "sum_product"))
    if algorithm not in {"sum_product", "min_sum"}:
        raise ValueError("algorithm must be sum_product or min_sum")
    measure_boundary_representation = body.get("measure_boundary_representation", False)
    if not isinstance(measure_boundary_representation, bool):
        raise ValueError("measure_boundary_representation must be boolean")
    orientation_mode = str(body.get("orientation", "directed"))
    if orientation_mode not in {"directed", "undirected"}:
        raise ValueError("orientation must be directed or undirected")

    lattice_graph = square_graph(size) if lattice == "square" else honeycomb_graph(size)
    incident_edges = lattice_graph.incident_edges
    detector_ids = lattice_graph.detector_vertices
    # Every physical site carrying an endpoint is observed.  Boundary sites
    # are not parity checks for matching, but a bond ending there traps its
    # fundamental/antifundamental irrep and is an informative BP factor.
    observed_ids = tuple(vertex for vertex, edges in enumerate(incident_edges) if edges)
    observed_row = {vertex: row for row, vertex in enumerate(observed_ids)}
    detector_rows = np.asarray([observed_row[vertex] for vertex in detector_ids], dtype=np.int64)
    boundary_factor_rows = tuple(
        row for row, vertex in enumerate(observed_ids)
        if not lattice_graph.vertices[vertex].detector
    )
    graph = Graph(
        tuple(f"v{vertex}" for vertex in observed_ids),
        tuple((f"v{tail}", f"v{head}") for tail, head in lattice_graph.edges),
    )
    total_start = perf_counter()
    rng = np.random.default_rng(seed)
    error = (rng.random(len(graph.edges)) < p).astype(np.uint8)
    # In the undirected channel, an active edge has either fundamental/anti-
    # fundamental ordering with probability 1/2.  This orientation is latent:
    # the decoder sums it out using the ternary edge variable.
    reversed_orientation = (
        rng.integers(0, 2, len(graph.edges), dtype=np.uint8)
        if orientation_mode == "undirected" else np.zeros(len(graph.edges), dtype=np.uint8)
    )
    records = []
    active_configurations = []
    for row, leaves in enumerate(graph.incident):
        active = tuple(
            "fund" if (rep == "3") == (not reversed_orientation[edge]) else "anti"
            for edge, rep in leaves if error[edge]
        )
        active_configurations.append(active)
        channel = group_fusion_distribution(group, active)
        labels, probabilities = zip(*channel.items())
        irrep = str(rng.choice(labels, p=probabilities))
        is_boundary = row in boundary_factor_rows
        records.append((0 if is_boundary else len(active) & 1,
                        irrep if (not is_boundary or measure_boundary_representation) else TRIVIAL[group]))

    observation = GeneralizedSyndrome(
        np.asarray([x[0] for x in records], dtype=np.uint8),
        tuple(x[1] for x in records),
    )
    decoder_p = min(max(p, 1e-9), 1 - 1e-9)
    # BP has factors at detector and boundary sites; matching retains only the
    # detector parity checks, so an anyon may legitimately terminate at rough.
    # Scratch message buffers are deliberately shared with the cache, hence a
    # short lock across the two decode passes for concurrent HTTP requests.
    with _DECODER_CACHE_LOCK:
        decoder = _cached_decoder(
            graph, group=group, orientation_mode=orientation_mode,
            use_irrep=True, p=decoder_p, damping=damping,
            boundary_factor_rows=boundary_factor_rows,
            measure_boundary_representation=measure_boundary_representation,
            algorithm=algorithm,
        )
        baseline_decoder = _cached_decoder(
            graph, group=group, orientation_mode=orientation_mode,
            use_irrep=False, p=decoder_p, damping=damping,
            boundary_factor_rows=boundary_factor_rows,
            measure_boundary_representation=measure_boundary_representation,
            algorithm=algorithm,
        )
        decoder.matrix = lattice_graph.check_matrix
        baseline_decoder.matrix = lattice_graph.check_matrix
        start = perf_counter()
        matching_m = observation.m[detector_rows]
        decoded = decoder.decode(observation, matching_m)
        decode_ms = 1000 * (perf_counter() - start)
        baseline = baseline_decoder.decode(observation, matching_m)
    total_ms = 1000 * (perf_counter() - total_start)
    residual = matching_m ^ (np.asarray(decoder.matrix @ decoded.correction).ravel().astype(np.uint8) & 1)

    irrep_marks = [
        {"vertex": observed_ids[row], "label": irrep, "color": COLORS[group][irrep]}
        for row, irrep in enumerate(observation.irrep)
        if irrep != TRIVIAL[group]
    ]
    marginals = decoded.bp.edge_marginals
    baseline_marginals = baseline.bp.edge_marginals
    # Matching uses w=log[P(no error)/P(error)].  The heralding evidence in
    # the error-log-odds convention is therefore ell_full-ell_m=w_m-w_full.
    error_llr_shift = baseline.edge_weights - decoded.edge_weights
    return {
        "model": {
            "group": group, "group_display": DISPLAY[group], "fusion_rule": RULES[group],
            "p": p, "lattice": lattice, "L": size, "seed": seed,
            "damping": damping,
            "algorithm": algorithm,
            "measure_boundary_representation": measure_boundary_representation,
            "boundary_m": "unmeasured (displayed as 0; marginalized in BP)",
            "backend": "cached-preallocated-numba-bp+posterior-llr-pymatching",
            "orientation_mode": orientation_mode,
            "orientation": (
                "each stored edge is oriented tail=antifundamental/-1 to head=fundamental/+1"
                if orientation_mode == "directed" else
                "each active edge independently uses stored or reversed fundamental ordering with probability 1/2"
            ),
            "boundaries": "display coordinates: open rough top/bottom; smooth left/right",
            "trivial_irrep": TRIVIAL[group], "irrep_colors": COLORS[group],
            "irrep_dimensions": IRREP_DIMENSIONS[group],
            "fusion_rules_used": _dynamic_fusion_rules(group, active_configurations),
        },
        "graph": {
            "vertices": [
                {
                    "id": vertex, "x": point.x, "y": point.y,
                    "detector": point.detector, "boundary_side": point.boundary_side,
                    # The honeycomb construction retains these virtual rough-boundary
                    # coordinates for its incidence bookkeeping.  A coordinate with
                    # no retained edge is not a physical site and must not be drawn.
                    "visible": bool(incident_edges[vertex]),
                }
                for vertex, point in enumerate(lattice_graph.vertices)
            ],
            "edges": [list(edge) for edge in lattice_graph.edges],
            "logical_edge_indices": sorted(lattice_graph.logical_edges),
            "logical_line": [{"x": point.x, "y": point.y} for point in lattice_graph.logical_line],
        },
        "observation": {
            "error_edges": np.flatnonzero(error).astype(int).tolist(),
            "m_vertices": [observed_ids[row] for row in np.flatnonzero(observation.m)],
            "irreps": list(observation.irrep), "irrep_marks": irrep_marks,
        },
        "posterior": {
            "edge_marginals": marginals.tolist(),
            "edge_weights": decoded.edge_weights.tolist(),
            "prior": decoder_p,
        },
        "m_only_baseline": {
            "edge_marginals": baseline_marginals.tolist(),
            "edge_weights": baseline.edge_weights.tolist(),
            "correction_edges": np.flatnonzero(baseline.correction).astype(int).tolist(),
            "error_llr_shift_from_irrep": error_llr_shift.tolist(),
            "mean_abs_error_llr_shift": float(np.mean(np.abs(error_llr_shift))),
            "max_abs_error_llr_shift": float(np.max(np.abs(error_llr_shift))),
            "effect_convention": "logit P(error|m,R) - logit P(error|m)",
            "bp": {
                "converged": baseline.bp.converged,
                "iterations": baseline.bp.iterations,
                "max_message_delta": baseline.bp.max_message_delta,
            },
        },
        "decoder": {
            "correction_edges": np.flatnonzero(decoded.correction).astype(int).tolist(),
            "residual_m_vertices": [detector_ids[row] for row in np.flatnonzero(residual)],
            "syndrome_faithful": bool(not np.any(residual)),
            "matching_weight": decoded.matching_weight,
            "decode_ms": decode_ms,
            "end_to_end_ms": total_ms,
            "logical_error": bool(lattice_graph.logical_parity(error ^ decoded.correction)),
            "bp": {"converged": decoded.bp.converged, "iterations": decoded.bp.iterations, "max_message_delta": decoded.bp.max_message_delta},
        },
        "quality": {"prior": _soft_metrics(np.full(len(error), decoder_p), error), "posterior": _soft_metrics(marginals, error)},
    }
