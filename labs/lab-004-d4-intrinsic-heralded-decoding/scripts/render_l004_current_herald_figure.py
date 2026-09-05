#!/usr/bin/env python3
"""Render the current reader-facing Lab 004 finite-size crossing diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


LAB = Path(__file__).resolve().parents[1]
BASELINE = LAB / "results/r6ae-signal-only-bp-threshold-stage5-analysis-2026-09-01.json"
REFINED = LAB / "results/r6ai-critical-band-refinement-analysis-2026-09-01.json"
OUT = LAB / "figures/l004-1-current-herald-aware-flux-curves.png"
POLICIES = (
    ("O2_published_herald_weight_MWPM", "Herald-weight MWPM"),
    ("R6D_local_BP_posterior_LLR_MWPM", "Signal-only BeliefMatching"),
)
PAIR_COLOURS = ("#3b528b", "#21918c", "#5ec962", "#d8b400")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    source = args.analysis or (REFINED if REFINED.is_file() else BASELINE)
    data = json.loads(source.read_text(encoding="utf-8"))
    cells = data["cells"]
    differences = data["adjacent_size_differences_all_final_iterates"]
    sizes = sorted({int(row["size"]) for row in cells})
    colours = plt.cm.viridis(np.linspace(0.05, 0.95, len(sizes)))
    histories = sorted({int(row["attempted_histories"]) for row in cells})
    p_values = sorted({float(row["p_X"]) for row in cells})

    plt.rcParams.update({
        "font.size": 13,
        "axes.titlesize": 16,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 11,
    })
    fig, axes = plt.subplots(
        2, 2, figsize=(15.5, 10.0), sharex="col",
        gridspec_kw={"height_ratios": (2.15, 1.0), "hspace": 0.12, "wspace": 0.16},
    )
    for column, (policy, title) in enumerate(POLICIES):
        curve_axis = axes[0, column]
        difference_axis = axes[1, column]
        for colour, size in zip(colours, sizes):
            selected = sorted(
                (row for row in cells if int(row["size"]) == size),
                key=lambda row: float(row["p_X"]),
            )
            x = np.asarray([float(row["p_X"]) for row in selected])
            summaries = [row[policy]["all_final_iterates"] for row in selected]
            y = np.asarray([float(summary["risk"]) for summary in summaries])
            lower = y - np.asarray([float(summary["wilson_90"][0]) for summary in summaries])
            upper = np.asarray([float(summary["wilson_90"][1]) for summary in summaries]) - y
            curve_axis.errorbar(
                x, y, yerr=(lower, upper), color=colour, marker="o",
                markersize=5.5, linewidth=1.8, capsize=3.5, label=f"L={size}",
            )
        if column == 0:
            curve_axis.axvline(
                0.20842, color="#b23a48", linestyle="--", linewidth=1.8,
                label=r"published $p_c=0.20842$",
            )
        curve_axis.set_title(title, pad=10)
        curve_axis.grid(alpha=0.24)
        curve_axis.legend(frameon=False, ncol=2, loc="upper left")

        selected_differences = [row for row in differences if row["policy"] == policy]
        pairs = sorted({(int(row["lower_size"]), int(row["upper_size"])) for row in selected_differences})
        for colour, pair in zip(PAIR_COLOURS, pairs):
            rows = sorted(
                (row for row in selected_differences if (int(row["lower_size"]), int(row["upper_size"])) == pair),
                key=lambda row: float(row["p_X"]),
            )
            x = np.asarray([float(row["p_X"]) for row in rows])
            y = np.asarray([float(row["upper_minus_lower_risk"]) for row in rows])
            lower = y - np.asarray([float(row["bootstrap_90"][0]) for row in rows])
            upper = np.asarray([float(row["bootstrap_90"][1]) for row in rows]) - y
            difference_axis.errorbar(
                x, y, yerr=(lower, upper), color=colour, marker="o",
                markersize=5, linewidth=1.5, capsize=3, label=f"L={pair[1]} minus L={pair[0]}",
            )
        difference_axis.axhline(0.0, color="black", linewidth=1.2)
        if column == 0:
            difference_axis.axvline(0.20842, color="#b23a48", linestyle="--", linewidth=1.8)
        difference_axis.grid(alpha=0.24)
        difference_axis.set_xlabel(r"physical X-error probability $p_X$")
        difference_axis.legend(frameon=False, ncol=2, loc="best", fontsize=10)

    axes[0, 0].set_ylabel("unconditional first-stage flux LER")
    axes[1, 0].set_ylabel(r"adjacent-size difference $R_{L_2}-R_{L_1}$")
    axes[0, 0].set_xlim(min(p_values) - 0.001, max(p_values) + 0.001)
    sample_label = (
        f"{histories[0]:,} matched histories/cell" if len(histories) == 1
        else f"{min(histories):,}–{max(histories):,} matched histories/cell"
    )
    grid_label = ", ".join(f"{value:.4f}".rstrip("0") for value in p_values)
    fig.suptitle(
        f"D4 herald-aware finite-size crossing diagnostic ({sample_label})",
        fontsize=20, y=0.985,
    )
    fig.text(
        0.5, 0.018,
        "Bottom panels show the quantity whose sign changes at a pairwise crossing. "
        f"Sampled p_X grid: {grid_label}. No thermodynamic threshold fit is imposed.",
        ha="center", fontsize=12,
    )
    fig.tight_layout(rect=(0.025, 0.055, 0.995, 0.955))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=200, facecolor="white")
    plt.close(fig)
    print(json.dumps({"output": str(args.output), "analysis": str(source), "p_X_grid": p_values}))


if __name__ == "__main__":
    main()
