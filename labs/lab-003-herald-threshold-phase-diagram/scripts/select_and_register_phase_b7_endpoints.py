#!/usr/bin/env python3
"""Register the 8000-decode Phase B7 endpoint-only follow-up."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_ANALYSIS = LAB_DIR / "results/phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json"
DEFAULT_DESIGN = LAB_DIR / "results/phase-b6-honeycomb-posterior-predictive-design-2026-08-28.json"
DEFAULT_SELECTION = LAB_DIR / "results/phase-b7-honeycomb-endpoint-followup-selection-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b7-honeycomb-endpoint-followup-manifest-2026-08-28.json"
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.60, 0.28)}
NEW_SEEDS = [877001, 877002, 877003, 877004, 877005]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def seed_overlap_audit() -> dict:
    records = []
    overlaps = []
    for path in sorted((LAB_DIR / "results").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        seeds = payload.get("seeds")
        if not isinstance(seeds, list):
            continue
        if payload.get("campaign") == "phase-b7-honeycomb-endpoint-followup-2026-08-28":
            continue
        intersection = sorted(set(int(seed) for seed in seeds) & set(NEW_SEEDS))
        records.append({"path": str(path.relative_to(LAB_DIR)), "sha256": sha256(path)})
        if intersection:
            overlaps.append({"path": str(path.relative_to(LAB_DIR)), "seeds": intersection})
    if overlaps:
        raise ValueError(f"Phase B7 seed overlap: {overlaps}")
    return {"planned_seeds": NEW_SEEDS, "summaries_checked": len(records), "records": records, "overlaps": []}


def build_selection(map_path: Path, analysis_path: Path, design_path: Path) -> dict:
    phase_map = json.loads(map_path.read_text())
    analysis = json.loads(analysis_path.read_text())
    design = json.loads(design_path.read_text())
    rows = {(float(row["q"]), float(row["p"])): row for row in analysis["analyses"]}
    if set(rows) != EXPECTED or any(row["classification"] != "unresolved" for row in rows.values()):
        raise ValueError("Phase B7 source-cell drift")
    endpoint = next(item for item in design["designs"] if item["name"] == "endpoints_1000")
    forecasts = {(float(item["q"]), float(item["p"])): item for item in endpoint["cells"]}
    if set(forecasts) != EXPECTED or endpoint["total_additional_decodes"] != 8000:
        raise ValueError("Phase B7 posterior-predictive design drift")

    jobs = []
    for q, p in sorted(EXPECTED):
        source = rows[(q, p)]
        forecast = forecasts[(q, p)]
        if source["sizes"] != [5, 7, 9, 11, 13] or forecast["additional_shots"] != [1000, 0, 0, 0, 1000]:
            raise ValueError(f"Phase B7 endpoint inventory drift: {(q, p)}")
        jobs.append(
            {
                "branch": "endpoint_extension_1000_each",
                "q": q,
                "p": p,
                "sizes": [5, 13],
                "additional_shots_per_size": 1000,
                "expected_decodes": 2000,
                "current_shots": source["shots"],
                "posterior_predictive_probability_resolved": forecast[
                    "posterior_predictive_probability_resolved"
                ],
                "posterior_predictive_probability_false_direction_resolution": forecast[
                    "posterior_predictive_probability_false_direction_resolution"
                ],
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "source_map": {"path": str(map_path.relative_to(LAB_DIR)), "sha256": sha256(map_path)},
        "source_analysis": {"path": str(analysis_path.relative_to(LAB_DIR)), "sha256": sha256(analysis_path)},
        "design_evidence": {"path": str(design_path.relative_to(LAB_DIR)), "sha256": sha256(design_path)},
        "design_rule": "Apply the descriptive-efficiency-leading endpoints_1000 design to all four persistent cells without ranking cells after outcomes.",
        "jobs": jobs,
        "job_count": 4,
        "expected_new_decodes": 8000,
        "expected_resolved_cells": endpoint["expected_resolved_cells"],
        "expected_false_direction_resolutions": endpoint["expected_false_direction_resolutions"],
        "seed_overlap_audit": seed_overlap_audit(),
        "claim_boundary": "Registration only: same four cells, L=5/13 only, fixed 0.90 gate, no interpolation, no square lattice, and no asymptotic phase claim.",
    }


def build_manifest(selection_path: Path, selection: dict) -> dict:
    base = json.loads(
        (LAB_DIR / "results/phase2-residual80-honeycomb-q030-discovery-1000-2026-08-28.json").read_text()
    )
    return {
        "schema_version": 1,
        "status": "registered",
        "campaign": "phase-b7-honeycomb-endpoint-followup-2026-08-28",
        "purpose": "Test the smallest posterior-predictive follow-up on all four persistent Phase B6 cells.",
        "selection_evidence": {"path": str(selection_path.relative_to(LAB_DIR)), "sha256": sha256(selection_path)},
        "source_map": selection["source_map"],
        "source_analysis": selection["source_analysis"],
        "design_evidence": selection["design_evidence"],
        "lattice": "honeycomb",
        "new_seeds": NEW_SEEDS,
        "shots_per_seed": 200,
        "jobs": [{key: row[key] for key in ("branch", "q", "p", "sizes", "expected_decodes")} for row in selection["jobs"]],
        "job_count": 4,
        "workers_cap": 4,
        "expected_new_decodes": 8000,
        "decoder": base["decoder"],
        "required_source_hashes": base["source_hashes"],
        "analysis": {
            "primary": "Bayesian posterior OLS linear-projection slope against code distance",
            "classification_threshold": 0.9,
            "prior_sensitivity": "Jeffreys primary and uniform sensitivity",
            "pooling": "Pool each fresh L5/L13 count with the corresponding Phase B6 map-count vector.",
            "claim_boundary": "Update only these four payloads after completion, source, and prior-stability gates.",
        },
        "preflight_gate": "Implement and test non-overwriting dispatch, exact completion audit, map-count pooling, and exact four-payload rendering before launch.",
        "stop_rule": "Stop after four jobs and 8000 decodes; do not adapt cells, sizes, p, q, lattice, gate, or shot count after outcomes.",
        "launch_gate": "closed_implementation",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    selection = build_selection(args.phase_map, args.analysis, args.design)
    atomic_json(args.selection, selection)
    atomic_json(args.manifest, build_manifest(args.selection, selection))
    print(json.dumps({key: selection[key] for key in ("job_count", "expected_new_decodes", "expected_resolved_cells")}, indent=2))


if __name__ == "__main__":
    main()
