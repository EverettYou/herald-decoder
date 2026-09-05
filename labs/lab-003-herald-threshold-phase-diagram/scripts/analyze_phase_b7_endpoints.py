#!/usr/bin/env python3
"""Pool Phase B7 endpoint counts with Phase B6 map counts."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b7-honeycomb-endpoint-followup-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b7-honeycomb-endpoint-followup-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b7-honeycomb-endpoint-followup-analysis-2026-08-28.json"


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def base_cell(phase_map: dict, q: float, p: float) -> dict:
    for row in phase_map["analyses"]:
        for cell in row["cells"]:
            if abs(float(row["q"]) - q) < 1e-12 and abs(float(cell["p"]) - p) < 1e-12:
                return cell
    raise ValueError("missing Phase B7 base cell")


def analyze_counts(cell: dict, fresh_payload: dict, job: dict, seed_offset: int = 0) -> dict:
    common = load("analyze_phase_b3_frontier_reuse.py", "phase_b7_common")
    pooled = {int(size): (int(errors), int(shots)) for size, errors, shots in zip(cell["sizes"], cell["logical_errors"], cell["shots"])}
    fresh = common.summary_counts(fresh_payload, job["q"], job["p"], [5, 13])
    for size in [5, 13]:
        old_errors, old_shots = pooled[size]
        new_errors, new_shots = fresh[size]
        pooled[size] = (old_errors + new_errors, old_shots + new_shots)
    sizes = sorted(pooled)
    errors = np.asarray([pooled[size][0] for size in sizes])
    shots = np.asarray([pooled[size][1] for size in sizes])
    fuzzy = load("analyze_phase_b1_bayesian_fuzzy_trend.py", "phase_b7_fuzzy")
    primary = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), seed=887128 + seed_offset)
    uniform = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), prior_alpha=1.0, prior_beta=1.0, seed=897128 + seed_offset)
    classification = primary["classification"] if primary["classification"] == uniform["classification"] else "unresolved"
    return {"q": job["q"], "p": job["p"], "pooling_kind": job["branch"], "sizes": sizes, "logical_errors": errors.tolist(), "shots": shots.tolist(), **primary, "jeffreys_classification": primary["classification"], "classification": classification, "uniform_prior_sensitivity": uniform, "prior_sensitivity_status": "stable" if classification == primary["classification"] else "classification_changed_conservative_gray"}


def analyze(manifest_path: Path, audit_path: Path) -> dict:
    common = load("analyze_phase_b3_frontier_reuse.py", "phase_b7_hash")
    manifest = json.loads(manifest_path.read_text())
    phase_map = json.loads((LAB_DIR / manifest["source_map"]["path"]).read_text())
    audit = json.loads(audit_path.read_text())
    if audit["status"] != "data_complete_not_analyzed" or audit["jobs_complete"] != 4 or audit["raw_rows_observed"] != 8000:
        raise ValueError("Phase B7 audit incomplete")
    fresh = {(row["q"], row["p"]): Path(row["summary"]) for row in audit["records"]}
    analyses = []
    for offset, job in enumerate(manifest["jobs"]):
        analyses.append(analyze_counts(base_cell(phase_map, job["q"], job["p"]), json.loads(fresh[(job["q"], job["p"])].read_text()), job, offset))
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "manifest": {"path": str(manifest_path), "sha256": common.sha256(manifest_path)}, "completion_audit": {"path": str(audit_path), "sha256": common.sha256(audit_path)}, "analyses": analyses, "cells_updated": 4, "new_decodes": 8000, "crossing_statistic_used": False, "grid_expanded": False, "evidence_boundary": "Exactly four persistent Phase B6 cells with fresh L5/L13 counts; no interpolation or asymptotic boundary claim."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.manifest, args.audit)
    load("submit_phase_b7_endpoints.py", "phase_b7_write").atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells_updated": 4}, indent=2))


if __name__ == "__main__":
    main()
