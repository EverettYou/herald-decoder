#!/usr/bin/env python3
"""Render the collaborator-facing B15 neural-versus-spline comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_ANALYSIS = LAB_DIR / "results/phase-b15-neural-spline-comparison-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b15-neural-spline-boundary-comparison-2026-08-28.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def midpoint_edges(values: list[float]) -> list[float]:
    interior = [(a + b) / 2.0 for a, b in zip(values[:-1], values[1:])]
    return [values[0] - (values[1] - values[0]) / 2.0, *interior, values[-1] + (values[-1] - values[-2]) / 2.0]


def render(evidence: dict, analysis: dict, destination: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

    q_values, p_values = evidence["q_values"], evidence["p_values"]
    by_key = {(row["q"], row["p"]): row for row in evidence["cells"]}
    matrix = np.asarray([[by_key[(q, p)]["display_log_odds"] for p in p_values] for q in q_values])
    spline = analysis["branches"]["spline"]
    neural = analysis["branches"]["neural"]
    q_curve = np.asarray(spline["q"])
    spline_curve = np.asarray(spline["full_data_curve"])
    neural_curve = np.asarray(neural["full_data_curve"])
    s_low = np.asarray(spline["posterior_interval90"]["lower"])
    s_high = np.asarray(spline["posterior_interval90"]["upper"])
    n_low = np.asarray(neural["posterior_interval90"]["lower"])
    n_high = np.asarray(neural["posterior_interval90"]["upper"])
    diff = analysis["pairwise_difference_neural_minus_spline"]
    diff_med = np.asarray(diff["median"])
    diff_low = np.asarray(diff["interval90"]["lower"])
    diff_high = np.asarray(diff["interval90"]["upper"])
    limit = float(evidence["display"]["symmetric_limit"])
    cmap = LinearSegmentedColormap.from_list("trend", ["#14866d", "#f7f7f3", "#cf3f45"], N=256)
    figure = plt.figure(figsize=(11.8, 8.6))
    grid = figure.add_gridspec(2, 1, height_ratios=[4.6, 1.25], hspace=0.34, left=0.09, right=0.86, top=0.90, bottom=0.10)
    axis = figure.add_subplot(grid[0])
    mesh = axis.pcolormesh(
        midpoint_edges(p_values), midpoint_edges(q_values), matrix,
        cmap=cmap, norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
        edgecolors="#ffffff", linewidth=0.32, shading="flat",
    )
    axis.fill_betweenx(q_curve, s_low, s_high, color="#244a8d", alpha=0.13, linewidth=0)
    axis.fill_betweenx(q_curve, n_low, n_high, color="#111827", alpha=0.10, linewidth=0)
    axis.plot(spline_curve, q_curve, color="#244a8d", linewidth=2.8, label="Constrained spline")
    axis.plot(neural_curve, q_curve, color="#111827", linewidth=2.8, linestyle="--", label="Width-3 constrained neural")
    axis.set_xlim(min(p_values) - 0.02, max(p_values) + 0.02)
    axis.set_ylim(-0.025, 1.025)
    axis.set_xlabel("Edge error probability p", fontsize=14)
    axis.set_ylabel("Herald probability q", fontsize=14)
    axis.set_title("Honeycomb finite-window trend evidence with two regularized LLR = 0 summaries", fontsize=17, pad=12)
    axis.tick_params(labelsize=11)
    axis.legend(loc="upper left", frameon=True, framealpha=0.93, fontsize=11)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.025, fraction=0.05, extend="both")
    colorbar.set_label("log posterior odds: upward / downward LER trend", rotation=270, labelpad=22, fontsize=12)
    colorbar.ax.tick_params(labelsize=10)

    difference_axis = figure.add_subplot(grid[1])
    difference_axis.fill_between(q_curve, diff_low, diff_high, color="#6b7280", alpha=0.20, linewidth=0)
    difference_axis.plot(q_curve, diff_med, color="#111827", linewidth=2.0)
    difference_axis.axhline(0.0, color="#6b7280", linewidth=1.0)
    difference_axis.set_xlabel("Herald probability q", fontsize=12)
    difference_axis.set_ylabel("Neural - spline\nboundary p", fontsize=11)
    difference_axis.tick_params(labelsize=10)
    difference_axis.grid(axis="y", color="#d1d5db", linewidth=0.6, alpha=0.7)
    max_displacement = diff["maximum_absolute_full_curve_displacement"]
    difference_axis.text(
        0.99, 0.91,
        f"max |difference| = {max_displacement:.3f} in p",
        transform=difference_axis.transAxes, ha="right", va="top", fontsize=10,
    )
    s_metric, n_metric = spline["metrics"], neural["metrics"]
    figure.text(
        0.47, 0.035,
        "Held-out weighted log loss: "
        f"spline {s_metric['heldout_weighted_log_loss']:.3f} ± {s_metric['heldout_weighted_log_loss_standard_error']:.3f}; "
        f"neural {n_metric['heldout_weighted_log_loss']:.3f} ± {n_metric['heldout_weighted_log_loss_standard_error']:.3f}. "
        "Bands: 90% posterior-propagation/model-fit envelopes; no thermodynamic boundary claim.",
        ha="center", va="center", fontsize=9.5, color="#374151",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=240)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    evidence, analysis = json.loads(args.evidence.read_text()), json.loads(args.analysis.read_text())
    if analysis["sources"]["current_evidence"]["sha256"] != sha256(args.evidence):
        raise ValueError("Phase B15 render evidence hash drift")
    render(evidence, analysis, args.figure)
    print(json.dumps({"figure": str(args.figure), "sha256": sha256(args.figure)}, indent=2))


if __name__ == "__main__":
    main()
