#!/usr/bin/env python3
"""Register the smallest Phase B5 matrix covering all five persistent frontier cells."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_B3_SELECTION = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-selection-2026-08-28.json"
DEFAULT_B3_ANALYSIS = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json"
DEFAULT_SELECTION = LAB_DIR / "results/phase-b5-honeycomb-persistent-frontier-selection-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b5-honeycomb-persistent-frontier-manifest-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_b3_selector():
    path = Path(__file__).with_name("select_phase_b3_frontier_reuse.py")
    spec = importlib.util.spec_from_file_location("phase_b3_selector_for_b5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def base_path(q: float) -> Path:
    return LAB_DIR / "results" / f"phase2-residual80-honeycomb-q{int(round(100*q)):03d}-discovery-1000-2026-08-28.json"


def build_selection(map_path: Path, b3_selection_path: Path, b3_analysis_path: Path) -> dict:
    phase_map = json.loads(map_path.read_text())
    b3_selection = json.loads(b3_selection_path.read_text())
    b3_analysis = json.loads(b3_analysis_path.read_text())
    candidates = load_b3_selector().frontier_candidates(phase_map)
    expected = {(0.30, 0.20), (0.35, 0.20), (0.40, 0.20), (0.55, 0.24), (0.60, 0.28)}
    if {(row["q"], row["p"]) for row in candidates} != expected:
        raise ValueError("Phase B5 persistent frontier set drift")
    b3_rows = {(float(row["q"]), float(row["p"])): row for row in b3_analysis["analyses"]}
    if set(b3_rows) - {(0.10, 0.20)} != expected or any(b3_rows[key]["classification"] != "unresolved" for key in expected):
        raise ValueError("Phase B5 candidates must be exactly the five B3-unresolved cells")
    reuse_by_key = {(float(row["q"]), float(row["p"])): row for row in b3_selection["reused_phase_s1_evidence"]}
    consumed = set()
    prior_evidence = []
    jobs = []
    for row in candidates:
        key = (row["q"], row["p"])
        base = base_path(row["q"])
        consumed.add(base.resolve())
        if key == (0.55, 0.24):
            existing = LAB_DIR / "results/phase-b3-honeycomb-l7-9-11-q055-p024-2026-08-28.json"
            branch, sizes, decodes = "independent_shots", [7, 9, 11], 3000
        else:
            existing = LAB_DIR / reuse_by_key[key]["path"]
            branch, sizes, decodes = "distance_extension_l5", [5], 1000
        consumed.add(existing.resolve())
        prior_evidence.append({"q": key[0], "p": key[1], "base_path": str(base.relative_to(LAB_DIR)), "base_sha256": sha256(base), "adaptive_path": str(existing.relative_to(LAB_DIR)), "adaptive_sha256": sha256(existing), "b3_pooling_kind": b3_rows[key]["pooling_kind"], "b3_classification": "unresolved"})
        jobs.append({**row, "branch": branch, "sizes": sizes, "additional_shots_per_size": 1000, "expected_decodes": decodes})
    audit_records = []
    compatible_unused = []
    for path in sorted((LAB_DIR / "results").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if payload.get("lattice") != "honeycomb" or "q" not in payload:
            continue
        q = float(payload["q"])
        matching = [key for key in expected if abs(key[0] - q) < 1e-12]
        if not matching:
            continue
        p_grid = [float(value) for value in payload.get("p_grid", [])]
        if not any(any(abs(p - key[1]) < 1e-12 for p in p_grid) for key in matching):
            continue
        active = json.loads(base_path(q).read_text())
        if path.resolve() in consumed:
            disposition = "already_consumed_in_phase_b5_pool"
        elif str(payload.get("campaign", "")).startswith("phase-b"):
            disposition = "post_registration_adaptive_output_not_prior_evidence"
        elif payload.get("decoder") != active["decoder"] or payload.get("source_hashes") != active["source_hashes"]:
            disposition = "excluded_incompatible_decoder_or_source"
        else:
            disposition = "compatible_unused"
            compatible_unused.append(str(path.relative_to(LAB_DIR)))
        audit_records.append({"path": str(path.relative_to(LAB_DIR)), "sha256": sha256(path), "disposition": disposition})
    if compatible_unused:
        raise ValueError(f"unexpected compatible unused persistent-frontier evidence: {compatible_unused}")
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "source_map": {"path": str(map_path), "sha256": sha256(map_path)}, "phase_b3_analysis": {"path": str(b3_analysis_path), "sha256": sha256(b3_analysis_path)}, "selection_rule": "Cover every persistent red/green-adjacent gray cell. Add L5 where B3 already supplied L13; add independent same-window shots where B3 supplied shots. Reuse all audited compatible evidence and do not expand the grid.", "frontier_candidates": candidates, "newly_exposed_cells": [], "prior_adaptive_evidence": sorted(prior_evidence, key=lambda row: (row["q"], row["p"])), "source_compatibility_audit": {"records": audit_records, "compatible_unused_count": 0}, "new_jobs": sorted(jobs, key=lambda row: (row["q"], row["p"])), "candidate_count": 5, "new_job_count": 5, "expected_new_decodes": 7000, "claim_boundary": "Selection and registration only. No crossing statistic, interpolation, p/q midpoint, square lattice, or unrestricted distance expansion."}


def build_manifest(selection_path: Path, selection: dict) -> dict:
    active = json.loads(base_path(0.30).read_text())
    return {"schema_version": 1, "status": "registered", "campaign": "phase-b5-honeycomb-persistent-frontier-2026-08-28", "purpose": "Cover all five persistent frontier cells with the smallest discriminating L5-or-shot matrix.", "selection_evidence": {"path": str(selection_path.relative_to(LAB_DIR)), "sha256": sha256(selection_path)}, "lattice": "honeycomb", "frontier_candidate_count": 5, "new_seeds": [875001, 875002, 875003, 875004, 875005], "shots_per_seed": 200, "jobs": [{"branch": row["branch"], "q": row["q"], "p": row["p"], "sizes": row["sizes"], "expected_decodes": row["expected_decodes"]} for row in selection["new_jobs"]], "job_count": 5, "workers_cap": 4, "expected_new_decodes": 7000, "decoder": active["decoder"], "required_source_hashes": active["source_hashes"], "analysis": {"primary": "Bayesian posterior OLS linear-projection slope against code distance", "classification_threshold": 0.9, "prior_sensitivity": "Jeffreys primary and uniform sensitivity", "distance_extension_pooling": "For q=0.30,0.35,0.40,p=0.20 and q=0.60,p=0.28, pool Phase 2 L7/L9/L11 with the consumed Phase S1 L11/L13 shard and add fresh L5, yielding L5/L7/L9/L11/L13.", "shot_pooling": "For q=0.55,p=0.24, pool Phase 2, Phase B3, and fresh independent L7/L9/L11 counts.", "claim_boundary": "Update only these five payloads and only after prior-stability sensitivity."}, "preflight_gate": "Implement and test a five-job non-overwriting dispatcher, source-chain audit, completion audit, heterogeneous pooled analyzer, and exact five-payload renderer before launch.", "stop_rule": "Stop after five jobs and 7000 decodes. Do not add another cell, p/q midpoint, square lattice, or distance beyond registered L5.", "launch_gate": "closed_implementation"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--phase-b3-selection", type=Path, default=DEFAULT_B3_SELECTION)
    parser.add_argument("--phase-b3-analysis", type=Path, default=DEFAULT_B3_ANALYSIS)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    selection = build_selection(args.phase_map, args.phase_b3_selection, args.phase_b3_analysis)
    atomic_json(args.selection, selection)
    manifest = build_manifest(args.selection, selection)
    atomic_json(args.manifest, manifest)
    print(json.dumps({"candidate_count": 5, "newly_exposed_count": 0, "job_count": 5, "expected_new_decodes": 7000}, indent=2))


if __name__ == "__main__":
    main()
