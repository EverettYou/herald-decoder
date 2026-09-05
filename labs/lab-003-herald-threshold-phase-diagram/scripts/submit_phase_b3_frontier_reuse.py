#!/usr/bin/env python3
"""Fail-closed one-job dispatcher for Phase B3 reuse-first frontier analysis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b3-honeycomb-frontier-reuse-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def artifact_stem() -> str:
    return "phase-b3-honeycomb-l7-9-11-q055-p024-2026-08-28"


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    registered = manifest["jobs"][0]
    stem = artifact_stem()
    result = lab_dir / "results" / f"{stem}.json"
    raw = lab_dir / "results" / f"{stem}-raw.jsonl.gz"
    decoder = manifest["decoder"]
    command = [str(project_root / "run_research_python.sh"), str(lab_dir / "scripts/run_phase2_scout.py"), "--lattice", "honeycomb", "--q", "0.55", "--p", "0.24", "--campaign", manifest["campaign"], "--stem", stem, "--shots-per-seed", str(manifest["shots_per_seed"]), "--sizes", "7", "9", "11", "--seeds", *[str(seed) for seed in manifest["new_seeds"]], "--max-iterations", str(decoder["max_iterations"]), "--update-schedule", decoder["update_schedule"], "--residual-priority-order", decoder["residual_priority_order"]]
    return [{"branch": registered["branch"], "q": 0.55, "p": 0.24, "sizes": [7, 9, 11], "stem": stem, "result": str(result), "raw": str(raw), "expected_decodes": 3000, "output_conflict": result.exists() or raw.exists(), "command": command}]


def validate_manifest(manifest: dict, jobs: list[dict]) -> None:
    if manifest["lattice"] != "honeycomb" or manifest["status"] not in {"registered", "preflight_passed", "ready", "data_complete", "analyzed"}:
        raise ValueError("invalid Phase B3 lifecycle or lattice")
    if manifest["new_seeds"] != [873001, 873002, 873003, 873004, 873005] or int(manifest["shots_per_seed"]) != 200:
        raise ValueError("Phase B3 sampling drift")
    if len(jobs) != int(manifest["job_count"]) or [(j["q"], j["p"], j["sizes"]) for j in jobs] != [(0.55, 0.24, [7, 9, 11])]:
        raise ValueError("Phase B3 job matrix drift")
    if sum(job["expected_decodes"] for job in jobs) != int(manifest["expected_new_decodes"]) or int(manifest["expected_new_decodes"]) != 3000:
        raise ValueError("Phase B3 decode-budget drift")


def validate_chain(manifest: dict) -> dict:
    evidence = manifest["selection_evidence"]
    for key, hash_key in (("path", "sha256"), ("phase_b2_map", "phase_b2_map_sha256"), ("phase_s1_completion_audit", "phase_s1_completion_audit_sha256")):
        if sha256(LAB_DIR / evidence[key]) != evidence[hash_key]:
            raise ValueError(f"Phase B3 evidence hash mismatch: {key}")
    runner = load_module("run_phase2_scout.py", "phase_b3_runner")
    if runner.source_hashes() != manifest["required_source_hashes"]:
        raise ValueError("Phase B3 current source hash drift")
    reuse = load_module("audit_phase_b3_reuse_sources.py", "phase_b3_reuse_audit").audit(DEFAULT_MANIFEST)
    return {"reuse_source_audit": reuse, "analyzer": {"path": str(Path(__file__).with_name("analyze_phase_b3_frontier_reuse.py")), "sha256": sha256(Path(__file__).with_name("analyze_phase_b3_frontier_reuse.py"))}, "completion_audit": {"path": str(Path(__file__).with_name("audit_phase_b3_new_output.py")), "sha256": sha256(Path(__file__).with_name("audit_phase_b3_new_output.py"))}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    jobs = expand_jobs(manifest)
    validate_manifest(manifest, jobs)
    conflicts = [job["stem"] for job in jobs if job["output_conflict"]]
    if conflicts:
        raise ValueError("refusing Phase B3 output conflict")
    audit = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "preflight_passed_not_launched", "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)}, "jobs": jobs, "job_count": 1, "expected_new_decodes": 3000, "output_conflicts": conflicts, "source_chain": validate_chain(manifest), "production_launched": False, "crossing_statistic_used": False}
    if args.dry_run:
        atomic_json(args.audit, audit)
        print(json.dumps(audit, indent=2))
        return
    if manifest["status"] != "ready" or manifest["launch_gate"] != "ready":
        raise SystemExit("Phase B3 is not production-ready; use --dry-run")
    code = subprocess.run(jobs[0]["command"], cwd=PROJECT_ROOT).returncode
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
