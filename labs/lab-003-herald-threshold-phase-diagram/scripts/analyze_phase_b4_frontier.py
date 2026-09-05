#!/usr/bin/env python3
"""Pool the fresh Phase B4 q=0.05 shard with its active base measurements."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-analysis-2026-08-28.json"
BASE = LAB_DIR / "results/phase2-residual80-honeycomb-q005-discovery-1000-2026-08-28.json"


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def analyze_counts(base_payload: dict, fresh_payload: dict) -> dict:
    common = load("analyze_phase_b3_frontier_reuse.py", "phase_b4_pooling")
    base = common.summary_counts(base_payload, 0.05, 0.20, [7, 9, 11])
    fresh = common.summary_counts(fresh_payload, 0.05, 0.20, [7, 9, 11])
    pooled = common.pool_counts("new_independent_shots", base, fresh)
    sizes = sorted(pooled)
    errors = np.asarray([pooled[size][0] for size in sizes])
    shots = np.asarray([pooled[size][1] for size in sizes])
    fuzzy = load("analyze_phase_b1_bayesian_fuzzy_trend.py", "phase_b4_fuzzy")
    primary = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), seed=884128)
    uniform = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), prior_alpha=1.0, prior_beta=1.0, seed=894128)
    classification = primary["classification"] if primary["classification"] == uniform["classification"] else "unresolved"
    return {"q": 0.05, "p": 0.20, "pooling_kind": "new_independent_shots", "sizes": sizes, "logical_errors": errors.tolist(), "shots": shots.tolist(), **primary, "jeffreys_classification": primary["classification"], "classification": classification, "uniform_prior_sensitivity": uniform, "prior_sensitivity_status": "stable" if classification == primary["classification"] else "classification_changed_conservative_gray"}


def analyze(manifest_path: Path, audit_path: Path) -> dict:
    common = load("analyze_phase_b3_frontier_reuse.py", "phase_b4_hashes")
    manifest, audit = json.loads(manifest_path.read_text()), json.loads(audit_path.read_text())
    if audit["status"] != "data_complete_not_analyzed":
        raise ValueError("Phase B4 completion audit is incomplete")
    fresh_path = Path(audit["record"]["summary"])
    row = analyze_counts(json.loads(BASE.read_text()), json.loads(fresh_path.read_text()))
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "manifest": {"path": str(manifest_path), "sha256": common.sha256(manifest_path)}, "new_output_audit": {"path": str(audit_path), "sha256": common.sha256(audit_path)}, "analyses": [row], "cells_updated": 1, "new_decodes": 3000, "crossing_statistic_used": False, "grid_expanded": False, "evidence_boundary": "Exactly the newly exposed q=0.05,p=0.20 cell; no interpolation or asymptotic boundary claim."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.manifest, args.audit)
    load("submit_phase_b4_frontier.py", "phase_b4_writer").atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells_updated": 1}, indent=2))


if __name__ == "__main__":
    main()
