#!/usr/bin/env python3
"""Pool five reused Phase S1 shards and one fresh Phase B3 shard under fuzzy trend."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b3-honeycomb-frontier-reuse-manifest-2026-08-28.json"
DEFAULT_REUSE_AUDIT = LAB_DIR / "results/phase-b3-honeycomb-reuse-source-audit-2026-08-28.json"
DEFAULT_NEW_AUDIT = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json"


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary_counts(payload: dict, q: float, p: float, sizes: list[int]) -> dict[int, tuple[int, int]]:
    rows = {int(row["L"]): (int(row["logical_errors"]), int(row["shots"])) for row in payload["summaries"] if abs(float(row["q"]) - q) < 1e-12 and abs(float(row["p"]) - p) < 1e-12 and int(row["L"]) in sizes}
    if set(rows) != set(sizes):
        raise ValueError(f"incomplete counts at {(q,p)}")
    return rows


def pool_counts(kind: str, base: dict[int, tuple[int, int]], extra: dict[int, tuple[int, int]]) -> dict[int, tuple[int, int]]:
    if set(base) != {7, 9, 11}:
        raise ValueError("Phase B3 base must be L7/L9/L11")
    if kind in {"seed_limited", "new_independent_shots"}:
        if set(extra) != {7, 9, 11}:
            raise ValueError("same-window pooling size mismatch")
        return {size: (base[size][0] + extra[size][0], base[size][1] + extra[size][1]) for size in (7, 9, 11)}
    if kind == "distance_limited":
        if set(extra) != {11, 13}:
            raise ValueError("distance-reuse pooling size mismatch")
        return {7: base[7], 9: base[9], 11: (base[11][0] + extra[11][0], base[11][1] + extra[11][1]), 13: extra[13]}
    raise ValueError(f"unknown Phase B3 pooling kind {kind}")


def base_path(q: float) -> Path:
    return LAB_DIR / "results" / f"phase2-residual80-honeycomb-q{int(round(100*q)):03d}-discovery-1000-2026-08-28.json"


def analyze(manifest_path: Path, reuse_audit_path: Path, new_audit_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    selection = json.loads((LAB_DIR / manifest["selection_evidence"]["path"]).read_text())
    reuse_audit = json.loads(reuse_audit_path.read_text())
    new_audit = json.loads(new_audit_path.read_text())
    if reuse_audit["status"] != "reuse_sources_verified" or new_audit["status"] != "data_complete_not_analyzed":
        raise ValueError("Phase B3 audits incomplete")
    fresh_path = Path(new_audit["record"]["summary"])
    work = [(row["q"], row["p"], row["reuse_kind"], LAB_DIR / row["path"]) for row in selection["reused_phase_s1_evidence"]] + [(0.55, 0.24, "new_independent_shots", fresh_path)]
    fuzzy = load_module("analyze_phase_b1_bayesian_fuzzy_trend.py", "phase_b3_fuzzy")
    analyses = []
    for offset, (q, p, kind, extra_path) in enumerate(sorted(work)):
        base_payload, extra_payload = json.loads(base_path(q).read_text()), json.loads(extra_path.read_text())
        base = summary_counts(base_payload, q, p, [7, 9, 11])
        extra_sizes = [7, 9, 11] if kind != "distance_limited" else [11, 13]
        pooled = pool_counts(kind, base, summary_counts(extra_payload, q, p, extra_sizes))
        sizes = sorted(pooled); errors=np.asarray([pooled[size][0] for size in sizes]); shots=np.asarray([pooled[size][1] for size in sizes])
        primary=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),seed=883128+offset); uniform=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),prior_alpha=1.0,prior_beta=1.0,seed=893128+offset)
        classification=primary["classification"] if primary["classification"]==uniform["classification"] else "unresolved"
        analyses.append({"q":q,"p":p,"pooling_kind":kind,"sizes":sizes,"logical_errors":errors.tolist(),"shots":shots.tolist(),**primary,"jeffreys_classification":primary["classification"],"classification":classification,"uniform_prior_sensitivity":uniform,"prior_sensitivity_status":"stable" if classification==primary["classification"] else "classification_changed_conservative_gray"})
    return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","manifest":{"path":str(manifest_path),"sha256":sha256(manifest_path)},"reuse_audit":{"path":str(reuse_audit_path),"sha256":sha256(reuse_audit_path)},"new_output_audit":{"path":str(new_audit_path),"sha256":sha256(new_audit_path)},"analyses":analyses,"cells_updated":6,"new_decodes":3000,"reused_decodes":11000,"crossing_statistic_used":False,"grid_expanded":False,"evidence_boundary":"Exactly six current red/green-adjacent gray cells; no interpolation or asymptotic boundary claim."}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST); parser.add_argument("--reuse-audit",type=Path,default=DEFAULT_REUSE_AUDIT); parser.add_argument("--new-audit",type=Path,default=DEFAULT_NEW_AUDIT); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args()
    output=analyze(args.manifest,args.reuse_audit,args.new_audit); load_module("submit_phase_b3_frontier_reuse.py","phase_b3_writer").atomic_json(args.output,output); print(json.dumps({"status":output["status"],"cells_updated":6},indent=2))


if __name__ == "__main__": main()
