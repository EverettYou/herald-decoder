#!/usr/bin/env python3
"""Analyze and plot the registered R6AB O2 finite-size threshold scan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_r5a_public_decoder_pilot import (
    independent_difference_bootstrap_interval,
    wilson_interval,
)


def _cell_values(rows: list[dict], size: int, rate: float, *, restored: bool) -> np.ndarray:
    selected = [row for row in rows if row["size"] == size and row["p_X"] == rate]
    values = []
    for row in selected:
        if row["status"] == "terminal_physical_winding":
            if restored:
                values.append(1.0)
            continue
        values.append(float(bool(row["flux_union_logical_failure"])))
    return np.asarray(values, dtype=float)


def crossings_from_differences(points: list[tuple[float, float]]) -> list[float]:
    crossings = []
    for (left_p, left_d), (right_p, right_d) in zip(points, points[1:]):
        if left_d == 0.0:
            crossings.append(left_p)
        if left_d * right_d <= 0.0 and right_d != left_d:
            crossings.append(left_p - left_d * (right_p - left_p) / (right_d - left_d))
    return crossings


def analyze(payload: dict, *, bootstrap_replicates: int = 10_000) -> dict:
    rows = payload["rows"]
    design = payload["scan_design"]
    sizes = [int(value) for value in design["sizes"]]
    grid = [float(value) for value in design["p_X_grid"]]
    cells = []
    conditional: dict[tuple[int, float], np.ndarray] = {}
    for size in sizes:
        for rate in grid:
            values = _cell_values(rows, size, rate, restored=False)
            restored = _cell_values(rows, size, rate, restored=True)
            conditional[(size, rate)] = values
            failures = int(values.sum())
            low, high = wilson_interval(failures, len(values))
            restored_failures = int(restored.sum())
            restored_low, restored_high = wilson_interval(restored_failures, len(restored))
            cells.append({
                "size": size,
                "p_X": rate,
                "attempted_histories": len(restored),
                "nonterminal_histories": len(values),
                "terminal_physical_windings": len(restored) - len(values),
                "conditional": {
                    "failures": failures,
                    "risk": float(values.mean()),
                    "wilson_90": [low, high],
                },
                "terminal_restored": {
                    "failures": restored_failures,
                    "risk": float(restored.mean()),
                    "wilson_90": [restored_low, restored_high],
                },
            })

    differences = []
    crossings = []
    for pair_index, (lower, upper) in enumerate(zip(sizes, sizes[1:])):
        points = []
        pair_differences = []
        for rate_index, rate in enumerate(grid):
            left = conditional[(lower, rate)]
            right = conditional[(upper, rate)]
            difference = float(right.mean() - left.mean())
            low, high = independent_difference_bootstrap_interval(
                left,
                right,
                replicates=bootstrap_replicates,
                seed=6_120_000 + 1000 * pair_index + rate_index,
            )
            points.append((rate, difference))
            difference_row = {
                "lower_size": lower,
                "upper_size": upper,
                "p_X": rate,
                "upper_minus_lower_risk": difference,
                "bootstrap_90": [low, high],
                "interval_contains_zero": low <= 0.0 <= high,
            }
            differences.append(difference_row)
            pair_differences.append(difference_row)
        estimates = crossings_from_differences(points)
        resolved_negative = [row["p_X"] for row in pair_differences if row["bootstrap_90"][1] < 0.0]
        resolved_positive = [row["p_X"] for row in pair_differences if row["bootstrap_90"][0] > 0.0]
        brackets = [
            [negative, positive]
            for negative in resolved_negative
            for positive in resolved_positive
            if negative < positive
        ]
        resolved_bracket = min(brackets, key=lambda pair: pair[1] - pair[0]) if brackets else None
        crossings.append({
            "lower_size": lower,
            "upper_size": upper,
            "linear_interpolated_crossings": estimates,
            "statistically_resolved_direction_bracket_90": resolved_bracket,
            "grid_differences": [{"p_X": p, "difference": d} for p, d in points],
        })
    finite = [estimate for row in crossings for estimate in row["linear_interpolated_crossings"]]
    resolved_brackets = [row for row in crossings if row["statistically_resolved_direction_bracket_90"] is not None]
    return {
        "schema_version": 1,
        "status": "completed_r6ab_o2_finite_size_analysis",
        "paper_reference_threshold": float(design["paper_reference_threshold"]),
        "cells": cells,
        "adjacent_size_differences": differences,
        "adjacent_size_crossings": crossings,
        "crossing_summary": {
            "raw_sign_change_count": len(finite),
            "raw_median_linear_interpolated_crossing": float(np.median(finite)) if finite else None,
            "raw_minimum_crossing": min(finite) if finite else None,
            "raw_maximum_crossing": max(finite) if finite else None,
            "statistically_resolved_direction_bracket_pair_count": len(resolved_brackets),
            "paper_value_inside_raw_crossing_range": bool(finite and min(finite) <= float(design["paper_reference_threshold"]) <= max(finite)),
        },
        "claim_boundary": payload["claim_boundary"],
    }


def plot_analysis(analysis: dict, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    sizes = sorted({int(cell["size"]) for cell in analysis["cells"]})
    for size in sizes:
        cells = sorted(
            (cell for cell in analysis["cells"] if cell["size"] == size),
            key=lambda row: row["p_X"],
        )
        x = np.asarray([cell["p_X"] for cell in cells])
        y = np.asarray([cell["conditional"]["risk"] for cell in cells])
        lower = y - np.asarray([cell["conditional"]["wilson_90"][0] for cell in cells])
        upper = np.asarray([cell["conditional"]["wilson_90"][1] for cell in cells]) - y
        axis.errorbar(x, y, yerr=np.vstack((lower, upper)), marker="o", capsize=2.5, label=f"L={size}")
    paper = analysis["paper_reference_threshold"]
    axis.axvline(paper, color="black", linestyle="--", linewidth=1.2, label=f"paper $p_c$={paper:.5f}")
    axis.set_xlabel("physical error probability $p_X$")
    axis.set_ylabel("conditional O2 flux logical-error rate")
    axis.set_title("Published O2 decoder: quick finite-size scan (not a threshold fit)")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2, fontsize=8)
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def render_report(analysis: dict) -> str:
    summary = analysis["crossing_summary"]
    lines = [
        "# R6AB published O2 threshold quick scan",
        "",
        "The scan uses 1,000 attempted histories per cell on the paper-normalized D4 honeycomb. The primary score is first-stage Boolean-union flux logical failure conditional on nonterminal physical records.",
        "",
        "Headline: the paper value is p_c=0.20842 (20.842%). This quick scan supports only a broad transition neighborhood around 0.20--0.22; it does not estimate a replacement threshold.",
        "",
        "| L | p_X | failures / nonterminal | conditional flux risk | 90% Wilson interval |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for cell in analysis["cells"]:
        result = cell["conditional"]
        lines.append(
            f"| {cell['size']} | {cell['p_X']:.3f} | {result['failures']} / {cell['nonterminal_histories']} | "
            f"{result['risk']:.4f} | [{result['wilson_90'][0]:.4f}, {result['wilson_90'][1]:.4f}] |"
        )
    lines.extend(["", "## Crossing diagnostic", ""])
    for crossing in analysis["adjacent_size_crossings"]:
        estimates = crossing["linear_interpolated_crossings"]
        bracket = crossing["statistically_resolved_direction_bracket_90"]
        lines.append(
            f"- L={crossing['lower_size']} to L={crossing['upper_size']}: "
            + ("raw linear sign changes " + ", ".join(f"{estimate:.5f}" for estimate in estimates) + "." if estimates else "no sign change inside the registered grid.")
            + (f" Resolved 90% direction bracket [{bracket[0]:.3f}, {bracket[1]:.3f}]." if bracket else " No 90% direction bracket is resolved.")
        )
    median = summary["raw_median_linear_interpolated_crossing"]
    lines.extend([
        "",
        f"For audit only, the median raw adjacent-size sign change is {'not available' if median is None else f'{median:.5f}'}. The paper reference is {analysis['paper_reference_threshold']:.5f}. The raw value is a small-L interpolation diagnostic, not a threshold estimate.",
        "",
        "## Interpretation",
        "",
        "The L=5->7 and L=7->9 raw crossings occur near 0.214, but these are upward-biased-capable small-L diagnostics on a 0.01 grid. The L=9->11 pair is statistically unresolved at every grid point and oscillates, so there is no stable size sequence from which to extrapolate. Only L=5->7 has a 90%-resolved change of size direction across the broad registered bracket [0.19,0.22]. The correct conclusion is consistency with a roughly 20%--22% transition window and with the paper's 20.842% value, not a project estimate of 21.4%.",
        "",
        "## Claim boundary",
        "",
        analysis["claim_boundary"],
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("figure", type=Path)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(payload, bootstrap_replicates=args.bootstrap_replicates)
    args.analysis.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render_report(result), encoding="utf-8")
    plot_analysis(result, args.figure)
    print(json.dumps({"analysis": str(args.analysis), "report": str(args.report), "figure": str(args.figure), "crossing": result["crossing_summary"]}))


if __name__ == "__main__":
    main()
