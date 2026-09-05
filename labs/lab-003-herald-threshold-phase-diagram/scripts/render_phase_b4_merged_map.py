#!/usr/bin/env python3
"""Update exactly q=0.05,p=0.20 in the Phase B3 map and render Phase B4."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = LAB_DIR / "results/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_UPDATE = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png"


def load_b2_renderer():
    path = Path(__file__).with_name("render_phase_b2_merged_map.py")
    spec = importlib.util.spec_from_file_location("phase_b2_renderer_for_b4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def update_row(update: dict) -> dict:
    rows = update["analyses"]
    if len(rows) != 1 or (float(rows[0]["q"]), float(rows[0]["p"])) != (0.05, 0.20):
        raise ValueError("Phase B4 analysis must contain exactly q=0.05,p=0.20")
    row = rows[0]
    if row["classification"] not in {"decodable", "undecodable", "unresolved"}:
        raise ValueError("invalid Phase B4 classification")
    if row["classification"] != "unresolved" and row["classification"] != row["uniform_prior_sensitivity"]["classification"]:
        raise ValueError("Phase B4 resolved classification is prior sensitive")
    return row


def merged_analyses(base: dict, update: dict) -> tuple[list[dict], list[dict]]:
    replacement = update_row(update)
    merged = copy.deepcopy(base["analyses"])
    changes = []
    for q_row in merged:
        for index, cell in enumerate(q_row["cells"]):
            key = (float(q_row["q"]), float(cell["p"]))
            if key != (0.05, 0.20):
                continue
            if cell["classification"] != "unresolved":
                raise ValueError("Phase B4 target was not gray in the Phase B3 map")
            updated = copy.deepcopy(cell)
            for field, value in replacement.items():
                if field not in {"q", "p"}:
                    updated[field] = copy.deepcopy(value)
            updated["p"] = 0.20
            if updated["classification"] != "unresolved":
                updated["gray_measurement_route"] = None
            updated["phase_b4_update"] = {"distance_window": replacement["sizes"], "pooling_kind": replacement["pooling_kind"], "shots_per_distance": replacement["shots"], "source": "phase_b4_new_frontier_analysis"}
            q_row["cells"][index] = updated
            changes.append({"q": 0.05, "p": 0.20, "before": cell["classification"], "after": updated["classification"], "sizes": replacement["sizes"], "logical_errors": replacement["logical_errors"], "shots": replacement["shots"]})
    if len(changes) != 1:
        raise ValueError(f"expected exactly one Phase B4 payload update, observed {len(changes)}")
    return merged, changes


def build(base_path: Path, update_path: Path, figure_path: Path) -> dict:
    renderer = load_b2_renderer()
    base, update = json.loads(base_path.read_text()), json.loads(update_path.read_text())
    analyses, changes = merged_analyses(base, update)
    counts = {label: sum(cell["classification"] == label for row in analyses for cell in row["cells"]) for label in ("decodable", "undecodable", "unresolved")}
    allowed = [
        {"decodable": 85, "undecodable": 40, "unresolved": 106},
        {"decodable": 86, "undecodable": 40, "unresolved": 105},
        {"decodable": 85, "undecodable": 41, "unresolved": 105},
    ]
    if counts not in allowed:
        raise ValueError(f"unexpected Phase B4 counts: {counts}")
    p_values = [float(cell["p"]) for cell in base["analyses"][0]["cells"]]
    renderer.plot_map(analyses, p_values, figure_path, phase_label="Phase B4")
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "definition": base["definition"], "classification_threshold": base["classification_threshold"], "prior_sensitivity_gate": base["prior_sensitivity_gate"], "counts": counts, "analyses": analyses, "changes": changes, "unchanged_cell_count": 230, "provenance": {"base_map": {"path": str(base_path), "sha256": renderer.sha256(base_path)}, "phase_b4_analysis": {"path": str(update_path), "sha256": renderer.sha256(update_path)}, "renderer": {"path": str(Path(__file__).resolve()), "sha256": renderer.sha256(Path(__file__).resolve())}}, "figure": str(figure_path), "crossing_statistic_used": False, "grid_expanded": False, "evidence_boundary": "Phase B3 map plus exactly one Phase B4 payload update; adaptive finite-window evidence, not an asymptotic phase boundary."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--update", type=Path, default=DEFAULT_UPDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    output = build(args.base, args.update, args.figure)
    load_b2_renderer().atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "counts": output["counts"], "changes": output["changes"]}, indent=2))


if __name__ == "__main__":
    main()
