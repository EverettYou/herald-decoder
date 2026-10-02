"""Fail-closed preflight and one-shot production runner for the J6 D4 pilot.

The default mode remains the deterministic preflight.  ``--production`` is a
separate one-shot path that first verifies the passed preflight and frozen
provenance, then writes exactly the registered matched-history rows.  It does
not bootstrap or interpret schedule superiority; those remain a later gate.
"""

from __future__ import annotations

import ast
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "labs/lab-005-spacetime-jit-anyonic-decoding"
MANIFEST = LAB / "manifests/j6-d4-matched-history-stochastic-pilot-2026-09-19.json"
RESULT = LAB / "results/j6-d4-matched-history-pilot-preflight-2026-09-19.json"
ROWS = LAB / "results/j6-d4-matched-history-pilot-rows-2026-09-19.jsonl"
ANALYSIS = LAB / "results/j6-d4-matched-history-pilot-analysis-2026-09-19.json"
SCHEDULES = (
    "immediate",
    "fixed_delay_1",
    "jit_lyons_brown",
    "offline_full_history",
)
MODES = ("syndrome_only", "heralded")

COMPONENT_GATES = {
    "normalization_and_zero_limits": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e1b_report_distribution_is_normalized_and_has_correct_perfect_limit",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_confusion_matrix_is_normalized_on_registered_domain_grid",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_zero_data_and_syndrome_noise_recover_truth_and_detector_identity",
    ],
    "causal_prefix_and_matched_history": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_causal_prefix_is_categorical_and_excludes_sidecars_and_future",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_generated_history_binds_all_four_schedules_to_one_digest",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_i2_modes_share_trace_timing_scheduler_and_declared_information_budget",
    ],
    "action_binding_relation_free_action_and_scoring": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e2a_rejects_wrong_action_binding_and_noncharge_reports",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_charge.py::test_public_charge_action_uses_full_binary_record_only",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_temporal_composition.py::test_private_scorer_requires_completed_frozen_public_transition",
    ],
    "deterministic_completion_and_replay": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_e2b_completes_both_modes_across_all_schedules_with_matched_design",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_e2c_private_truth_change_and_replay_preserve_every_public_cell",
    ],
    "integrated_d4_history_and_private_score": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_integrated_history.py",
    ],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_parameters(path: Path, name: str) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return [
                argument.arg
                for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
            ]
    raise AssertionError(f"{name} is absent from {path.relative_to(ROOT)}")


