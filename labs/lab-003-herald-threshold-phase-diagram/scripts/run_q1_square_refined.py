#!/usr/bin/env python3
"""Refined square q=1 confirmation scan for the largest discovery sizes."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numba
import numpy as np
import pymatching

from herald_decoder import (
    NUMBA_AVAILABLE,
    HeraldAwareBpMatchingDecoder,
    SyndromeOnlyMatchingDecoder,
    square_graph,
)


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
SIZES = (11, 13)
P_GRID = tuple(round(value, 2) for value in np.arange(0.20, 0.321, 0.01))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return center - radius, center + radius


def directed_crossing(summaries: list[dict]) -> dict:
    lower = {row["p"]: row["logical_error_rate"] for row in summaries if row["L"] == 11}
    upper = {row["p"]: row["logical_error_rate"] for row in summaries if row["L"] == 13}
    p_values = sorted(set(lower) & set(upper))
    # Positive delta means the larger distance is better.  A physical
    # threshold crossing changes from positive to negative as p increases.
    deltas = [lower[p] - upper[p] for p in p_values]
    changes: list[float] = []
    for index, (left, right) in enumerate(zip(deltas, deltas[1:])):
        if left > 0 and right < 0:
            fraction = left / (left - right)
            changes.append(p_values[index] + fraction * (p_values[index + 1] - p_values[index]))
        elif left == 0 and right < 0:
            changes.append(p_values[index])
    if len(changes) == 1:
        return {"estimate": changes[0], "status": "directed_linear_interpolation", "all_directed_sign_changes": changes}
    if changes:
        return {"estimate": None, "status": "multiple_directed_crossings", "all_directed_sign_changes": changes}
    trend = "larger_distance_lower_ler" if all(delta >= 0 for delta in deltas) else "larger_distance_higher_ler" if all(delta <= 0 for delta in deltas) else "mixed_without_directed_bracket"
    return {"estimate": None, "status": "not_bracketed", "observed_trend": trend, "all_directed_sign_changes": []}


def run(*, seeds: tuple[int, ...], shots_per_seed: int) -> dict:
    raw_shots: list[dict] = []
    summaries: list[dict] = []
    for size in SIZES:
        graph = square_graph(size)
        baseline_decoders = {p: SyndromeOnlyMatchingDecoder(graph, p=p) for p in P_GRID}
        herald_decoders = {
            p: HeraldAwareBpMatchingDecoder(
                graph,
                p=p,
                q=1.0,
                p_m=0.0,
                p_h=0.0,
                recurrence_mode="damping",
                damping=0.25,
                max_iterations=40,
                use_numba=True,
            )
            for p in P_GRID
        }
        counts = {p: {"herald": 0, "mwpm": 0, "converged": 0} for p in P_GRID}
        elapsed = {p: {"herald": 0.0, "mwpm": 0.0} for p in P_GRID}
        iteration_total = {p: 0 for p in P_GRID}
        for seed in seeds:
            rng = np.random.default_rng(seed + 100_003 * size)
            for shot in range(shots_per_seed):
                uniforms = rng.random(len(graph.edges))
                for p in P_GRID:
                    error = (uniforms < p).astype(np.uint8)
                    syndrome = graph.true_syndrome(error)
                    detector_degrees = graph.degrees(error)[list(graph.detector_vertices)]
                    herald = (detector_degrees >= 2).astype(np.uint8)

                    started = perf_counter()
                    baseline_correction, baseline_weight = baseline_decoders[p].decode(syndrome)
                    baseline_ms = 1000 * (perf_counter() - started)
                    baseline_failure = bool(graph.logical_parity(error ^ baseline_correction))

                    started = perf_counter()
                    result = herald_decoders[p].decode(syndrome, herald)
                    herald_ms = 1000 * (perf_counter() - started)
                    herald_failure = bool(graph.logical_parity(error ^ result.correction))

                    counts[p]["mwpm"] += baseline_failure
                    counts[p]["herald"] += herald_failure
                    counts[p]["converged"] += result.bp.converged
                    elapsed[p]["mwpm"] += baseline_ms
                    elapsed[p]["herald"] += herald_ms
                    iteration_total[p] += result.bp.iterations
                    raw_shots.append({
                        "lattice": "square", "L": size, "p": p, "q": 1.0,
                        "seed": seed, "shot": shot,
                        "observation_id": f"square-L{size}-seed{seed}-shot{shot}",
                        "mwpm_logical_failure": baseline_failure,
                        "herald_logical_failure": herald_failure,
                        "mwpm_matching_weight": baseline_weight,
                        "herald_matching_weight": result.matching_weight,
                        "mwpm_decode_ms": baseline_ms, "herald_decode_ms": herald_ms,
                        "bp_converged": result.bp.converged,
                        "bp_iterations": result.bp.iterations,
                        "bp_max_message_delta": result.bp.max_message_delta,
                    })
        shots = len(seeds) * shots_per_seed
        for p in P_GRID:
            errors = counts[p]["herald"]
            low, high = wilson_interval(errors, shots)
            summaries.append({
                "lattice": "square", "L": size, "edges": len(graph.edges),
                "detectors": len(graph.detector_vertices), "p": p, "q": 1.0,
                "decoder": "herald_bp_mwpm", "shots": shots,
                "logical_errors": errors, "logical_error_rate": errors / shots,
                "logical_error_ci95": [low, high],
                "mwpm_logical_errors": counts[p]["mwpm"],
                "mwpm_logical_error_rate": counts[p]["mwpm"] / shots,
                "bp_converged": counts[p]["converged"],
                "bp_convergence_rate": counts[p]["converged"] / shots,
                "mean_bp_iterations": iteration_total[p] / shots,
                "mean_herald_decode_ms": elapsed[p]["herald"] / shots,
                "mean_mwpm_decode_ms": elapsed[p]["mwpm"] / shots,
            })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "Lab 003 q=1 square refined largest-size crossing scan",
        "lattice": "square", "q": 1.0,
        "sizes": list(SIZES), "p_grid": list(P_GRID),
        "seeds": list(seeds), "shots_per_seed": shots_per_seed,
        "total_shots_per_cell": len(seeds) * shots_per_seed,
        "sampling": {
            "nested_common_random_numbers": True,
            "master_rng": "numpy.default_rng(seed + 100003 * L)",
            "error_rule": "x_e(p) = 1[u_e < p]",
            "q1_herald_rule": "h_v = 1[degree_v >= 2]",
            "measurement_noise": {"p_m": 0.0, "p_h": 0.0},
        },
        "decoder": {
            "name": "HeraldAwareBpMatchingDecoder",
            "recurrence_mode": "damping", "damping": 0.25,
            "max_iterations": 40, "matching_projection": "posterior_llr",
            "backend": "pymatching.Matching.from_check_matrix",
        },
        "runtime": {
            "python_executable": sys.executable, "python_version": platform.python_version(),
            "numpy_version": np.__version__, "numba_version": numba.__version__,
            "pymatching_version": pymatching.__version__, "numba_available": bool(NUMBA_AVAILABLE),
        },
        "source_hashes": {
            "runner": sha256(Path(__file__)),
            "lattice_model": sha256(PROJECT_ROOT / "src/herald_decoder/lattice_model.py"),
            "decoder": sha256(PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py"),
            "damping_decoder": sha256(
                PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py"
            ),
            "numba_kernels": sha256(
                PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py"
            ),
        },
        "raw_shots": raw_shots,
        "summaries": summaries,
        "largest_pair_crossing": directed_crossing(summaries),
        "evidence_boundary": "Refined finite-size L=11/13 operational crossing diagnostic; not an asymptotic threshold or phase transition.",
    }


def plot(payload: dict, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.7, 5.2), constrained_layout=True)
    colors = {11: "#CC79A7", 13: "#D55E00"}
    for size in SIZES:
        rows = sorted((row for row in payload["summaries"] if row["L"] == size), key=lambda row: row["p"])
        p = [row["p"] for row in rows]
        ler = [row["logical_error_rate"] for row in rows]
        low = [rate - row["logical_error_ci95"][0] for rate, row in zip(ler, rows)]
        high = [row["logical_error_ci95"][1] - rate for rate, row in zip(ler, rows)]
        axis.errorbar(p, ler, yerr=[low, high], marker="o", linewidth=1.9, capsize=2.8, color=colors[size], label=f"L={size}")
    crossing = payload["largest_pair_crossing"]
    if crossing["estimate"] is not None:
        estimate = crossing["estimate"]
        axis.axvline(estimate, color="#555555", linestyle="--", linewidth=1.1)
        label = f"L11/L13 crossing: p={estimate:.4f}"
    else:
        label = f"L11/L13: {crossing['status']}"
    maximum = max(row["logical_error_ci95"][1] for row in payload["summaries"])
    axis.set(
        title=f"Square q=1 refined L=11/13 crossing — {payload['total_shots_per_cell']} shots/cell",
        xlabel="physical edge-error rate p", ylabel="logical error rate (LER)",
        ylim=(0, min(1.0, maximum + 0.04)),
    )
    axis.grid(alpha=0.22)
    axis.legend(title="code size")
    axis.text(0.985, 0.035, label, transform=axis.transAxes, ha="right", va="bottom", fontsize=9, bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9})
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots-per-seed", type=int, default=1000)
    parser.add_argument("--seeds", type=int, nargs="+", default=(410001, 410002, 410003, 410004, 410005))
    parser.add_argument("--stem", default="q1-square-l11-l13-refined-5000-2026-08-27")
    args = parser.parse_args()
    if args.shots_per_seed < 1 or not args.seeds:
        raise SystemExit("shots-per-seed and seeds must be positive")
    if not NUMBA_AVAILABLE:
        raise SystemExit("accelerated Lab runtime is required; use ./run_research_python.sh")
    payload = run(seeds=tuple(args.seeds), shots_per_seed=args.shots_per_seed)
    result_path = LAB_DIR / "results" / f"{args.stem}.json"
    figure_path = LAB_DIR / "figures" / f"{args.stem}-ler-vs-p.png"
    result_path.write_text(json.dumps(payload, indent=2) + "\n")
    plot(payload, figure_path)
    print(json.dumps({"result": str(result_path), "figure": str(figure_path), "crossing": payload["largest_pair_crossing"]}, indent=2))


if __name__ == "__main__":
    main()
