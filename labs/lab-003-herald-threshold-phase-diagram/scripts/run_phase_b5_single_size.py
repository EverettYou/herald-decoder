#!/usr/bin/env python3
"""Run one preregistered Phase B5 size through the frozen Phase 2 kernel.

The shared Phase 2 CLI historically required two sizes because its original
deliverable was a crossing diagnostic.  Phase B5 legitimately measures L=5
alone and pools it with separately audited L=7/9/11/13 evidence.  This narrow
adapter calls the unchanged, single-size-capable ``run_shard`` function and
preserves the Phase 2 scientific source fingerprints.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = Path(__file__).with_name("run_phase2_scout.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("phase_b5_single_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lattice", choices=("honeycomb",), required=True)
    parser.add_argument("--q", type=float, required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--shots-per-seed", type=int, required=True)
    parser.add_argument("--max-iterations", type=int, required=True)
    parser.add_argument("--update-schedule", choices=("residual_priority",), required=True)
    parser.add_argument("--residual-priority-order", choices=("stable_sort",), required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--stem", required=True)
    args = parser.parse_args()

    if args.size != 5 or not 0 < args.p < 0.5 or not 0 <= args.q <= 1:
        raise SystemExit("Phase B5 single-size adapter accepts only registered L=5 cells")
    seeds = tuple(dict.fromkeys(args.seeds))
    if not seeds or args.shots_per_seed < 1 or args.max_iterations < 1:
        raise SystemExit("invalid Phase B5 sampling or iteration budget")

    runner = load_runner()
    if not runner.NUMBA_AVAILABLE:
        raise SystemExit("accelerated Numba runtime is required; use run_research_python.sh")
    result_path = LAB_DIR / "results" / f"{args.stem}.json"
    raw_path = LAB_DIR / "results" / f"{args.stem}-raw.jsonl.gz"
    if result_path.exists() or raw_path.exists():
        raise SystemExit("refusing to overwrite existing Phase B5 single-size shard")

    wrapper_hash = sha256(Path(__file__))
    source_hashes = runner.source_hashes()
    config = runner.config_payload(
        campaign=args.campaign,
        lattice=args.lattice,
        q=args.q,
        p_grid=(args.p,),
        sizes=(args.size,),
        seeds=seeds,
        shots_per_seed=args.shots_per_seed,
        max_iterations=args.max_iterations,
        update_schedule=args.update_schedule,
        residual_priority_order=args.residual_priority_order,
        residual_priority_buffer_reuse=False,
        residual_priority_cached_products=False,
    )
    generated = runner.run_shard(
        campaign=args.campaign,
        lattice=args.lattice,
        q=args.q,
        p_grid=(args.p,),
        sizes=(args.size,),
        seeds=seeds,
        shots_per_seed=args.shots_per_seed,
        max_iterations=args.max_iterations,
        update_schedule=args.update_schedule,
        residual_priority_order=args.residual_priority_order,
        residual_priority_buffer_reuse=False,
        residual_priority_cached_products=False,
        raw_path=raw_path,
        expected_source_hashes=source_hashes,
    )
    if sha256(Path(__file__)) != wrapper_hash:
        raw_path.unlink(missing_ok=True)
        raise RuntimeError("Phase B5 single-size wrapper drifted during execution")
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "Lab 003 Phase B5 preregistered single-size extension",
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        **config,
        "total_shots_per_cell": len(seeds) * args.shots_per_seed,
        "runtime": runner.runtime_provenance(),
        "source_hashes": source_hashes,
        "execution_wrapper": {
            "path": str(Path(__file__)),
            "sha256": wrapper_hash,
            "source_stable": True,
        },
        **generated,
        "evidence_boundary": "Fresh L=5 evidence only; scientific inference requires preregistered heterogeneous pooling.",
    }
    runner.atomic_json(result_path, payload)
    print(json.dumps({"status": "complete", "result": str(result_path), "raw": str(raw_path), "records": generated["raw_records"]["records"]}))


if __name__ == "__main__":
    main()