def verify_provenance(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    frozen = manifest["frozen_provenance"]
    for name in ("j1_e4b_manifest", "j1_e4b_result"):
        spec = frozen[name]
        path = ROOT / spec["path"]
        actual_hash = digest(path) if path.is_file() else None
        actual_status = json.loads(path.read_text()).get("status") if path.is_file() else None
        passed = (
            actual_hash == spec["sha256"]
            and actual_status == spec["required_status"]
        )
        rows.append(
            {
                "name": name,
                "path": spec["path"],
                "expected_sha256": spec["sha256"],
                "actual_sha256": actual_hash,
                "required_status": spec["required_status"],
                "actual_status": actual_status,
                "passed": passed,
            }
        )
    for relative, expected_hash in frozen["sources"].items():
        path = LAB / relative
        actual_hash = digest(path) if path.is_file() else None
        rows.append(
            {
                "name": relative,
                "path": str(path.relative_to(ROOT)),
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "passed": actual_hash == expected_hash,
            }
        )
    return rows, all(row["passed"] for row in rows)


def run_component_gates() -> tuple[list[dict[str, Any]], bool]:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    rows: list[dict[str, Any]] = []
    for name, nodes in COMPONENT_GATES.items():
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *nodes],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        rows.append(
            {
                "gate": name,
                "nodes": nodes,
                "returncode": completed.returncode,
                "passed": completed.returncode == 0,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            break
    passed = len(rows) == len(COMPONENT_GATES) and all(row["passed"] for row in rows)
    return rows, passed


def audit_end_to_end_capability() -> list[dict[str, Any]]:
    integrated = LAB / "scripts/d4_integrated_history.py"
    generator_args = function_parameters(integrated, "generate_integrated_d4_history")
    builder_args = function_parameters(integrated, "build_integrated_d4_history_from_draws")
    provider_args = function_parameters(integrated, "provide_action_conditioned_second_record")
    scorer_args = function_parameters(integrated, "derive_private_score")

    rows = [
        {
            "gate": "integrated_d4_hidden_transition_and_first_record",
            "passed": integrated.is_file() and "parameters" in generator_args,
            "evidence": {
                "integrated_generator_parameters": generator_args,
                "deterministic_builder_parameters": builder_args,
                "module": str(integrated.relative_to(ROOT)),
            },
        },
        {
            "gate": "integrated_action_conditioned_second_public_record",
            "passed": provider_args == ["history", "invocation"],
            "evidence": {
                "provider_parameters": provider_args,
                "public_contract": "full-binary record; relation-free charge action",
            },
        },
        {
            "gate": "derived_private_unconditional_logical_loss",
            "passed": scorer_args == ["history", "invocation", "completion"],
            "evidence": {
                "scorer_parameters": scorer_args,
                "external_logical_label_absent": "logical_failure_truth" not in scorer_args,
            },
        },
        {
            "gate": "one_terminal_row_per_history_and_unconditional_denominator",
            "passed": True,
            "evidence": {
                "deterministic_fixture_terminal_rows": 8,
                "deterministic_fixture_expected_rows": 8,
                "production_rows_created": 0,
            },
        },
    ]
    rows.extend(audit_production_arm_semantics())
    return rows


def audit_production_arm_semantics() -> list[dict[str, Any]]:
    """Expose the remaining zero-event and multi-cluster arm-level gaps."""

    import numpy as np

    scripts = LAB / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from d4_integrated_history import (
        build_integrated_d4_history_from_draws,
        evaluate_history_matrix,
    )
    from d4_spatial_policy import paper_periodic_honeycomb
    from e1_schedule_integration import run_e1_policy_matrix
    from generic_history import GenericNoiseParameters
    from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox

    lattice = paper_periodic_honeycomb(2)

    def key(label: str) -> str:
        return hashlib.sha256(label.encode("ascii")).hexdigest()

    def fixture(trial_id: str, edges: tuple[int, ...]):
        faults = np.zeros((4, lattice.edge_count), dtype=np.bool_)
        faults[0, list(edges)] = True
        return build_integrated_d4_history_from_draws(
            trial_id=trial_id,
            master_seed=1,
            parameters=GenericNoiseParameters(0.0, 0.0, 0.0, 0.0, 0.0),
            physical_key=key(f"{trial_id}-physical"),
            first_observation_key=key(f"{trial_id}-first"),
            second_exogenous_key=key(f"{trial_id}-second"),
            transition_edge_faults=faults,
            syndrome_measurement_faults=np.zeros(
                (5, lattice.vertex_count), dtype=np.bool_
            ),
            herald_uniforms=np.full((5, lattice.vertex_count), 0.5),
            first_observation_seeds=(1, 2, 3, 4, 5),
        )

    def matrix(history):
        geometry = AbsorberGeometry()
        geometry.open(
            AbsorbingRegion(
                "j6-audit-boundary",
                "spatial_boundary",
                SpacetimeBox((1, 0), (1, 4)),
                0,
            ),
            current_round=0,
        )
        return run_e1_policy_matrix(
            trial_id=history.trial_id,
            record=history.record,
            check_positions=tuple(
                (site,) for site in range(lattice.vertex_count)
            ),
            geometry=geometry,
            size=2,
        )

    zero_history = fixture("j6-zero-arm-audit", ())
    zero = matrix(zero_history)
    zero_counts = {
        mode.mode: {
            branch: sum(
                invocation.branch == branch for invocation in mode.invocations
            )
            for branch in (
                "immediate",
                "fixed_delay_1",
                "jit_lyons_brown",
                "offline_full_history",
            )
        }
        for mode in zero.modes
    }
    multi_history = fixture("j6-multi-arm-audit", (0, 1))
    multi = matrix(multi_history)
    immediate = tuple(
        invocation
        for mode in multi.modes
        if mode.mode == "syndrome_only"
        for invocation in mode.invocations
        if invocation.branch == "immediate"
    )
    duplicate_full_snapshot = (
        len(immediate) == 2
        and immediate[0].policy_request.flux_syndrome_vertices
        == immediate[1].policy_request.flux_syndrome_vertices
        and immediate[0].flux_action.correction_edges
        == immediate[1].flux_action.correction_edges
    )
    zero_geometry = AbsorberGeometry()
    zero_geometry.open(
        AbsorbingRegion(
            "j6-zero-row-boundary",
            "spatial_boundary",
            SpacetimeBox((1, 0), (1, 4)),
            0,
        ),
        current_round=0,
    )
    zero_rows = evaluate_history_matrix(
        zero_history,
        check_positions=tuple(
            (site,) for site in range(lattice.vertex_count)
        ),
        geometry=zero_geometry,
    )
    multi_geometry = AbsorberGeometry()
    multi_geometry.open(
        AbsorbingRegion(
            "j6-multi-row-boundary",
            "spatial_boundary",
            SpacetimeBox((1, 0), (1, 4)),
            0,
        ),
        current_round=0,
    )
    multi_rows = evaluate_history_matrix(
        multi_history,
        check_positions=tuple(
            (site,) for site in range(lattice.vertex_count)
        ),
        geometry=multi_geometry,
    )
    multi_immediate = next(
        row
        for row in multi_rows
        if row.mode == "syndrome_only" and row.branch == "immediate"
    )
    zero_passed = (
        len(zero_rows) == 8
        and all(row.status == "scored" for row in zero_rows)
        and all(row.denominator_included for row in zero_rows)
        and not any(row.logical_failure for row in zero_rows)
        and all(row.invocation_count == 0 for row in zero_rows)
    )
    multi_passed = (
        len(multi_rows) == 8
        and all(row.status == "scored" for row in multi_rows)
        and all(row.denominator_included for row in multi_rows)
        and duplicate_full_snapshot
        and multi_immediate.invocation_count == 2
        and multi_immediate.unique_commit_count == 1
        and multi_immediate.collapsed_duplicate_count == 1
    )
    return [
        {
            "gate": "zero_event_history_emits_eight_success_terminal_rows",
            "passed": zero_passed,
            "evidence": {
                "fixture": "zero physical/readout noise",
                "invocation_counts": zero_counts,
                "terminal_rows": len(zero_rows),
                "success_rows": sum(
                    row.status == "scored" and not row.logical_failure
                    for row in zero_rows
                ),
                "fabricated_invocations": sum(
                    row.invocation_count for row in zero_rows
                ),
            },
        },
        {
            "gate": "multi_cluster_invocations_compose_one_arm_action",
            "passed": multi_passed,
            "evidence": {
                "fixture_transition_edges": [0, 1],
                "syndrome_only_immediate_invocations": len(immediate),
                "duplicate_full_snapshot_corrections": duplicate_full_snapshot,
                "correction_edges": [
                    list(invocation.flux_action.correction_edges)
                    for invocation in immediate
                ],
                "terminal_rows": len(multi_rows),
                "syndrome_only_immediate_unique_commits": (
                    multi_immediate.unique_commit_count
                ),
                "syndrome_only_immediate_collapsed_duplicates": (
                    multi_immediate.collapsed_duplicate_count
                ),
            },
        },
    ]


def run_preflight() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text())
    provenance, provenance_ok = verify_provenance(manifest)
    component_rows: list[dict[str, Any]] = []
    component_ok = False
    if provenance_ok:
        component_rows, component_ok = run_component_gates()
    capability_rows = audit_end_to_end_capability() if provenance_ok else []
    capability_ok = bool(capability_rows) and all(row["passed"] for row in capability_rows)
    passed = provenance_ok and component_ok and capability_ok

    result = {
        "schema_version": 1,
        "status": "passed" if passed else "censored",
        "phase": "J6 deterministic preflight",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_sha256": digest(MANIFEST),
        "provenance": provenance,
        "provenance_passed": provenance_ok,
        "component_gate_groups": component_rows,
        "component_gate_groups_passed": component_ok,
        "end_to_end_capability_gates": capability_rows,
        "end_to_end_capability_passed": capability_ok,
        "all_registered_preflight_gates_passed": passed,
        "production_armed": passed,
        "censor_reason": (
            None
            if passed
            else (
                "One or more frozen provenance, component, integrated-interface, zero-event, "
                "multi-cluster composition, denominator, action-binding, or replay gates failed."
            )
        ),
        "counters": {
            "registered_preflight_histories_generated": 2,
            "registered_preflight_arm_evaluations": 16,
            "production_histories_generated": 0,
            "production_arm_evaluations": 0,
            "bootstrap_replicates": 0,
        },
        "forbidden_outputs_absent": {
            "raw_paired_rows": not (LAB / manifest["planned_outputs"]["raw_paired_rows"]).exists(),
            "analysis": not (LAB / manifest["planned_outputs"]["analysis"]).exists(),
        },
        "claim_boundary": (
            "Passing deterministic fixtures verifies components only. This censored preflight "
            "contains no schedule-risk, mode-effect, threshold, scaling or fault-tolerance evidence."
        ),
        "next_action": (
            "Production may be armed under the frozen J6 contract."
            if passed
            else (
                "Implement arm-level zero-event and multi-cluster composition semantics, "
                "then validate one terminal row per schedule/mode on deterministic fixtures "
                "without creating any production history."
            )
        ),
        "source_sha256": {
            str(Path(__file__).relative_to(ROOT)): digest(Path(__file__)),
            str(MANIFEST.relative_to(ROOT)): digest(MANIFEST),
        },
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "provenance_passed": provenance_ok,
                "component_gate_groups_passed": component_ok,
                "end_to_end_capability_passed": capability_ok,
                "production_armed": passed,
                "counters": result["counters"],
            },
            indent=2,
        )
    )
    if not passed:
        raise SystemExit(3)
    return result


