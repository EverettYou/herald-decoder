#!/usr/bin/env python3
"""Audit all eight Phase B14 branch-specific output pairs before inference."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json"


def load_submit():
    path = Path(__file__).with_name("submit_phase_b14_two_branch.py")
    spec = importlib.util.spec_from_file_location("phase_b14_submit_for_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit_pair(manifest: dict, payload: dict, raw_path: Path, job: dict) -> tuple[int, int]:
    submit = load_submit()
    if (
        payload["campaign"] != manifest["campaign"]
        or payload["lattice"] != "honeycomb"
        or float(payload["q"]) != float(job["q"])
        or list(map(float, payload["p_grid"])) != [float(job["p"])]
        or list(map(int, payload["sizes"])) != job["sizes"]
        or list(map(int, payload["seeds"])) != job["seeds"]
        or int(payload["shots_per_seed"]) != job["shots_per_seed"]
    ):
        raise ValueError("Phase B14 output coordinate/sampling mismatch")
    if (
        payload["decoder"] != manifest["decoder"]
        or payload["source_hashes"] != manifest["required_source_hashes"]
        or not payload["source_stability"]["start_equals_end"]
    ):
        raise ValueError("Phase B14 decoder/source mismatch")
    expected = job["expected_decodes"]
    if payload["raw_records"]["records"] != expected or payload["raw_records"]["sha256"] != submit.sha256(raw_path):
        raise ValueError("Phase B14 raw metadata mismatch")
    rows = faithful = 0
    seen = set()
    with gzip.open(raw_path, "rt", encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if (
                row["campaign"] != manifest["campaign"]
                or row["lattice"] != "honeycomb"
                or float(row["q"]) != float(job["q"])
                or float(row["p"]) != float(job["p"])
                or int(row["L"]) not in job["sizes"]
                or int(row["seed"]) not in job["seeds"]
            ):
                raise ValueError("Phase B14 raw coordinate mismatch")
            key = (int(row["L"]), int(row["seed"]), int(row["shot"]))
            if key in seen or not 0 <= key[2] < job["shots_per_seed"]:
                raise ValueError("Phase B14 duplicate/out-of-range raw observation")
            seen.add(key)
            rows += 1
            faithful += bool(row["syndrome_faithful"])
    if rows != expected or len(seen) != expected or faithful != rows or not payload["syndrome_fidelity"]["all_faithful"]:
        raise ValueError("Phase B14 row/syndrome mismatch")
    return rows, faithful


def audit(manifest_path: Path) -> dict:
    submit = load_submit()
    manifest = json.loads(Path(manifest_path).read_text())
    jobs = submit.expand_jobs(manifest)
    submit.validate(manifest_path, manifest, jobs, reject_output_conflicts=False)
    records = []
    rows = faithful = 0
    for job in jobs:
        result_path, raw_path = Path(job["result"]), Path(job["raw"])
        if not result_path.is_file() or not raw_path.is_file():
            raise ValueError("missing Phase B14 output pair")
        count, faithful_count = audit_pair(manifest, json.loads(result_path.read_text()), raw_path, job)
        rows += count
        faithful += faithful_count
        records.append({
            "branch": job["branch"], "q": job["q"], "p": job["p"], "sizes": job["sizes"],
            "summary": str(result_path), "summary_sha256": submit.sha256(result_path),
            "raw": str(raw_path), "raw_sha256": submit.sha256(raw_path),
            "rows": count, "syndrome_faithful_rows": faithful_count,
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "data_complete_not_analyzed",
        "manifest": {"path": str(manifest_path), "sha256": submit.sha256(manifest_path)},
        "jobs_expected": 8, "jobs_complete": len(records),
        "raw_rows_expected": 10000, "raw_rows_observed": rows,
        "syndrome_faithful_rows": faithful,
        "records": records,
        "scientific_analysis_performed": False,
    }


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
