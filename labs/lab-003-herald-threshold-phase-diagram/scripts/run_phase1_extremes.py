#!/usr/bin/env python3
"""Run the Lab 003 Phase 1 q=0 and q=1 LER-versus-p scans.

This runner intentionally makes one two-panel figure per q extreme (square
and honeycomb).  It uses the frozen Lab 002 damping decoder and writes only
Lab 003-owned artifacts.
"""

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
import numpy as np
import pymatching

LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]

from herald_decoder import (
    NUMBA_AVAILABLE,
    HeraldAwareBpMatchingDecoder,
    SyndromeOnlyMatchingDecoder,
    honeycomb_graph,
    sample_observation,
    square_graph,
)


SIZES = (5, 7, 9, 11)
P_GRID = {
    "square": (0.04, 0.085, 0.13, 0.175, 0.22),
    "honeycomb": (0.10, 0.15, 0.20, 0.25, 0.30),
}


def runtime_provenance() -> dict:
    """Return the mandatory accelerated-runtime identity for every artifact."""
    import numba

    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "numba_version": numba.__version__,
        "pymatching_version": pymatching.__version__,
        "numba_available": bool(NUMBA_AVAILABLE),
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict:
    return {
        "runner": sha256(Path(__file__)),
        "lattice_model": sha256(PROJECT_ROOT / "src/herald_decoder/lattice_model.py"),
        "decoder": sha256(PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py"),
        "damping_decoder": sha256(
            PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py"
        ),
        "numba_kernels": sha256(PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py"),
    }


def require_numba_runtime() -> None:
    """Fail closed instead of silently producing an unaccelerated Lab artifact."""
    if not NUMBA_AVAILABLE:
        raise RuntimeError(
            "Lab 003 production/pilot runs require the Lab 002-compatible Numba runtime; "
            "do not invoke this file with the system python3. Use ./run_phase1_extremes.sh."
        )


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return center - radius, center + radius


def estimate_crossing(rows: list[dict], *, decoder: str) -> dict:
    """Piecewise-linear L=7/L=9 crossing, explicitly an initial diagnostic."""
    by_size = {size: [] for size in (7, 9)}
    for row in rows:
        if row["L"] in by_size and row["decoder"] == decoder:
            by_size[row["L"]].append(row)
    if any(not values for values in by_size.values()):
        return {"estimate": None, "status": "missing_curve"}
    left = sorted(by_size[7], key=lambda row: row["p"])
    right = sorted(by_size[9], key=lambda row: row["p"])
    p = np.asarray([row["p"] for row in left], dtype=float)
    delta = np.asarray(
        [a["logical_error_rate"] - b["logical_error_rate"] for a, b in zip(left, right)], dtype=float
    )
    for index in range(len(p) - 1):
        if delta[index] * delta[index + 1] < 0:
            fraction = -delta[index] / (delta[index + 1] - delta[index])
            return {
                "estimate": float(p[index] + fraction * (p[index + 1] - p[index])),
                "status": "linear_interpolation",
            }
    return {"estimate": None, "status": "not_bracketed"}


def run_extreme(
    *,
    q: float,
    seeds: tuple[int, ...],
    shots_per_seed: int,
    sizes: tuple[int, ...] = SIZES,
    p_grid: dict[str, tuple[float, ...]] = P_GRID,
) -> dict:
    rows: list[dict] = []
    for lattice, make_graph in (("square", square_graph), ("honeycomb", honeycomb_graph)):
        for size in sizes:
            graph = make_graph(size)
            for p in p_grid[lattice]:
                baseline = SyndromeOnlyMatchingDecoder(graph, p=p)
                herald = (
                    HeraldAwareBpMatchingDecoder(
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
                    if q == 1.0
                    else None
                )
                counts = {"mwpm": 0, "herald_bp_mwpm": 0}
                elapsed = {"mwpm": 0.0, "herald_bp_mwpm": 0.0}
                rescued = harmed = 0
                for seed in seeds:
                    rng = np.random.default_rng(seed + 10_000 * size + int(1_000_000 * p) + int(q))
                    for _ in range(shots_per_seed):
                        observation = sample_observation(graph, rng, p=p, q=q, p_m=0.0, p_h=0.0)
                        started = perf_counter()
                        correction, _ = baseline.decode(observation.syndrome)
                        elapsed["mwpm"] += perf_counter() - started
                        baseline_failure = bool(graph.logical_parity(observation.error ^ correction))
                        counts["mwpm"] += baseline_failure
                        if herald is not None:
                            started = perf_counter()
                            result = herald.decode(observation.syndrome, observation.herald)
                            elapsed["herald_bp_mwpm"] += perf_counter() - started
                            herald_failure = bool(graph.logical_parity(observation.error ^ result.correction))
                            counts["herald_bp_mwpm"] += herald_failure
                            rescued += baseline_failure and not herald_failure
                            harmed += herald_failure and not baseline_failure
                shots = len(seeds) * shots_per_seed
                active = ("mwpm",) if q == 0.0 else ("mwpm", "herald_bp_mwpm")
                for decoder in active:
                    low, high = wilson_interval(counts[decoder], shots)
                    rows.append(
                        {
                            "lattice": lattice,
                            "L": size,
                            "edges": len(graph.edges),
                            "detectors": len(graph.detector_vertices),
                            "q": q,
                            "p": p,
                            "decoder": decoder,
                            "shots": shots,
                            "logical_errors": counts[decoder],
                            "logical_error_rate": counts[decoder] / shots,
                            "logical_error_ci95": [low, high],
                            "mean_decode_ms": 1000 * elapsed[decoder] / shots,
                            "paired_rescued_failures": rescued if decoder == "herald_bp_mwpm" else None,
                            "paired_introduced_failures": harmed if decoder == "herald_bp_mwpm" else None,
                        }
                    )
    primary = "mwpm" if q == 0.0 else "herald_bp_mwpm"
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "q": q,
        "seeds": list(seeds),
        "shots_per_seed": shots_per_seed,
        "total_shots_per_cell": len(seeds) * shots_per_seed,
        "fixed_decoder": {
            "recurrence_mode": "damping",
            "damping": 0.25,
            "max_iterations": 40,
            "matching_projection": "posterior_llr",
        },
        "p_grid": {name: list(values) for name, values in p_grid.items()},
        "sizes": list(sizes),
        "pymatching_version": pymatching.__version__,
        "runtime": runtime_provenance(),
        "source_hashes": source_hashes(),
        "rows": rows,
        "crossings_l7_l9": {
            lattice: estimate_crossing([row for row in rows if row["lattice"] == lattice], decoder=primary)
            for lattice in p_grid
        },
        "evidence_boundary": "Initial fixed-grid finite-shot LER curves only; not an asymptotic threshold estimate.",
    }


def plot_extreme(payload: dict, destination: Path) -> None:
    q = payload["q"]
    primary = "mwpm" if q == 0.0 else "herald_bp_mwpm"
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.7), sharey=True, constrained_layout=True)
    colors = {5: "#0072B2", 7: "#E69F00", 9: "#009E73", 11: "#CC79A7", 13: "#D55E00", 15: "#56B4E9"}
    for axis, lattice in zip(axes, ("square", "honeycomb")):
        for size in payload["sizes"]:
            rows = sorted(
                (row for row in payload["rows"] if row["lattice"] == lattice and row["L"] == size and row["decoder"] == primary),
                key=lambda row: row["p"],
            )
            x = [row["p"] for row in rows]
            y = [row["logical_error_rate"] for row in rows]
            lower = [max(0.0, row["logical_error_rate"] - row["logical_error_ci95"][0]) for row in rows]
            upper = [max(0.0, row["logical_error_ci95"][1] - row["logical_error_rate"]) for row in rows]
            axis.errorbar(x, y, yerr=[lower, upper], marker="o", linewidth=1.7, capsize=2.8, color=colors[size], label=f"L={size}")
        crossing = payload["crossings_l7_l9"][lattice]
        if crossing["estimate"] is not None:
            axis.axvline(crossing["estimate"], color="#555555", linestyle="--", linewidth=1)
            axis.text(crossing["estimate"], 0.97, f"L7/L9 ≈ {crossing['estimate']:.3f}", rotation=90, va="top", ha="right", fontsize=8)
        axis.set_title(lattice)
        axis.set_xlabel("physical edge-error rate p")
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.22)
    axes[0].set_ylabel("logical error rate (LER)")
    axes[0].legend(title="code size")
    title = "Phase 1a: q=0 static-MWPM calibration" if q == 0.0 else "Phase 1b: q=1 herald-aware BP + PyMatching"
    figure.suptitle(f"{title} — {payload['total_shots_per_cell']} shots/cell")
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots-per-seed", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(SIZES))
    parser.add_argument("--square-p", type=float, nargs="+", default=list(P_GRID["square"]))
    parser.add_argument("--honeycomb-p", type=float, nargs="+", default=list(P_GRID["honeycomb"]))
    parser.add_argument(
        "--q",
        type=float,
        choices=(0.0, 1.0),
        action="append",
        help="run only the requested registered extreme; omit to run both",
    )
    parser.add_argument(
        "--output-stem",
        help="result/figure basename for a single-extreme pilot; preserves prior artifacts",
    )
    parser.add_argument("--refresh-plots", action="store_true", help="refresh figures and crossing diagnostics from existing JSON")
    parser.add_argument("--preflight", action="store_true", help="validate and print the required runtime without running a sweep")
    args = parser.parse_args()
    if args.shots_per_seed < 1 or args.seeds < 1:
        raise SystemExit("shots-per-seed and seeds must be positive")
    if any(size < 2 for size in args.sizes):
        raise SystemExit("all sizes must be at least 2")
    if any(not 0 < p < 0.5 for p in (*args.square_p, *args.honeycomb_p)):
        raise SystemExit("all p values must lie strictly between 0 and 0.5")
    sizes = tuple(dict.fromkeys(args.sizes))
    p_grid = {
        "square": tuple(sorted(set(args.square_p))),
        "honeycomb": tuple(sorted(set(args.honeycomb_p))),
    }
    extremes = tuple(args.q) if args.q else (0.0, 1.0)
    if args.output_stem and len(extremes) != 1:
        raise SystemExit("--output-stem requires exactly one --q extreme")

    def stem_for(q: float) -> str:
        if args.output_stem:
            return args.output_stem
        return "q0-calibration" if q == 0.0 else "q1-herald-scan"

    results_dir = LAB_DIR / "results"
    figures_dir = LAB_DIR / "figures"
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    require_numba_runtime()
    if args.preflight:
        print(json.dumps(runtime_provenance(), indent=2))
        return
    if args.refresh_plots:
        for q in extremes:
            stem = stem_for(q)
            result_path = results_dir / f"{stem}.json"
            payload = json.loads(result_path.read_text())
            primary = "mwpm" if q == 0.0 else "herald_bp_mwpm"
            payload["crossings_l7_l9"] = {
                lattice: estimate_crossing([row for row in payload["rows"] if row["lattice"] == lattice], decoder=primary)
                for lattice in payload["p_grid"]
            }
            result_path.write_text(json.dumps(payload, indent=2) + "\n")
            plot_extreme(payload, figures_dir / f"{stem}-ler-vs-p.png")
        return
    seeds = tuple(range(1, args.seeds + 1))
    for q in extremes:
        stem = stem_for(q)
        payload = run_extreme(
            q=q,
            seeds=seeds,
            shots_per_seed=args.shots_per_seed,
            sizes=sizes,
            p_grid=p_grid,
        )
        (results_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2) + "\n")
        plot_extreme(payload, figures_dir / f"{stem}-ler-vs-p.png")


if __name__ == "__main__":
    main()
