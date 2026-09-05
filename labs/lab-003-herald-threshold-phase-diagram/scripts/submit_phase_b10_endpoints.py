#!/usr/bin/env python3
"""Fail-closed dispatcher and preflight for Phase B10."""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json"
DEFAULT_PREFLIGHT = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-preflight-2026-08-28.json"
EXPECTED = {
    (0.30, 0.20, (5, 13), 2000),
    (0.35, 0.20, (5, 13), 2000),
    (0.55, 0.24, (5, 13), 2000),
    (0.65, 0.32, (7, 11), 2000),
}
NEW_SEEDS = [890001, 890002, 890003, 890004, 890005]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b10_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def stem(job: dict) -> str:
    sizes = "-".join(map(str, job["sizes"]))
    return f"phase-b10-honeycomb-l{sizes}-q{int(round(100*job['q'])):03d}-p{int(round(100*job['p'])):03d}-2026-08-28"


def expand_jobs(manifest: dict, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    jobs = []
    for row in manifest["jobs"]:
        artifact = stem(row)
        result = lab_dir / "results" / f"{artifact}.json"
        raw = lab_dir / "results" / f"{artifact}-raw.jsonl.gz"
        decoder = manifest["decoder"]
        command = [
            str(project_root / "run_research_python.sh"), str(lab_dir / "scripts/run_phase2_scout.py"),
            "--lattice", "honeycomb", "--q", str(row["q"]), "--p", str(row["p"]),
            "--campaign", manifest["campaign"], "--stem", artifact,
            "--shots-per-seed", str(manifest["shots_per_seed"]), "--sizes", *map(str, row["sizes"]),
            "--seeds", *map(str, manifest["new_seeds"]), "--max-iterations", str(decoder["max_iterations"]),
            "--update-schedule", decoder["update_schedule"],
            "--residual-priority-order", decoder["residual_priority_order"],
        ]
        jobs.append({**row, "stem": artifact, "result": str(result), "raw": str(raw),
                     "output_conflict": result.exists() or raw.exists(), "command": command})
    return jobs


def validate(manifest_path: Path, manifest: dict, jobs: list[dict], reject_output_conflicts: bool = True) -> None:
    if manifest["status"] not in {"registered", "ready", "data_complete", "analyzed"}:
        raise ValueError("invalid Phase B10 lifecycle")
    if manifest["launch_gate"] not in {"closed_implementation", "ready", "closed_data_complete"}:
        raise ValueError("invalid Phase B10 launch gate")
    matrix = {(j["q"], j["p"], tuple(j["sizes"]), j["expected_decodes"]) for j in jobs}
    if matrix != EXPECTED or sum(j["expected_decodes"] for j in jobs) != 8000:
        raise ValueError("Phase B10 matrix/budget drift")
    if manifest["new_seeds"] != NEW_SEEDS or manifest["shots_per_seed"] != 200:
        raise ValueError("Phase B10 sampling drift")
    for field in ("selection_evidence", "source_map", "design_evidence"):
        path = LAB_DIR / manifest[field]["path"]
        if sha256(path) != manifest[field]["sha256"]:
            raise ValueError(f"Phase B10 {field} hash drift")
    selection = json.loads((LAB_DIR / manifest["selection_evidence"]["path"]).read_text())
    for record in selection["seed_overlap_audit"]["records"]:
        if sha256(LAB_DIR / record["path"]) != record["sha256"]:
            raise ValueError("Phase B10 seed-inventory hash drift")
    if selection["seed_overlap_audit"]["overlaps"]:
        raise ValueError("Phase B10 seed overlap")
    if load_runner().source_hashes() != manifest["required_source_hashes"]:
        raise ValueError("Phase B10 source hash drift")
    if reject_output_conflicts and any(j["output_conflict"] for j in jobs):
        raise ValueError("refusing Phase B10 output conflict")


def cli_shape_smoke(jobs: list[dict]) -> list[dict]:
    passed = []
    for job in jobs:
        command = list(job["command"])
        command[command.index("--shots-per-seed") + 1] = "0"
        run = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True)
        transcript = run.stdout + run.stderr
        if run.returncode == 0 or "seeds and shots-per-seed must be positive" not in transcript:
            raise ValueError(f"Phase B10 CLI smoke failed: {job['stem']}")
        passed.append({"stem": job["stem"], "sizes": job["sizes"], "reached_post_size_validation": True,
                       "no_output_written": not Path(job["result"]).exists() and not Path(job["raw"]).exists()})
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    jobs = expand_jobs(manifest)
    validate(args.manifest, manifest, jobs)
    gates = {}
    for filename in ("audit_phase_b10_outputs.py", "analyze_phase_b10_frontier.py", "render_phase_b10_merged_map.py"):
        path = Path(__file__).with_name(filename)
        if not path.is_file():
            raise ValueError(f"missing Phase B10 gate: {filename}")
        gates[filename] = sha256(path)
    if args.dry_run:
        payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                   "status": "preflight_passed_not_launched", "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
                   "jobs": jobs, "job_count": 4, "expected_new_decodes": 8000, "workers_cap": 4,
                   "cli_shape_smoke": cli_shape_smoke(jobs), "gate_scripts": gates,
                   "production_launched": False, "crossing_statistic_used": False, "grid_expanded": False}
        atomic_json(args.preflight, payload)
        print(json.dumps(payload, indent=2))
        return
    if manifest["status"] != "ready" or manifest["launch_gate"] != "ready":
        raise SystemExit("Phase B10 is not production-ready; use --dry-run")
    with concurrent.futures.ThreadPoolExecutor(max_workers=manifest["workers_cap"]) as pool:
        codes = list(pool.map(lambda job: subprocess.run(job["command"], cwd=PROJECT_ROOT).returncode, jobs))
    if any(codes):
        raise SystemExit(f"Phase B10 failures: {codes}")


if __name__ == "__main__":
    main()
