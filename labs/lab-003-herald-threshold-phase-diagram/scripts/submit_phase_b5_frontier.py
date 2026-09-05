#!/usr/bin/env python3
"""Fail-closed five-job dispatcher for the Phase B5 persistent frontier."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b5-honeycomb-persistent-frontier-manifest-2026-08-28.json"
DEFAULT_PREFLIGHT = LAB_DIR / "results/phase-b5-honeycomb-persistent-frontier-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b5_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_auditor():
    path = Path(__file__).with_name("audit_phase_b5_outputs.py")
    spec = importlib.util.spec_from_file_location("phase_b5_resume_auditor", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def stem(job: dict) -> str:
    sizes = "l5" if job["sizes"] == [5] else "l7-9-11"
    return f"phase-b5-honeycomb-{sizes}-q{int(round(100*job['q'])):03d}-p{int(round(100*job['p'])):03d}-2026-08-28"


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    jobs = []
    for registered in manifest["jobs"]:
        artifact = stem(registered)
        result = lab_dir / "results" / f"{artifact}.json"
        raw = lab_dir / "results" / f"{artifact}-raw.jsonl.gz"
        decoder = manifest["decoder"]
        if registered["sizes"] == [5]:
            command = [str(project_root / "run_research_python.sh"), str(lab_dir / "scripts/run_phase_b5_single_size.py"), "--lattice", "honeycomb", "--q", str(registered["q"]), "--p", str(registered["p"]), "--campaign", manifest["campaign"], "--stem", artifact, "--shots-per-seed", str(manifest["shots_per_seed"]), "--size", "5", "--seeds", *[str(seed) for seed in manifest["new_seeds"]], "--max-iterations", str(decoder["max_iterations"]), "--update-schedule", decoder["update_schedule"], "--residual-priority-order", decoder["residual_priority_order"]]
        else:
            command = [str(project_root / "run_research_python.sh"), str(lab_dir / "scripts/run_phase2_scout.py"), "--lattice", "honeycomb", "--q", str(registered["q"]), "--p", str(registered["p"]), "--campaign", manifest["campaign"], "--stem", artifact, "--shots-per-seed", str(manifest["shots_per_seed"]), "--sizes", *[str(size) for size in registered["sizes"]], "--seeds", *[str(seed) for seed in manifest["new_seeds"]], "--max-iterations", str(decoder["max_iterations"]), "--update-schedule", decoder["update_schedule"], "--residual-priority-order", decoder["residual_priority_order"]]
        jobs.append({**registered, "stem": artifact, "result": str(result), "raw": str(raw), "output_conflict": result.exists() or raw.exists(), "command": command})
    return jobs


def validate(manifest_path: Path, manifest: dict, jobs: list[dict], *, reject_output_conflicts: bool = True) -> None:
    if manifest["status"] not in {"registered", "ready", "data_complete", "analyzed"} or manifest["launch_gate"] not in {"closed_implementation", "ready", "closed_data_complete"}:
        raise ValueError("invalid Phase B5 lifecycle")
    expected = {(0.30,0.20,(5,),1000),(0.35,0.20,(5,),1000),(0.40,0.20,(5,),1000),(0.55,0.24,(7,9,11),3000),(0.60,0.28,(5,),1000)}
    observed = {(j["q"],j["p"],tuple(j["sizes"]),j["expected_decodes"]) for j in jobs}
    if observed != expected or len(jobs) != 5 or sum(j["expected_decodes"] for j in jobs) != 7000:
        raise ValueError("Phase B5 matrix/budget drift")
    if manifest["new_seeds"] != [875001,875002,875003,875004,875005] or manifest["shots_per_seed"] != 200:
        raise ValueError("Phase B5 sampling drift")
    selection_path = LAB_DIR / manifest["selection_evidence"]["path"]
    if sha256(selection_path) != manifest["selection_evidence"]["sha256"]:
        raise ValueError("Phase B5 selection hash drift")
    selection = json.loads(selection_path.read_text())
    for row in selection["prior_adaptive_evidence"]:
        for key in ("base", "adaptive"):
            if sha256(LAB_DIR / row[f"{key}_path"]) != row[f"{key}_sha256"]:
                raise ValueError(f"Phase B5 {key} evidence hash drift")
    if load_runner().source_hashes() != manifest["required_source_hashes"]:
        raise ValueError("Phase B5 source hash drift")
    wrapper = Path(__file__).with_name("run_phase_b5_single_size.py")
    if sha256(wrapper) != manifest["required_execution_hashes"]["single_size_wrapper"]:
        raise ValueError("Phase B5 execution-wrapper hash drift")
    if reject_output_conflicts and any(job["output_conflict"] for job in jobs):
        raise ValueError("refusing Phase B5 output conflict")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);parser.add_argument("--audit",type=Path,default=DEFAULT_PREFLIGHT);parser.add_argument("--dry-run",action="store_true");args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text());jobs=expand_jobs(manifest)
    validate(args.manifest,manifest,jobs,reject_output_conflicts=args.dry_run)
    gate_scripts={}
    for filename in ("audit_phase_b5_outputs.py","analyze_phase_b5_frontier.py","render_phase_b5_merged_map.py"):
        path=Path(__file__).with_name(filename)
        if not path.is_file():raise ValueError(f"missing Phase B5 gate script: {filename}")
        gate_scripts[filename]=sha256(path)
    payload={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"preflight_passed_not_launched","manifest":{"path":str(args.manifest),"sha256":sha256(args.manifest)},"jobs":jobs,"job_count":5,"expected_new_decodes":7000,"workers_cap":4,"gate_scripts":gate_scripts,"production_launched":False,"crossing_statistic_used":False,"grid_expanded":False}
    if args.dry_run:atomic_json(args.audit,payload);print(json.dumps(payload,indent=2));return
    if manifest["status"]!="ready" or manifest["launch_gate"]!="ready":raise SystemExit("Phase B5 is not production-ready; use --dry-run")
    auditor=load_auditor();pending=[]
    for job in jobs:
        result,raw=Path(job["result"]),Path(job["raw"])
        if not job["output_conflict"]:
            pending.append(job);continue
        if not result.is_file() or not raw.is_file():
            raise SystemExit(f"refusing partial Phase B5 output pair: {job['stem']}")
        auditor.audit_pair(manifest,json.loads(result.read_text()),raw,job)
    with concurrent.futures.ThreadPoolExecutor(max_workers=manifest["workers_cap"]) as pool:
        codes=list(pool.map(lambda job: subprocess.run(job["command"],cwd=PROJECT_ROOT).returncode,pending))
    if any(codes):raise SystemExit(f"Phase B5 job failures: {codes}")
    print(json.dumps({"status":"complete","jobs_reused":len(jobs)-len(pending),"jobs_run":len(pending)}))


if __name__=="__main__":main()
