#!/usr/bin/env python3
"""Select and register the newly exposed Phase B4 honeycomb frontier cell."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_B3_ANALYSIS = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json"
DEFAULT_SELECTION = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-selection-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json"
ACTIVE_BASE = LAB_DIR / "results/phase2-residual80-honeycomb-q005-discovery-1000-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_b3_selector():
    path = Path(__file__).with_name("select_phase_b3_frontier_reuse.py")
    spec = importlib.util.spec_from_file_location("phase_b3_selector_for_b4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def contains_p(summary: dict, target: float) -> bool:
    grid = summary.get("p_grid", summary.get("p_values", []))
    return any(abs(float(value) - target) < 1e-12 for value in grid)


def source_compatibility_audit(active_base: dict) -> dict:
    records = []
    for path in sorted((LAB_DIR / "results").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if payload.get("lattice") != "honeycomb" or abs(float(payload.get("q", -1.0)) - 0.05) > 1e-12:
            continue
        if not contains_p(payload, 0.20) or not {7, 9, 11}.issubset(set(payload.get("sizes", []))):
            continue
        if path == ACTIVE_BASE:
            disposition = "already_consumed_in_active_map"
        elif path.name == "phase-b4-honeycomb-l7-9-11-q005-p020-2026-08-28.json":
            disposition = "registered_phase_b4_output"
        elif payload.get("decoder") != active_base["decoder"] or payload.get("source_hashes") != active_base["source_hashes"]:
            disposition = "excluded_incompatible_decoder_or_source"
        else:
            disposition = "compatible_unused"
        records.append({"path": str(path.relative_to(LAB_DIR)), "sha256": sha256(path), "disposition": disposition})
    temporary_raw = sorted((LAB_DIR / "results").glob(".phase2-honeycomb-q005-*.tmp-*"))
    for path in temporary_raw:
        records.append({
            "path": str(path.relative_to(LAB_DIR)),
            "sha256": sha256(path),
            "disposition": "excluded_orphan_temporary_raw_without_compatible_final_summary",
        })
    compatible_unused = [row for row in records if row["disposition"] == "compatible_unused"]
    if compatible_unused:
        raise ValueError(f"unexpected compatible unused q=0.05,p=0.20 evidence: {compatible_unused}")
    if not any(row["disposition"] == "already_consumed_in_active_map" for row in records):
        raise ValueError("active q=0.05 base shard missing from audit")
    return {"records": records, "compatible_unused_count": 0, "conclusion": "No source-compatible unused measurement can replace fresh independent shots."}


def build_selection(map_path: Path, b3_analysis_path: Path) -> dict:
    phase_map = json.loads(map_path.read_text())
    b3_analysis = json.loads(b3_analysis_path.read_text())
    active_base = json.loads(ACTIVE_BASE.read_text())
    candidates = load_b3_selector().frontier_candidates(phase_map)
    expected = {(0.30, 0.20), (0.40, 0.20), (0.55, 0.24), (0.60, 0.28), (0.05, 0.20), (0.35, 0.20)}
    if {(row["q"], row["p"]) for row in candidates} != expected:
        raise ValueError("Phase B4 frontier candidate set drift")
    recently_tested = {(float(row["q"]), float(row["p"])) for row in b3_analysis["analyses"] if row["classification"] == "unresolved"}
    expected_recent = expected - {(0.05, 0.20)}
    if recently_tested != expected_recent:
        raise ValueError("Phase B3 unresolved carry-forward set drift")
    newly_exposed = [row for row in candidates if (row["q"], row["p"]) not in recently_tested]
    if [(row["q"], row["p"]) for row in newly_exposed] != [(0.05, 0.20)]:
        raise ValueError("expected exactly the newly exposed q=0.05,p=0.20 cell")
    audit = source_compatibility_audit(active_base)
    job = {**newly_exposed[0], "branch": "independent_shots", "sizes": [7, 9, 11], "additional_shots_per_size": 1000}
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "source_map": {"path": str(map_path), "sha256": sha256(map_path)},
        "phase_b3_analysis": {"path": str(b3_analysis_path), "sha256": sha256(b3_analysis_path)},
        "selection_rule": "Recompute all red/green-adjacent gray cells; carry forward cells just tested in Phase B3 and select only a newly exposed untested cell after a source-compatibility audit.",
        "frontier_candidates": candidates,
        "recently_tested_unresolved_cells": sorted([{"q": q, "p": p} for q, p in recently_tested], key=lambda row: (row["q"], row["p"])),
        "newly_exposed_cells": newly_exposed,
        "source_compatibility_audit": audit,
        "new_jobs": [job],
        "candidate_count": 6,
        "recently_tested_count": 5,
        "new_job_count": 1,
        "expected_new_decodes": 3000,
        "claim_boundary": "Selection and registration only. Do not reinterpret the five Phase B3-unresolved cells, expand the grid, or use crossing statistics.",
    }


def build_manifest(selection_path: Path, selection: dict) -> dict:
    active_base = json.loads(ACTIVE_BASE.read_text())
    return {
        "schema_version": 1,
        "status": "registered",
        "campaign": "phase-b4-honeycomb-new-frontier-2026-08-28",
        "purpose": "Test the one newly exposed red/green-adjacent gray cell without immediately resampling five cells that Phase B3 just left unresolved.",
        "selection_evidence": {"path": str(selection_path.relative_to(LAB_DIR)), "sha256": sha256(selection_path)},
        "lattice": "honeycomb",
        "frontier_candidate_count": selection["candidate_count"],
        "recently_tested_count": selection["recently_tested_count"],
        "new_seeds": [874001, 874002, 874003, 874004, 874005],
        "shots_per_seed": 200,
        "jobs": [{"branch": "independent_shots", "q": 0.05, "p": 0.20, "sizes": [7, 9, 11], "expected_decodes": 3000}],
        "job_count": 1,
        "workers_cap": 1,
        "expected_new_decodes": 3000,
        "decoder": active_base["decoder"],
        "required_source_hashes": active_base["source_hashes"],
        "analysis": {
            "primary": "Bayesian posterior OLS linear-projection slope against code distance",
            "classification_threshold": 0.9,
            "prior_sensitivity": "Jeffreys Beta(1/2,1/2) primary and uniform Beta(1,1) sensitivity",
            "pooling": "Pool only the new independent L7/L9/L11 counts with the active Phase 2 q=0.05,p=0.20 base counts.",
            "claim_boundary": "Update only q=0.05,p=0.20 if it resolves under both priors; otherwise leave it gray.",
        },
        "preflight_gate": "Implement and test a non-overwriting dispatcher, completion audit, pooled analyzer, and exact one-cell renderer before production launch.",
        "stop_rule": "Stop after one job and 3000 decodes. Do not resample the five Phase B3-unresolved cells or expand p/q/L.",
        "launch_gate": "closed_implementation",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--phase-b3-analysis", type=Path, default=DEFAULT_B3_ANALYSIS)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    selection = build_selection(args.phase_map, args.phase_b3_analysis)
    atomic_json(args.selection, selection)
    manifest = build_manifest(args.selection, selection)
    atomic_json(args.manifest, manifest)
    print(json.dumps({"selection": str(args.selection), "manifest": str(args.manifest), "candidate_count": 6, "new_job_count": 1, "expected_new_decodes": 3000}, indent=2))


if __name__ == "__main__":
    main()
