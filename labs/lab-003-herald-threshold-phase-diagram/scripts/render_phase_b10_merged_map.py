#!/usr/bin/env python3
"""Update exactly four Phase B10 payloads and render the map."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


def load_base():
    path = Path(__file__).with_name("render_phase_b9_merged_map.py")
    spec = importlib.util.spec_from_file_location("phase_b10_render_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BASE = load_base()
LAB_DIR = Path(__file__).resolve().parents[1]
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.65, 0.32)}
BASE.EXPECTED = EXPECTED
BASE.DEFAULT_BASE = LAB_DIR / "results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
BASE.DEFAULT_UPDATE = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-analysis-2026-08-28.json"
BASE.DEFAULT_OUTPUT = LAB_DIR / "results/phase-b10-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
BASE.DEFAULT_FIGURE = LAB_DIR / "figures/phase-b10-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png"
_BASE_MERGED = BASE.merged_analyses


def merged_analyses(base: dict, update: dict):
    analyses, changes = _BASE_MERGED(base, update)
    for row in analyses:
        for cell in row["cells"]:
            if "phase_b9_update" in cell and (float(row["q"]), float(cell["p"])) in EXPECTED:
                record = cell.pop("phase_b9_update")
                record["source"] = "phase_b10_measured_endpoints_analysis"
                cell["phase_b10_update"] = record
    return analyses, changes


BASE.merged_analyses = merged_analyses


def build(base_path: Path, update_path: Path, figure_path: Path) -> dict:
    renderer = BASE.load_b2()
    base = json.loads(Path(base_path).read_text())
    update = json.loads(Path(update_path).read_text())
    analyses, changes = merged_analyses(base, update)
    counts = {name: sum(cell["classification"] == name for row in analyses for cell in row["cells"])
              for name in ("decodable", "undecodable", "unresolved")}
    if sum(counts.values()) != 231:
        raise ValueError("Phase B10 count drift")
    renderer.plot_map(analyses, [float(cell["p"]) for cell in base["analyses"][0]["cells"]],
                      figure_path, phase_label="Phase B10")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "definition": base["definition"],
        "classification_threshold": base["classification_threshold"],
        "prior_sensitivity_gate": base["prior_sensitivity_gate"],
        "counts": counts,
        "analyses": analyses,
        "changes": changes,
        "unchanged_cell_count": 227,
        "provenance": {
            "base_map": {"path": str(base_path), "sha256": renderer.sha256(base_path)},
            "phase_b10_analysis": {"path": str(update_path), "sha256": renderer.sha256(update_path)},
            "renderer": {"path": str(Path(__file__).resolve()), "sha256": renderer.sha256(Path(__file__).resolve())},
        },
        "figure": str(figure_path),
        "crossing_statistic_used": False,
        "grid_expanded": False,
        "evidence_boundary": "Phase B9 map plus exactly four Phase B10 payload updates; finite-window evidence only.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE.DEFAULT_BASE)
    parser.add_argument("--update", type=Path, default=BASE.DEFAULT_UPDATE)
    parser.add_argument("--output", type=Path, default=BASE.DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=BASE.DEFAULT_FIGURE)
    args = parser.parse_args()
    output = build(args.base, args.update, args.figure)
    BASE.load_b2().atomic_json(args.output, output)
    print(json.dumps({"counts": output["counts"], "changes": output["changes"]}, indent=2))


if __name__ == "__main__":
    main()
