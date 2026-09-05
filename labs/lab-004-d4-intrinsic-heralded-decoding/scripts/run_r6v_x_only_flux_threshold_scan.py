#!/usr/bin/env python3
"""Run the gated R6V matched D4 X-only flux-threshold scan.

This program deliberately refuses the large scan until the separately produced
R6U integrity report marks its scorer/provenance gate as passed.  Each output
row serializes physical and public observation provenance so the logical score
can be reproduced without re-sampling hidden truth.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import (
    build_r6d_dense_template,
    require_r6d_dense_backend,
    r6d_dense_backend_provenance,
    run_r6d_dense_template,
    validate_r6d_dense_checkpoint,
)
from d4_matching import edge_chain_boundary, published_herald_weights, syndrome_only_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import (
    decode_matching_policy,
    llr_weights,
    paired_summary,
    policy_summary,
    trajectory_seeds,
)


DEFAULT_MANIFEST = LAB_DIR / "manifests/r6v-x-only-flux-threshold-validation-manifest-2026-08-30.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6v-x-only-flux-threshold-scan-2026-08-30.json"


def decode_bp_policy_dense(template, lattice, physical: np.ndarray, observation, config: dict) -> dict:
    """Public-record BP->MWPM using the validated cached dense recurrence."""
    public = PublicD4Observation(
        tuple(int(value) for value in edge_chain_boundary(lattice, physical)),
        tuple(int(value) for value in observation.charge_outcomes),
    )
    started = time.perf_counter()
    try:
        bp = run_r6d_dense_template(
            template, public,
            old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]),
            tolerance=float(config["tolerance"]),
        )
        recovery = decode_and_score_flux_recovery(
            lattice, physical, llr_weights(bp.marginals[: lattice.edge_count, 1])
        )
    except Exception as error:
        return {
            "status": "unavailable",
            "reason": repr(error),
            "wall_seconds": time.perf_counter() - started,
            "backend_provenance": r6d_dense_backend_provenance(),
        }
    return {
        "status": "decoded",
        "flux_union_logical_failure": bool(recovery.logical_error),
        "objective_weight": float(recovery.objective_weight),
        "correction_edges": [int(edge) for edge in np.flatnonzero(recovery.correction)],
        "wall_seconds": time.perf_counter() - started,
        "bp": {"converged": bool(bp.converged), "iterations": int(bp.iterations),
               "max_message_delta": float(bp.max_message_delta)},
        "backend_provenance": r6d_dense_backend_provenance(),
    }


def _require_integrity_gate(manifest: dict, report: Path | None) -> Path:
    guard = manifest["launch_guard"]
    candidate = report or (LAB_DIR / guard["required_integrity_report"])
    if not candidate.is_file():
        raise RuntimeError(f"R6V launch refused: missing integrity report {candidate}")
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if payload.get(guard["required_field"]) is not guard["required_value"]:
        raise RuntimeError(
            "R6V launch refused: integrity gate field "
            f"{guard['required_field']!r} is not {guard['required_value']!r}"
        )
    return candidate


def planned_cells(
    manifest: dict,
    histories: int | None = None,
    selected_cells: set[tuple[int, float]] | None = None,
) -> list[dict]:
    design = manifest["scan_design"]
    count = int(histories if histories is not None else design["stage_1_attempted_histories_per_cell"])
    if count <= 0:
        raise ValueError("histories must be positive")
    cells = [
        {"size": int(size), "p_X": float(rate), "attempted_histories": count}
        for size in design["sizes"] for rate in design["p_X_grid"]
    ]
    if selected_cells is not None:
        registered = {(cell["size"], cell["p_X"]) for cell in cells}
        unknown = selected_cells - registered
        if unknown:
            raise ValueError(f"Stage-2 selection contains unregistered cells: {sorted(unknown)}")
        cells = [cell for cell in cells if (cell["size"], cell["p_X"]) in selected_cells]
    return cells


def load_stage_2_selection(path: Path) -> set[tuple[int, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("stage_2_selected_cells")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Stage-2 analysis has no selected cells")
    selected = {(int(row["size"]), float(row["p_X"])) for row in rows}
    if len(selected) != len(rows):
        raise ValueError("Stage-2 analysis contains duplicate selected cells")
    return selected


def _payload(manifest: dict, rows: list[dict], histories: int | None, *, status: str,
             manifest_name: str = DEFAULT_MANIFEST.name) -> dict:
    design = manifest["scan_design"]
    policies = [
        "O0_unit_weight_MWPM",
        "O2_published_herald_weight_MWPM",
        "R6D_local_BP_posterior_LLR_MWPM",
    ]
    cells = []
    for cell in planned_cells(manifest, histories):
        selected = [r for r in rows if r["size"] == cell["size"] and r["p_X"] == cell["p_X"]]
        if len(selected) != cell["attempted_histories"]:
            continue
        cells.append({
            **cell,
            "summaries": {policy: policy_summary(selected, policy) for policy in policies},
            "pairings": [
                paired_summary(selected, policies[0], policies[1]),
                paired_summary(selected, policies[0], policies[2]),
                paired_summary(selected, policies[1], policies[2]),
            ],
        })
    return {
        "schema_version": 2,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": manifest_name,
        "scan_design": design,
        "backend_provenance": r6d_dense_backend_provenance(),
        "cells": cells, "rows": rows,
        "claim_boundary": manifest["claim_boundary"],
    }


def _write_checkpoint(path: Path, manifest: dict, rows: list[dict], histories: int | None,
                      manifest_name: str) -> None:
    payload = _payload(manifest, rows, histories, status="in_progress_r6v_stage_1_x_only_flux_scan",
                       manifest_name=manifest_name)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(manifest: dict, *, histories: int | None = None, checkpoint: Path | None = None,
        resume_from: Path | None = None,
        selected_cells: set[tuple[int, float]] | None = None,
        manifest_name: str = DEFAULT_MANIFEST.name, progress_every: int = 0) -> dict:
    backend_provenance = require_r6d_dense_backend(manifest.get("backend_id"))
    design = manifest["scan_design"]
    policies = [
        "O0_unit_weight_MWPM",
        "O2_published_herald_weight_MWPM",
        "R6D_local_BP_posterior_LLR_MWPM",
    ]
    rows: list[dict] = []
    resume_path = checkpoint if checkpoint is not None and checkpoint.is_file() else resume_from
    if resume_path is not None:
        if not resume_path.is_file():
            raise RuntimeError(f"resume checkpoint does not exist: {resume_path}")
        prior = json.loads(resume_path.read_text(encoding="utf-8"))
        if prior.get("manifest") != manifest_name:
            raise RuntimeError(f"refusing incompatible checkpoint {resume_path}")
        validate_r6d_dense_checkpoint(prior)
        rows = list(prior.get("rows", []))
    for cell in planned_cells(manifest, histories, selected_cells):
        size, error_rate = cell["size"], cell["p_X"]
        existing = [r for r in rows if r["size"] == size and r["p_X"] == error_rate]
        existing_indices = sorted(int(row["trajectory_index"]) for row in existing)
        if existing_indices != list(range(len(existing_indices))):
            raise RuntimeError(f"non-contiguous trajectory indices for L={size}, p_X={error_rate}")
        if len(existing) > cell["attempted_histories"]:
            raise RuntimeError(f"checkpoint exceeds target for L={size}, p_X={error_rate}")
        if len(existing) == cell["attempted_histories"]:
            continue
        lattice = paper_periodic_honeycomb(size)
        bp_template = build_r6d_dense_template(lattice, error_rate=error_rate)
        for index in range(len(existing), cell["attempted_histories"]):
            physical_seed, observation_seed = trajectory_seeds(
                int(design["seed_salt"]), size, error_rate, index
            )
            physical = (
                np.random.default_rng(physical_seed).random(lattice.edge_count) < error_rate
            ).astype(np.uint8)
            observation = observation_from_error_edges(lattice, physical, seed=observation_seed)
            row = {
                "size": size, "p_X": error_rate, "trajectory_index": index,
                "physical_seed": physical_seed, "observation_seed": observation_seed,
                "physical_error_edges": [int(edge) for edge in np.flatnonzero(physical)],
                "observation_status": observation.status, "policies": {},
            }
            if observation.status == "logical_failure":
                row["status"] = "terminal_physical_winding"
                rows.append(row)
                continue
            if observation.status != "sampled" or observation.charge_outcomes is None:
                raise RuntimeError(f"unexpected observation status {observation.status!r}")
            row["status"] = "nonterminal"
            row["public_observation"] = {
                "flux_syndrome": [int(value) for value in edge_chain_boundary(lattice, physical)],
                "charge_outcomes": [int(value) for value in observation.charge_outcomes],
            }
            row["policies"][policies[0]] = decode_matching_policy(
                lattice, physical, syndrome_only_weights(lattice)
            )
            row["policies"][policies[1]] = decode_matching_policy(
                lattice, physical,
                published_herald_weights(lattice, np.asarray(observation.charge_outcomes, dtype=np.int64)),
            )
            row["policies"][policies[2]] = decode_bp_policy_dense(
                bp_template, lattice, physical, observation, design["bp_defaults"]
            )
            rows.append(row)
            if progress_every and (index + 1) % progress_every == 0:
                print(json.dumps({"progress": "running", "size": size, "p_X": error_rate,
                                  "completed_in_cell": index + 1,
                                  "target_in_cell": cell["attempted_histories"]}), flush=True)
        if checkpoint is not None:
            _write_checkpoint(checkpoint, manifest, rows, histories, manifest_name)
    return _payload(manifest, rows, histories, status="completed_r6v_stage_1_x_only_flux_scan",
                    manifest_name=manifest_name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--integrity-report", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, help="Resumable, cell-granular output checkpoint.")
    parser.add_argument("--resume-from", type=Path,
                        help="Seed a new checkpoint from a completed earlier stage without overwriting it.")
    parser.add_argument("--stage2-selection", type=Path,
                        help="Frozen analysis JSON containing stage_2_selected_cells.")
    parser.add_argument("--histories", type=int,
                        help="Target histories per selected cell; Stage 2 requires --stage2-selection.")
    parser.add_argument("--progress-every", type=int, default=0,
                        help="Emit progress every N trajectories without changing checkpoint cadence.")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    stage_1 = int(manifest["scan_design"]["stage_1_attempted_histories_per_cell"])
    stage_2_cap = int(manifest["scan_design"]["stage_2_max_attempted_histories_per_cell"])
    if args.histories is not None and not 0 < args.histories <= stage_2_cap:
        raise ValueError("--histories must be in [1, stage_2_max_attempted_histories_per_cell]")
    if args.histories is not None and args.histories > stage_1 and args.stage2_selection is None:
        raise ValueError("Stage-2 histories require --stage2-selection")
    allowed_statuses = {
        "registered_integrity_gate_pending",
        "stage_1_analyzed_refinement_pending",
        "stage_2_analyzed_refinement_pending",
        "stage_3_analyzed_refinement_pending",
        "stage_4_analyzed_refinement_pending",
    }
    if manifest.get("status") not in allowed_statuses:
        raise ValueError("scan manifest is not in a runnable registered state")
    if args.histories is not None and args.histories > stage_1 and not str(manifest.get("status", "")).endswith("_analyzed_refinement_pending"):
        raise ValueError("Stage-2 execution requires an analyzed Stage-1 manifest")
    selected_cells = load_stage_2_selection(args.stage2_selection) if args.stage2_selection else None
    gate = _require_integrity_gate(manifest, args.integrity_report)
    payload = run(manifest, histories=args.histories, checkpoint=args.checkpoint,
                  resume_from=args.resume_from, selected_cells=selected_cells,
                  manifest_name=args.manifest.name, progress_every=args.progress_every)
    payload["integrity_gate_report"] = str(gate)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cells": len(payload["cells"]), "rows": len(payload["rows"])}, sort_keys=True))


if __name__ == "__main__":
    main()
