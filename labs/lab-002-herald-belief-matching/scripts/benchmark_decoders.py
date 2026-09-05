#!/usr/bin/env python3
"""Reproducible MWPM versus BP+MWPM benchmark for Lab 002."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from math import comb, sqrt
from pathlib import Path
from time import perf_counter

import numpy as np
import pymatching

from herald_bp_decoder import (
    HeraldBeliefMatchingDecoder,
    SyndromeOnlyMatchingDecoder,
    exact_posterior,
)
from lattice_model import LatticeGraph, honeycomb_graph, sample_observation, square_graph


DECODERS = ("mwpm", "syndrome_bp_mwpm", "herald_bp_mwpm")


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    if shots <= 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return center - radius, center + radius


def _proper_scores(probabilities: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    probabilities = np.clip(np.asarray(probabilities, dtype=float), 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    log_loss = -np.mean(truth * np.log(probabilities) + (1 - truth) * np.log(1 - probabilities))
    brier = np.mean((probabilities - truth) ** 2)
    return float(log_loss), float(brier)


def _mcnemar_exact(rescued: int, harmed: int) -> float:
    """Two-sided exact sign test on discordant paired failures."""
    discordant = rescued + harmed
    if discordant == 0:
        return 1.0
    tail = sum(comb(discordant, index) for index in range(min(rescued, harmed) + 1))
    return min(1.0, 2 * tail / (2**discordant))


def effective_physical_error(rows: list[dict]) -> list[dict]:
    """Invert each finite-size MWPM LER curve at herald-decoder LER values.

    This is an operational, decoder-relative p_eff rather than a claim about
    the latent edge density. Values outside the simulated p grid are censored.
    """
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["lattice"], row["L"])].append(row)
    estimates: list[dict] = []
    for (lattice, size), group in groups.items():
        baseline = sorted((row for row in group if row["decoder"] == "mwpm"), key=lambda row: row["p"])
        herald = sorted((row for row in group if row["decoder"] == "herald_bp_mwpm"), key=lambda row: row["p"])
        p_grid = np.asarray([row["p"] for row in baseline], dtype=float)
        # Finite-shot fluctuations can violate monotonicity; the cumulative
        # envelope makes the point-estimate inversion explicit and stable.
        ler_grid = np.maximum.accumulate([row["logical_error_rate"] for row in baseline])
        for row in herald:
            target = row["logical_error_rate"]
            if target < ler_grid[0]:
                estimate, status = None, f"below_grid:{p_grid[0]:.6g}"
            elif target > ler_grid[-1]:
                estimate, status = None, f"above_grid:{p_grid[-1]:.6g}"
            else:
                estimate = float(np.interp(target, ler_grid, p_grid))
                status = "interpolated"
            estimates.append(
                {
                    "lattice": lattice,
                    "L": size,
                    "p": row["p"],
                    "herald_logical_error_rate": target,
                    "p_eff_against_mwpm": estimate,
                    "effective_reduction": None if estimate is None else row["p"] - estimate,
                    "status": status,
                }
            )
    return estimates


def _metrics_row(
    *,
    graph: LatticeGraph,
    p: float,
    q: float,
    p_m: float,
    p_h: float,
    shots: int,
    decoder: str,
    accum: dict,
) -> dict:
    low, high = wilson_interval(accum["logical_errors"], shots)
    return {
        "lattice": graph.name,
        "L": graph.size,
        "edges": len(graph.edges),
        "detectors": len(graph.detector_vertices),
        "p": p,
        "q": q,
        "p_m": p_m,
        "p_h": p_h,
        "shots": shots,
        "decoder": decoder,
        "logical_errors": accum["logical_errors"],
        "logical_error_rate": accum["logical_errors"] / shots,
        "logical_error_ci95": [low, high],
        "mean_correction_edges": accum["correction_edges"] / shots,
        "mean_residual_density": accum["residual_density"] / shots,
        "mean_edge_log_loss": accum["edge_log_loss"] / shots,
        "mean_edge_brier": accum["edge_brier"] / shots,
        "mean_decode_ms": 1000 * accum["seconds"] / shots,
        "logical_disagreement_with_mwpm": accum["disagree_mwpm"] / shots,
        "bp_convergence_rate": None if decoder == "mwpm" else accum["bp_converged"] / shots,
        "mean_bp_iterations": None if decoder == "mwpm" else accum["bp_iterations"] / shots,
    }


def run_case(
    graph: LatticeGraph,
    *,
    p: float,
    q: float,
    p_m: float,
    p_h: float,
    shots: int,
    seed: int,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    baseline = SyndromeOnlyMatchingDecoder(graph, p=p)
    syndrome_bp = HeraldBeliefMatchingDecoder(
        graph, p=p, q=0, p_m=p_m, p_h=p_h
    )
    herald_bp = HeraldBeliefMatchingDecoder(
        graph, p=p, q=q, p_m=p_m, p_h=p_h
    )
    accum = {decoder: defaultdict(float) for decoder in DECODERS}
    paired = {
        ("syndrome_bp_mwpm", "mwpm"): defaultdict(int),
        ("herald_bp_mwpm", "syndrome_bp_mwpm"): defaultdict(int),
        ("herald_bp_mwpm", "mwpm"): defaultdict(int),
    }

    for _shot in range(shots):
        observation = sample_observation(graph, rng, p=p, q=q, p_m=p_m, p_h=p_h)
        start = perf_counter()
        mwpm_correction, _weight = baseline.decode(observation.syndrome)
        accum["mwpm"]["seconds"] += perf_counter() - start
        mwpm_logical = graph.logical_parity(mwpm_correction)

        start = perf_counter()
        syndrome_result = syndrome_bp.decode(
            observation.syndrome, np.zeros_like(observation.herald)
        )
        accum["syndrome_bp_mwpm"]["seconds"] += perf_counter() - start

        start = perf_counter()
        herald_result = herald_bp.decode(observation.syndrome, observation.herald)
        accum["herald_bp_mwpm"]["seconds"] += perf_counter() - start

        results = {
            "mwpm": (mwpm_correction, None),
            "syndrome_bp_mwpm": (syndrome_result.correction, syndrome_result.bp),
            "herald_bp_mwpm": (herald_result.correction, herald_result.bp),
        }
        soft_probabilities = {
            "mwpm": np.full(len(graph.edges), p, dtype=float),
            "syndrome_bp_mwpm": syndrome_result.bp.edge_marginals,
            "herald_bp_mwpm": herald_result.bp.edge_marginals,
        }
        failures: dict[str, bool] = {}
        for decoder, (correction, bp_result) in results.items():
            residual = observation.error ^ correction
            failed = bool(graph.logical_parity(residual))
            failures[decoder] = failed
            predicted_logical = graph.logical_parity(correction)
            accum[decoder]["logical_errors"] += failed
            accum[decoder]["correction_edges"] += int(np.sum(correction))
            accum[decoder]["residual_density"] += float(np.mean(residual))
            accum[decoder]["disagree_mwpm"] += predicted_logical != mwpm_logical
            log_loss, brier = _proper_scores(soft_probabilities[decoder], observation.error)
            accum[decoder]["edge_log_loss"] += log_loss
            accum[decoder]["edge_brier"] += brier
            if bp_result is not None:
                accum[decoder]["bp_converged"] += bp_result.converged
                accum[decoder]["bp_iterations"] += bp_result.iterations

        for (candidate, reference), counts in paired.items():
            if failures[reference] and not failures[candidate]:
                counts["rescued"] += 1
            elif failures[candidate] and not failures[reference]:
                counts["harmed"] += 1

    rows = [
        _metrics_row(
            graph=graph,
            p=p,
            q=q,
            p_m=p_m,
            p_h=p_h,
            shots=shots,
            decoder=decoder,
            accum=accum[decoder],
        )
        for decoder in DECODERS
    ]
    by_decoder = {row["decoder"]: row for row in rows}
    for (candidate, reference), counts in paired.items():
        rescued, harmed = counts["rescued"], counts["harmed"]
        by_decoder[candidate].setdefault("paired_comparisons", []).append(
            {
                "reference": reference,
                "rescued_failures": rescued,
                "introduced_failures": harmed,
                "net_logical_error_rate_delta": (harmed - rescued) / shots,
                "mcnemar_exact_p_value": _mcnemar_exact(rescued, harmed),
            }
        )
    by_decoder["mwpm"]["paired_comparisons"] = []
    return rows


def run_exact_case(
    graph: LatticeGraph,
    *,
    p: float,
    q: float,
    p_m: float,
    p_h: float,
    shots: int,
    seed: int,
) -> dict:
    rng = np.random.default_rng(seed)
    baseline = SyndromeOnlyMatchingDecoder(graph, p=p)
    herald_bp = HeraldBeliefMatchingDecoder(
        graph, p=p, q=q, p_m=p_m, p_h=p_h
    )
    errors = {"mwpm": 0, "herald_bp_mwpm": 0, "exact_logical_map": 0}
    marginal_absolute_error = 0.0
    cache: dict[tuple[bytes, bytes], tuple[np.ndarray, np.ndarray]] = {}
    for _shot in range(shots):
        observation = sample_observation(graph, rng, p=p, q=q, p_m=p_m, p_h=p_h)
        key = (observation.syndrome.tobytes(), observation.herald.tobytes())
        if key not in cache:
            cache[key] = exact_posterior(
                graph,
                observation.syndrome,
                observation.herald,
                p=p,
                q=q,
                p_m=p_m,
                p_h=p_h,
            )
        exact_edges, exact_logical = cache[key]
        bp = herald_bp.infer(observation.syndrome, observation.herald)
        marginal_absolute_error += float(np.mean(np.abs(bp.edge_marginals - exact_edges)))
        mwpm_correction, _ = baseline.decode(observation.syndrome)
        herald_correction = herald_bp.decode(observation.syndrome, observation.herald).correction
        truth = graph.logical_parity(observation.error)
        errors["mwpm"] += graph.logical_parity(mwpm_correction) != truth
        errors["herald_bp_mwpm"] += graph.logical_parity(herald_correction) != truth
        errors["exact_logical_map"] += int(np.argmax(exact_logical)) != truth
    return {
        "lattice": graph.name,
        "L": graph.size,
        "edges": len(graph.edges),
        "p": p,
        "q": q,
        "p_m": p_m,
        "p_h": p_h,
        "shots": shots,
        "logical_error_rate": {name: count / shots for name, count in errors.items()},
        "mean_bp_edge_marginal_absolute_error": marginal_absolute_error / shots,
        "unique_observations_enumerated": len(cache),
    }


def markdown_report(payload: dict) -> str:
    lines = [
        "# BP + PyMatching benchmark",
        "",
        f"Generated `{payload['generated_at']}` with PyMatching `{payload['pymatching_version']}` and seed `{payload['seed']}`.",
        "",
        "`mwpm` is static-prior syndrome-only PyMatching. `syndrome_bp_mwpm` applies BP without herald factors, while `herald_bp_mwpm` includes the fusion-remnant herald likelihood before calling PyMatching. Matching itself is never reimplemented. Edge log loss and Brier score evaluate the soft posterior against simulator truth; logical error is the primary decoder outcome.",
        "",
        "| Lattice | L | p | q | Decoder | Logical error rate | 95% CI | Disagree with MWPM | Mean ms/shot | BP convergence |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        low, high = row["logical_error_ci95"]
        convergence = "—" if row["bp_convergence_rate"] is None else f"{row['bp_convergence_rate']:.1%}"
        lines.append(
            f"| {row['lattice']} | {row['L']} | {row['p']:.3f} | {row['q']:.2f} | {row['decoder']} | "
            f"{row['logical_error_rate']:.4f} | [{low:.4f}, {high:.4f}] | "
            f"{row['logical_disagreement_with_mwpm']:.4f} | {row['mean_decode_ms']:.3f} | {convergence} |"
        )
    lines.extend(["", "## Small-graph exact posterior checks", ""])
    for row in payload["exact_rows"]:
        rates = row["logical_error_rate"]
        lines.append(
            f"- {row['lattice']} L={row['L']} ({row['edges']} edges, {row['shots']} shots): "
            f"MWPM={rates['mwpm']:.4f}, herald BP+MWPM={rates['herald_bp_mwpm']:.4f}, "
            f"exact logical MAP={rates['exact_logical_map']:.4f}; mean BP edge-marginal MAE="
            f"{row['mean_bp_edge_marginal_absolute_error']:.4g}."
        )
    lines.extend(
        [
            "",
            "## Paired attribution",
            "",
        ]
    )
    for row in payload["rows"]:
        for comparison in row["paired_comparisons"]:
            lines.append(
                f"- {row['lattice']} L={row['L']} p={row['p']:.3f}: {row['decoder']} versus "
                f"{comparison['reference']} rescued {comparison['rescued_failures']} failures and introduced "
                f"{comparison['introduced_failures']} (paired LER delta "
                f"{comparison['net_logical_error_rate_delta']:+.4f}, exact McNemar "
                f"p={comparison['mcnemar_exact_p_value']:.4g})."
            )
    lines.extend(
        [
            "",
            "These are finite-shot implementation benchmarks, not a threshold estimate. The exact oracle is restricted to tiny graphs and predicts the logical class, so it is the accuracy reference rather than another scalable decoder.",
            "",
        ]
    )
    lines.extend(["", "## Operational effective physical error", ""])
    for row in payload["effective_physical_error"]:
        if row["p_eff_against_mwpm"] is None:
            value = row["status"].replace("below_grid:", "< ").replace("above_grid:", "> ")
        else:
            value = f"{row['p_eff_against_mwpm']:.4f} (reduction {row['effective_reduction']:.4f})"
        lines.append(
            f"- {row['lattice']} L={row['L']} at p={row['p']:.3f}: p_eff {value}."
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=500)
    parser.add_argument("--exact-shots", type=int, default=250)
    parser.add_argument("--sizes", type=int, nargs="+", default=[5, 9])
    parser.add_argument("--p", type=float, nargs="+", default=[0.06, 0.10])
    parser.add_argument("--q", type=float, default=0.75)
    parser.add_argument("--p-m", type=float, default=0.0)
    parser.add_argument("--p-h", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1001)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "results" / "bp-matching-benchmark.json")
    args = parser.parse_args()
    if args.shots < 1 or args.exact_shots < 1:
        parser.error("shot counts must be positive")

    rows: list[dict] = []
    case = 0
    for lattice_name, builder in (("square", square_graph), ("honeycomb", honeycomb_graph)):
        for size in args.sizes:
            graph = builder(size)
            for p in args.p:
                rows.extend(
                    run_case(
                        graph,
                        p=p,
                        q=args.q,
                        p_m=args.p_m,
                        p_h=args.p_h,
                        shots=args.shots,
                        seed=args.seed + case,
                    )
                )
                case += 1
                print(f"finished {lattice_name} L={size} p={p:.3f}", flush=True)

    exact_rows = [
        run_exact_case(
            graph,
            p=args.p[-1],
            q=args.q,
            p_m=args.p_m,
            p_h=args.p_h,
            shots=args.exact_shots,
            seed=args.seed + 10_000 + index,
        )
        for index, graph in enumerate((square_graph(3), honeycomb_graph(2)))
    ]
    payload = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "pymatching_version": pymatching.__version__,
        "matching_projection": "posterior_llr",
        "rows": rows,
        "effective_physical_error": effective_physical_error(rows),
        "exact_rows": exact_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(markdown_report(payload))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
