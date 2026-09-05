#!/usr/bin/env python3
"""Execute and analyze the preregistered R6AF paired two-stage pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_honeycomb import paper_periodic_honeycomb
from d4_pipeline import decode_physical_error_with_keys


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json"
DEFAULT_PREFLIGHT = LAB_DIR / "results/r6af-two-stage-public-charge-preflight-2026-09-01.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def trajectory_keys(salt: int, size: int, error_rate: float, index: int) -> tuple[int, int, int]:
    rate_key = int(round(1_000_000 * float(error_rate)))
    tags = (0xD400, 0xD401, 0xD402)
    return tuple(
        int(
            np.random.SeedSequence(
                [int(salt), int(size), rate_key, int(index), tag]
            ).generate_state(1)[0]
        )
        for tag in tags
    )


def wilson_interval(successes: int, total: int, z: float = 1.6448536269514722) -> list[float]:
    if total <= 0:
        raise ValueError("Wilson interval requires a positive denominator")
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = (
        z
        * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def exact_discordance_p_value(o0_only: int, o2_only: int) -> float:
    discordant = int(o0_only) + int(o2_only)
    if discordant == 0:
        return 1.0
    tail = min(int(o0_only), int(o2_only))
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def paired_bootstrap_interval(
    differences: np.ndarray,
    *,
    size: int,
    error_rate: float,
    salt: int,
    replicates: int,
) -> list[float]:
    values = np.asarray(differences, dtype=np.int8)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("paired bootstrap requires one nonempty difference vector")
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [int(salt), int(size), int(round(1_000_000 * error_rate))]
        )
    )
    estimates = np.empty(replicates, dtype=np.float64)
    chunk = 500
    for start in range(0, replicates, chunk):
        stop = min(replicates, start + chunk)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        estimates[start:stop] = np.mean(values[indices], axis=1)
    low, high = np.quantile(estimates, (0.05, 0.95))
    return [float(low), float(high)]


def _stage(record) -> str:
    if record.status == "physical_winding_failure":
        return "physical_winding_failure"
    if record.status == "flux_union_logical_failure":
        return "flux_union_logical_failure"
    if record.status != "decoded" or record.charge_recovery is None:
        raise RuntimeError(f"unexpected integrated status {record.status!r}")
    return "charge_logical_failure" if record.charge_recovery.logical_error else "decoded_success"


def _check_finite_weights(record) -> None:
    if record.flux_recovery is not None and not math.isfinite(record.flux_recovery.objective_weight):
        raise RuntimeError("nonfinite flux objective")
    if record.charge_recovery is not None:
        for result in (record.charge_recovery.blue, record.charge_recovery.green):
            if not math.isfinite(result.objective_weight):
                raise RuntimeError("nonfinite charge objective")


def trajectory_row(
    *,
    size: int,
    error_rate: float,
    index: int,
    salt: int,
) -> dict:
    lattice = paper_periodic_honeycomb(size)
    physical_key, first_key, second_key = trajectory_keys(salt, size, error_rate, index)
    physical = (
        np.random.default_rng(physical_key).random(lattice.edge_count) < error_rate
    ).astype(np.uint8)
    records = {
        "O0": decode_physical_error_with_keys(
            lattice,
            physical,
            mode="syndrome_only",
            provenance_seed=physical_key,
            first_observation_seed=first_key,
            second_exogenous_seed=second_key,
        ),
        "O2": decode_physical_error_with_keys(
            lattice,
            physical,
            mode="heralded",
            provenance_seed=physical_key,
            first_observation_seed=first_key,
            second_exogenous_seed=second_key,
        ),
    }
    if records["O0"].physical_error_edges != records["O2"].physical_error_edges:
        raise RuntimeError("paired arms received different physical errors")
    if records["O0"].observation != records["O2"].observation:
        raise RuntimeError("paired arms received different first observations")
    first_charge = records["O0"].observation.charge_outcomes
    if first_charge is not None and not set(first_charge) <= {0, 1}:
        raise RuntimeError("first public record is not signal-only binary")
    forbidden = (
        "physical_error",
        "postflux_relations",
        "active_vertices",
        "effective_error",
        "logical_error",
    )
    arms = {}
    for label, record in records.items():
        _check_finite_weights(record)
        transcript = record.public_transcript()
        transcript_text = json.dumps(transcript, sort_keys=True)
        if any(field in transcript_text for field in forbidden):
            raise RuntimeError("public transcript contains private truth")
        second = transcript["second_charge_record"]
        if second is not None and not set(second) <= {0, 1}:
            raise RuntimeError("second public record is not full binary")
        stage = _stage(record)
        expected_loss = stage != "decoded_success"
        if bool(record.logical_error) != expected_loss:
            raise RuntimeError("final Boolean-union loss disagrees with stage decomposition")
        arms[label] = {
            "status": record.status,
            "stage": stage,
            "logical_error": bool(record.logical_error),
            "public_transcript": transcript,
        }
    return {
        "size": int(size),
        "p_X": float(error_rate),
        "trajectory_index": int(index),
        "keys": {
            "physical": physical_key,
            "first_observation": first_key,
            "second_exogenous": second_key,
        },
        "physical_error_edges": [int(edge) for edge in np.flatnonzero(physical)],
        "arms": arms,
    }


def structural_gates() -> dict:
    zero = trajectory_row(size=3, error_rate=0.0, index=0, salt=68615)
    return {
        "zero_fixture_both_arms_decode": all(
            arm["stage"] == "decoded_success" for arm in zero["arms"].values()
        ),
        "zero_fixture_public_records_binary": all(
            set(arm["public_transcript"]["second_charge_record"]) <= {0, 1}
            for arm in zero["arms"].values()
        ),
        "explicit_keys_distinct": len(set(zero["keys"].values())) == 3,
    }


def _checkpoint_payload(manifest_name: str, rows: list[dict], started_at: str) -> dict:
    return {
        "schema_version": 1,
        "status": "in_progress",
        "manifest": manifest_name,
        "started_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_independent_histories": len(rows),
        "rows": rows,
    }


def _require_source_freeze(manifest: dict) -> dict:
    freeze = manifest.get("pilot_source_freeze")
    if not isinstance(freeze, dict) or not freeze:
        raise RuntimeError("pilot_source_freeze is missing")
    actual = {}
    for relative, expected in freeze.items():
        path = LAB_DIR / relative
        actual[relative] = _sha256(path)
        if actual[relative] != expected:
            raise RuntimeError(f"source freeze mismatch: {relative}")
    return actual


def execute(manifest: dict, checkpoint: Path, manifest_name: str) -> dict:
    pilot = manifest["pilot_registration"]
    grid = pilot["grid"]
    budget = pilot["compute_budget"]
    if manifest.get("status") != "pilot_registered_execution_pending":
        raise RuntimeError("R6AF manifest is not in a runnable pilot state")
    if budget.get("pilot_execution_authorized") is not True:
        raise RuntimeError("pilot execution is not authorized")
    preflight = json.loads(DEFAULT_PREFLIGHT.read_text(encoding="utf-8"))
    if (
        preflight.get("status") != "passed"
        or preflight.get("failed_gates") != []
        or preflight.get("pilot_registration_authorized") is not True
    ):
        raise RuntimeError("R6AF public-interface preflight is not passed")
    source_hashes = _require_source_freeze(manifest)
    gates = structural_gates()
    if not all(gates.values()):
        raise RuntimeError(f"structural gate failed: {gates}")
    expected_histories = int(grid["total_independent_histories"])
    per_cell = int(grid["matched_attempted_histories_per_cell"])
    if expected_histories != len(grid["sizes"]) * len(grid["p_X"]) * per_cell:
        raise RuntimeError("registered history total does not match grid")

    started_at = datetime.now(timezone.utc).isoformat()
    start_wall = time.perf_counter()
    rows: list[dict] = []
    if checkpoint.is_file():
        prior = json.loads(checkpoint.read_text(encoding="utf-8"))
        if prior.get("manifest") != manifest_name:
            raise RuntimeError("checkpoint manifest mismatch")
        rows = list(prior.get("rows", []))
        started_at = prior.get("started_at", started_at)
    by_cell = Counter((int(row["size"]), float(row["p_X"])) for row in rows)
    for size in grid["sizes"]:
        for error_rate in grid["p_X"]:
            key = (int(size), float(error_rate))
            existing = int(by_cell[key])
            indices = sorted(
                int(row["trajectory_index"])
                for row in rows
                if (int(row["size"]), float(row["p_X"])) == key
            )
            if indices != list(range(existing)) or existing > per_cell:
                raise RuntimeError(f"invalid checkpoint cell {key}")
            for index in range(existing, per_cell):
                rows.append(
                    trajectory_row(
                        size=int(size),
                        error_rate=float(error_rate),
                        index=index,
                        salt=int(pilot["seed_contract"]["master_salt"]),
                    )
                )
                if (index + 1) % int(budget["checkpoint_every_histories"]) == 0:
                    _atomic_json(
                        checkpoint,
                        _checkpoint_payload(manifest_name, rows, started_at),
                    )
                    print(
                        json.dumps(
                            {
                                "size": size,
                                "p_X": error_rate,
                                "completed_in_cell": index + 1,
                                "total_completed": len(rows),
                            },
                            sort_keys=True,
                        ),
                        flush=True,
                    )
                if time.perf_counter() - start_wall > 60 * float(
                    budget["maximum_wall_time_minutes"]
                ):
                    _atomic_json(
                        checkpoint,
                        _checkpoint_payload(manifest_name, rows, started_at),
                    )
                    raise RuntimeError("registered wall-time budget exceeded")

    replay_checks = []
    for size in grid["sizes"]:
        for error_rate in grid["p_X"]:
            cell_rows = [
                row
                for row in rows
                if int(row["size"]) == int(size)
                and float(row["p_X"]) == float(error_rate)
            ]
            for index in (0, per_cell // 2, per_cell - 1):
                replay = trajectory_row(
                    size=int(size),
                    error_rate=float(error_rate),
                    index=index,
                    salt=int(pilot["seed_contract"]["master_salt"]),
                )
                passed = replay == cell_rows[index]
                replay_checks.append(
                    {"size": size, "p_X": error_rate, "index": index, "passed": passed}
                )
                if not passed:
                    raise RuntimeError("deterministic replay mismatch")
    return {
        "schema_version": 1,
        "status": "completed_registered_pilot",
        "manifest": manifest_name,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": time.perf_counter() - start_wall,
        "source_sha256": source_hashes,
        "structural_gates": gates,
        "replay_checks": replay_checks,
        "completed_independent_histories": len(rows),
        "completed_arm_evaluations": 2 * len(rows),
        "rows": rows,
        "claim_boundary": "Registered complete two-stage paired pilot only; no threshold, crossing, scaling, fault-tolerance, BP, or Lab 003 comparison claim.",
    }


def analyze(raw: dict, manifest: dict) -> dict:
    pilot = manifest["pilot_registration"]
    grid = pilot["grid"]
    cells = []
    for size in grid["sizes"]:
        for error_rate in grid["p_X"]:
            rows = [
                row
                for row in raw["rows"]
                if int(row["size"]) == int(size)
                and float(row["p_X"]) == float(error_rate)
            ]
            o0 = np.asarray([row["arms"]["O0"]["logical_error"] for row in rows], dtype=np.int8)
            o2 = np.asarray([row["arms"]["O2"]["logical_error"] for row in rows], dtype=np.int8)
            differences = o2 - o0
            interval = paired_bootstrap_interval(
                differences,
                size=int(size),
                error_rate=float(error_rate),
                salt=68616,
                replicates=10000,
            )
            direction = (
                "resolved_improvement"
                if interval[1] < 0
                else "resolved_regression"
                if interval[0] > 0
                else "unresolved"
            )
            o0_only = int(np.sum((o0 == 1) & (o2 == 0)))
            o2_only = int(np.sum((o0 == 0) & (o2 == 1)))
            cells.append(
                {
                    "size": int(size),
                    "p_X": float(error_rate),
                    "attempted_histories": len(rows),
                    "arms": {
                        "O0": {
                            "logical_losses": int(np.sum(o0)),
                            "risk": float(np.mean(o0)),
                            "wilson_90": wilson_interval(int(np.sum(o0)), len(rows)),
                            "stage_counts": dict(
                                sorted(Counter(row["arms"]["O0"]["stage"] for row in rows).items())
                            ),
                        },
                        "O2": {
                            "logical_losses": int(np.sum(o2)),
                            "risk": float(np.mean(o2)),
                            "wilson_90": wilson_interval(int(np.sum(o2)), len(rows)),
                            "stage_counts": dict(
                                sorted(Counter(row["arms"]["O2"]["stage"] for row in rows).items())
                            ),
                        },
                    },
                    "paired": {
                        "delta_O2_minus_O0": float(np.mean(differences)),
                        "bootstrap_90": interval,
                        "direction": direction,
                        "O0_only_losses": o0_only,
                        "O2_only_losses": o2_only,
                        "discordant_pairs": o0_only + o2_only,
                        "exact_mcnemar_p_two_sided": exact_discordance_p_value(o0_only, o2_only),
                    },
                }
            )
    return {
        "schema_version": 1,
        "status": "analyzed_registered_pilot",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": raw["manifest"],
        "raw_status": raw["status"],
        "integrity": {
            "completed_independent_histories": raw["completed_independent_histories"],
            "completed_arm_evaluations": raw["completed_arm_evaluations"],
            "all_structural_gates_passed": all(raw["structural_gates"].values()),
            "all_replays_passed": all(item["passed"] for item in raw["replay_checks"]),
        },
        "cells": cells,
        "resolved_improvement_cells": sum(
            cell["paired"]["direction"] == "resolved_improvement" for cell in cells
        ),
        "resolved_regression_cells": sum(
            cell["paired"]["direction"] == "resolved_regression" for cell in cells
        ),
        "unresolved_cells": sum(
            cell["paired"]["direction"] == "unresolved" for cell in cells
        ),
        "claim_boundary": "Pointwise paired pilot directions only. No multiplicity-adjusted discovery, threshold, crossing, scaling, fault-tolerance, BP, or Lab 003 comparison claim.",
    }


def report_markdown(analysis: dict, raw: dict) -> str:
    lines = [
        "# R6AF complete two-stage O0/O2 pilot",
        "",
        f"Status: **{analysis['status']}**.",
        "",
        "## Paired results",
        "",
        "| L | p_X | O0 risk (90% Wilson) | O2 risk (90% Wilson) | Delta O2-O0 (90% paired bootstrap) | direction | discordance O0-only/O2-only |",
        "|---:|---:|---:|---:|---:|:---|:---|",
    ]
    for cell in analysis["cells"]:
        o0 = cell["arms"]["O0"]
        o2 = cell["arms"]["O2"]
        pair = cell["paired"]
        lines.append(
            f"| {cell['size']} | {cell['p_X']:.2f} | {o0['risk']:.4f} "
            f"[{o0['wilson_90'][0]:.4f}, {o0['wilson_90'][1]:.4f}] | "
            f"{o2['risk']:.4f} [{o2['wilson_90'][0]:.4f}, {o2['wilson_90'][1]:.4f}] | "
            f"{pair['delta_O2_minus_O0']:+.4f} [{pair['bootstrap_90'][0]:+.4f}, "
            f"{pair['bootstrap_90'][1]:+.4f}] | {pair['direction']} | "
            f"{pair['O0_only_losses']}/{pair['O2_only_losses']} |"
        )
    lines.extend(
        [
            "",
            "## Integrity",
            "",
            f"All {raw['completed_independent_histories']:,} independent matched histories and "
            f"{raw['completed_arm_evaluations']:,} arm evaluations completed in "
            f"{raw['wall_seconds']:.2f} s. All structural gates and all 12 registered "
            "first/middle/final replay checks passed.",
            "",
            "## Claim boundary",
            "",
            analysis["claim_boundary"],
            "The registered 512-history/cell stop is final for this pilot; unresolved cells are not adaptively extended.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--raw-output", type=Path)
    parser.add_argument("--analysis-output", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    outputs = manifest["pilot_registration"]["outputs"]
    checkpoint = args.checkpoint or LAB_DIR / outputs["checkpoint"]
    raw_output = args.raw_output or LAB_DIR / outputs["raw_result"]
    analysis_output = args.analysis_output or LAB_DIR / outputs["analysis"]
    report_output = args.report_output or LAB_DIR / outputs["report"]
    raw = execute(manifest, checkpoint, args.manifest.name)
    _atomic_json(raw_output, raw)
    analysis = analyze(raw, manifest)
    _atomic_json(analysis_output, analysis)
    report_output.write_text(report_markdown(analysis, raw), encoding="utf-8")
    _atomic_json(
        checkpoint,
        {
            "schema_version": 1,
            "status": "completed",
            "manifest": args.manifest.name,
            "completed_independent_histories": raw["completed_independent_histories"],
            "raw_output": str(raw_output.relative_to(LAB_DIR)),
            "analysis_output": str(analysis_output.relative_to(LAB_DIR)),
        },
    )
    print(
        json.dumps(
            {
                "raw_output": str(raw_output),
                "analysis_output": str(analysis_output),
                "report_output": str(report_output),
                "histories": raw["completed_independent_histories"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
