#!/usr/bin/env python3
"""Registered square-lattice Phase 1a q=0 MWPM calibration."""

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

from herald_decoder import NUMBA_AVAILABLE, SyndromeOnlyMatchingDecoder, square_graph


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
SIZES = (5, 7, 9, 11)
P_GRID = (0.09, 0.10, 0.105, 0.11, 0.115, 0.12, 0.125, 0.13, 0.135, 0.14, 0.15)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return center - radius, center + radius


def interpolated_crossing(rows: list[dict], lower_size: int, upper_size: int) -> float | None:
    lower = {row["p"]: row["logical_error_rate"] for row in rows if row["L"] == lower_size}
    upper = {row["p"]: row["logical_error_rate"] for row in rows if row["L"] == upper_size}
    p_values = sorted(set(lower) & set(upper))
    deltas = [lower[p] - upper[p] for p in p_values]
    for index, (left, right) in enumerate(zip(deltas, deltas[1:])):
        if left == 0:
            return p_values[index]
        if left * right < 0:
            fraction = -left / (right - left)
            return p_values[index] + fraction * (p_values[index + 1] - p_values[index])
    return None


def run(*, seeds: tuple[int, ...], shots_per_seed: int) -> dict:
    raw_shots: list[dict] = []
    summaries: list[dict] = []
    for size in SIZES:
        graph = square_graph(size)
        decoders = {p: SyndromeOnlyMatchingDecoder(graph, p=p) for p in P_GRID}
        counts = {p: 0 for p in P_GRID}
        elapsed = {p: 0.0 for p in P_GRID}
        for seed in seeds:
            rng = np.random.default_rng(seed + 100_003 * size)
            for shot in range(shots_per_seed):
                # Thresholding the same uniforms at every p yields nested,
                # correctly distributed Bernoulli error fields.
                uniforms = rng.random(len(graph.edges))
                for p in P_GRID:
                    error = (uniforms < p).astype(np.uint8)
                    syndrome = graph.true_syndrome(error)
                    started = perf_counter()
                    correction, matching_weight = decoders[p].decode(syndrome)
                    decode_ms = 1000 * (perf_counter() - started)
                    logical_failure = bool(graph.logical_parity(error ^ correction))
                    counts[p] += logical_failure
                    elapsed[p] += decode_ms
                    raw_shots.append({
                        "lattice": "square", "L": size, "p": p, "q": 0.0,
                        "decoder": "static_mwpm", "seed": seed, "shot": shot,
                        "observation_id": f"square-L{size}-seed{seed}-shot{shot}",
                        "logical_failure": logical_failure,
                        "matching_weight": matching_weight, "decode_ms": decode_ms,
                        "bp_converged": None, "bp_iterations": None,
                    })
        total_shots = len(seeds) * shots_per_seed
        for p in P_GRID:
            low, high = wilson_interval(counts[p], total_shots)
            summaries.append({
                "lattice": "square", "L": size, "edges": len(graph.edges),
                "detectors": len(graph.detector_vertices), "p": p, "q": 0.0,
                "decoder": "static_mwpm", "shots": total_shots,
                "logical_errors": counts[p], "logical_error_rate": counts[p] / total_shots,
                "logical_error_ci95": [low, high], "mean_decode_ms": elapsed[p] / total_shots,
            })
    crossings = {
        f"L{left}-L{right}": interpolated_crossing(summaries, left, right)
        for left, right in zip(SIZES, SIZES[1:])
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "Lab 003 Phase 1a q=0 square static-MWPM calibration",
        "lattice": "square", "q": 0.0, "p_grid": list(P_GRID), "sizes": list(SIZES),
        "seeds": list(seeds), "shots_per_seed": shots_per_seed,
        "total_shots_per_cell": len(seeds) * shots_per_seed,
        "sampling": {
            "nested_common_random_numbers": True,
            "master_rng": "numpy.default_rng(seed + 100003 * L)",
            "error_rule": "x_e(p) = 1[u_e < p]",
            "measurement_noise": {"p_m": 0.0, "p_h": 0.0},
        },
        "decoder": {
            "name": "SyndromeOnlyMatchingDecoder",
            "backend": "pymatching.Matching.from_check_matrix",
            "edge_weight": "log((1-p)/p)", "use_virtual_boundary_node": True,
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
        },
        "raw_shots": raw_shots,
        "summaries": summaries,
        "adjacent_size_crossings": {
            key: {"estimate": estimate, "method": "piecewise_linear_LER_intersection" if estimate is not None else "not_bracketed"}
            for key, estimate in crossings.items()
        },
        "evidence_boundary": "First-wave finite-size operational crossing diagnostics only; not an asymptotic threshold or thermodynamic phase transition.",
    }


