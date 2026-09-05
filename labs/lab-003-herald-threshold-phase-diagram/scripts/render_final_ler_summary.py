#!/usr/bin/env python3
"""Render the six-panel final selected LER evidence in ``results/``."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


LAB_DIR = Path(__file__).resolve().parents[1]
RESULTS = LAB_DIR / "results"
OUTPUT = RESULTS / "final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.png"
SUMMARY = RESULTS / "final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.json"
COLORS = {3: "#56B4E9", 5: "#0072B2", 7: "#E69F00", 9: "#009E73", 11: "#CC79A7", 13: "#D55E00"}

PANELS = (
    {"lattice": "square", "q": 0.0, "title": "Square lattice, q=0", "subtitle": "static-prior MWPM; 5000 shots/cell", "sources": ("q0-square-refined-5000-2026-08-27.json",)},
    {"lattice": "honeycomb", "q": 0.0, "title": "Honeycomb lattice, q=0", "subtitle": "40-step damping BP; 1000 shots/cell", "sources": ("phase2-honeycomb-q000-discovery-1000-2026-08-27.json",)},
    {"lattice": "square", "q": 0.75, "title": "Square lattice, q=0.75", "subtitle": "40-step damping BP; 5000 shots/cell", "sources": ("q075-square-l11-l13-refined-low-5000-2026-08-27.json", "q075-square-l11-l13-refined-5000-2026-08-27.json")},
    {"lattice": "honeycomb", "q": 0.75, "title": "Honeycomb lattice, q=0.75", "subtitle": "residual-priority-80 BP; 5000 shots/cell", "sources": ("q075-honeycomb-residual80-confirmation-5000-2026-08-27.json",)},
    {"lattice": "square", "q": 1.0, "title": "Square lattice, q=1", "subtitle": "40-step damping BP; 10000 shots/cell", "sources": ("q1-square-l5-l13-crossing-refined-10000-2026-08-27.json",)},
    {"lattice": "honeycomb", "q": 1.0, "title": "Honeycomb lattice, q=1", "subtitle": "residual-priority-80 BP; 1000 shots/cell", "sources": ("q1-honeycomb-full-p-residual80-discovery-1000-2026-08-27.json",), "endpoints": "q1-honeycomb-full-p-endpoints-1000-2026-08-27.json"},
)


def load_rows(sources: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    payloads = [json.loads((RESULTS / source).read_text()) for source in sources]
    by_cell = {}
    for payload in payloads:
        for row in payload["summaries"]:
            by_cell[(int(row["L"]), float(row["p"]))] = row
    return list(by_cell.values()), payloads


def plot_panel(axis, panel: dict) -> dict:
    rows, payloads = load_rows(panel["sources"])
    sizes = sorted({int(row["L"]) for row in rows})
    for size in sizes:
        curve = sorted((row for row in rows if int(row["L"]) == size), key=lambda row: float(row["p"]))
        x = np.asarray([float(row["p"]) for row in curve])
        y = np.asarray([float(row["logical_error_rate"]) for row in curve])
        ci = np.asarray([row["logical_error_ci95"] for row in curve], dtype=float)
        axis.errorbar(x, y, yerr=[np.maximum(0.0, y - ci[:, 0]), np.maximum(0.0, ci[:, 1] - y)], color=COLORS[size], marker="o", markersize=3.4, capsize=2, linewidth=1.25, label=f"L={size}")
    if panel.get("endpoints"):
        for size in sizes:
            endpoint_rows = [row for row in json.loads((RESULTS / panel["endpoints"]).read_text())["summaries"] if int(row["L"]) == size]
            axis.plot([row["p"] for row in endpoint_rows], [row["logical_error_rate"] for row in endpoint_rows], linestyle="none", marker="s", markersize=4, color=COLORS[size], markerfacecolor="white")
    points = [float(row["p"]) for row in rows]
    if panel.get("endpoints"):
        points.extend((0.0, 1.0))
    axis.set(title=f"{panel['title']}\n{panel['subtitle']}", xlabel="physical edge-error rate p", ylabel="logical error rate (LER)", xlim=(min(points) - 0.01, max(points) + 0.01), ylim=(-0.015, 0.56))
    axis.grid(alpha=0.22)
    axis.legend(fontsize=7, ncol=2)
    return {**panel, "sources": list(panel["sources"]), "sizes": sizes, "p_range": [min(points), max(points)], "source_config_sha256": [payload.get("config_sha256") for payload in payloads]}


def main() -> None:
    figure, axes = plt.subplots(3, 2, figsize=(13.0, 13.6), constrained_layout=True)
    selected = [plot_panel(axis, panel) for axis, panel in zip(axes.flat, PANELS)]
    figure.suptitle("Lab 003 final selected LER curves — independent finite-window cohorts", fontsize=15)
    figure.savefig(OUTPUT, dpi=200)
    plt.close(figure)
    SUMMARY.write_text(json.dumps({"schema_version": 1, "title": "Lab 003 final selected q=0/q=0.75/q=1 LER curves", "figure": str(OUTPUT.relative_to(LAB_DIR)), "layout": "3 rows (q=0, 0.75, 1) by 2 columns (square, honeycomb)", "panels": selected, "evidence_boundary": "Each panel uses its selected immutable cohort and possibly its own p range, sizes, shots, and decoder schedule. The raster is a six-panel finite-window evidence summary, not a pooled threshold fit or a cross-geometry performance comparison."}, indent=2) + "\n")


if __name__ == "__main__":
    main()
