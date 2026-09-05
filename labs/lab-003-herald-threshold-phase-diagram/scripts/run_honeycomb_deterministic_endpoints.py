#!/usr/bin/env python3
"""Persist the exact p=0 and p=1 honeycomb q=1 endpoint checks.

BP is intentionally not evaluated at either degenerate Bernoulli prior.  The
known configurations are their own syndrome-faithful MAP corrections: all-zero
at p=0 and all-one at p=1.  The endpoint artifact is kept separate from the
open-interval BP series.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from herald_decoder import honeycomb_graph


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
CAMPAIGN = "honeycomb-q1-full-p-endpoints-2026-08-27"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=(5, 7, 9, 11))
    parser.add_argument("--seeds", type=int, nargs="+", default=(540001, 540002, 540003, 540004, 540005))
    parser.add_argument("--shots-per-seed", type=int, default=200)
    parser.add_argument("--stem", default="q1-honeycomb-full-p-endpoints-1000-2026-08-27")
    args = parser.parse_args()
    if not args.sizes or any(size < 2 for size in args.sizes) or not args.seeds or args.shots_per_seed < 1:
        raise SystemExit("sizes, seeds, and shots-per-seed must be positive")
    results_dir = LAB_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    result_path = results_dir / f"{args.stem}.json"
    raw_path = results_dir / f"{args.stem}-raw.jsonl.gz"
    if result_path.exists() or raw_path.exists():
        raise SystemExit(f"refusing to overwrite endpoint artifact: {result_path}")
    temporary_raw = raw_path.with_name(f".{raw_path.name}.tmp-{os.getpid()}")
    records = 0
    summaries = []
    with gzip.open(temporary_raw, "wt", encoding="utf-8", compresslevel=6) as raw:
        for size in args.sizes:
            graph = honeycomb_graph(size)
            detector = list(graph.detector_vertices)
            for p in (0.0, 1.0):
                error = np.full(len(graph.edges), int(p), dtype=np.uint8)
                syndrome = graph.true_syndrome(error)
                herald = (graph.degrees(error)[detector] >= 2).astype(np.uint8)
                correction = error.copy()
                if not np.array_equal(graph.true_syndrome(correction), syndrome):
                    raise RuntimeError(f"endpoint correction is not syndrome faithful at L={size}, p={p}")
                logical_failure = bool(graph.logical_parity(error ^ correction))
                for seed in args.seeds:
                    for shot in range(args.shots_per_seed):
                        raw.write(json.dumps({
                            "campaign": CAMPAIGN,
                            "lattice": "honeycomb",
                            "L": size,
                            "p": p,
                            "q": 1.0,
                            "decoder": "deterministic_known_configuration_endpoint",
                            "seed": seed,
                            "shot": shot,
                            "logical_failure": logical_failure,
                            "syndrome_faithful": True,
                        }, separators=(",", ":")) + "\n")
                        records += 1
                summaries.append({
                    "lattice": "honeycomb", "L": size, "p": p, "q": 1.0,
                    "shots": len(args.seeds) * args.shots_per_seed,
                    "logical_errors": 0, "logical_error_rate": 0.0,
                    "logical_error_ci95": [0.0, 0.0],
                    "decoder": "deterministic_known_configuration_endpoint",
                    "syndrome_fidelity_rate": 1.0,
                    "interpretation": "exact deterministic endpoint; not BP",
                })
    os.replace(temporary_raw, raw_path)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "Honeycomb q=1 deterministic full-p endpoints",
        "campaign": CAMPAIGN,
        "lattice": "honeycomb", "q": 1.0,
        "sizes": args.sizes, "seeds": args.seeds, "shots_per_seed": args.shots_per_seed,
        "endpoint_rule": "At p=0 or p=1 use the known all-zero or all-one error configuration as the syndrome-faithful correction; BP is undefined at these degenerate priors.",
        "summaries": summaries,
        "raw_records": {"path": str(raw_path.relative_to(LAB_DIR)), "format": "gzip_json_lines", "records": records, "sha256": sha256(raw_path)},
        "source_hashes": {"runner": sha256(Path(__file__)), "lattice_model": sha256(PROJECT_ROOT / "src/herald_decoder/lattice_model.py")},
    }
    atomic_json(result_path, payload)
    print(json.dumps({"status": "complete", "result": str(result_path), "records": records}))


if __name__ == "__main__":
    main()
