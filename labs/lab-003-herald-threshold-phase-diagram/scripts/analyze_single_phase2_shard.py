#!/usr/bin/env python3
"""Render one immutable Phase 2 shard and diagnose adjacent-size crossings."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def crossing(rows: list[dict], smaller: int, larger: int) -> dict:
    curves = {
        size: {float(row["p"]): float(row["logical_error_rate"]) for row in rows if int(row["L"]) == size}
        for size in (smaller, larger)
    }
    points = sorted(set(curves[smaller]) & set(curves[larger]))
    deltas = [(p, curves[smaller][p] - curves[larger][p]) for p in points]
    estimates = []
    for (left_p, left), (right_p, right) in zip(deltas, deltas[1:]):
        if left > 0 and right < 0:
            estimates.append(left_p - left * (right_p - left_p) / (right - left))
    if estimates:
        return {"sizes": [smaller, larger], "status": "linear_interpolation", "estimate": estimates[0], "all_sign_changes": estimates}
    trend = "larger_size_lower_LER" if all(delta > 0 for _, delta in deltas) else "larger_size_higher_LER" if all(delta < 0 for _, delta in deltas) else "nonmonotone_or_unresolved"
    return {"sizes": [smaller, larger], "status": "not_bracketed", "estimate": None, "observed_trend": trend}


def bootstrap_adjacent_pair(
    per_seed: list[dict],
    *,
    smaller: int,
    larger: int,
    replicates: int,
    seed: int,
) -> dict:
    """Resample seed clusters independently within size, preserving each p trajectory."""
    p_grid = sorted({float(row["p"]) for row in per_seed if int(row["L"]) in (smaller, larger)})
    seed_ids = {
        size: sorted({int(row["seed"]) for row in per_seed if int(row["L"]) == size})
        for size in (smaller, larger)
    }
    shots = {
        size: int(next(row["shots"] for row in per_seed if int(row["L"]) == size))
        for size in (smaller, larger)
    }
    errors = {
        size: np.asarray([
            [
                next(
                    int(row["logical_errors"])
                    for row in per_seed
                    if int(row["L"]) == size
                    and int(row["seed"]) == seed_id
                    and float(row["p"]) == p
                )
                for p in p_grid
            ]
            for seed_id in seed_ids[size]
        ], dtype=float)
        for size in (smaller, larger)
    }
    rng = np.random.default_rng(seed)
    delta_samples = np.empty((replicates, len(p_grid)), dtype=float)
    directed_estimates: list[float] = []
    larger_lower_all = 0
    larger_higher_all = 0
    directed_replicates = 0
    for replicate in range(replicates):
        rates = {}
        for size in (smaller, larger):
            draw = rng.integers(0, len(seed_ids[size]), size=len(seed_ids[size]))
            rates[size] = errors[size][draw].sum(axis=0) / (len(draw) * shots[size])
        deltas = rates[smaller] - rates[larger]
        delta_samples[replicate] = deltas
        larger_lower_all += int(np.all(deltas > 0))
        larger_higher_all += int(np.all(deltas < 0))
        estimates = []
        for (left_p, left), (right_p, right) in zip(zip(p_grid, deltas), zip(p_grid[1:], deltas[1:])):
            if left > 0 and right < 0:
                estimates.append(float(left_p - left * (right_p - left_p) / (right - left)))
        if estimates:
            directed_replicates += 1
            directed_estimates.extend(estimates)
    delta_intervals = []
    for index, p in enumerate(p_grid):
        samples = delta_samples[:, index]
        delta_intervals.append({
            "p": p,
            "interval95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
            "probability_larger_size_lower_LER": float(np.mean(samples > 0)),
        })
    return {
        "replicates": replicates,
        "seed": seed,
        "cluster_policy": "resample seed trajectories independently within each size and preserve all p values in a selected trajectory",
        "larger_size_lower_at_every_p_fraction": larger_lower_all / replicates,
        "larger_size_higher_at_every_p_fraction": larger_higher_all / replicates,
        "one_or_more_directed_crossings_fraction": directed_replicates / replicates,
        "directed_crossing_estimate_interval95": (
            [float(np.quantile(directed_estimates, 0.025)), float(np.quantile(directed_estimates, 0.975))]
            if directed_estimates else None
        ),
        "delta_LER_smaller_minus_larger": delta_intervals,
    }


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-figure", type=Path, required=True)
    parser.add_argument("--endpoint-input", type=Path)
    parser.add_argument("--bootstrap-replicates", type=int, default=10000)
    parser.add_argument("--bootstrap-seed", type=int, default=531999)
    parser.add_argument(
        "--ler-only",
        action="store_true",
        help="render a report-friendly LER panel without BP convergence metadata",
    )
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    decoder = payload.get("decoder", {})
    q = float(payload.get("q"))
    if payload.get("lattice") != "honeycomb" or not 0.0 <= q <= 1.0:
        raise SystemExit("this focused analyzer accepts one honeycomb q in [0, 1]")
    if decoder.get("matching_projection") != "posterior_llr":
        raise SystemExit("posterior-LLR matching provenance is required")
    rows = payload["summaries"]
    endpoint_rows: list[dict] = []
    if args.endpoint_input is not None:
        endpoints = json.loads(args.endpoint_input.read_text())
        if endpoints.get("lattice") != "honeycomb" or float(endpoints.get("q")) != q:
            raise SystemExit("endpoint artifact must match the honeycomb shard q")
        endpoint_rows = endpoints.get("summaries", [])
        if {float(row["p"]) for row in endpoint_rows} != {0.0, 1.0}:
            raise SystemExit("endpoint artifact must contain exactly p=0 and p=1")
    sizes = sorted({int(row["L"]) for row in rows})
    if len(sizes) < 2:
        raise SystemExit("at least two sizes are required")
    diagnostics = []
    for pair_index, (left, right) in enumerate(zip(sizes, sizes[1:])):
        diagnostic = crossing(rows, left, right)
        diagnostic["seed_cluster_bootstrap"] = bootstrap_adjacent_pair(
            payload["per_seed"],
            smaller=left,
            larger=right,
            replicates=args.bootstrap_replicates,
            seed=args.bootstrap_seed + pair_index,
        )
        diagnostics.append(diagnostic)
    estimates = [item["estimate"] for item in diagnostics if item["estimate"] is not None]
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_artifact": str(args.input),
        "source_config_sha256": payload["config_sha256"],
        "lattice": "honeycomb",
        "q": q,
        "decoder": decoder,
        "sizes": sizes,
        "shots_per_cell": payload["total_shots_per_cell"],
        "source_raw_sha256": payload["raw_records"]["sha256"],
        "endpoint_source_artifact": str(args.endpoint_input) if args.endpoint_input else None,
        "endpoint_rows": endpoint_rows,
        "syndrome_fidelity": payload.get("syndrome_fidelity"),
        "adjacent_crossings": diagnostics,
        "finite_size_interpretation": "crossings_observed_with_size_drift" if estimates else "no_directed_crossing_bracketed",
        "threshold_statement": "This is a decoder-specific finite-size crossing diagnostic. It is not an asymptotic threshold estimate; N0 showed residual BP nonconvergence at large sizes.",
    }
    atomic_json(args.output_json, result)

    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]
    if args.ler_only:
        figure, ler_axis = plt.subplots(1, 1, figsize=(7.2, 5.2), constrained_layout=True)
        convergence_axis = None
    else:
        figure, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), constrained_layout=True)
        ler_axis, convergence_axis = axes
    all_p = sorted({float(row["p"]) for row in rows} | {float(row["p"]) for row in endpoint_rows})
    p_span = all_p[-1] - all_p[0]
    p_margin = max(0.01, 0.08 * p_span)
    x_limits = (max(0.0, all_p[0] - p_margin), min(1.0, all_p[-1] + p_margin))
    largest_ler_upper = max(float(row["logical_error_ci95"][1]) for row in rows)
    ler_upper = min(0.57, max(0.03, 1.2 * largest_ler_upper))
    for color, size in zip(colors, sizes):
        curve = sorted((row for row in rows if int(row["L"]) == size), key=lambda row: float(row["p"]))
        x = np.array([row["p"] for row in curve])
        ler = np.array([row["logical_error_rate"] for row in curve])
        ci = np.array([row["logical_error_ci95"] for row in curve])
        conv = np.array([row["bp_convergence_rate"] for row in curve])
        ler_axis.errorbar(x, ler, yerr=[np.maximum(0.0, ler - ci[:, 0]), np.maximum(0.0, ci[:, 1] - ler)], color=color, marker="o", capsize=2.5, linewidth=1.6, label=f"L={size}")
        if convergence_axis is not None:
            convergence_axis.plot(x, conv, color=color, marker="o", linewidth=1.6, label=f"L={size}")
        endpoint_curve = sorted((row for row in endpoint_rows if int(row["L"]) == size), key=lambda row: float(row["p"]))
        if endpoint_curve:
            ler_axis.plot(
                [row["p"] for row in endpoint_curve],
                [row["logical_error_rate"] for row in endpoint_curve],
                color=color,
                marker="s",
                markersize=5,
                linestyle="none",
                markerfacecolor="white",
                markeredgewidth=1.4,
            )
    for item in diagnostics:
        if item["estimate"] is not None:
            ler_axis.axvline(item["estimate"], color="#555555", linestyle="--", linewidth=1.0)
    ler_axis.set(title=f"q={q:g} honeycomb LER", xlabel="physical edge-error rate p", ylabel="logical error rate", xlim=x_limits, ylim=(-0.02 * ler_upper, ler_upper))
    ler_axis.grid(alpha=0.24)
    ler_axis.legend(title="size")
    if convergence_axis is not None:
        convergence_axis.set(title="BP convergence metadata", xlabel="physical edge-error rate p", ylabel="converged fraction", xlim=x_limits, ylim=(-0.03, 1.03))
        convergence_axis.grid(alpha=0.24)
        convergence_axis.legend(title="size")
    endpoint_note = "; open squares: deterministic endpoints" if endpoint_rows else ""
    if args.ler_only:
        figure.suptitle(
            f"Honeycomb q={q:g} LER — residual-priority-80, "
            f"{payload['total_shots_per_cell']} shots/cell{endpoint_note}"
        )
    else:
        figure.suptitle(
            "Residual-priority-80 damping BP + posterior-LLR PyMatching — "
            f"{payload['total_shots_per_cell']} shots/cell{endpoint_note}"
        )
    args.output_figure.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output_figure, dpi=200)
    plt.close(figure)


if __name__ == "__main__":
    main()
