#!/usr/bin/env python3
"""Plot the selected square and honeycomb q=0.75 LER evidence for REPORT.md."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB = Path(__file__).resolve().parents[1]
RESULTS = LAB / "results"
FIGURES = LAB / "figures"
SQUARE_SOURCES = [
    RESULTS / "q075-square-l11-l13-refined-low-5000-2026-08-27.json",
    RESULTS / "q075-square-l11-l13-refined-5000-2026-08-27.json",
]
SQUARE_ANALYSIS = RESULTS / "q075-square-l11-l13-refined-5000-2026-08-27-analysis.json"
HONEYCOMB_SOURCE = RESULTS / "q075-honeycomb-residual80-confirmation-5000-2026-08-27.json"
HONEYCOMB_ANALYSIS = RESULTS / "q075-honeycomb-residual80-confirmation-5000-2026-08-27-analysis.json"
OUTPUT_FIGURE = FIGURES / "q075-square-honeycomb-selected-ler-2026-08-28.png"
OUTPUT_MAP = RESULTS / "q075-square-honeycomb-selected-ler-2026-08-28.json"


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def plot_curve(axis, rows: list[dict], size: int, color: str) -> None:
    curve = sorted((row for row in rows if int(row["L"]) == size), key=lambda row: float(row["p"]))
    x = np.asarray([float(row["p"]) for row in curve])
    y = np.asarray([float(row["logical_error_rate"]) for row in curve])
    ci = np.asarray([row["logical_error_ci95"] for row in curve], dtype=float)
    axis.errorbar(
        x,
        y,
        yerr=[np.maximum(0.0, y - ci[:, 0]), np.maximum(0.0, ci[:, 1] - y)],
        color=color,
        marker="o",
        linewidth=1.7,
        capsize=2.5,
        label=f"L={size}",
    )


def main() -> None:
    square_payloads = [json.loads(path.read_text()) for path in SQUARE_SOURCES]
    square_analysis = json.loads(SQUARE_ANALYSIS.read_text())
    honeycomb = json.loads(HONEYCOMB_SOURCE.read_text())
    honeycomb_analysis = json.loads(HONEYCOMB_ANALYSIS.read_text())

    square_rows_by_cell = {}
    for payload in square_payloads:
        for row in payload["summaries"]:
            square_rows_by_cell[(int(row["L"]), float(row["p"]))] = row
    square_rows = list(square_rows_by_cell.values())
    honeycomb_rows = honeycomb["summaries"]

    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7"]
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), constrained_layout=True)

    for color, size in zip(colors, [11, 13]):
        plot_curve(axes[0], square_rows, size, color)
    square_crossing = float(square_analysis["adjacent_crossings"]["L11_L13"]["point_directed_crossings"][0])
    axes[0].axvline(square_crossing, color="#555555", linestyle="--", linewidth=1.2)
    axes[0].text(
        square_crossing + 0.003,
        0.055,
        f"L11/L13: {square_crossing:.4f}",
        fontsize=9,
        color="#444444",
    )
    axes[0].set(
        title="Square lattice",
        xlabel="physical edge-error rate p",
        ylabel="logical error rate (LER)",
        xlim=(0.115, 0.325),
        ylim=(0.01, 0.525),
    )

    honeycomb_sizes = sorted({int(row["L"]) for row in honeycomb_rows})
    for color, size in zip(colors, honeycomb_sizes):
        plot_curve(axes[1], honeycomb_rows, size, color)
    honeycomb_crossings = [
        float(item["estimate"])
        for item in honeycomb_analysis["adjacent_crossings"]
        if item["estimate"] is not None
    ]
    axes[1].axvspan(
        min(honeycomb_crossings),
        max(honeycomb_crossings),
        color="#777777",
        alpha=0.12,
        label="first adjacent-crossing span",
    )
    for estimate in honeycomb_crossings:
        axes[1].axvline(estimate, color="#555555", linestyle="--", linewidth=0.9)
    axes[1].set(
        title="Honeycomb lattice",
        xlabel="physical edge-error rate p",
        ylabel="logical error rate (LER)",
        xlim=(0.065, 0.515),
        ylim=(-0.01, 0.52),
    )

    for axis in axes:
        axis.grid(alpha=0.24)
        axis.legend(title="code size")
    figure.suptitle(
        "q=0.75 selected LER evidence — independent p ranges; 5000 shots/cell"
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_FIGURE, dpi=200)
    plt.close(figure)

    atomic_json(
        OUTPUT_MAP,
        {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "title": "Selected q=0.75 square and honeycomb LER evidence",
            "figure": str(OUTPUT_FIGURE.relative_to(LAB)),
            "panels": [
                {
                    "lattice": "square",
                    "q": 0.75,
                    "sources": [str(path.relative_to(LAB)) for path in SQUARE_SOURCES],
                    "analysis": str(SQUARE_ANALYSIS.relative_to(LAB)),
                    "sizes": [11, 13],
                    "shots_per_cell": 5000,
                    "directed_crossing": square_crossing,
                },
                {
                    "lattice": "honeycomb",
                    "q": 0.75,
                    "source": str(HONEYCOMB_SOURCE.relative_to(LAB)),
                    "analysis": str(HONEYCOMB_ANALYSIS.relative_to(LAB)),
                    "sizes": honeycomb_sizes,
                    "shots_per_cell": honeycomb["total_shots_per_cell"],
                    "first_directed_adjacent_crossings": honeycomb_crossings,
                },
            ],
            "comparison_boundary": (
                "The panels use independent p ranges, size sets, and decoder schedules. "
                "They ground lattice-specific operational crossings and must not be read "
                "as a same-p performance comparison or pooled threshold fit."
            ),
        },
    )


if __name__ == "__main__":
    main()
