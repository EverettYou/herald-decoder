#!/usr/bin/env python3
"""Generate the registered R5a production cohort after a passing preflight.

This executable is intentionally not invoked by the preflight tick. It writes
the complete matched trajectory records needed by the frozen analyzer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
LAB_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from d4_honeycomb import paper_periodic_honeycomb  # noqa: E402
from d4_pipeline import decode_physical_error  # noqa: E402
from run_r5a_public_decoder_preflight import (  # noqa: E402
    stage_outcome,
    trajectory_seeds,
    validate_record,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_production(manifest_path: Path, output_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "preflight_passed_production_authorized":
        raise RuntimeError("R5a production is not authorized by the manifest")
    activation = manifest.get("production_activation", {})
    frozen_sources = dict(manifest.get("source_freeze", {}))
    frozen_sources.update(activation.get("source_freeze", {}))
    for relative, expected in frozen_sources.items():
        actual = sha256(LAB_DIR / relative)
        if actual != expected:
            raise RuntimeError(f"production source hash mismatch: {relative}")

    design = manifest["design"]
    salt = int(design["seed_salt"])
    histories_per_cell = int(design["production_histories_per_size_rate"])
    temporary = output_path.with_name(output_path.name + ".partial")
    counts = {"histories": 0, "public_decoder_evaluations": 0}
    started = time.perf_counter()
    try:
        with gzip.open(temporary, "wt", encoding="utf-8") as handle:
            for size in design["sizes"]:
                lattice = paper_periodic_honeycomb(int(size))
                for error_rate in design["physical_error_rates"]:
                    for seed_index in range(histories_per_cell):
                        physical_seed, decoder_seed = trajectory_seeds(
                            salt, int(size), float(error_rate), seed_index
                        )
                        physical = (
                            np.random.default_rng(physical_seed).random(lattice.edge_count)
                            < float(error_rate)
                        ).astype(np.uint8)
                        records = {}
                        for mode in design["public_policies"]:
                            record = decode_physical_error(
                                lattice, physical, mode=str(mode), seed=decoder_seed
                            )
                            failures = validate_record(lattice, record)
                            if failures:
                                raise RuntimeError(
                                    f"pipeline invariant failure at L={size}, p={error_rate}, "
                                    f"seed={seed_index}, mode={mode}: {failures}"
                                )
                            records[str(mode)] = record
                            row = {
                                "schema_version": 1,
                                "size": int(size),
                                "error_rate": float(error_rate),
                                "seed_index": seed_index,
                                "physical_seed": physical_seed,
                                "decoder_seed": decoder_seed,
                                "mode": str(mode),
                                "status": record.status,
                                "stage_outcome": stage_outcome(record),
                                "logical_error": bool(record.logical_error),
                                "pipeline_record": record.to_dict(),
                            }
                            handle.write(json.dumps(row, sort_keys=True) + "\n")
                            counts["public_decoder_evaluations"] += 1
                        left, right = records["syndrome_only"], records["heralded"]
                        if left.physical_error_edges != right.physical_error_edges:
                            raise RuntimeError("paired policies do not share the physical error")
                        if left.observation != right.observation:
                            raise RuntimeError("paired policies do not share the initial observation")
                        counts["histories"] += 1
        os.replace(temporary, output_path)
    except Exception:
        if temporary.exists():
            failed = output_path.with_name(output_path.name + ".failed-partial")
            os.replace(temporary, failed)
        raise

    return {
        **counts,
        "wall_seconds": time.perf_counter() - started,
        "output": str(output_path),
        "output_sha256": sha256(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=LAB_DIR / "r5a-paper-lattice-public-decoder-pilot-manifest-2026-08-29.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LAB_DIR / "results/r5a-paper-lattice-public-decoder-pilot.jsonl.gz",
    )
    args = parser.parse_args()
    print(json.dumps(run_production(args.manifest.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
