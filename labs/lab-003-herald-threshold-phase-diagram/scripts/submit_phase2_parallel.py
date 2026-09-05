#!/usr/bin/env python3
"""Resume-safe bounded parallel dispatcher for Lab 003 Phase 2 shards."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase2-scout-manifest.json"


def q_tag(q: float) -> str:
    return f"q{int(round(100 * q)):03d}"


def artifact_stem(manifest: dict, lattice: str, q: float) -> str:
    template = manifest.get(
        "artifact_stem_template",
        "phase2-{lattice}-{q_tag}-discovery-1000-2026-08-27",
    )
    return template.format(lattice=lattice, q_tag=q_tag(q))


def build_command(*, manifest: dict, runtime: Path, runner: Path, lattice: str, q: float) -> list[str]:
    decoder = manifest.get("decoder", {})
    command = [
        str(runtime), str(runner),
        "--lattice", lattice,
        "--q", f"{q:.2f}",
        "--campaign", manifest["campaign"],
        "--stem", artifact_stem(manifest, lattice, q),
        "--shots-per-seed", str(manifest["shots_per_seed"]),
        "--sizes", *[str(value) for value in manifest["sizes"]],
        "--seeds", *[str(value) for value in manifest["seeds"]],
        "--p", *[str(value) for value in manifest["p_grid"][lattice]],
        "--max-iterations", str(decoder.get("max_iterations", 40)),
        "--update-schedule", decoder.get("update_schedule", "synchronous"),
        "--residual-priority-order", decoder.get("residual_priority_order", "scan"),
        "--skip-existing",
    ]
    if decoder.get("residual_priority_buffer_reuse", False):
        command.append("--residual-priority-buffer-reuse")
    if decoder.get("residual_priority_cached_products", False):
        command.append("--residual-priority-cached-products")
    if lattice == "honeycomb" and any(float(value) >= 0.5 for value in manifest["p_grid"][lattice]):
        command.append("--allow-honeycomb-high-p")
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    workers = args.workers or int(manifest["workers"])
    if not 1 <= workers <= 8:
        raise SystemExit("workers must lie in [1, 8]")
    runtime = PROJECT_ROOT / "run_research_python.sh"
    runner = Path(__file__).with_name("run_phase2_scout.py")
    if not args.dry_run and manifest.get("status", "ready") != "ready":
        raise SystemExit("manifest is not production-ready; complete its execution_gate and set status=ready")
    planned_jobs = [(lattice, float(q)) for q in manifest["q_values"] for lattice in manifest["lattices"]]
    if args.dry_run:
        print(json.dumps({
            "campaign": manifest["campaign"],
            "jobs": [
                {
                    "lattice": lattice,
                    "q": q,
                    "stem": artifact_stem(manifest, lattice, q),
                    "command": build_command(
                        manifest=manifest,
                        runtime=runtime,
                        runner=runner,
                        lattice=lattice,
                        q=q,
                    ),
                }
                for lattice, q in planned_jobs
            ],
        }, indent=2))
        return
    run_dir = PROJECT_ROOT / ".tmp" / manifest["campaign"]
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    jobs = deque(planned_jobs)
    completed = []
    failed = []
    active: dict[int, dict] = {}

    def write_status() -> None:
        # This is ephemeral progress, not a scientific commit marker.  A
        # direct low-frequency write avoids Dropbox conflict copies caused by
        # renaming a status file every polling second.
        status_path.write_text(json.dumps({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "manifest": str(args.manifest),
            "workers": workers,
            "queued": [{"lattice": lattice, "q": q} for lattice, q in jobs],
            "active": [{"pid": pid, "lattice": item["lattice"], "q": item["q"], "log": str(item["log"])} for pid, item in active.items()],
            "completed": completed,
            "failed": failed,
        }, indent=2) + "\n")

    while jobs or active:
        changed = False
        while jobs and len(active) < workers:
            lattice, q = jobs.popleft()
            tag = f"q{int(round(q * 100)):03d}"
            log_path = run_dir / f"{lattice}-{tag}.log"
            command = build_command(
                manifest=manifest,
                runtime=runtime,
                runner=runner,
                lattice=lattice,
                q=q,
            )
            log = log_path.open("a")
            process = subprocess.Popen(command, cwd=PROJECT_ROOT, stdout=log, stderr=subprocess.STDOUT)
            active[process.pid] = {"process": process, "log_handle": log, "log": log_path, "lattice": lattice, "q": q}
            print(json.dumps({"event": "started", "pid": process.pid, "lattice": lattice, "q": q, "log": str(log_path)}), flush=True)
            changed = True
        if changed:
            write_status()
        time.sleep(1.0)
        changed = False
        for pid, item in list(active.items()):
            return_code = item["process"].poll()
            if return_code is None:
                continue
            item["log_handle"].close()
            record = {"lattice": item["lattice"], "q": item["q"], "return_code": return_code, "log": str(item["log"])}
            (completed if return_code == 0 else failed).append(record)
            print(json.dumps({"event": "finished", **record}), flush=True)
            del active[pid]
            changed = True
        if changed:
            write_status()
    write_status()
    if failed:
        raise SystemExit(f"{len(failed)} Phase 2 shards failed; inspect {status_path}")


if __name__ == "__main__":
    main()
