#!/usr/bin/env python3
"""Register the smallest Phase B6 matrix for the four Phase B5 frontier cells."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_B5_SELECTION = LAB_DIR / "results/phase-b5-honeycomb-persistent-frontier-selection-2026-08-28.json"
DEFAULT_B5_AUDIT = LAB_DIR / "results/phase-b5-honeycomb-persistent-frontier-completion-audit-2026-08-28.json"
DEFAULT_SELECTION = LAB_DIR / "results/phase-b6-honeycomb-four-cell-frontier-selection-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b6-honeycomb-four-cell-frontier-manifest-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_frontier():
    path = Path(__file__).with_name("select_phase_b3_frontier_reuse.py")
    spec = importlib.util.spec_from_file_location("phase_b6_frontier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cell_by_key(phase_map: dict, key: tuple[float, float]) -> dict:
    for qrow in phase_map["analyses"]:
        for cell in qrow["cells"]:
            if abs(float(qrow["q"]) - key[0]) < 1e-12 and abs(float(cell["p"]) - key[1]) < 1e-12:
                return cell
    raise ValueError(f"missing Phase B6 source cell: {key}")


def build_selection(map_path: Path, b5_selection_path: Path, b5_audit_path: Path) -> dict:
    phase_map = json.loads(map_path.read_text())
    candidates = load_frontier().frontier_candidates(phase_map)
    expected = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.60, 0.28)}
    if {(row["q"], row["p"]) for row in candidates} != expected:
        raise ValueError("Phase B6 frontier candidate set drift")

    jobs = []
    for row in candidates:
        key = (row["q"], row["p"])
        cell = cell_by_key(phase_map, key)
        current = {int(size): int(shots) for size, shots in zip(cell["sizes"], cell["shots"])}
        if key == (0.55, 0.24):
            branch, sizes = "endpoint_extension_l5_l13", [5, 13]
        else:
            if current != {5: 1000, 7: 1000, 9: 1000, 11: 2000, 13: 1000}:
                raise ValueError(f"Phase B6 five-distance shot inventory drift: {key}")
            branch, sizes = "rebalance_to_2000_shots", [5, 7, 9, 13]
        jobs.append({**row, "branch": branch, "sizes": sizes, "additional_shots_per_size": 1000, "expected_decodes": 1000 * len(sizes), "current_sizes": list(cell["sizes"]), "current_shots": list(cell["shots"])})

    b5_selection = json.loads(b5_selection_path.read_text())
    b5_audit = json.loads(b5_audit_path.read_text())
    consumed = set()
    for row in b5_selection["prior_adaptive_evidence"]:
        consumed.add((LAB_DIR / row["base_path"]).resolve())
        consumed.add((LAB_DIR / row["adaptive_path"]).resolve())
    for row in b5_audit["records"]:
        consumed.add(Path(row["summary"]).resolve())

    active_decoder = phase_map["analyses"][0]["cells"][0].get("decoder")
    if active_decoder is None:
        base = json.loads((LAB_DIR / "results/phase2-residual80-honeycomb-q030-discovery-1000-2026-08-28.json").read_text())
        active_decoder, active_sources = base["decoder"], base["source_hashes"]
    else:
        active_sources = phase_map["analyses"][0]["cells"][0]["source_hashes"]
    records, compatible_unused = [], []
    for path in sorted((LAB_DIR / "results").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if payload.get("lattice") != "honeycomb" or "q" not in payload:
            continue
        matching = [key for key in expected if abs(float(payload["q"]) - key[0]) < 1e-12 and any(abs(float(p) - key[1]) < 1e-12 for p in payload.get("p_grid", []))]
        if not matching:
            continue
        if payload.get("campaign") == "phase-b6-honeycomb-four-cell-frontier-2026-08-28":
            disposition = "registered_phase_b6_output_not_prior_evidence"
        elif payload.get("campaign") == "phase-b7-honeycomb-endpoint-followup-2026-08-28":
            disposition = "subsequent_phase_b7_output_not_prior_evidence"
        elif payload.get("campaign") == "phase-b8-honeycomb-raise-minimum-2026-08-28":
            disposition = "subsequent_phase_b8_output_not_prior_evidence"
        elif payload.get("campaign") == "phase-b9-honeycomb-measured-endpoints-2026-08-28":
            disposition = "subsequent_phase_b9_output_not_prior_evidence"
        elif payload.get("campaign") == "phase-b10-honeycomb-measured-endpoints-2026-08-28":
            # This is a reconstruction of the Phase B6 registration-time
            # inventory. Later campaigns cannot be retroactive prior evidence.
            disposition = "subsequent_phase_b10_output_not_prior_evidence"
        elif path.resolve() in consumed:
            disposition = "already_consumed_in_phase_b5_map"
        elif payload.get("decoder") != active_decoder or payload.get("source_hashes") != active_sources:
            disposition = "excluded_incompatible_decoder_or_source"
        else:
            disposition = "compatible_unused"
            compatible_unused.append(str(path.relative_to(LAB_DIR)))
        records.append({"path": str(path.relative_to(LAB_DIR)), "sha256": sha256(path), "disposition": disposition})
    if compatible_unused:
        raise ValueError(f"unexpected compatible unused Phase B6 evidence: {compatible_unused}")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "source_map": {"path": str(map_path.relative_to(LAB_DIR)), "sha256": sha256(map_path)},
        "frontier_rule": "All unresolved four-neighbor cells adjacent to both decodable and undecodable cells.",
        "frontier_candidates": candidates,
        "source_compatibility_audit": {"records": records, "compatible_unused_count": 0},
        "design_rule": "Broaden the three-distance q=0.55 cell with L5/L13; for five-distance cells, add shots only at the four 1000-shot sizes so every distance reaches 2000 without oversampling L11.",
        "new_jobs": sorted(jobs, key=lambda row: (row["q"], row["p"])),
        "candidate_count": 4,
        "new_job_count": 4,
        "expected_new_decodes": 14000,
        "claim_boundary": "Registration only. No crossing statistic, p/q interpolation, new cell, square lattice, or distance outside L=5..13.",
    }


def build_manifest(selection_path: Path, selection: dict) -> dict:
    base = json.loads((LAB_DIR / "results/phase2-residual80-honeycomb-q030-discovery-1000-2026-08-28.json").read_text())
    return {
        "schema_version": 1,
        "status": "registered",
        "campaign": "phase-b6-honeycomb-four-cell-frontier-2026-08-28",
        "purpose": "Cover all four Phase B5 persistent frontier cells with balanced shots or missing endpoints.",
        "selection_evidence": {"path": str(selection_path.relative_to(LAB_DIR)), "sha256": sha256(selection_path)},
        "source_map": selection["source_map"],
        "lattice": "honeycomb",
        "frontier_candidate_count": 4,
        "new_seeds": [876001, 876002, 876003, 876004, 876005],
        "shots_per_seed": 200,
        "jobs": [{k: row[k] for k in ("branch", "q", "p", "sizes", "expected_decodes")} for row in selection["new_jobs"]],
        "job_count": 4,
        "workers_cap": 4,
        "expected_new_decodes": 14000,
        "decoder": base["decoder"],
        "required_source_hashes": base["source_hashes"],
        "analysis": {
            "primary": "Bayesian posterior OLS linear-projection slope against code distance",
            "classification_threshold": 0.9,
            "prior_sensitivity": "Jeffreys primary and uniform sensitivity",
            "pooling": "Pool fresh counts only with each Phase B5 map cell's declared logical_errors/shots vector.",
            "claim_boundary": "Update only these four payloads after completion, source, and prior-stability gates."
        },
        "preflight_gate": "Implement and test a four-job non-overwriting dispatcher, exact completion audit, map-count pooling analyzer, and exact four-payload renderer before launch.",
        "stop_rule": "Stop after four jobs and 14000 decodes. Do not add another cell, p/q midpoint, square lattice, or distance outside L=5..13.",
        "launch_gate": "closed_implementation"
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--phase-b5-selection", type=Path, default=DEFAULT_B5_SELECTION)
    parser.add_argument("--phase-b5-audit", type=Path, default=DEFAULT_B5_AUDIT)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    selection = build_selection(args.phase_map, args.phase_b5_selection, args.phase_b5_audit)
    atomic_json(args.selection, selection)
    atomic_json(args.manifest, build_manifest(args.selection, selection))
    print(json.dumps({key: selection[key] for key in ("candidate_count", "new_job_count", "expected_new_decodes")}, indent=2))


if __name__ == "__main__":
    main()
