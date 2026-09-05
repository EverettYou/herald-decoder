#!/usr/bin/env python3
"""Audit Phase B2 outputs without performing scientific inference."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-completion-audit-2026-08-28.json"


def load_dispatcher():
    path = Path(__file__).with_name("submit_phase_b2_gray_frontier.py")
    spec = importlib.util.spec_from_file_location("phase_b2_dispatcher", path)
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


def audit(manifest_path: Path) -> dict:
    dispatcher = load_dispatcher()
    manifest = json.loads(manifest_path.read_text())
    jobs = dispatcher.expand_jobs(manifest)
    dispatcher.validate_manifest(manifest, jobs)
    baseline_path = LAB_DIR / "results/phase2-residual80-honeycomb-q000-discovery-1000-2026-08-28.json"
    baseline = json.loads(baseline_path.read_text())
    records, total_rows, total_faithful = [], 0, 0
    for job in jobs:
        result_path, raw_path = Path(job["result"]), Path(job["raw"])
        if not result_path.is_file() or not raw_path.is_file():
            raise ValueError(f"missing output pair for {job['stem']}")
        payload = json.loads(result_path.read_text())
        if payload["campaign"] != manifest["campaign"] or payload["lattice"] != manifest["lattice"]:
            raise ValueError(f"campaign or lattice mismatch for {job['stem']}")
        if float(payload["q"]) != job["q"] or [float(value) for value in payload["p_grid"]] != [job["p"]]:
            raise ValueError(f"coordinate mismatch for {job['stem']}")
        if [int(value) for value in payload["sizes"]] != job["sizes"]:
            raise ValueError(f"size mismatch for {job['stem']}")
        if payload["seeds"] != manifest["new_seeds"] or int(payload["shots_per_seed"]) != int(manifest["shots_per_seed"]):
            raise ValueError(f"sampling mismatch for {job['stem']}")
        if payload["decoder"] != manifest["decoder"] or payload["decoder"] != baseline["decoder"]:
            raise ValueError(f"decoder mismatch for {job['stem']}")
        if payload["source_hashes"] != manifest["required_source_hashes"] or payload["source_hashes"] != baseline["source_hashes"]:
            raise ValueError(f"source-cohort mismatch for {job['stem']}")
        if payload["runtime"] != baseline["runtime"] or not payload["source_stability"]["start_equals_end"]:
            raise ValueError(f"runtime or source-stability mismatch for {job['stem']}")
        raw_metadata = payload["raw_records"]
        if int(raw_metadata["records"]) != job["expected_decodes"] or raw_metadata["sha256"] != sha256(raw_path):
            raise ValueError(f"raw metadata mismatch for {job['stem']}")
        rows = faithful = 0
        with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if (row["campaign"] != manifest["campaign"] or row["lattice"] != manifest["lattice"] or float(row["q"]) != job["q"] or float(row["p"]) != job["p"] or int(row["L"]) not in job["sizes"] or int(row["seed"]) not in manifest["new_seeds"]):
                    raise ValueError(f"raw coordinate mismatch for {job['stem']}")
                rows += 1
                faithful += bool(row["syndrome_faithful"])
        fidelity = payload["syndrome_fidelity"]
        if rows != job["expected_decodes"] or faithful != rows or int(fidelity["checked_corrections"]) != rows or int(fidelity["faithful_corrections"]) != rows or not fidelity["all_faithful"]:
            raise ValueError(f"row-count or syndrome-fidelity mismatch for {job['stem']}")
        if len(payload["per_seed"]) != len(job["sizes"]) * len(manifest["new_seeds"]) or len(payload["summaries"]) != len(job["sizes"]):
            raise ValueError(f"summary coverage mismatch for {job['stem']}")
        total_rows += rows
        total_faithful += faithful
        records.append({"stem": job["stem"], "branch": job["branch"], "q": job["q"], "p": job["p"], "sizes": job["sizes"], "summary": str(result_path), "summary_sha256": sha256(result_path), "raw": str(raw_path), "raw_sha256": raw_metadata["sha256"], "rows": rows, "syndrome_faithful_rows": faithful, "source_stable": True})
    if len(records) != int(manifest["job_count"]) or total_rows != int(manifest["expected_new_decodes"]):
        raise ValueError("completed matrix differs from Phase B2 contract")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "data_complete_not_analyzed",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "jobs_expected": int(manifest["job_count"]),
        "jobs_complete": len(records),
        "raw_rows_expected": int(manifest["expected_new_decodes"]),
        "raw_rows_observed": total_rows,
        "syndrome_faithful_rows": total_faithful,
        "source_cohort_matches_phase2": True,
        "decoder_config_matches_phase2": True,
        "records": records,
        "scientific_analysis_performed": False,
        "crossing_statistic_used": False,
    }


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
