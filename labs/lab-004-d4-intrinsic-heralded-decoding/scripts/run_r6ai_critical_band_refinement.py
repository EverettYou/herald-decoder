#!/usr/bin/env python3
"""Run the compact, checkpointed R6AI critical-band refinement."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_dense_template, require_r6d_dense_backend
from d4_matching import edge_chain_boundary, published_herald_weights
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import decode_matching_policy, trajectory_seeds
from run_r6v_x_only_flux_threshold_scan import decode_bp_policy_dense


DEFAULT_MANIFEST = LAB / "manifests/r6ai-critical-band-refinement-manifest-2026-09-01.json"
DEFAULT_CHECKPOINT = LAB / "results/r6ai-critical-band-refinement.checkpoint.json"
DEFAULT_OUTPUT = LAB / "results/r6ai-critical-band-refinement-stage1-2026-09-01.json"
POLICIES = (
    "O2_published_herald_weight_MWPM",
    "R6D_local_BP_posterior_LLR_MWPM",
)


def require_launch_guard(manifest: dict) -> Path:
    guard = manifest["launch_guard"]
    path = LAB / guard["required_integrity_report"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get(guard["required_field"]) is not guard["required_value"]:
        raise RuntimeError("R6AI launch guard failed")
    return path


def planned_cells(manifest: dict) -> list[tuple[int, float]]:
    design = manifest["scan_design"]
    return [
        (int(size), float(rate))
        for size in design["sizes"]
        for rate in design["new_p_X_grid"]
    ]


def load_selected_cells(path: Path | None) -> set[tuple[int, float]] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("stage_2_selected_cells")
    if not isinstance(rows, list):
        raise ValueError("selection file has no stage_2_selected_cells")
    return {(int(row["size"]), float(row["p_X"])) for row in rows}


def simulate_one(manifest: dict, size: int, rate: float, index: int, lattice, template) -> dict:
    design = manifest["scan_design"]
    physical_seed, observation_seed = trajectory_seeds(
        int(design["seed_salt"]), size, rate, index
    )
    physical = (
        np.random.default_rng(physical_seed).random(lattice.edge_count) < rate
    ).astype(np.uint8)
    observation = observation_from_error_edges(lattice, physical, seed=observation_seed)
    row = {
        "size": size,
        "p_X": rate,
        "trajectory_index": index,
        "physical_seed": int(physical_seed),
        "observation_seed": int(observation_seed),
        "observation_status": observation.status,
    }
    if observation.status == "logical_failure":
        row.update({
            "status": "terminal_physical_winding",
            "logical_failures": {policy: True for policy in POLICIES},
            "bp": None,
        })
        return row
    if observation.status != "sampled" or observation.charge_outcomes is None:
        raise RuntimeError(f"unexpected observation status {observation.status!r}")
    charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    o2 = decode_matching_policy(
        lattice, physical, published_herald_weights(lattice, charge)
    )
    bp = decode_bp_policy_dense(
        template, lattice, physical, observation, design["bp_defaults"]
    )
    if o2.get("status") != "decoded" or bp.get("status") != "decoded":
        raise RuntimeError(f"decoder unavailable: O2={o2.get('status')}, BP={bp.get('status')}")
    row.update({
        "status": "nonterminal",
        "public_flux_weight": int(np.count_nonzero(edge_chain_boundary(lattice, physical))),
        "public_charge_signal_weight": int(np.count_nonzero(charge)),
        "logical_failures": {
            POLICIES[0]: bool(o2["flux_union_logical_failure"]),
            POLICIES[1]: bool(bp["flux_union_logical_failure"]),
        },
        "bp": {
            "converged": bool(bp["bp"]["converged"]),
            "iterations": int(bp["bp"]["iterations"]),
            "max_message_delta": float(bp["bp"]["max_message_delta"]),
        },
    })
    return row


def scientific_fields(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "size", "p_X", "trajectory_index", "physical_seed", "observation_seed",
            "observation_status", "status", "public_flux_weight",
            "public_charge_signal_weight", "logical_failures", "bp",
        )
    }


def payload(manifest: dict, rows: list[dict], target: int, replays: list[dict], guard: Path) -> dict:
    complete = []
    for size, rate in planned_cells(manifest):
        count = sum(row["size"] == size and row["p_X"] == rate for row in rows)
        if count == target:
            complete.append({"size": size, "p_X": rate, "attempted_histories": count})
    return {
        "schema_version": 1,
        "status": "completed" if len(complete) == len(planned_cells(manifest)) else "in_progress",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": DEFAULT_MANIFEST.name,
        "target_histories_per_cell": target,
        "launch_guard": str(guard.relative_to(LAB)),
        "completed_cells": complete,
        "rows": rows,
        "deterministic_replays": replays,
        "compact_schema": True,
        "claim_boundary": manifest["claim_boundary"],
    }


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(manifest: dict, checkpoint: Path, target: int, selected: set[tuple[int, float]] | None,
        progress_every: int) -> dict:
    require_r6d_dense_backend(manifest.get("backend_id"))
    guard = require_launch_guard(manifest)
    rows: list[dict] = []
    prior_replays: list[dict] = []
    if checkpoint.is_file():
        prior = json.loads(checkpoint.read_text(encoding="utf-8"))
        if prior.get("manifest") != DEFAULT_MANIFEST.name:
            raise RuntimeError("refusing incompatible R6AI checkpoint")
        rows = list(prior.get("rows", []))
        prior_replays = list(prior.get("deterministic_replays", []))
    registered = set(planned_cells(manifest))
    active = registered if selected is None else selected
    if not active.issubset(registered):
        raise ValueError("selection includes an unregistered R6AI cell")
    replay_map = {
        (int(item["size"]), float(item["p_X"]), int(item["trajectory_index"])): item
        for item in prior_replays
    }
    for size, rate in sorted(active):
        existing = sorted(
            (row for row in rows if row["size"] == size and row["p_X"] == rate),
            key=lambda row: int(row["trajectory_index"]),
        )
        indices = [int(row["trajectory_index"]) for row in existing]
        if indices != list(range(len(existing))) or len(existing) > target:
            raise RuntimeError(f"invalid checkpoint cell L={size}, p_X={rate}")
        lattice = paper_periodic_honeycomb(size)
        template = build_r6d_dense_template(lattice, error_rate=rate)
        for index in range(len(existing), target):
            rows.append(simulate_one(manifest, size, rate, index, lattice, template))
            if progress_every and (index + 1) % progress_every == 0:
                print(json.dumps({
                    "progress": "running", "size": size, "p_X": rate,
                    "completed_in_cell": index + 1, "target_in_cell": target,
                }), flush=True)
        for index in sorted({0, target // 2, target - 1}):
            original = next(
                row for row in rows
                if row["size"] == size and row["p_X"] == rate and row["trajectory_index"] == index
            )
            replay = simulate_one(manifest, size, rate, index, lattice, template)
            exact = scientific_fields(original) == scientific_fields(replay)
            item = {"size": size, "p_X": rate, "trajectory_index": index, "exact": exact}
            replay_map[(size, rate, index)] = item
            if not exact:
                raise AssertionError(f"deterministic replay failed for {item}")
        current = payload(manifest, rows, target, list(replay_map.values()), guard)
        write_json(checkpoint, current)
    return payload(manifest, rows, target, list(replay_map.values()), guard)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--histories", type=int)
    parser.add_argument("--selected-cells", type=Path)
    parser.add_argument("--progress-every", type=int, default=250)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("status") not in {"registered_stage_1", "stage_1_analyzed_refinement_pending"}:
        raise ValueError("R6AI manifest is not runnable")
    default_target = int(manifest["scan_design"]["stage_1_attempted_histories_per_new_cell"])
    target = args.histories or default_target
    cap = int(manifest["scan_design"]["stage_2_max_attempted_histories_per_new_cell"])
    if not 0 < target <= cap:
        raise ValueError("histories target is outside the registered cap")
    selected = load_selected_cells(args.selected_cells)
    if target > default_target and selected is None:
        raise ValueError("Stage-2 increments require a frozen selected-cell analysis")
    result = run(manifest, args.checkpoint, target, selected, args.progress_every)
    write_json(args.output, result)
    print(json.dumps({
        "output": str(args.output), "rows": len(result["rows"]),
        "completed_cells": len(result["completed_cells"]),
        "replay_count": len(result["deterministic_replays"]),
    }), flush=True)


if __name__ == "__main__":
    main()
