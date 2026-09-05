#!/usr/bin/env python3
"""Audit all Phase B7 summary/raw pairs before inference."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b7-honeycomb-endpoint-followup-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b7-honeycomb-endpoint-followup-completion-audit-2026-08-28.json"


def load_submit():
    path = Path(__file__).with_name("submit_phase_b7_endpoints.py")
    spec = importlib.util.spec_from_file_location("phase_b7_submit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_pair(manifest: dict, payload: dict, raw_path: Path, job: dict) -> tuple[int, int]:
    if payload["campaign"] != manifest["campaign"] or payload["lattice"] != "honeycomb" or float(payload["q"]) != job["q"] or [float(value) for value in payload["p_grid"]] != [job["p"]] or [int(value) for value in payload["sizes"]] != [5, 13]:
        raise ValueError("Phase B7 output coordinate/config mismatch")
    if payload["seeds"] != manifest["new_seeds"] or payload["decoder"] != manifest["decoder"] or payload["source_hashes"] != manifest["required_source_hashes"] or not payload["source_stability"]["start_equals_end"]:
        raise ValueError("Phase B7 sampling/source/decoder mismatch")
    if payload["raw_records"]["records"] != 2000 or payload["raw_records"]["sha256"] != sha256(raw_path):
        raise ValueError("Phase B7 raw metadata mismatch")
    rows = faithful = 0
    with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["campaign"] != manifest["campaign"] or float(row["q"]) != job["q"] or float(row["p"]) != job["p"] or int(row["L"]) not in [5, 13] or int(row["seed"]) not in manifest["new_seeds"]:
                raise ValueError("Phase B7 raw coordinate mismatch")
            rows += 1
            faithful += bool(row["syndrome_faithful"])
    if rows != 2000 or faithful != rows or not payload["syndrome_fidelity"]["all_faithful"]:
        raise ValueError("Phase B7 row/syndrome mismatch")
    return rows, faithful


def audit(manifest_path: Path) -> dict:
    submit = load_submit()
    manifest = json.loads(manifest_path.read_text())
    jobs = submit.expand_jobs(manifest)
    submit.validate(manifest_path, manifest, jobs, reject_output_conflicts=False)
    records = []
    rows = faithful = 0
    for job in jobs:
        result, raw = Path(job["result"]), Path(job["raw"])
        if not result.is_file() or not raw.is_file():
            raise ValueError("missing Phase B7 output pair")
        observed, valid = audit_pair(manifest, json.loads(result.read_text()), raw, job)
        rows += observed
        faithful += valid
        records.append({"q": job["q"], "p": job["p"], "sizes": [5, 13], "summary": str(result), "summary_sha256": sha256(result), "raw": str(raw), "raw_sha256": sha256(raw), "rows": observed, "syndrome_faithful_rows": valid})
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "data_complete_not_analyzed", "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)}, "jobs_expected": 4, "jobs_complete": 4, "raw_rows_expected": 8000, "raw_rows_observed": rows, "syndrome_faithful_rows": faithful, "records": records, "scientific_analysis_performed": False, "crossing_statistic_used": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = audit(args.manifest)
    load_submit().atomic_json(args.output, output)
    print(json.dumps({key: output[key] for key in ("status", "jobs_complete", "raw_rows_observed")}, indent=2))


if __name__ == "__main__":
    main()