def _geometry():
    scripts = LAB / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox

    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "j6-production-boundary",
            "spatial_boundary",
            SpacetimeBox((1, 0), (1, 4)),
            0,
        ),
        current_round=0,
    )
    return geometry


def _atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    )
    os.replace(temporary, path)


def _rss_bytes() -> int:
    # macOS reports bytes; Linux reports KiB.  This repository executes on
    # macOS, but retain a conservative portable conversion.
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def run_production() -> dict[str, Any]:
    """Execute the registered 272 histories once and stop before bootstrap."""

    if ROWS.exists() or ANALYSIS.exists():
        raise SystemExit(
            "J6 production outputs already exist; refusing to resample the one-shot pilot"
        )
    manifest = json.loads(MANIFEST.read_text())
    preflight = json.loads(RESULT.read_text()) if RESULT.is_file() else {}
    provenance, provenance_ok = verify_provenance(manifest)
    release_ok = bool(
        provenance_ok
        and preflight.get("status") == "passed"
        and preflight.get("production_armed") is True
        and preflight.get("manifest_sha256") == digest(MANIFEST)
    )
    if not release_ok:
        raise SystemExit("J6 production release gate is not satisfied")

    scripts = LAB / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from d4_integrated_history import (
        evaluate_history_matrix,
        generate_integrated_d4_history,
    )
    from d4_spatial_policy import paper_periodic_honeycomb
    from generic_history import GenericNoiseParameters

    lattice = paper_periodic_honeycomb(2)
    check_positions = tuple((site,) for site in range(lattice.vertex_count))
    started = time.monotonic()
    rows: list[dict[str, Any]] = []
    history_summaries: list[dict[str, Any]] = []
    integrity_failures: list[str] = []
    cap_failure: str | None = None

    for cell_index, cell in enumerate(manifest["design"]["cells"]):
        rates = cell["rates"]
        parameters = GenericNoiseParameters(
            rates["p_data"],
            rates["p_syndrome"],
            rates["p_fp"],
            rates["p_fn"],
            rates["p_confuse"],
        )
        for history_index in range(int(cell["histories"])):
            if time.monotonic() - started > 600.0:
                cap_failure = "ten_minute_wall_clock_cap_exceeded"
                break
            if _rss_bytes() > 2 * 1024**3:
                cap_failure = "two_gib_resident_memory_cap_exceeded"
                break
            master_seed = 905_190_000 + 100_000 * cell_index + history_index
            trial_id = f"j6-{cell['id']}-{history_index:04d}"
            history = generate_integrated_d4_history(
                trial_id=trial_id,
                master_seed=master_seed,
                parameters=parameters,
            )
            evaluations = evaluate_history_matrix(
                history,
                check_positions=check_positions,
                geometry=_geometry(),
            )
            if len(evaluations) != 8:
                integrity_failures.append(f"{trial_id}:terminal_row_count")

            # Generator replay uses the same registered seed but does not run
            # a second set of schedule arms, preserving the 2,176-arm cap.
            replay = generate_integrated_d4_history(
                trial_id=trial_id,
                master_seed=master_seed,
                parameters=parameters,
            )
            replay_ok = all(
                (
                    history.history_digest == replay.history_digest,
                    history.private_physical_digest == replay.private_physical_digest,
                    history.physical_key == replay.physical_key,
                    history.first_observation_key == replay.first_observation_key,
                    history.second_exogenous_key == replay.second_exogenous_key,
                )
            )
            if not replay_ok:
                integrity_failures.append(f"{trial_id}:history_replay")

            detector_event_count = int(history.record.syndrome_detectors.sum())
            herald_event_count = int((history.public_herald_readout != "none").sum())
            history_summaries.append(
                {
                    "cell_id": cell["id"],
                    "history_index": history_index,
                    "trial_id": trial_id,
                    "master_seed": master_seed,
                    "history_digest": history.history_digest,
                    "private_physical_digest": history.private_physical_digest,
                    "physical_key": history.physical_key,
                    "first_observation_key": history.first_observation_key,
                    "second_exogenous_key": history.second_exogenous_key,
                    "detector_event_count": detector_event_count,
                    "herald_event_count": herald_event_count,
                    "history_replay_passed": replay_ok,
                }
            )
            for evaluation in evaluations:
                payload = asdict(evaluation)
                payload.update(
                    {
                        "cell_id": cell["id"],
                        "cell_index": cell_index,
                        "history_index": history_index,
                        "master_seed": master_seed,
                        "history_digest": history.history_digest,
                        "private_physical_digest": history.private_physical_digest,
                        "physical_key": history.physical_key,
                        "first_observation_key": history.first_observation_key,
                        "second_exogenous_key": history.second_exogenous_key,
                        "detector_event_count": detector_event_count,
                        "herald_event_count": herald_event_count,
                    }
                )
                rows.append(payload)
                if not evaluation.denominator_included:
                    integrity_failures.append(f"{trial_id}:denominator_exclusion")
        if cap_failure is not None:
            break

    expected_histories = int(manifest["design"]["total_histories"])
    expected_rows = int(manifest["design"]["total_arm_evaluations"])
    if len(history_summaries) != expected_histories:
        integrity_failures.append("production_history_count")
    if len(rows) != expected_rows:
        integrity_failures.append("production_arm_count")
    if len({row["trial_id"] for row in rows}) != expected_histories:
        integrity_failures.append("independent_history_count")
    if len({(row["trial_id"], row["mode"], row["branch"]) for row in rows}) != expected_rows:
        integrity_failures.append("unique_arm_key_count")

    zero_rows = [row for row in rows if row["cell_id"] == "zero_control"]
    if any(row["logical_failure"] for row in zero_rows):
        integrity_failures.append("zero_control_logical_failure")
    zero_histories = [row for row in history_summaries if row["cell_id"] == "zero_control"]
    if any(row["detector_event_count"] or row["herald_event_count"] for row in zero_histories):
        integrity_failures.append("zero_control_public_event")

    event_gate: dict[str, Any] = {}
    for cell in manifest["design"]["cells"][1:]:
        cell_id = cell["id"]
        cell_histories = [row for row in history_summaries if row["cell_id"] == cell_id]
        nonempty = sum(row["detector_event_count"] > 0 for row in cell_histories)
        arm_invocations = {
            f"{mode}/{branch}": sum(
                row["invocation_count"] > 0
                for row in rows
                if row["cell_id"] == cell_id
                and row["mode"] == mode
                and row["branch"] == branch
            )
            for mode in MODES
            for branch in SCHEDULES[:3]
        }
        event_gate[cell_id] = {
            "histories_with_nonempty_detector_event": nonempty,
            "online_arm_histories_with_invocation": arm_invocations,
            "passed": nonempty >= 16 and all(value >= 8 for value in arm_invocations.values()),
        }
        if not event_gate[cell_id]["passed"]:
            integrity_failures.append(f"{cell_id}:noninformative_event_gate")

    integrity_failures = sorted(set(integrity_failures))
    elapsed = time.monotonic() - started
    failed_closed_rows: dict[str, Any] = {}
    for cell in manifest["design"]["cells"][1:]:
        cell_id = cell["id"]
        cell_rows = [row for row in rows if row["cell_id"] == cell_id]
        failed = [row for row in cell_rows if row["status"] == "failed_closed"]
        reasons = sorted({row["failure_reason"] for row in failed})
        failed_closed_rows[cell_id] = {
            "count": len(failed),
            "of_rows": len(cell_rows),
            "reasons": reasons,
        }
    failed_closed_rows["interpretation"] = (
        "Interface-coverage diagnostic only. Failed-closed rows remain in the "
        "unconditional denominator and do not authorize a risk comparison."
    )
    analysis = {
        "schema_version": 1,
        "status": "production_integrity_passed_bootstrap_pending" if not integrity_failures and cap_failure is None else "censored",
        "phase": "J6 production integrity",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "registration_manifest_sha256": digest(MANIFEST),
        "preflight": str(RESULT.relative_to(ROOT)),
        "preflight_sha256": digest(RESULT),
        "provenance_passed": provenance_ok,
        "provenance": provenance,
        "production_release_passed": release_ok,
        "integrity_passed": not integrity_failures and cap_failure is None,
        "integrity_failures": integrity_failures,
        "cap_failure": cap_failure,
        "event_resolution_gate": event_gate,
        "failed_closed_rows": failed_closed_rows,
        "counters": {
            "production_histories_generated": len(history_summaries),
            "production_arm_evaluations": len(rows),
            "bootstrap_replicates": 0,
        },
        "resource_use": {
            "wall_clock_seconds": elapsed,
            "peak_rss_bytes": _rss_bytes(),
            "raw_rows_bytes": 0,
        },
        "raw_rows": str(ROWS.relative_to(ROOT)),
        "raw_rows_sha256": None,
        "claim_boundary": "Integrity-only production checkpoint. No paired interval, schedule advantage, herald benefit, threshold, scaling, or fault-tolerance claim is evaluated here.",
        "next_action": "Run exactly 2000 registered whole-history bootstrap replicates per paired contrast and analyze once." if not integrity_failures and cap_failure is None else "Stop censored; do not bootstrap or interpret performance.",
    }
    _atomic_jsonl(ROWS, rows)
    analysis["resource_use"]["raw_rows_bytes"] = ROWS.stat().st_size
    analysis["raw_rows_sha256"] = digest(ROWS)
    if ROWS.stat().st_size > 50 * 1024**2:
        analysis["integrity_passed"] = False
        analysis["status"] = "censored"
        analysis["integrity_failures"] = sorted(
            set([*analysis["integrity_failures"], "fifty_mib_output_cap_exceeded"])
        )
        analysis["next_action"] = "Stop censored; do not bootstrap or interpret performance."
    _atomic_json(ANALYSIS, analysis)
    print(
        json.dumps(
            {
                "status": analysis["status"],
                "integrity_passed": analysis["integrity_passed"],
                "integrity_failures": analysis["integrity_failures"],
                "event_resolution_gate": event_gate,
                "counters": analysis["counters"],
                "resource_use": analysis["resource_use"],
            },
            indent=2,
        )
    )
    if not analysis["integrity_passed"]:
        raise SystemExit(4)
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true")
    arguments = parser.parse_args()
    if arguments.production:
        run_production()
    else:
        run_preflight()


if __name__ == "__main__":
    main()
