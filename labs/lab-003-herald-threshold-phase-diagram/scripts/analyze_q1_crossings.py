#!/usr/bin/env python3
"""Merge corrected q=1 scans and visualize adjacent-distance LER crossings."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def adjacent_crossing(
    rows: list[dict], smaller: int, larger: int, *, delta_tolerance: float = 0.005
) -> dict:
    by_size = {}
    for size in (smaller, larger):
        by_size[size] = {
            float(row["p"]): float(row["logical_error_rate"])
            for row in rows
            if row["L"] == size and row["decoder"] == "herald_bp_mwpm"
        }
    common = sorted(set(by_size[smaller]) & set(by_size[larger]))
    if len(common) < 2:
        return {"sizes": [smaller, larger], "estimate": None, "status": "missing_curve"}
    differences = [by_size[smaller][p] - by_size[larger][p] for p in common]
    informative = [
        (p, difference)
        for p, difference in zip(common, differences)
        if abs(difference) >= delta_tolerance
    ]
    if len(informative) < 2:
        return {
            "sizes": [smaller, larger],
            "estimate": None,
            "status": "insufficient_informative_difference",
            "delta_tolerance": delta_tolerance,
        }
    candidates = []
    for index in range(len(informative) - 1):
        left_p, left = informative[index]
        right_p, right = informative[index + 1]
        # A threshold crossing must have the physical direction: below threshold
        # the larger code wins (delta > 0), while above it the larger code loses
        # (delta < 0). Ignore reverse sign changes near the LER=1/2 ceiling.
        if left > 0 and right < 0:
            fraction = -left / (right - left)
            candidates.append(left_p + fraction * (right_p - left_p))
    if not candidates:
        informative_differences = [difference for _, difference in informative]
        trend = (
            "larger_distance_lower_ler"
            if all(value > 0 for value in informative_differences)
            else "larger_distance_higher_ler"
        )
        return {
            "sizes": [smaller, larger],
            "estimate": None,
            "status": "not_bracketed",
            "observed_trend": trend,
            "delta_tolerance": delta_tolerance,
        }
    return {
        "sizes": [smaller, larger],
        "estimate": float(candidates[0]),
        "status": "linear_interpolation",
        "all_sign_changes": [float(value) for value in candidates],
        "delta_tolerance": delta_tolerance,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-figure", type=Path, required=True)
    args = parser.parse_args()

    payloads = [json.loads(path.read_text()) for path in args.inputs]
    rows_by_key = {}
    for payload in payloads:
        if payload.get("q") != 1.0:
            raise SystemExit("all inputs must be q=1 artifacts")
        if payload.get("fixed_decoder", {}).get("matching_projection") != "posterior_llr":
            raise SystemExit("all inputs must use posterior_llr")
        if payload.get("total_shots_per_cell") != 1000:
            raise SystemExit("all inputs must contain exactly 1000 shots per cell")
        for row in payload["rows"]:
            key = (row["lattice"], row["L"], row["p"], row["decoder"])
            rows_by_key[key] = row
    rows = list(rows_by_key.values())
    sizes = sorted({int(row["L"]) for row in rows})
    adjacent = list(zip(sizes[:-1], sizes[1:]))
    crossings = {
        lattice: [
            adjacent_crossing([row for row in rows if row["lattice"] == lattice], smaller, larger)
            for smaller, larger in adjacent
        ]
        for lattice in ("square", "honeycomb")
    }
    square_estimates = [item["estimate"] for item in crossings["square"] if item["estimate"] is not None]
    honeycomb_estimates = [item["estimate"] for item in crossings["honeycomb"] if item["estimate"] is not None]
    summary = {
        "square": {
            "classification": (
                "finite_crossing_with_size_drift"
                if square_estimates and crossings["square"][-1]["estimate"] is not None
                else "unresolved_finite_size_behavior"
                if square_estimates
                else "not_bracketed"
            ),
            "adjacent_crossing_range": [min(square_estimates), max(square_estimates)] if square_estimates else None,
            "largest_pair_estimate": crossings["square"][-1]["estimate"],
        },
        "honeycomb": {
            "classification": "finite_crossing_with_size_drift" if honeycomb_estimates else "ceiling_compatible_through_p_0.49",
            "adjacent_crossing_range": [min(honeycomb_estimates), max(honeycomb_estimates)] if honeycomb_estimates else None,
            "lower_bound": None if honeycomb_estimates else 0.49,
        },
    }
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "q": 1.0,
        "shots_per_cell": 1000,
        "source_artifacts": [str(path) for path in args.inputs],
        "matching_projection": "posterior_llr",
        "recurrence_mode": "damping",
        "sizes": sizes,
        "crossings": crossings,
        "summary": summary,
        "rows": sorted(rows, key=lambda row: (row["lattice"], row["decoder"], row["L"], row["p"])),
        "evidence_boundary": (
            "Piecewise-linear adjacent-size crossing diagnostic at 1000 shots/cell. "
            "Size drift prevents a final asymptotic threshold claim; honeycomb is a lower bound only."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2) + "\n")

    figure, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), sharey=True, constrained_layout=True)
    colors = {5: "#0072B2", 7: "#E69F00", 9: "#009E73", 11: "#CC79A7", 13: "#D55E00"}
    line_styles = [":", "--", "-.", (0, (3, 1, 1, 1))]
    for axis, lattice in zip(axes, ("square", "honeycomb")):
        lattice_rows = [row for row in rows if row["lattice"] == lattice and row["decoder"] == "herald_bp_mwpm"]
        for size in sizes:
            curve = sorted((row for row in lattice_rows if row["L"] == size), key=lambda row: row["p"])
            x = np.asarray([row["p"] for row in curve])
            y = np.asarray([row["logical_error_rate"] for row in curve])
            low = np.asarray([row["logical_error_ci95"][0] for row in curve])
            high = np.asarray([row["logical_error_ci95"][1] for row in curve])
            axis.errorbar(
                x,
                y,
                yerr=[np.maximum(0.0, y - low), np.maximum(0.0, high - y)],
                marker="o",
                markersize=4.2,
                linewidth=1.7,
                capsize=2.3,
                color=colors[size],
                label=f"L={size}",
            )
        for index, crossing in enumerate(crossings[lattice]):
            if crossing["estimate"] is None:
                continue
            estimate = crossing["estimate"]
            smaller, larger = crossing["sizes"]
            axis.axvline(estimate, color="#555555", linestyle=line_styles[index], linewidth=1.1, alpha=0.9)
            axis.text(
                estimate,
                0.96 - 0.13 * index,
                f"L{smaller}/L{larger}: {estimate:.3f}",
                transform=axis.get_xaxis_transform(),
                rotation=90,
                va="top",
                ha="right",
                fontsize=8,
                color="#333333",
            )
        if lattice == "honeycomb" and not honeycomb_estimates:
            axis.text(
                0.97,
                0.94,
                "no crossing through p=0.49\n$\\Rightarrow p_c(q=1) \\geq 0.49$ over tested sizes",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "#888888", "alpha": 0.9},
            )
        if lattice == "square" and crossings["square"][-1]["estimate"] is None:
            axis.text(
                0.03,
                0.57,
                "nominal small-size crossings: 0.344–0.438\n"
                r"L11/L13 not bracketed $\Rightarrow$ threshold unresolved",
                transform=axis.transAxes,
                ha="left",
                va="top",
                fontsize=8.5,
                bbox={"facecolor": "white", "edgecolor": "#888888", "alpha": 0.9},
            )
        axis.set_title(lattice)
        axis.set_xlabel("physical edge-error rate p")
        axis.set_xlim(0.02, 0.5)
        axis.set_ylim(-0.02, 0.56)
        axis.grid(alpha=0.22)
    axes[0].set_ylabel("logical error rate (LER)")
    axes[0].legend(title="code distance proxy")
    figure.suptitle("q=1 herald-aware damping BP + posterior-LLR PyMatching — 1000 shots/cell")
    args.output_figure.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output_figure, dpi=200)
    plt.close(figure)


if __name__ == "__main__":
    main()
