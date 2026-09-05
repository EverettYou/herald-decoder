#!/usr/bin/env python3
"""Merge exactly the one resolved Phase B3 cell into the Phase B2 map."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = LAB_DIR / "results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_UPDATE = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png"


def load_phase_b2_renderer():
    path = Path(__file__).with_name("render_phase_b2_merged_map.py")
    spec = importlib.util.spec_from_file_location("phase_b2_renderer_for_b3", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def resolved_update_rows(update: dict) -> dict[tuple[float, float], dict]:
    rows = [row for row in update["analyses"] if row["classification"] != "unresolved"]
    indexed = {(float(row["q"]), float(row["p"])): row for row in rows}
    if set(indexed) != {(0.10, 0.20)} or len(rows) != 1:
        raise ValueError("Phase B3 merged map requires exactly the registered resolved cell q=0.10,p=0.20")
    row = rows[0]
    if row["classification"] != row["uniform_prior_sensitivity"]["classification"]:
        raise ValueError("Phase B3 resolved target is prior sensitive")
    if row["classification"] != row["jeffreys_classification"]:
        raise ValueError("Phase B3 Jeffreys classification is internally inconsistent")
    return indexed


def merged_analyses(base: dict, update: dict) -> tuple[list[dict], list[dict]]:
    indexed = resolved_update_rows(update)
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
                raise ValueError(f"Phase B3 target was not gray in the Phase B2 map: {key}")
            updated = copy.deepcopy(cell)
            for field, value in replacement.items():
                if field not in {"q", "p"}:
                    updated[field] = copy.deepcopy(value)
            updated["p"] = key[1]
            updated["gray_measurement_route"] = None
            updated["phase_b3_update"] = {
                "distance_window": replacement["sizes"],
                "pooling_kind": replacement["pooling_kind"],
                "shots_per_distance": replacement["shots"],
                "source": "phase_b3_frontier_reuse_analysis",
            }
            q_row["cells"][index] = updated
            changes.append({
                "q": key[0],
                "p": key[1],
                "before": cell["classification"],
                "after": updated["classification"],
                "sizes": replacement["sizes"],
                "logical_errors": replacement["logical_errors"],
                "shots": replacement["shots"],
                "posterior_probability_upward_trend": replacement["posterior_probability_upward_trend"],
            })
    if len(changes) != 1:
        raise ValueError(f"expected one Phase B3 map change, observed {len(changes)}")
    return merged, changes


def build(base_path: Path, update_path: Path, figure_path: Path) -> dict:
    renderer = load_phase_b2_renderer()
    base = json.loads(base_path.read_text())
    update = json.loads(update_path.read_text())
    analyses, changes = merged_analyses(base, update)
    counts = {
        label: sum(cell["classification"] == label for row in analyses for cell in row["cells"])
        for label in ("decodable", "undecodable", "unresolved")
    }
    if counts != {"decodable": 85, "undecodable": 40, "unresolved": 106}:
        raise ValueError(f"unexpected Phase B3 merged counts: {counts}")
    gray_routes = {
        route: sum(cell.get("gray_measurement_route") == route for row in analyses for cell in row["cells"])
        for route in ("more_shots_existing_L7_L9_L11_first", "add_L5_L13_distance_leverage")
    }
    if gray_routes != {"more_shots_existing_L7_L9_L11_first": 106, "add_L5_L13_distance_leverage": 0}:
        raise ValueError(f"unexpected Phase B3 gray routes: {gray_routes}")
    p_values = [float(cell["p"]) for cell in base["analyses"][0]["cells"]]
    renderer.plot_map(analyses, p_values, figure_path, phase_label="Phase B3")
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
        "unchanged_cell_count": 230,
        "provenance": {
            "base_map": {"path": str(base_path), "sha256": renderer.sha256(base_path)},
            "phase_b3_analysis": {"path": str(update_path), "sha256": renderer.sha256(update_path)},
            "renderer": {"path": str(Path(__file__).resolve()), "sha256": renderer.sha256(Path(__file__).resolve())},
        },
        "figure": str(figure_path),
        "crossing_statistic_used": False,
        "grid_expanded": False,
        "evidence_boundary": "Phase B2 map plus exactly one prior-stable Phase B3 update; adaptive finite-window evidence, not an asymptotic phase boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--update", type=Path, default=DEFAULT_UPDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    output = build(args.base, args.update, args.figure)
    renderer = load_phase_b2_renderer()
    renderer.atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "figure": str(args.figure), "counts": output["counts"], "changes": output["changes"]}, indent=2))


if __name__ == "__main__":
    main()
