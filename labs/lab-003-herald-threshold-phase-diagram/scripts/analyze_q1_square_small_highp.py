#!/usr/bin/env python3
"""Analyze the 5000-shot q=1 square small-size high-p refinement."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
STEM = "q1-square-l3-l9-highp-refined-5000-2026-08-27"
SIZES = (3, 5, 7, 9)
PAIRS = tuple(zip(SIZES, SIZES[1:]))
BOOTSTRAP_REPLICATES = 20_000


def directed_crossings(p_values: list[float], lower: np.ndarray, upper: np.ndarray) -> list[float]:
    """Return positive-to-negative LER-difference sign changes."""
    delta = lower - upper
    estimates: list[float] = []
    for index, (left, right) in enumerate(zip(delta, delta[1:])):
        if left > 0 and right < 0:
            fraction = left / (left - right)
            estimates.append(p_values[index] + fraction * (p_values[index + 1] - p_values[index]))
        elif left == 0 and right < 0:
            estimates.append(p_values[index])
    return estimates


def summarize_crossings(payload: dict) -> dict:
    p_values = [float(value) for value in payload["p_grid"]]
    rows = payload["summaries"]
    rates = {
        size: np.asarray([
            next(row["logical_error_rate"] for row in rows if row["L"] == size and row["p"] == p)
            for p in p_values
        ])
        for size in SIZES
    }
    point = {
        f"L{lower}_L{upper}": directed_crossings(p_values, rates[lower], rates[upper])
        for lower, upper in PAIRS
    }

    seeds = [int(seed) for seed in payload["seeds"]]
    seed_counts: dict[tuple[int, int, float], tuple[int, int]] = {}
    for row in payload["per_seed"]:
        seed_counts[(int(row["seed"]), int(row["L"]), float(row["p"]))] = (
            int(row["logical_errors"]), int(row["shots"])
        )
    rng = np.random.default_rng(620001)
    bootstrap = {
        f"L{lower}_L{upper}": {"single": [], "none": 0, "multiple": 0}
        for lower, upper in PAIRS
    }
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(seeds, size=len(seeds), replace=True)
        sampled_rates: dict[int, np.ndarray] = {}
        for size in SIZES:
            values = []
            for p in p_values:
                errors = sum(seed_counts[(int(seed), size, p)][0] for seed in sampled)
                shots = sum(seed_counts[(int(seed), size, p)][1] for seed in sampled)
                values.append(errors / shots)
            sampled_rates[size] = np.asarray(values)
        for lower, upper in PAIRS:
            key = f"L{lower}_L{upper}"
            estimates = directed_crossings(p_values, sampled_rates[lower], sampled_rates[upper])
            if len(estimates) == 1:
                bootstrap[key]["single"].append(estimates[0])
            elif estimates:
                bootstrap[key]["multiple"] += 1
            else:
                bootstrap[key]["none"] += 1

    output = {}
    for lower, upper in PAIRS:
        key = f"L{lower}_L{upper}"
        single = bootstrap[key]["single"]
        quantiles = np.quantile(single, [0.025, 0.5, 0.975]).tolist() if single else [None, None, None]
        output[key] = {
            "sizes": [lower, upper],
            "point_directed_crossings": point[key],
            "point_status": "single" if len(point[key]) == 1 else "multiple" if point[key] else "not_bracketed",
            "bootstrap": {
                "method": "seed-cluster bootstrap preserving the nested p trajectory",
                "seed": 620001,
                "replicates": BOOTSTRAP_REPLICATES,
                "single_crossing_replicates": len(single),
                "no_crossing_replicates": bootstrap[key]["none"],
                "multiple_crossing_replicates": bootstrap[key]["multiple"],
                "single_crossing_fraction": len(single) / BOOTSTRAP_REPLICATES,
                "conditional_quantiles": {"q025": quantiles[0], "median": quantiles[1], "q975": quantiles[2]},
            },
        }
    return output


def plot(payload: dict, analysis: dict, destination: Path) -> None:
    figure, (axis, convergence_axis) = plt.subplots(
        2, 1, figsize=(8.2, 7.0), gridspec_kw={"height_ratios": [3.2, 1]}, sharex=True, constrained_layout=True
    )
    colors = {3: "#0072B2", 5: "#009E73", 7: "#E69F00", 9: "#D55E00"}
    for size in SIZES:
        rows = sorted((row for row in payload["summaries"] if row["L"] == size), key=lambda row: row["p"])
        x = [row["p"] for row in rows]
        y = [row["logical_error_rate"] for row in rows]
        low = [rate - row["logical_error_ci95"][0] for rate, row in zip(y, rows)]
        high = [row["logical_error_ci95"][1] - rate for rate, row in zip(y, rows)]
        axis.errorbar(x, y, yerr=[low, high], marker="o", markersize=3.8, linewidth=1.65, capsize=2.2, color=colors[size], label=f"L={size}")
        convergence_axis.plot(x, [row["bp_convergence_rate"] for row in rows], marker="o", markersize=3.2, linewidth=1.35, color=colors[size], label=f"L={size}")

    annotations = []
    line_styles = ("--", ":", "-.")
    for index, (key, item) in enumerate(analysis["adjacent_size_crossings"].items()):
        crossings = item["point_directed_crossings"]
        if len(crossings) == 1:
            estimate = crossings[0]
            axis.axvline(estimate, color="#555555", linestyle=line_styles[index], linewidth=1.0, alpha=0.8)
            annotations.append(f"{key.replace('_', '/')}: {estimate:.4f}")
        else:
            annotations.append(f"{key.replace('_', '/')}: {item['point_status']}")
    axis.text(
        0.015, 0.97, "\n".join(annotations), transform=axis.transAxes, ha="left", va="top", fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9},
    )
    axis.set_title(f"Square q=1 small-size high-p refinement — {payload['total_shots_per_cell']} shots/cell")
    axis.set_ylabel("logical error rate (LER)")
    axis.grid(alpha=0.22)
    axis.legend(title="code size", ncol=2)
    maximum = max(row["bp_convergence_rate"] for row in payload["summaries"])
    convergence_axis.set(xlabel="physical edge-error rate p", ylabel="BP converged", ylim=(-0.005, min(1.0, maximum + 0.05)))
    convergence_axis.grid(alpha=0.22)
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    source = LAB_DIR / "results" / f"{STEM}.json"
    payload = json.loads(source.read_text())
    if tuple(payload["sizes"]) != SIZES or payload["total_shots_per_cell"] != 5000:
        raise SystemExit("unexpected source design")
    crossings = summarize_crossings(payload)
    analysis = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": f"results/{STEM}.json",
        "design": {"lattice": "square", "q": 1.0, "sizes": list(SIZES), "p_grid": payload["p_grid"], "shots_per_cell": 5000},
        "adjacent_size_crossings": crossings,
        "convergence": {
            f"L{size}": {
                "minimum_rate": min(row["bp_convergence_rate"] for row in payload["summaries"] if row["L"] == size),
                "maximum_rate": max(row["bp_convergence_rate"] for row in payload["summaries"] if row["L"] == size),
            }
            for size in SIZES
        },
        "evidence_boundary": "Finite-size high-p operational crossings of the fixed 40-iteration decoder; not an asymptotic or converged-BP threshold.",
    }
    destination = LAB_DIR / "results" / f"{STEM}-analysis.json"
    destination.write_text(json.dumps(analysis, indent=2) + "\n")
    figure = LAB_DIR / "figures" / f"{STEM}-ler-vs-p.png"
    plot(payload, analysis, figure)
    print(json.dumps({"analysis": str(destination), "figure": str(figure), "crossings": crossings}, indent=2))


if __name__ == "__main__":
    main()
