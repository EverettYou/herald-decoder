#!/usr/bin/env python3
"""Update exactly four payloads and render a Phase B7 map."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = LAB_DIR / "results/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_UPDATE = LAB_DIR / "results/phase-b7-honeycomb-endpoint-followup-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png"
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.60, 0.28)}


def load_b2():
    path = Path(__file__).with_name("render_phase_b2_merged_map.py")
    spec = importlib.util.spec_from_file_location("phase_b7_render_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def merged_analyses(base: dict, update: dict) -> tuple[list, list]:
    rows = {(float(row["q"]), float(row["p"])): row for row in update["analyses"]}
    if set(rows) != EXPECTED or len(update["analyses"]) != 4:
        raise ValueError("Phase B7 analysis must contain exactly four cells")
    merged = copy.deepcopy(base["analyses"])
    changes = []
    for qrow in merged:
        for index, cell in enumerate(qrow["cells"]):
            key = (float(qrow["q"]), float(cell["p"]))
            replacement = rows.get(key)
            if replacement is None:
                continue
            if cell["classification"] != "unresolved":
                raise ValueError("Phase B7 target was not gray")
            updated = copy.deepcopy(cell)
            for field, value in replacement.items():
                if field not in {"q", "p"}:
                    updated[field] = copy.deepcopy(value)
            updated["p"] = key[1]
            if updated["classification"] != "unresolved":
                updated["gray_measurement_route"] = None
            updated["phase_b7_update"] = {"distance_window": replacement["sizes"], "pooling_kind": replacement["pooling_kind"], "shots_per_distance": replacement["shots"], "source": "phase_b7_endpoint_followup_analysis"}
            qrow["cells"][index] = updated
            changes.append({"q": key[0], "p": key[1], "before": cell["classification"], "after": updated["classification"], "sizes": replacement["sizes"], "logical_errors": replacement["logical_errors"], "shots": replacement["shots"]})
    if len(changes) != 4:
        raise ValueError("expected exactly four Phase B7 payload updates")
    return merged, sorted(changes, key=lambda row: (row["q"], row["p"]))


def build(base_path: Path, update_path: Path, figure_path: Path) -> dict:
    renderer = load_b2()
    base = json.loads(base_path.read_text())
    update = json.loads(update_path.read_text())
    analyses, changes = merged_analyses(base, update)
    counts = {label: sum(cell["classification"] == label for row in analyses for cell in row["cells"]) for label in ("decodable", "undecodable", "unresolved")}
    if sum(counts.values()) != 231:
        raise ValueError("Phase B7 count drift")
    renderer.plot_map(analyses, [float(cell["p"]) for cell in base["analyses"][0]["cells"]], figure_path, phase_label="Phase B7")
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "definition": base["definition"], "classification_threshold": base["classification_threshold"], "prior_sensitivity_gate": base["prior_sensitivity_gate"], "counts": counts, "analyses": analyses, "changes": changes, "unchanged_cell_count": 227, "provenance": {"base_map": {"path": str(base_path), "sha256": renderer.sha256(base_path)}, "phase_b7_analysis": {"path": str(update_path), "sha256": renderer.sha256(update_path)}, "renderer": {"path": str(Path(__file__).resolve()), "sha256": renderer.sha256(Path(__file__).resolve())}}, "figure": str(figure_path), "crossing_statistic_used": False, "grid_expanded": False, "evidence_boundary": "Phase B6 map plus exactly four Phase B7 payload updates; finite-window evidence only."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--update", type=Path, default=DEFAULT_UPDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    output = build(args.base, args.update, args.figure)
    load_b2().atomic_json(args.output, output)
    print(json.dumps({"counts": output["counts"], "changes": output["changes"]}, indent=2))


if __name__ == "__main__":
    main()
