#!/usr/bin/env python3
"""Fail-closed dispatcher for the registered Phase B1 L5/L13 sentinels."""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b1-honeycomb-l5-l13-sentinels-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-sentinels-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b1_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def coordinate_tag(value: float) -> str:
    return f"{int(round(100 * value)):03d}"


def artifact_stem(cell: dict) -> str:
    return (
        f"phase-b1-honeycomb-l5-l13-q{coordinate_tag(cell['q'])}-"
        f"p{coordinate_tag(cell['p'])}-2026-08-28"
    )


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    runtime = project_root / "run_research_python.sh"
    runner = lab_dir / "scripts/run_phase2_scout.py"
    decoder = manifest["decoder"]
    sizes = [int(value) for value in manifest["new_sizes"]]
    jobs = []
    seen = set()
    for cell in manifest["cells"]:
        coordinate = (float(cell["q"]), float(cell["p"]))
        if coordinate in seen:
            raise ValueError(f"duplicate Phase B1 coordinate {coordinate}")
        seen.add(coordinate)
        stem = artifact_stem(cell)
        result_path = lab_dir / "results" / f"{stem}.json"
        raw_path = lab_dir / "results" / f"{stem}-raw.jsonl.gz"
        command = [
            str(runtime),
            str(runner),
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
        ]
        if decoder["residual_priority_buffer_reuse"]:
            command.append("--residual-priority-buffer-reuse")
        if decoder["residual_priority_cached_products"]:
            command.append("--residual-priority-cached-products")
        jobs.append(
            {
                "role": cell["role"],
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
        raise ValueError("Phase B1 is honeycomb only")
    if manifest["status"] not in {"registered", "preflight_passed", "ready", "data_complete", "analyzed"}:
        raise ValueError("unrecognized Phase B1 lifecycle state")
    if [int(value) for value in manifest["new_sizes"]] != [5, 13]:
        raise ValueError("Phase B1 may add only L=5 and L=13")
    seeds = [int(value) for value in manifest["new_seeds"]]
    if len(seeds) != 5 or len(seeds) != len(set(seeds)) or any(seed < 1 for seed in seeds):
        raise ValueError("Phase B1 requires five unique positive seeds")
    if int(manifest["shots_per_seed"]) != 200:
        raise ValueError("Phase B1 shots_per_seed drift")
    if len(jobs) != int(manifest["jobs"]):
        raise ValueError("Phase B1 job-count drift")
    if any(job["sizes"] != [5, 13] for job in jobs):
        raise ValueError("Phase B1 job size drift")
    expected = sum(job["expected_decodes"] for job in jobs)
    if expected != int(manifest["expected_new_decodes"]) or expected != 8000:
        raise ValueError("Phase B1 decode-budget drift")


def validate_source_chain(manifest: dict, *, lab_dir: Path = LAB_DIR) -> dict:
    selection = lab_dir / manifest["selection_evidence"]["path"]
    bayesian = lab_dir / manifest["selection_evidence"]["bayesian_source"]
    if sha256(bayesian) != manifest["selection_evidence"]["bayesian_source_sha256"]:
        raise ValueError("Bayesian selection source hash mismatch")
    baseline = lab_dir / "results/phase2-residual80-honeycomb-q000-discovery-1000-2026-08-28.json"
    baseline_payload = json.loads(baseline.read_text())
    current_sources = load_runner().source_hashes()
    if current_sources != manifest["required_source_hashes"]:
        raise ValueError("current source hashes differ from Phase B1 contract")
    if current_sources != baseline_payload["source_hashes"]:
        raise ValueError("current source cohort differs from Phase 2 baseline")
    if manifest["decoder"] != baseline_payload["decoder"]:
        raise ValueError("Phase B1 decoder differs from Phase 2 baseline")
    analyzer = lab_dir / "scripts/analyze_phase_b1_l5_l13_sentinels.py"
    return {
        "selection": {"path": str(selection), "sha256": sha256(selection)},
        "bayesian_source": {"path": str(bayesian), "sha256": sha256(bayesian)},
        "baseline": {"path": str(baseline), "sha256": sha256(baseline)},
        "analyzer": {"path": str(analyzer), "sha256": sha256(analyzer)},
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
        "existing_distances_rerun": False,
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
        atomic_json(status_path, {"updated_at": datetime.now(timezone.utc).isoformat(), "queued": [job["stem"] for job in queue], "active": [item["job"]["stem"] for item in active.values()], "completed": completed, "failed": failed})

    while queue or active:
        while queue and len(active) < workers:
            job = queue.popleft()
            log_path = run_dir / f"{job['stem']}.log"
            log_handle = log_path.open("a")
            process = subprocess.Popen(job["command"], cwd=PROJECT_ROOT, stdout=log_handle, stderr=subprocess.STDOUT)
            active[process.pid] = {"process": process, "job": job, "log": log_path, "handle": log_handle}
        write_status()
        time.sleep(1.0)
        for pid, item in list(active.items()):
            code = item["process"].poll()
            if code is None:
                continue
            item["handle"].close()
            record = {"stem": item["job"]["stem"], "return_code": code, "log": str(item["log"])}
            (completed if code == 0 else failed).append(record)
            del active[pid]
    write_status()
    if failed:
        raise SystemExit(f"{len(failed)} Phase B1 jobs failed; inspect {status_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workers", type=int)
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
    if manifest["status"] != "ready" or manifest["launch_gate"] != "ready":
        raise SystemExit("Phase B1 is not production-ready; use --dry-run")
    workers = args.workers or int(manifest["workers_cap"])
    if not 1 <= workers <= int(manifest["workers_cap"]):
        raise SystemExit("workers exceed Phase B1 cap")
    execute(jobs, workers=workers, campaign=manifest["campaign"])


if __name__ == "__main__":
    main()
