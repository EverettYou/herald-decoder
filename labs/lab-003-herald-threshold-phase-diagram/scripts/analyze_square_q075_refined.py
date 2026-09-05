#!/usr/bin/env python3
"""Analyze the refined square q=3/4 LER scan and estimate directed crossings."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
STEMS = (
    "q075-square-l11-l13-refined-low-5000-2026-08-27",
    "q075-square-l11-l13-refined-5000-2026-08-27",
)
BOOTSTRAP_REPLICATES = 20_000


def directed_crossings(p_values: list[float], lower: np.ndarray, upper: np.ndarray) -> list[float]:
    delta = lower - upper
    estimates: list[float] = []
    for index, (left, right) in enumerate(zip(delta, delta[1:])):
        if left > 0 and right < 0:
            estimates.append(float(p_values[index] + left * (p_values[index + 1] - p_values[index]) / (left - right)))
        elif left == 0 and right < 0:
            estimates.append(float(p_values[index]))
    return estimates


def main() -> None:
    sources = [LAB_DIR / "results" / f"{stem}.json" for stem in STEMS]
    payloads = [json.loads(source.read_text()) for source in sources]
    reference = payloads[0]
    for payload in payloads:
        if payload.get("lattice") != "square" or float(payload.get("q")) != 0.75:
            raise SystemExit("expected square q=0.75 artifacts")
        if payload.get("decoder", {}).get("matching_projection") != "posterior_llr":
            raise SystemExit("posterior-LLR matching provenance is required")
        if payload.get("total_shots_per_cell") != reference.get("total_shots_per_cell"):
            raise SystemExit("source shot designs do not match")
    sizes = sorted({int(size) for payload in payloads for size in payload["sizes"]})
    p_values = sorted({float(value) for payload in payloads for value in payload["p_grid"]})
    summaries = [row for payload in payloads for row in payload["summaries"]]
    per_seed = [row for payload in payloads for row in payload["per_seed"]]
    rates = {
        size: np.asarray([next(row["logical_error_rate"] for row in summaries if int(row["L"]) == size and float(row["p"]) == p) for p in p_values])
        for size in sizes
    }
    point = {
        f"L{left}_L{right}": directed_crossings(p_values, rates[left], rates[right])
        for left, right in zip(sizes, sizes[1:])
    }
    seeds = sorted({int(row["seed"]) for row in per_seed})
    seed_counts = {
        (int(row["seed"]), int(row["L"]), float(row["p"])): (int(row["logical_errors"]), int(row["shots"]))
        for row in per_seed
    }
    rng = np.random.default_rng(750001)
    bootstrap = {key: {"single": [], "none": 0, "multiple": 0} for key in point}
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = {
            size: rng.choice(seeds, size=len(seeds), replace=True)
            for size in sizes
        }
        sampled_rates = {}
        for size in sizes:
            values = []
            for p in p_values:
                errors = sum(seed_counts[(int(seed), size, p)][0] for seed in sampled[size])
                shots = sum(seed_counts[(int(seed), size, p)][1] for seed in sampled[size])
                values.append(errors / shots)
            sampled_rates[size] = np.asarray(values)
        for left, right in zip(sizes, sizes[1:]):
            key = f"L{left}_L{right}"
            estimates = directed_crossings(p_values, sampled_rates[left], sampled_rates[right])
            if len(estimates) == 1:
                bootstrap[key]["single"].append(estimates[0])
            elif estimates:
                bootstrap[key]["multiple"] += 1
            else:
                bootstrap[key]["none"] += 1
    crossings = {}
    for left, right in zip(sizes, sizes[1:]):
        key = f"L{left}_L{right}"
        single = bootstrap[key]["single"]
        quantiles = np.quantile(single, [0.025, 0.5, 0.975]).tolist() if single else [None, None, None]
        crossings[key] = {
            "sizes": [left, right],
            "point_directed_crossings": point[key],
            "point_status": "single" if len(point[key]) == 1 else "multiple" if point[key] else "not_bracketed",
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": 750001,
                "single_crossing_replicates": len(single),
                "no_crossing_replicates": bootstrap[key]["none"],
                "multiple_crossing_replicates": bootstrap[key]["multiple"],
                "single_crossing_fraction": len(single) / BOOTSTRAP_REPLICATES,
                "conditional_quantiles": {"q025": quantiles[0], "median": quantiles[1], "q975": quantiles[2]},
            },
        }
    analysis = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_artifacts": [str(source) for source in sources],
        "lattice": "square",
        "q": 0.75,
        "decoder": reference["decoder"],
        "sizes": sizes,
        "p_grid": p_values,
        "shots_per_cell": reference["total_shots_per_cell"],
        "total_decoder_observations": len(sizes) * len(p_values) * reference["total_shots_per_cell"],
        "adjacent_crossings": crossings,
        "convergence": {
            f"L{size}": {
                "minimum_rate": min(row["bp_convergence_rate"] for row in summaries if int(row["L"]) == size),
                "maximum_rate": max(row["bp_convergence_rate"] for row in summaries if int(row["L"]) == size),
            }
            for size in sizes
        },
        "evidence_boundary": "Finite-size q=0.75 operational crossing diagnostic for the fixed 40-iteration posterior-LLR damping decoder; bootstrap uncertainty does not establish an asymptotic threshold.",
    }
    output_stem = "q075-square-l11-l13-refined-5000-2026-08-27"
    analysis_path = LAB_DIR / "results" / f"{output_stem}-analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2) + "\n")

    figure, (axis, convergence_axis) = plt.subplots(2, 1, figsize=(9.0, 7.1), gridspec_kw={"height_ratios": [3.2, 1]}, sharex=True, constrained_layout=True)
    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]
    for color, size in zip(colors, sizes):
        rows = sorted((row for row in summaries if int(row["L"]) == size), key=lambda row: float(row["p"]))
        x = np.asarray([row["p"] for row in rows])
        y = np.asarray([row["logical_error_rate"] for row in rows])
        ci = np.asarray([row["logical_error_ci95"] for row in rows])
        axis.errorbar(x, y, yerr=[np.maximum(0, y - ci[:, 0]), np.maximum(0, ci[:, 1] - y)], marker="o", markersize=3.7, linewidth=1.6, capsize=2.2, color=color, label=f"L={size}")
        convergence_axis.plot(x, [row["bp_convergence_rate"] for row in rows], marker="o", markersize=2.8, linewidth=1.2, color=color, label=f"L={size}")
    labels = []
    for key, item in crossings.items():
        estimates = item["point_directed_crossings"]
        labels.append(f"{key.replace('_', '/')}: " + (f"{estimates[0]:.4f}" if len(estimates) == 1 else f"{len(estimates)} crossings" if estimates else "none"))
        for estimate in estimates:
            axis.axvline(estimate, color="#555555", linestyle="--", linewidth=1.0, alpha=0.85)
    axis.text(0.012, 0.975, "\n".join(labels), transform=axis.transAxes, ha="left", va="top", fontsize=8.3, bbox={"facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9})
    axis.set_title(f"Square q=3/4 refined LER scan — {reference['total_shots_per_cell']} shots/cell")
    axis.set_ylabel("logical error rate (LER)")
    axis.grid(alpha=0.22)
    axis.legend(title="code size", ncol=3, loc="lower right")
    convergence_axis.set(xlabel="physical edge-error rate p", ylabel="BP converged", ylim=(-0.01, 1.02))
    convergence_axis.grid(alpha=0.22)
    convergence_axis.legend(title="code size", ncol=3, loc="upper left")
    figure_path = LAB_DIR / "figures" / f"{output_stem}-ler-vs-p.png"
    figure.savefig(figure_path, dpi=180)
    plt.close(figure)
    print(json.dumps({"analysis": str(analysis_path), "figure": str(figure_path), "crossings": crossings}, indent=2))


if __name__ == "__main__":
    main()
