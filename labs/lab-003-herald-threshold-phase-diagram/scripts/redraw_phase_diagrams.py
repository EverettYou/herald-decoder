#!/usr/bin/env python3
"""Overwrite every existing Lab 003 phase-map PNG using p horizontally and q vertically.

This is presentation-only: it reads immutable JSON analyses and redraws their
existing figure paths without altering raw data, posterior values, or summaries.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


LAB = Path(__file__).resolve().parents[1]
RESULTS = LAB / "results"


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def payload(name: str) -> dict:
    return json.loads((RESULTS / name).read_text())


def draw_monotone_order_map(data: dict) -> None:
    analyses = data["analyses"]
    q_values = [float(row["q"]) for row in analyses]
    p_values = [float(cell["p"]) for cell in analyses[0]["cells"]]
    code = {"undecodable": 0, "unresolved": 1, "decodable": 2}
    matrix = np.asarray(
        [[code[cell["classification"]] for cell in row["cells"]] for row in analyses]
    )
    edges = load_module("analyze_bayesian_order_phase_map.py", "order_edges").cell_edges
    figure, axis = plt.subplots(figsize=(9.8, 7.7), constrained_layout=True)
    axis.pcolormesh(
        edges(p_values),
        edges(q_values, 0.0, 1.0),
        matrix,
        cmap=ListedColormap(["#C63F32", "#D9DEE3", "#16834A"]),
        norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5], 3),
        shading="flat",
        edgecolors="white",
        linewidth=0.45,
    )
    axis.set(
        title="Honeycomb monotone LER-direction map\n"
        "adjacent-size ordering over L = 7, 9, 11",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(edges(p_values)[0], edges(p_values)[-1]),
        ylim=(0.0, 1.0),
    )
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0.0, 1.01, 0.1))
    axis.legend(
        handles=[
            Patch(facecolor="#16834A", label="decodable: LER decreases with size"),
            Patch(facecolor="#C63F32", label="undecodable: LER increases with size"),
            Patch(facecolor="#D9DEE3", label="unresolved / nonmonotone"),
        ],
        loc="upper right",
        fontsize=9,
    )
    destination = Path(data["figure"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def redraw() -> list[str]:
    written: list[str] = []
    order = load_module("analyze_bayesian_order_phase_map.py", "order_renderer")
    fuzzy = load_module("analyze_bayesian_fuzzy_trend_phase_map.py", "fuzzy_renderer")
    slope = load_module("analyze_slope_flow_phase_map.py", "slope_renderer")
    scout = load_module("analyze_phase2_scout.py", "scout_renderer")
    merged = load_module("render_phase_b2_merged_map.py", "merged_renderer")

    data = payload("phase2-residual80-honeycomb-bayesian-order-phase-2026-08-28.json")
    order.plot_posterior_map(data["analyses"], data["p_values"], Path(data["figure"]))
    written.append(data["figure"])

    data = payload("phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json")
    fuzzy.plot_map(data["analyses"], [float(cell["p"]) for cell in data["analyses"][0]["cells"]], Path(data["figure"]))
    written.append(data["figure"])

    for phase in range(2, 10):
        name = f"phase-b{phase}-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
        path = RESULTS / name
        if not path.exists():
            continue
        data = payload(name)
        figure = Path(data["figure"])
        merged.plot_map(
            data["analyses"],
            [float(cell["p"]) for cell in data["analyses"][0]["cells"]],
            figure,
            phase_label=f"Phase B{phase}",
        )
        written.append(str(figure))

    for name, title in [
        (
            "phase2-residual80-honeycomb-slope-flow-2026-08-28.json",
            None,
        ),
        (
            "phase-s1-honeycomb-slope-flow-gray-frontier-analysis-2026-08-28.json",
            "Honeycomb operational phase map from all-distance LER scaling flow\n"
            "Phase S1 updates 10 measured gray-frontier cells; no crossing statistic",
        ),
    ]:
        data = payload(name)
        p_values = [float(cell["p"]) for cell in data["analyses"][0]["cells"]]
        slope.plot_phase_map(data["analyses"], p_values, Path(data["figure"]), title=title)
        written.append(data["figure"])

    monotone = payload("phase2-residual80-honeycomb-monotone-ler-direction-2026-08-28.json")
    draw_monotone_order_map(monotone)
    written.append(monotone["figure"])

    for path in sorted(RESULTS.glob("phase*-analysis.json")):
        data = json.loads(path.read_text())
        if "lattices" not in data or "figures" not in data or "manifest" not in data:
            continue
        manifest_path = LAB.parents[1] / data["manifest"]
        manifest = scout.load_manifest(manifest_path)
        for lattice, analyses in data["lattices"].items():
            destination = Path(data["figures"][lattice])
            scout.plot_lattice(lattice, analyses, manifest, destination)
            written.append(str(destination))
    return written


if __name__ == "__main__":
    paths = redraw()
    print(json.dumps({"status": "complete", "figures_redrawn": len(paths), "figures": paths}, indent=2))
