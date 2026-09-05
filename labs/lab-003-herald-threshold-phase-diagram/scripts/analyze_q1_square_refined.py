#!/usr/bin/env python3
"""Seed-cluster uncertainty analysis for the refined square q=1 scan."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
STEM = "q1-square-l11-l13-refined-5000-2026-08-27"


def directed_crossings(p_values: list[float], lower: np.ndarray, upper: np.ndarray) -> list[float]:
    delta = lower - upper
    crossings: list[float] = []
    for index, (left, right) in enumerate(zip(delta, delta[1:])):
        if left > 0 and right < 0:
            fraction = left / (left - right)
            crossings.append(p_values[index] + fraction * (p_values[index + 1] - p_values[index]))
        elif left == 0 and right < 0:
            crossings.append(p_values[index])
    return crossings


def main() -> None:
    data_path = LAB_DIR / "results" / f"{STEM}.json"
    payload = json.loads(data_path.read_text())
    p_values = payload["p_grid"]
    seeds = payload["seeds"]
    counts: dict[tuple[int, int, float], list[int]] = defaultdict(lambda: [0, 0])
    for row in payload["raw_shots"]:
        key = (row["seed"], row["L"], row["p"])
        counts[key][0] += int(row["herald_logical_failure"])
        counts[key][1] += 1

    rng = np.random.default_rng(510001)
    estimates: list[float] = []
    no_bracket = multiple = 0
    bootstrap_replicates = 20_000
    for _ in range(bootstrap_replicates):
        sampled = rng.choice(seeds, size=len(seeds), replace=True)
        rates: dict[int, np.ndarray] = {}
        for size in (11, 13):
            errors = np.asarray([sum(counts[(int(seed), size, p)][0] for seed in sampled) for p in p_values], dtype=float)
            shots = np.asarray([sum(counts[(int(seed), size, p)][1] for seed in sampled) for p in p_values], dtype=float)
            rates[size] = errors / shots
        crossings = directed_crossings(p_values, rates[11], rates[13])
        if len(crossings) == 1:
            estimates.append(crossings[0])
        elif not crossings:
            no_bracket += 1
        else:
            multiple += 1

    interval = np.quantile(estimates, [0.025, 0.5, 0.975]).tolist() if estimates else [None, None, None]
    analysis = {
        "schema_version": 1,
        "source": f"results/{STEM}.json",
        "method": "seed-cluster bootstrap preserving all p values within each resampled seed",
        "bootstrap_seed": 510001,
        "replicates": bootstrap_replicates,
        "single_directed_crossing_replicates": len(estimates),
        "no_directed_bracket_replicates": no_bracket,
        "multiple_directed_crossing_replicates": multiple,
        "single_crossing_fraction": len(estimates) / bootstrap_replicates,
        "crossing_conditional_quantiles": {"q025": interval[0], "median": interval[1], "q975": interval[2]},
        "point_estimate": payload["largest_pair_crossing"]["estimate"],
        "convergence_boundary": {
            "maximum_L11_rate": max(row["bp_convergence_rate"] for row in payload["summaries"] if row["L"] == 11),
            "maximum_L13_rate": max(row["bp_convergence_rate"] for row in payload["summaries"] if row["L"] == 13),
            "interpretation": "The reported crossing is for the fixed 40-iteration truncated decoder; fixed-point convergence is effectively absent over this grid.",
        },
        "evidence_boundary": "Bootstrap uncertainty is conditional on this five-seed finite-size design and does not cure BP non-convergence or establish an asymptotic threshold.",
    }
    analysis_path = LAB_DIR / "results" / f"{STEM}-analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2) + "\n")

    figure, (axis, convergence_axis) = plt.subplots(2, 1, figsize=(7.8, 6.6), gridspec_kw={"height_ratios": [3.2, 1]}, sharex=True, constrained_layout=True)
    colors = {11: "#CC79A7", 13: "#D55E00"}
    for size in (11, 13):
        rows = sorted((row for row in payload["summaries"] if row["L"] == size), key=lambda row: row["p"])
        x = [row["p"] for row in rows]
        y = [row["logical_error_rate"] for row in rows]
        low = [rate - row["logical_error_ci95"][0] for rate, row in zip(y, rows)]
        high = [row["logical_error_ci95"][1] - rate for rate, row in zip(y, rows)]
        axis.errorbar(x, y, yerr=[low, high], marker="o", linewidth=1.9, capsize=2.8, color=colors[size], label=f"L={size}")
        convergence_axis.plot(x, [row["bp_convergence_rate"] for row in rows], marker="o", linewidth=1.5, color=colors[size], label=f"L={size}")
    point = payload["largest_pair_crossing"]["estimate"]
    axis.axvline(point, color="#555555", linestyle="--", linewidth=1.1)
    if interval[0] is not None:
        axis.axvspan(interval[0], interval[2], color="#777777", alpha=0.14, label="seed-bootstrap 95% interval")
    axis.set_title(f"Square q=1 refined L=11/13 crossing — {payload['total_shots_per_cell']} shots/cell")
    axis.set_ylabel("logical error rate (LER)")
    axis.grid(alpha=0.22)
    axis.legend(title="code size")
    axis.text(0.985, 0.035, f"point: {point:.4f}\nbootstrap: [{interval[0]:.4f}, {interval[2]:.4f}]\nsingle bracket: {len(estimates)/bootstrap_replicates:.1%}", transform=axis.transAxes, ha="right", va="bottom", fontsize=8.8, bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9})
    convergence_axis.set(xlabel="physical edge-error rate p", ylabel="BP converged", ylim=(-0.0005, max(0.012, analysis["convergence_boundary"]["maximum_L11_rate"] + 0.003)))
    convergence_axis.grid(alpha=0.22)
    figure_path = LAB_DIR / "figures" / f"{STEM}-ler-vs-p.png"
    figure.savefig(figure_path, dpi=180)
    plt.close(figure)
    print(json.dumps({"analysis": str(analysis_path), "figure": str(figure_path), "bootstrap": analysis}, indent=2))


if __name__ == "__main__":
    main()
