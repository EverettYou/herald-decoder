#!/usr/bin/env python3
"""Fail-closed audit of the five Phase S1 measurement shards reused by Phase B3."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b3-honeycomb-frontier-reuse-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b3-honeycomb-reuse-source-audit-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def audit(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    selection_path = LAB_DIR / manifest["selection_evidence"]["path"]
    selection = json.loads(selection_path.read_text())
    completion_path = LAB_DIR / manifest["selection_evidence"]["phase_s1_completion_audit"]
    completion = json.loads(completion_path.read_text())
    baseline_path = LAB_DIR / "results/phase2-residual80-honeycomb-q000-discovery-1000-2026-08-28.json"
    baseline = json.loads(baseline_path.read_text())
    records_by_coordinate = {(float(row["q"]), float(row["p"])): row for row in completion["records"]}
    records = []
    for source in selection["reused_phase_s1_evidence"]:
        key = (float(source["q"]), float(source["p"]))
        path = LAB_DIR / source["path"]
        payload = json.loads(path.read_text())
        record = records_by_coordinate.get(key)
        if record is None or sha256(path) != source["sha256"] or sha256(path) != record["summary_sha256"]:
            raise ValueError(f"Phase B3 reuse summary hash/audit mismatch at {key}")
        expected_sizes = [7, 9, 11] if source["reuse_kind"] == "seed_limited" else [11, 13]
        if [int(value) for value in payload["sizes"]] != expected_sizes or record["sizes"] != expected_sizes:
            raise ValueError(f"Phase B3 reuse size mismatch at {key}")
        if float(payload["q"]) != key[0] or [float(value) for value in payload["p_grid"]] != [key[1]]:
            raise ValueError(f"Phase B3 reuse coordinate mismatch at {key}")
        if payload["source_hashes"] != manifest["required_source_hashes"] or payload["source_hashes"] != baseline["source_hashes"]:
            raise ValueError(f"Phase B3 reuse source cohort mismatch at {key}")
        if payload["decoder"] != manifest["decoder"] or payload["decoder"] != baseline["decoder"]:
            raise ValueError(f"Phase B3 reuse decoder mismatch at {key}")
        if not payload["source_stability"]["start_equals_end"] or record["rows"] != record["syndrome_faithful_rows"]:
            raise ValueError(f"Phase B3 reuse stability/fidelity mismatch at {key}")
        records.append({"q": key[0], "p": key[1], "reuse_kind": source["reuse_kind"], "sizes": expected_sizes, "summary": str(path), "summary_sha256": sha256(path), "raw": record["raw"], "raw_sha256": record["raw_sha256"], "rows": record["rows"], "syndrome_faithful_rows": record["syndrome_faithful_rows"]})
    if len(records) != 5 or sum(row["rows"] for row in records) != 11000:
        raise ValueError("Phase B3 reuse cohort must contain five audited shards and 11000 rows")
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "reuse_sources_verified", "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)}, "selection": {"path": str(selection_path), "sha256": sha256(selection_path)}, "phase_s1_completion_audit": {"path": str(completion_path), "sha256": sha256(completion_path)}, "records": records, "reuse_sources_verified": 5, "reused_raw_rows": 11000, "source_cohort_matches": True, "decoder_config_matches": True, "withdrawn_interpretation_reused": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = audit(args.manifest)
    atomic_json(args.output, output)
    print(json.dumps({key: output[key] for key in ("status", "reuse_sources_verified", "reused_raw_rows")}, indent=2))


if __name__ == "__main__":
    main()
