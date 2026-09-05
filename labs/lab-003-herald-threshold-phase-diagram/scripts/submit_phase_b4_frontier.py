#!/usr/bin/env python3
"""Fail-closed dispatcher scaffold for the one-job Phase B4 frontier cohort."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json"
DEFAULT_PREFLIGHT = LAB_DIR / "results/phase-b4-honeycomb-new-frontier-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b4_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    registered = manifest["jobs"][0]
    stem = "phase-b4-honeycomb-l7-9-11-q005-p020-2026-08-28"
    result = lab_dir / "results" / f"{stem}.json"
    raw = lab_dir / "results" / f"{stem}-raw.jsonl.gz"
    decoder = manifest["decoder"]
    command = [
        str(project_root / "run_research_python.sh"), str(lab_dir / "scripts/run_phase2_scout.py"),
        "--lattice", "honeycomb", "--q", "0.05", "--p", "0.20", "--campaign", manifest["campaign"],
        "--stem", stem, "--shots-per-seed", str(manifest["shots_per_seed"]), "--sizes", "7", "9", "11",
        "--seeds", *[str(seed) for seed in manifest["new_seeds"]], "--max-iterations", str(decoder["max_iterations"]),
        "--update-schedule", decoder["update_schedule"], "--residual-priority-order", decoder["residual_priority_order"],
    ]
    return [{"branch": registered["branch"], "q": 0.05, "p": 0.20, "sizes": [7, 9, 11], "stem": stem, "result": str(result), "raw": str(raw), "expected_decodes": 3000, "output_conflict": result.exists() or raw.exists(), "command": command}]


def validate(manifest_path: Path, manifest: dict, jobs: list[dict], *, reject_output_conflicts: bool = True) -> None:
    if manifest["status"] not in {"registered", "preflight_passed", "ready", "data_complete", "analyzed"}:
        raise ValueError("invalid Phase B4 lifecycle")
    if manifest["launch_gate"] not in {"closed_implementation", "ready", "closed_data_complete"}:
        raise ValueError("invalid Phase B4 launch gate")
    if manifest["new_seeds"] != [874001, 874002, 874003, 874004, 874005] or manifest["shots_per_seed"] != 200:
        raise ValueError("Phase B4 sampling drift")
    if [(job["q"], job["p"], job["sizes"], job["expected_decodes"]) for job in jobs] != [(0.05, 0.20, [7, 9, 11], 3000)]:
        raise ValueError("Phase B4 job matrix drift")
    evidence = manifest["selection_evidence"]
    selection = LAB_DIR / evidence["path"]
    if sha256(selection) != evidence["sha256"]:
        raise ValueError("Phase B4 selection hash mismatch")
    if load_runner().source_hashes() != manifest["required_source_hashes"]:
        raise ValueError("Phase B4 source hash drift")
    if reject_output_conflicts and any(job["output_conflict"] for job in jobs):
        raise ValueError("refusing Phase B4 output conflict")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    jobs = expand_jobs(manifest)
    validate(args.manifest, manifest, jobs)
    gate_scripts = {}
    for filename in ("audit_phase_b4_new_output.py", "analyze_phase_b4_frontier.py", "render_phase_b4_merged_map.py"):
        path = Path(__file__).with_name(filename)
        if not path.is_file():
            raise ValueError(f"missing Phase B4 gate script: {filename}")
        gate_scripts[filename] = sha256(path)
    payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "status": "preflight_passed_not_launched", "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)}, "jobs": jobs, "job_count": 1, "expected_new_decodes": 3000, "gate_scripts": gate_scripts, "production_launched": False, "crossing_statistic_used": False, "grid_expanded": False}
    if args.dry_run:
        atomic_json(args.audit, payload)
        print(json.dumps(payload, indent=2))
        return
    if manifest["status"] != "ready" or manifest["launch_gate"] != "ready":
        raise SystemExit("Phase B4 is not production-ready; use --dry-run")
    import subprocess
    code = subprocess.run(jobs[0]["command"], cwd=PROJECT_ROOT).returncode
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
