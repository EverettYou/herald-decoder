#!/usr/bin/env python3
"""Fail-closed dispatcher and real CLI-shape preflight for Phase B14."""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json"
DEFAULT_PREFLIGHT = LAB_DIR / "results/phase-b14-honeycomb-two-branch-preflight-2026-08-28.json"
EXPECTED_CELLS = {(0.20, 0.16), (0.20, 0.20), (0.70, 0.28), (0.70, 0.32)}
EXPECTED_BRANCHES = {
    "distance_leverage_L5_L13": ((5, 13), (891001, 891002, 891003, 891004, 891005), 1000),
    "same_window_precision_L7_L9_L11": ((7, 9, 11), (892001, 892002, 892003, 892004, 892005), 1500),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_hash(path: Path, hash_kind: str) -> str:
    if hash_kind == "full_file_sha256":
        return sha256(path)
    if hash_kind == "canonical_json_excluding_generated_at":
        payload = json.loads(Path(path).read_text())
        payload.pop("generated_at", None)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()
    raise ValueError(f"unknown Phase B14 evidence hash kind: {hash_kind}")


def atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def load_runner():
    path = Path(__file__).with_name("run_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase_b14_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def stem(job: dict) -> str:
    branch = "distance-l5-l13" if job["branch"] == "distance_leverage_L5_L13" else "precision-l7-l9-l11"
    return (
        f"phase-b14-honeycomb-{branch}-q{int(round(100 * job['q'])):03d}"
        f"-p{int(round(100 * job['p'])):03d}-2026-08-28"
    )


def expand_jobs(manifest: dict, project_root: Path = PROJECT_ROOT, lab_dir: Path = LAB_DIR) -> list[dict]:
    jobs = []
    for row in manifest["jobs"]:
        artifact = stem(row)
        result = lab_dir / "results" / f"{artifact}.json"
        raw = lab_dir / "results" / f"{artifact}-raw.jsonl.gz"
        decoder = manifest["decoder"]
        command = [
            str(project_root / "run_research_python.sh"),
            str(lab_dir / "scripts/run_phase2_scout.py"),
            "--lattice", "honeycomb",
            "--q", str(row["q"]),
            "--p", str(row["p"]),
            "--campaign", manifest["campaign"],
            "--stem", artifact,
            "--shots-per-seed", str(row["shots_per_seed"]),
            "--sizes", *map(str, row["sizes"]),
            "--seeds", *map(str, row["seeds"]),
            "--max-iterations", str(decoder["max_iterations"]),
            "--update-schedule", decoder["update_schedule"],
            "--residual-priority-order", decoder["residual_priority_order"],
        ]
        jobs.append({
            **row,
            "stem": artifact,
            "result": str(result),
            "raw": str(raw),
            "output_conflict": result.exists() or raw.exists(),
            "command": command,
        })
    return jobs


def historical_seed_overlap(manifest_path: Path, jobs: list[dict]) -> list[dict]:
    proposed = {int(seed) for job in jobs for seed in job["seeds"]}
    overlaps = []
    for path in sorted(LAB_DIR.glob("phase-*-manifest-*.json")):
        if path.resolve() == Path(manifest_path).resolve():
            continue
        payload = json.loads(path.read_text())
        used = {int(seed) for seed in payload.get("new_seeds", [])}
        historical_jobs = payload.get("jobs", [])
        if isinstance(historical_jobs, list):
            for job in historical_jobs:
                if isinstance(job, dict):
                    used.update(map(int, job.get("seeds", [])))
        shared = sorted(proposed & used)
        if shared:
            overlaps.append({"path": str(path.relative_to(LAB_DIR)), "seeds": shared})
    return overlaps


def validate(manifest_path: Path, manifest: dict, jobs: list[dict], reject_output_conflicts: bool = True) -> None:
    if manifest["status"] != "registered_preflight_required":
        raise ValueError("invalid Phase B14 lifecycle")
    if manifest["launch_gate"] != "requires_valid_preflight_artifact":
        raise ValueError("invalid Phase B14 launch gate")
    cells = {(float(job["q"]), float(job["p"])) for job in jobs}
    if cells != EXPECTED_CELLS or len(jobs) != 8:
        raise ValueError("Phase B14 cell/job matrix drift")
    for cell in EXPECTED_CELLS:
        at_cell = [job for job in jobs if (float(job["q"]), float(job["p"])) == cell]
        if {job["branch"] for job in at_cell} != set(EXPECTED_BRANCHES):
            raise ValueError("Phase B14 branch coverage drift")
        for job in at_cell:
            sizes, seeds, decodes = EXPECTED_BRANCHES[job["branch"]]
            if tuple(job["sizes"]) != sizes or tuple(job["seeds"]) != seeds:
                raise ValueError("Phase B14 size/seed drift")
            if job["shots_per_seed"] != 100 or job["expected_decodes"] != decodes:
                raise ValueError("Phase B14 shot/budget drift")
    if sum(job["expected_decodes"] for job in jobs) != 10000 or manifest["workers_cap"] != 4:
        raise ValueError("Phase B14 total budget/worker drift")
    for source in manifest["sources"]:
        if evidence_hash(LAB_DIR / source["path"], source["hash_kind"]) != source["sha256"]:
            raise ValueError("Phase B14 source evidence hash drift")
    selection = LAB_DIR / manifest["selection_evidence"]["path"]
    designer = LAB_DIR / manifest["designer"]["path"]
    if sha256(selection) != manifest["selection_evidence"]["sha256"]:
        raise ValueError("Phase B14 selection hash drift")
    if sha256(designer) != manifest["designer"]["sha256"]:
        raise ValueError("Phase B14 designer hash drift")
    if load_runner().source_hashes() != manifest["required_source_hashes"]:
        raise ValueError("Phase B14 source hash drift")
    if historical_seed_overlap(manifest_path, jobs):
        raise ValueError("Phase B14 seed overlap")
    if reject_output_conflicts and any(job["output_conflict"] for job in jobs):
        raise ValueError("refusing Phase B14 output conflict")


def cli_shape_smoke(jobs: list[dict]) -> list[dict]:
    records = []
    for job in jobs:
        command = list(job["command"])
        command[command.index("--shots-per-seed") + 1] = "0"
        run = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True)
        transcript = run.stdout + run.stderr
        no_output = not Path(job["result"]).exists() and not Path(job["raw"]).exists()
        if run.returncode == 0 or "seeds and shots-per-seed must be positive" not in transcript or not no_output:
            raise ValueError(f"Phase B14 CLI smoke failed: {job['stem']}")
        records.append({
            "stem": job["stem"],
            "branch": job["branch"],
            "sizes": job["sizes"],
            "reached_post_size_validation": True,
            "no_output_written": True,
        })
    return records


def require_preflight(manifest_path: Path, preflight_path: Path) -> dict:
    if not preflight_path.is_file():
        raise ValueError("missing Phase B14 preflight artifact")
    payload = json.loads(preflight_path.read_text())
    if payload.get("status") != "preflight_passed_not_launched":
        raise ValueError("Phase B14 preflight not passed")
    if payload.get("manifest", {}).get("sha256") != sha256(manifest_path):
        raise ValueError("Phase B14 preflight manifest hash drift")
    for filename, expected in payload.get("gate_scripts", {}).items():
        if sha256(Path(__file__).with_name(filename)) != expected:
            raise ValueError("Phase B14 gate script hash drift")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    jobs = expand_jobs(manifest)
    validate(args.manifest, manifest, jobs)
    gate_scripts = {}
    for filename in ("audit_phase_b14_outputs.py", "analyze_phase_b14_two_branch.py"):
        path = Path(__file__).with_name(filename)
        if not path.is_file():
            raise ValueError(f"missing Phase B14 gate: {filename}")
        gate_scripts[filename] = sha256(path)
    if args.dry_run:
        payload = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "preflight_passed_not_launched",
            "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
            "jobs": jobs,
            "job_count": len(jobs),
            "expected_new_decodes": sum(job["expected_decodes"] for job in jobs),
            "workers_cap": manifest["workers_cap"],
            "source_hashes_verified": manifest["required_source_hashes"],
            "historical_seed_overlap": [],
            "cli_shape_smoke": cli_shape_smoke(jobs),
            "gate_scripts": gate_scripts,
            "production_launched": False,
            "cell_or_phase_classification": False,
            "boundary_inference": False,
        }
        atomic_json(args.preflight, payload)
        print(json.dumps(payload, indent=2))
        return
    require_preflight(args.manifest, args.preflight)
    with concurrent.futures.ThreadPoolExecutor(max_workers=manifest["workers_cap"]) as pool:
        codes = list(pool.map(lambda job: subprocess.run(job["command"], cwd=PROJECT_ROOT).returncode, jobs))
    if any(codes):
        raise SystemExit(f"Phase B14 failures: {codes}")


if __name__ == "__main__":
    main()