def plot(payload: dict, destination: Path) -> None:
    colors = {5: "#0072B2", 7: "#E69F00", 9: "#009E73", 11: "#CC79A7"}
    figure, axis = plt.subplots(figsize=(7.6, 5.1), constrained_layout=True)
    for size in SIZES:
        rows = sorted((row for row in payload["summaries"] if row["L"] == size), key=lambda row: row["p"])
        p = [row["p"] for row in rows]
        ler = [row["logical_error_rate"] for row in rows]
        low = [rate - row["logical_error_ci95"][0] for rate, row in zip(ler, rows)]
        high = [row["logical_error_ci95"][1] - rate for rate, row in zip(ler, rows)]
        axis.errorbar(p, ler, yerr=[low, high], marker="o", linewidth=1.8, capsize=2.8, color=colors[size], label=f"L={size}")
    crossing_values = [
        value["estimate"]
        for value in payload["adjacent_size_crossings"].values()
        if value["estimate"] is not None
    ]
    if crossing_values:
        axis.axvspan(min(crossing_values), max(crossing_values), color="#777777", alpha=0.12, label="adjacent-size crossing span")
    for value in crossing_values:
        axis.axvline(value, color="#555555", linestyle="--", linewidth=0.9, alpha=0.72)
    maximum_rate = max(row["logical_error_ci95"][1] for row in payload["summaries"])
    axis.set(
        title=f"Square q=0 static-MWPM refined crossing — {payload['total_shots_per_cell']} shots/cell",
        xlabel="physical edge-error rate p",
        ylabel="logical error rate (LER)",
        ylim=(0, min(1.0, maximum_rate + 0.04)),
    )
    axis.grid(alpha=0.22)
    axis.legend(title="code size")
    crossing_text = "\n".join(
        f"{name}: {value['estimate']:.4f}"
        for name, value in payload["adjacent_size_crossings"].items()
        if value["estimate"] is not None
    )
    axis.text(
        0.985,
        0.03,
        crossing_text,
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9},
    )
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots-per-seed", type=int, default=1000)
    parser.add_argument("--seeds", type=int, nargs="+", default=(310001, 310002, 310003, 310004, 310005))
    parser.add_argument("--stem", default="q0-square-refined-5000-2026-08-27")
    parser.add_argument("--refresh-plot", action="store_true")
    args = parser.parse_args()
    if args.shots_per_seed < 1 or not args.seeds:
        raise SystemExit("shots-per-seed and seeds must be positive")
    if not NUMBA_AVAILABLE:
        raise SystemExit("accelerated Lab runtime is required; run through ./run_research_python.sh")
    results = LAB_DIR / "results" / f"{args.stem}.json"
    figure = LAB_DIR / "figures" / f"{args.stem}-ler-vs-p.png"
    if args.refresh_plot:
        payload = json.loads(results.read_text())
        payload["source_hashes"]["figure_renderer"] = sha256(Path(__file__))
        results.write_text(json.dumps(payload, indent=2) + "\n")
        plot(payload, figure)
        print(json.dumps({"result": str(results), "figure": str(figure), "crossings": payload["adjacent_size_crossings"]}, indent=2))
        return
    payload = run(seeds=tuple(args.seeds), shots_per_seed=args.shots_per_seed)
    results.write_text(json.dumps(payload, indent=2) + "\n")
    plot(payload, figure)
    print(json.dumps({"result": str(results), "figure": str(figure), "crossings": payload["adjacent_size_crossings"]}, indent=2))


if __name__ == "__main__":
    main()
