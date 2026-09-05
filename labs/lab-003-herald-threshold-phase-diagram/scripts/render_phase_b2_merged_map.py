#!/usr/bin/env python3
"""Merge exactly the four Phase B2 cells into the Bayesian phase map and render it."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap, TwoSlopeNorm


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = LAB_DIR / "results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json"
DEFAULT_UPDATE = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png"


def load_base_module():
    path = Path(__file__).with_name("analyze_bayesian_fuzzy_trend_phase_map.py")
    spec = importlib.util.spec_from_file_location("phase_b2_base_map", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def update_rows(update: dict) -> dict[tuple[float, float], dict]:
    rows = list(update["new_analyses"]) + [update["reused_analysis"]]
    indexed = {(float(row["q"]), float(row["p"])): row for row in rows}
    expected = {(0.20, 0.08), (0.45, 0.20), (0.50, 0.20), (0.75, 0.40)}
    if set(indexed) != expected or len(rows) != 4:
        raise ValueError("Phase B2 merged map requires exactly the four registered/reused cells")
    if any(row["classification"] == "unresolved" for row in rows):
        raise ValueError("Phase B2 target unexpectedly remains unresolved")
    if any(row["classification"] != row["uniform_prior_sensitivity"]["classification"] for row in rows):
        raise ValueError("Phase B2 target is prior sensitive")
    return indexed


def merged_analyses(base: dict, update: dict) -> tuple[list[dict], list[dict]]:
    indexed = update_rows(update)
    merged = copy.deepcopy(base["analyses"])
    changes = []
    for q_row in merged:
        q = float(q_row["q"])
        for index, cell in enumerate(q_row["cells"]):
            key = (q, float(cell["p"]))
            replacement = indexed.get(key)
            if replacement is None:
                continue
            if cell["classification"] != "unresolved":
                raise ValueError(f"Phase B2 target was not gray in the base map: {key}")
            updated = copy.deepcopy(cell)
            protected = {"q", "p", "role", "branch", "reuse_reason", "strict_order_classification", "ordering_entropy_bits", "effective_ordering_count", "jeffreys_classification"}
            for field, value in replacement.items():
                if field not in protected:
                    updated[field] = copy.deepcopy(value)
            updated["p"] = key[1]
            updated["gray_measurement_route"] = None
            updated["phase_b2_update"] = {
                "distance_window": replacement["sizes"],
                "source": "reused_phase_b1" if key == (0.45, 0.20) else replacement["branch"],
            }
            q_row["cells"][index] = updated
            changes.append({"q": key[0], "p": key[1], "before": cell["classification"], "after": updated["classification"], "sizes": replacement["sizes"]})
    if len(changes) != 4:
        raise ValueError(f"expected four Phase B2 map changes, observed {len(changes)}")
    return merged, sorted(changes, key=lambda row: (row["q"], row["p"]))


def plot_map(analyses: list[dict], p_values: list[float], destination: Path, phase_label: str = "Phase B2") -> None:
    base = load_base_module()
    q_values = [row["q"] for row in analyses]
    cells = [row["cells"] for row in analyses]
    evidence = np.asarray([[cell["posterior_log_odds_upward_vs_downward"] if cell["posterior_log_odds_upward_vs_downward"] is not None else cell["posterior_log_odds_censoring"]["bound"] for cell in row] for row in cells])
    q_edges, p_edges = base.cell_edges(q_values, 0.0, 1.0), base.cell_edges(p_values)
    figure, axis = plt.subplots(figsize=(8.8, 7.2), constrained_layout=True)
    mesh = axis.pcolormesh(p_edges, q_edges, np.clip(evidence, -8.0, 8.0), cmap=LinearSegmentedColormap.from_list("trend_evidence", ["#16834A", "#F1F3F4", "#C63F32"]), norm=TwoSlopeNorm(vmin=-8.0, vcenter=0.0, vmax=8.0), shading="flat", edgecolors="white", linewidth=0.45)
    axis.set(
        title=r"$\log\!\left[\Pr(\mathrm{upward}\mid\mathrm{data}) / \Pr(\mathrm{downward}\mid\mathrm{data})\right]$",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(p_edges[0], p_edges[-1]),
        ylim=(0.0, 1.0),
    )
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0.0, 1.01, 0.1))
    axis.tick_params(labelsize=12)
    axis.xaxis.label.set_size(14)
    axis.yaxis.label.set_size(14)
    axis.title.set_size(16)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.025)
    colorbar.set_label("log likelihood ratio  (clipped at +/-8)", fontsize=13)
    colorbar.ax.tick_params(labelsize=11)
    figure.suptitle(f"Honeycomb phase diagram · Bayesian fuzzy trend · {phase_label}", fontsize=16)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def build(base_path: Path, update_path: Path, figure_path: Path) -> dict:
    base, update = json.loads(base_path.read_text()), json.loads(update_path.read_text())
    analyses, changes = merged_analyses(base, update)
    counts = {label: sum(cell["classification"] == label for row in analyses for cell in row["cells"]) for label in ("decodable", "undecodable", "unresolved")}
    if counts != {"decodable": 85, "undecodable": 39, "unresolved": 107}:
        raise ValueError(f"unexpected Phase B2 merged counts: {counts}")
    gray_routes = {
        route: sum(cell.get("gray_measurement_route") == route for row in analyses for cell in row["cells"])
        for route in ("more_shots_existing_L7_L9_L11_first", "add_L5_L13_distance_leverage")
    }
    if gray_routes != {"more_shots_existing_L7_L9_L11_first": 107, "add_L5_L13_distance_leverage": 0}:
        raise ValueError(f"unexpected Phase B2 gray routes: {gray_routes}")
    plot_map(analyses, [float(cell["p"]) for cell in base["analyses"][0]["cells"]], figure_path)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "definition": base["definition"],
        "classification_threshold": base["classification_threshold"],
        "prior_sensitivity_gate": base["prior_sensitivity_gate"],
        "counts": counts,
        "gray_measurement_routes": gray_routes,
        "analyses": analyses,
        "changes": changes,
        "unchanged_cell_count": 227,
        "provenance": {"base_map": {"path": str(base_path), "sha256": sha256(base_path)}, "phase_b2_analysis": {"path": str(update_path), "sha256": sha256(update_path)}, "renderer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())}},
        "figure": str(figure_path),
        "crossing_statistic_used": False,
        "grid_expanded": False,
        "evidence_boundary": "Base L7/L9/L11 map plus exactly four preregistered Phase B2 updates; adaptive finite-window evidence, not an asymptotic phase boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--update", type=Path, default=DEFAULT_UPDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    output = build(args.base, args.update, args.figure)
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "figure": str(args.figure), "counts": output["counts"], "changes": output["changes"]}, indent=2))


if __name__ == "__main__":
    main()
