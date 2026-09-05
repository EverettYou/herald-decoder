#!/usr/bin/env python3
"""Run the registered O2-only D4 flux-threshold quick scan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d4_honeycomb import paper_periodic_honeycomb
from d4_matching import published_herald_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import trajectory_seeds


DEFAULT_MANIFEST = LAB_DIR / "r6ab-o2-threshold-quick-scan-manifest-2026-08-31.json"
DEFAULT_CHECKPOINT = LAB_DIR / "results/r6ab-o2-threshold-quick-scan-2026-08-31.checkpoint.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6ab-o2-threshold-quick-scan-2026-08-31.json"
SOURCE_FILES = (
    "d4_honeycomb.py",
    "d4_matching.py",
    "d4_recovery.py",
    "d4_sampler.py",
    "run_r6ab_o2_threshold_quick_scan.py",
)


def source_provenance() -> dict[str, str]:
    return {
        name: hashlib.sha256((SCRIPT_DIR / name).read_bytes()).hexdigest()
        for name in SOURCE_FILES
    }


def planned_cells(manifest: dict) -> list[tuple[int, float, int]]:
    design = manifest["scan_design"]
    count = int(design["attempted_histories_per_cell"])
    return [
        (int(size), float(rate), count)
        for size in design["sizes"]
        for rate in design["p_X_grid"]
    ]


def summarize_cell(rows: list[dict], size: int, rate: float) -> dict:
    selected = [row for row in rows if row["size"] == size and row["p_X"] == rate]
    nonterminal = [row for row in selected if row["status"] == "nonterminal"]
    failures = sum(bool(row["flux_union_logical_failure"]) for row in nonterminal)
    terminal = len(selected) - len(nonterminal)
    return {
        "size": size,
        "p_X": rate,
        "attempted_histories": len(selected),
        "nonterminal_histories": len(nonterminal),
        "terminal_physical_windings": terminal,
        "conditional_flux_failures": failures,
        "conditional_flux_failure_rate": failures / len(nonterminal) if nonterminal else None,
        "terminal_restored_failures": failures + terminal,
        "terminal_restored_flux_failure_rate": (failures + terminal) / len(selected) if selected else None,
    }


def make_payload(manifest: dict, rows: list[dict], *, status: str, manifest_name: str) -> dict:
    cells = [summarize_cell(rows, size, rate) for size, rate, _count in planned_cells(manifest)]
    return {
        "schema_version": 1,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": manifest_name,
        "source_provenance": source_provenance(),
        "scan_design": manifest["scan_design"],
        "decoder": manifest["decoder"],
        "cells": cells,
        "rows": rows,
        "claim_boundary": manifest["claim_boundary"],
    }


def write_payload(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(manifest: dict, checkpoint: Path, *, manifest_name: str) -> dict:
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6AB":
        raise ValueError("manifest is not an active R6AB registration")
    provenance = source_provenance()
    rows: list[dict] = []
    if checkpoint.is_file():
        prior = json.loads(checkpoint.read_text(encoding="utf-8"))
        if prior.get("manifest") != manifest_name or prior.get("source_provenance") != provenance:
            raise RuntimeError("refusing incompatible or stale R6AB checkpoint")
        rows = list(prior.get("rows", []))
    completed = {
        (cell["size"], cell["p_X"])
        for cell in prior.get("cells", [])
        if checkpoint.is_file()
        if cell.get("attempted_histories") == manifest["scan_design"]["attempted_histories_per_cell"]
    } if checkpoint.is_file() else set()

    design = manifest["scan_design"]
    for size, rate, count in planned_cells(manifest):
        if (size, rate) in completed:
            continue
        lattice = paper_periodic_honeycomb(size)
        for index in range(count):
            physical_seed, observation_seed = trajectory_seeds(
                int(design["seed_salt"]), size, rate, index
            )
            physical = (
                np.random.default_rng(physical_seed).random(lattice.edge_count) < rate
            ).astype(np.uint8)
            observation = observation_from_error_edges(
                lattice, physical, seed=observation_seed
            )
            row = {
                "size": size,
                "p_X": rate,
                "trajectory_index": index,
                "physical_seed": physical_seed,
                "observation_seed": observation_seed,
                "status": "terminal_physical_winding" if observation.status == "logical_failure" else "nonterminal",
            }
            if observation.status == "logical_failure":
                row["flux_union_logical_failure"] = None
                rows.append(row)
                continue
            if observation.status != "sampled" or observation.charge_outcomes is None:
                raise RuntimeError(f"unexpected observation status {observation.status!r}")
            started = time.perf_counter()
            result = decode_and_score_flux_recovery(
                lattice,
                physical,
                published_herald_weights(
                    lattice, np.asarray(observation.charge_outcomes, dtype=np.int64)
                ),
            )
            row.update({
                "flux_union_logical_failure": bool(result.logical_error),
                "objective_weight": float(result.objective_weight),
                "correction_edges": [int(edge) for edge in np.flatnonzero(result.correction)],
                "decode_wall_seconds": time.perf_counter() - started,
            })
            rows.append(row)
        write_payload(
            checkpoint,
            make_payload(manifest, rows, status="in_progress_r6ab_o2_threshold_scan", manifest_name=manifest_name),
        )
    return make_payload(
        manifest, rows, status="completed_r6ab_o2_threshold_scan", manifest_name=manifest_name
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    payload = run(manifest, args.checkpoint, manifest_name=args.manifest.name)
    write_payload(args.output, payload)
    print(json.dumps({"output": str(args.output), "rows": len(payload["rows"]), "cells": len(payload["cells"])}))


if __name__ == "__main__":
    main()
