#!/usr/bin/env python3
"""Audit the single fresh Phase B4 output without scientific inference."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-completion-audit-2026-08-28.json"


def load_dispatcher():
    path = Path(__file__).with_name("submit_phase_b4_frontier.py")
    spec = importlib.util.spec_from_file_location("phase_b4_dispatcher_for_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_pair(manifest: dict, payload: dict, raw_path: Path) -> tuple[int, int]:
    if payload["campaign"] != manifest["campaign"] or payload["lattice"] != "honeycomb" or float(payload["q"]) != 0.05:
        raise ValueError("Phase B4 output campaign/lattice/q mismatch")
    if [float(value) for value in payload["p_grid"]] != [0.20] or [int(value) for value in payload["sizes"]] != [7, 9, 11]:
        raise ValueError("Phase B4 output p/size mismatch")
    if payload["seeds"] != manifest["new_seeds"] or payload["decoder"] != manifest["decoder"] or payload["source_hashes"] != manifest["required_source_hashes"]:
        raise ValueError("Phase B4 sampling/source/decoder mismatch")
    if not payload["source_stability"]["start_equals_end"]:
        raise ValueError("Phase B4 source changed during execution")
    metadata = payload["raw_records"]
    if int(metadata["records"]) != 3000 or metadata["sha256"] != sha256(raw_path):
        raise ValueError("Phase B4 raw metadata mismatch")
    rows = faithful = 0
    with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["campaign"] != manifest["campaign"] or float(row["q"]) != 0.05 or float(row["p"]) != 0.20:
                raise ValueError("Phase B4 raw coordinate mismatch")
            if int(row["L"]) not in {7, 9, 11} or int(row["seed"]) not in manifest["new_seeds"]:
                raise ValueError("Phase B4 raw size/seed mismatch")
            rows += 1
            faithful += bool(row["syndrome_faithful"])
    if rows != 3000 or faithful != rows or not payload["syndrome_fidelity"]["all_faithful"]:
        raise ValueError("Phase B4 row-count/syndrome-fidelity mismatch")
    return rows, faithful


def audit(manifest_path: Path) -> dict:
    dispatcher = load_dispatcher()
    manifest = json.loads(manifest_path.read_text())
    jobs = dispatcher.expand_jobs(manifest)
    dispatcher.validate(manifest_path, manifest, jobs, reject_output_conflicts=False)
    job = jobs[0]
    result_path, raw_path = Path(job["result"]), Path(job["raw"])
    if not result_path.is_file() or not raw_path.is_file():
        raise ValueError("missing Phase B4 output pair")
    payload = json.loads(result_path.read_text())
    rows, faithful = audit_pair(manifest, payload, raw_path)
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "data_complete_not_analyzed", "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)}, "jobs_expected": 1, "jobs_complete": 1, "raw_rows_expected": 3000, "raw_rows_observed": rows, "syndrome_faithful_rows": faithful, "record": {"summary": str(result_path), "summary_sha256": sha256(result_path), "raw": str(raw_path), "raw_sha256": sha256(raw_path)}, "scientific_analysis_performed": False, "crossing_statistic_used": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = audit(args.manifest)
    load_dispatcher().atomic_json(args.output, output)
    print(json.dumps({key: output[key] for key in ("status", "jobs_complete", "raw_rows_observed", "syndrome_faithful_rows")}, indent=2))


if __name__ == "__main__":
    main()
