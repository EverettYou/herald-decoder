#!/usr/bin/env python3
"""Fail-closed dispatcher for the registered Phase B2 gray-frontier cohort."""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-preflight-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b2_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def coordinate_tag(value: float) -> str:
    return f"{int(round(100 * value)):03d}"


def artifact_stem(job: dict) -> str:
    size_tag = "l" + "-".join(str(int(value)) for value in job["sizes"])
    return (
        f"phase-b2-honeycomb-{size_tag}-q{coordinate_tag(job['q'])}-"
        f"p{coordinate_tag(job['p'])}-2026-08-28"
    )


def expand_jobs(manifest: dict, *, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    runtime = project_root / "run_research_python.sh"
    runner = lab_dir / "scripts/run_phase2_scout.py"
    decoder = manifest["decoder"]
    expanded = []
    seen = set()
    for registered in manifest["jobs"]:
        coordinate = (float(registered["q"]), float(registered["p"]))
        if coordinate in seen:
            raise ValueError(f"duplicate Phase B2 coordinate {coordinate}")
        seen.add(coordinate)
        sizes = [int(value) for value in registered["sizes"]]
        stem = artifact_stem(registered)
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
        ]
        if decoder["residual_priority_buffer_reuse"]:
            command.append("--residual-priority-buffer-reuse")
        if decoder["residual_priority_cached_products"]:
            command.append("--residual-priority-cached-products")
        expanded.append(
            {
                "branch": registered["branch"],
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
    return expanded


def validate_manifest(manifest: dict, jobs: list[dict]) -> None:
    if manifest["lattice"] != "honeycomb":
        raise ValueError("Phase B2 is honeycomb only")
    if manifest["status"] not in {"registered", "preflight_passed", "ready", "data_complete", "analyzed"}:
        raise ValueError("unrecognized Phase B2 lifecycle state")
    seeds = [int(value) for value in manifest["new_seeds"]]
    if len(seeds) != 5 or len(set(seeds)) != 5 or any(seed < 1 for seed in seeds):
        raise ValueError("Phase B2 requires five unique positive seeds")
    if int(manifest["shots_per_seed"]) != 200:
        raise ValueError("Phase B2 shots_per_seed drift")
    expected_matrix = {
        (0.20, 0.08, (5, 13)),
        (0.75, 0.40, (7, 9, 11)),
        (0.50, 0.20, (7, 9, 11)),
    }
    observed_matrix = {(job["q"], job["p"], tuple(job["sizes"])) for job in jobs}
    if observed_matrix != expected_matrix or len(jobs) != int(manifest["job_count"]) or len(jobs) != 3:
        raise ValueError("Phase B2 registered matrix drift")
    expected = sum(job["expected_decodes"] for job in jobs)
    if expected != int(manifest["expected_new_decodes"]) or expected != 8000:
        raise ValueError("Phase B2 decode-budget drift")
    if [(float(row["q"]), float(row["p"])) for row in manifest["reused_evidence"]] != [(0.45, 0.20)]:
        raise ValueError("Phase B2 reused-evidence drift")


def validate_source_chain(manifest: dict, *, lab_dir: Path = LAB_DIR) -> dict:
    evidence = manifest["selection_evidence"]
    verified = {}
    for key, hash_key in (("path", "sha256"), ("phase_map", "phase_map_sha256"), ("phase_b1", "phase_b1_sha256")):
        path = lab_dir / evidence[key]
        digest = sha256(path)
        if digest != evidence[hash_key]:
            raise ValueError(f"Phase B2 evidence hash mismatch: {key}")
        verified[key] = {"path": str(path), "sha256": digest}
    baseline_path = lab_dir / "results/phase2-residual80-honeycomb-q000-discovery-1000-2026-08-28.json"
    baseline = json.loads(baseline_path.read_text())
    current_sources = load_runner().source_hashes()
    if current_sources != manifest["required_source_hashes"] or current_sources != baseline["source_hashes"]:
        raise ValueError("current source cohort differs from Phase B2 contract")
    if manifest["decoder"] != baseline["decoder"]:
        raise ValueError("Phase B2 decoder differs from Phase 2 baseline")
    analyzer = lab_dir / "scripts/analyze_phase_b2_gray_frontier.py"
    completion_audit = lab_dir / "scripts/audit_phase_b2_gray_frontier.py"
    return {
        "selection_evidence": verified,
        "baseline": {"path": str(baseline_path), "sha256": sha256(baseline_path)},
        "analyzer": {"path": str(analyzer), "sha256": sha256(analyzer)},
        "completion_audit": {"path": str(completion_audit), "sha256": sha256(completion_audit)},
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
        "unregistered_gray_cells_added": False,
    }


def execute(jobs: list[dict], *, workers: int, campaign: str) -> None:
    run_dir = PROJECT_ROOT / ".tmp" / campaign
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    queue, active, completed, failed = deque(jobs), {}, [], []

    def write_status() -> None:
        atomic_json(status_path, {"updated_at": datetime.now(timezone.utc).isoformat(), "queued": [j["stem"] for j in queue], "active": [v["job"]["stem"] for v in active.values()], "completed": completed, "failed": failed})

    while queue or active:
        while queue and len(active) < workers:
            job = queue.popleft()
            log_path = run_dir / f"{job['stem']}.log"
            handle = log_path.open("a")
            process = subprocess.Popen(job["command"], cwd=PROJECT_ROOT, stdout=handle, stderr=subprocess.STDOUT)
            active[process.pid] = {"process": process, "job": job, "log": log_path, "handle": handle}
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
        raise SystemExit(f"{len(failed)} Phase B2 jobs failed; inspect {status_path}")


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
        raise SystemExit("Phase B2 is not production-ready; use --dry-run")
    workers = args.workers or int(manifest["workers_cap"])
    if not 1 <= workers <= int(manifest["workers_cap"]):
        raise SystemExit("workers exceed Phase B2 cap")
    execute(jobs, workers=workers, campaign=manifest["campaign"])


if __name__ == "__main__":
    main()
