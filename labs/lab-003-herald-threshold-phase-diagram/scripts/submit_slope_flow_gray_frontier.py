#!/usr/bin/env python3
"""Fail-closed dispatcher for the registered slope-flow gray-frontier matrix."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-s1-honeycomb-slope-flow-gray-frontier-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-s1-honeycomb-slope-flow-gray-frontier-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_s1_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def coordinate_tag(value: float) -> str:
    return f"{int(round(100 * value)):03d}"


def artifact_stem(manifest: dict, branch: dict, cell: dict) -> str:
    branch_tag = "seed" if branch["id"] == "seed-limited-pinch" else "distance"
    return (
        f"phase-s1-honeycomb-{branch_tag}-q{coordinate_tag(cell['q'])}-"
        f"p{coordinate_tag(cell['p'])}-2026-08-28"
    )


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    decoder = manifest["decoder"]
    runtime = project_root / "run_research_python.sh"
    runner = lab_dir / "scripts/run_phase2_scout.py"
    jobs = []
    seen = set()
    for branch in manifest["branches"]:
        sizes = [int(value) for value in branch["sizes"]]
        for cell in branch["cells"]:
            coordinate = (float(cell["q"]), float(cell["p"]))
            if coordinate in seen:
                raise ValueError(f"duplicate target coordinate {coordinate}")
            seen.add(coordinate)
            stem = artifact_stem(manifest, branch, cell)
            result_path = lab_dir / "results" / f"{stem}.json"
            raw_path = lab_dir / "results" / f"{stem}-raw.jsonl.gz"
            command = [
                str(runtime), str(runner),
                "--lattice", manifest["lattice"],
                "--q", f"{coordinate[0]:.2f}",
                "--p", f"{coordinate[1]:.2f}",
                "--campaign", manifest["campaign"],
                "--stem", stem,
                "--shots-per-seed", str(manifest["shots_per_seed"]),
                "--sizes", *[str(value) for value in sizes],
                "--seeds", *[str(value) for value in manifest["new_seeds"]],
                "--max-iterations", str(decoder["max_iterations"]),
                "--update-schedule", decoder["update_schedule"],
                "--residual-priority-order", decoder["residual_priority_order"],
                "--skip-existing",
            ]
            if decoder["residual_priority_buffer_reuse"]:
                command.append("--residual-priority-buffer-reuse")
            if decoder["residual_priority_cached_products"]:
                command.append("--residual-priority-cached-products")
            if coordinate[1] >= 0.5:
                command.append("--allow-honeycomb-high-p")
            jobs.append(
                {
                    "branch": branch["id"],
                    "q": coordinate[0],
                    "p": coordinate[1],
                    "sizes": sizes,
                    "stem": stem,
                    "result": str(result_path),
                    "raw": str(raw_path),
                    "expected_decodes": len(sizes) * len(manifest["new_seeds"]) * int(manifest["shots_per_seed"]),
                    "output_conflict": result_path.exists() or raw_path.exists(),
                    "command": command,
                }
            )
    return jobs


def validate_manifest(manifest: dict, jobs: list[dict]) -> None:
    if manifest["lattice"] != "honeycomb":
        raise ValueError("Phase S1 is honeycomb only")
    if manifest["status"] not in {"registered_not_started", "preflight_passed_not_started", "ready", "data_complete_not_analyzed", "analyzed"}:
        raise ValueError("manifest status is not a recognized Phase S1 lifecycle state")
    seeds = [int(value) for value in manifest["new_seeds"]]
    if not seeds or len(seeds) != len(set(seeds)) or any(value < 1 for value in seeds):
        raise ValueError("new seeds must be unique positive integers")
    if int(manifest["shots_per_seed"]) < 1:
        raise ValueError("shots_per_seed must be positive")
    for job in jobs:
        if len(job["sizes"]) < 2 or len(job["sizes"]) != len(set(job["sizes"])):
            raise ValueError(f"job {job['stem']} must contain at least two unique sizes")
        if not 0 <= job["q"] <= 1 or not 0 < job["p"] < 1:
            raise ValueError(f"invalid coordinate in {job['stem']}")
    expected = sum(job["expected_decodes"] for job in jobs)
    if len(jobs) != int(manifest["jobs"]):
        raise ValueError("expanded job count does not match manifest")
    if expected != int(manifest["expected_new_decodes"]):
        raise ValueError("expanded decode count does not match manifest")
    for branch in manifest["branches"]:
        branch_total = sum(job["expected_decodes"] for job in jobs if job["branch"] == branch["id"])
        if branch_total != int(branch["expected_new_decodes"]):
            raise ValueError(f"decode count mismatch for {branch['id']}")


def validate_source_chain(manifest: dict, *, lab_dir: Path = LAB_DIR) -> dict:
    evidence = manifest["source_evidence"]
    verified = {}
    for path_key, hash_key in (
        ("slope_flow_result", "slope_flow_sha256"),
        ("stability_result", "stability_sha256"),
        ("baseline_source_shard", "baseline_source_shard_sha256"),
    ):
        path = lab_dir / evidence[path_key]
        observed = sha256(path)
        if observed != evidence[hash_key]:
            raise ValueError(f"source evidence hash mismatch: {path}")
        verified[path_key] = {"path": str(path), "sha256": observed}
    baseline = json.loads((lab_dir / evidence["baseline_source_shard"]).read_text())
    runner = load_runner()
    current_sources = runner.source_hashes()
    if current_sources != baseline["source_hashes"]:
        raise ValueError("current runner/source cohort differs from the Phase 2 baseline")
    if manifest["decoder"] != baseline["decoder"]:
        raise ValueError("registered decoder configuration differs from the Phase 2 baseline")
    return {
        "evidence": verified,
        "baseline_source_hashes": baseline["source_hashes"],
        "current_source_hashes": current_sources,
        "source_cohort_matches": True,
        "decoder_config_matches": True,
    }


def build_audit(manifest_path: Path, manifest: dict, jobs: list[dict], source_chain: dict) -> dict:
    conflicts = [job["stem"] for job in jobs if job["output_conflict"]]
    if conflicts:
        raise ValueError("refusing preflight with existing outputs: " + ", ".join(conflicts))
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "preflight_passed_not_launched",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "campaign": manifest["campaign"],
        "jobs": jobs,
        "job_count": len(jobs),
        "expected_new_decodes": sum(job["expected_decodes"] for job in jobs),
        "workers_cap": int(manifest["workers_cap"]),
        "output_conflicts": conflicts,
        "source_chain": source_chain,
        "production_launched": False,
        "crossing_statistic_used": False,
    }


def execute(jobs: list[dict], *, workers: int, campaign: str) -> None:
    run_dir = PROJECT_ROOT / ".tmp" / campaign
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    queue = deque(jobs)
    active = {}
    completed = []
    failed = []

    def write_status() -> None:
        atomic_json(
            status_path,
            {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "queued": [job["stem"] for job in queue],
                "active": [{"pid": pid, "stem": item["job"]["stem"], "log": str(item["log_path"])} for pid, item in active.items()],
                "completed": completed,
                "failed": failed,
            },
        )

    while queue or active:
        while queue and len(active) < workers:
            job = queue.popleft()
            log_path = run_dir / f"{job['stem']}.log"
            log_handle = log_path.open("a")
            process = subprocess.Popen(job["command"], cwd=PROJECT_ROOT, stdout=log_handle, stderr=subprocess.STDOUT)
            active[process.pid] = {"process": process, "job": job, "log_path": log_path, "log_handle": log_handle}
        write_status()
        time.sleep(1.0)
        for pid, item in list(active.items()):
            return_code = item["process"].poll()
            if return_code is None:
                continue
            item["log_handle"].close()
            record = {"stem": item["job"]["stem"], "return_code": return_code, "log": str(item["log_path"])}
            (completed if return_code == 0 else failed).append(record)
            del active[pid]
    write_status()
    if failed:
        raise SystemExit(f"{len(failed)} Phase S1 jobs failed; inspect {status_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    jobs = expand_jobs(manifest)
    validate_manifest(manifest, jobs)
    source_chain = validate_source_chain(manifest)
    audit = build_audit(args.manifest, manifest, jobs, source_chain)
    if args.dry_run:
        atomic_json(args.audit, audit)
        print(json.dumps(audit, indent=2))
        return
    if manifest["status"] != "ready":
        raise SystemExit("manifest is not production-ready; keep --dry-run until status is explicitly set to ready")
    workers = args.workers or int(manifest["workers_cap"])
    if not 1 <= workers <= int(manifest["workers_cap"]):
        raise SystemExit(f"workers must lie in [1, {manifest['workers_cap']}]")
    execute(jobs, workers=workers, campaign=manifest["campaign"])


if __name__ == "__main__":
    main()
