#!/usr/bin/env python3
"""Pool Phase B2 counts and apply the preregistered Bayesian fuzzy trend."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json"


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary_counts(payload: dict, *, q: float, p: float, sizes: list[int]) -> dict[int, tuple[int, int]]:
    rows = {}
    for row in payload["summaries"]:
        if abs(float(row["q"]) - q) < 1e-12 and abs(float(row["p"]) - p) < 1e-12 and int(row["L"]) in sizes:
            size = int(row["L"])
            if size in rows:
                raise ValueError(f"duplicate summary for L={size}")
            rows[size] = (int(row["logical_errors"]), int(row["shots"]))
    if set(rows) != set(sizes):
        raise ValueError(f"incomplete summary coverage: expected {sizes}, observed {sorted(rows)}")
    return rows


def pool_counts(branch: str, existing: dict[int, tuple[int, int]], fresh: dict[int, tuple[int, int]]) -> dict[int, tuple[int, int]]:
    if branch == "distance_leverage":
        if set(existing) != {7, 9, 11} or set(fresh) != {5, 13}:
            raise ValueError("distance-leverage pooling requires old L7/9/11 plus fresh L5/13")
        return {**fresh, **existing}
    if branch.startswith("shot_limited_"):
        if set(existing) != {7, 9, 11} or set(fresh) != {7, 9, 11}:
            raise ValueError("shot pooling requires matching L7/9/11 summaries")
        return {size: (existing[size][0] + fresh[size][0], existing[size][1] + fresh[size][1]) for size in (7, 9, 11)}
    raise ValueError(f"unknown Phase B2 branch {branch}")


def base_summary_path(q: float) -> Path:
    return LAB_DIR / "results" / f"phase2-residual80-honeycomb-q{int(round(100*q)):03d}-discovery-1000-2026-08-28.json"


def analyze(manifest_path: Path, audit_path: Path) -> dict:
    dispatcher = load_module("submit_phase_b2_gray_frontier.py", "phase_b2_dispatcher_for_analysis")
    fuzzy = load_module("analyze_phase_b1_bayesian_fuzzy_trend.py", "phase_b2_fuzzy")
    manifest = json.loads(manifest_path.read_text())
    dispatcher.validate_manifest(manifest, dispatcher.expand_jobs(manifest))
    audit = json.loads(audit_path.read_text())
    if audit["status"] != "data_complete_not_analyzed" or int(audit["raw_rows_observed"]) != int(manifest["expected_new_decodes"]):
        raise ValueError("Phase B2 completion audit is absent or incomplete")
    audit_records = {record["stem"]: record for record in audit["records"]}
    analyses = []
    inputs = []
    for offset, job in enumerate(dispatcher.expand_jobs(manifest)):
        record = audit_records.get(job["stem"])
        if record is None or record["summary_sha256"] != sha256(Path(job["result"])):
            raise ValueError(f"completion-audit hash mismatch for {job['stem']}")
        existing_path = base_summary_path(job["q"])
        existing_payload = json.loads(existing_path.read_text())
        fresh_payload = json.loads(Path(job["result"]).read_text())
        existing = summary_counts(existing_payload, q=job["q"], p=job["p"], sizes=[7, 9, 11])
        fresh = summary_counts(fresh_payload, q=job["q"], p=job["p"], sizes=job["sizes"])
        pooled = pool_counts(job["branch"], existing, fresh)
        sizes = sorted(pooled)
        errors = np.asarray([pooled[size][0] for size in sizes])
        shots = np.asarray([pooled[size][1] for size in sizes])
        primary = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), seed=882128 + offset)
        uniform = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), prior_alpha=1.0, prior_beta=1.0, seed=892128 + offset)
        classification = primary["classification"] if primary["classification"] == uniform["classification"] else "unresolved"
        analyses.append({"branch": job["branch"], "q": job["q"], "p": job["p"], "sizes": sizes, "logical_errors": errors.tolist(), "shots": shots.tolist(), **primary, "jeffreys_classification": primary["classification"], "classification": classification, "uniform_prior_sensitivity": uniform, "prior_sensitivity_status": "stable" if classification == primary["classification"] else "classification_changed_conservative_gray"})
        inputs.extend([{"path": str(existing_path), "sha256": sha256(existing_path)}, {"path": job["result"], "sha256": sha256(Path(job["result"]))}])
    reused_path = LAB_DIR / manifest["reused_evidence"][0]["path"]
    reused_payload = json.loads(reused_path.read_text())
    reused = next(row for row in reused_payload["analyses"] if abs(float(row["q"]) - 0.45) < 1e-12 and abs(float(row["p"]) - 0.20) < 1e-12)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "completion_audit": {"path": str(audit_path), "sha256": sha256(audit_path)},
        "definition": manifest["analysis"],
        "new_analyses": analyses,
        "reused_analysis": {**reused, "reuse_reason": manifest["reused_evidence"][0]["reason"]},
        "provenance": {"inputs": inputs, "reused": {"path": str(reused_path), "sha256": sha256(reused_path)}, "analyzer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())}},
        "cells_updated": 4,
        "new_decodes": int(manifest["expected_new_decodes"]),
        "crossing_statistic_used": False,
        "grid_expanded": False,
        "evidence_boundary": "Only the three registered Phase B2 jobs plus one audited Phase B1 reuse; no interpolation or asymptotic phase claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.manifest, args.audit)
    load_module("submit_phase_b2_gray_frontier.py", "phase_b2_dispatcher_writer").atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells_updated": output["cells_updated"], "new_decodes": output["new_decodes"]}, indent=2))


if __name__ == "__main__":
    main()
