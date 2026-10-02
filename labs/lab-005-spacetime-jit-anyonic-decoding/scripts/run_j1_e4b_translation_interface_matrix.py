"""Run the registered deterministic J1-E4B translation interface matrix."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "labs/lab-005-spacetime-jit-anyonic-decoding"
MANIFEST = LAB / "manifests/j1-e4b-d4-translation-interface-matrix-2026-09-19.json"
RESULT = LAB / "results/j1-e4b-d4-translation-interface-matrix-2026-09-19.json"

GATE_GROUPS = {
    "normalization_and_perfect_limits": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e1b_report_distribution_is_normalized_and_has_correct_perfect_limit",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_confusion_matrix_is_normalized_on_registered_domain_grid",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_zero_data_and_syndrome_noise_recover_truth_and_detector_identity",
    ],
    "action_binding_and_r6af_boundary": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e2a_rejects_wrong_action_binding_and_noncharge_reports",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_r6af_two_stage_public_charge.py::test_r6af_localizes_public_charge_interface_before_sampling",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_charge.py::test_private_scorer_rejects_record_bound_to_wrong_action_support",
    ],
    "full_binary_relation_free_public_action": [
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_charge.py::test_public_charge_action_uses_full_binary_record_only",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_r4_sequential.py::test_second_record_is_binary_and_internal_sentinel_is_not_observable",
    ],
    "causal_prefix_and_truth_separation": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_causal_prefix_is_categorical_and_excludes_sidecars_and_future",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_temporal_composition.py::test_public_state_has_deterministic_digest_and_no_truth_fields",
    ],
    "shared_history_four_schedule_binding": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_generic_history.py::test_generated_history_binds_all_four_schedules_to_one_digest",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_e2b_completes_both_modes_across_all_schedules_with_matched_design",
    ],
    "matched_mode_schedule_semantics": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_i2_modes_share_trace_timing_scheduler_and_declared_information_budget",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_i3_private_truth_change_preserves_every_public_request_and_action",
    ],
    "ground_state_relative_scoring": [
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_sampler.py::test_winding_observation_is_sector_agnostic_logical_failure",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_temporal_composition.py::test_private_scorer_requires_completed_frozen_public_transition",
    ],
    "deterministic_replay": [
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py::test_e2c_private_truth_change_and_replay_preserve_every_public_cell",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_r6af_two_stage_pilot.py::test_zero_and_small_history_gates_are_replayable",
    ],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    provenance = []
    provenance_ok = True
    for name, frozen in manifest["frozen_dependencies"].items():
        path = ROOT / frozen["path"]
        actual = digest(path)
        row = {
            "name": name,
            "path": frozen["path"],
            "expected_sha256": frozen["sha256"],
            "actual_sha256": actual,
            "passed": actual == frozen["sha256"],
        }
        if "required_status" in frozen:
            status = json.loads(path.read_text()).get("status")
            row["required_status"] = frozen["required_status"]
            row["actual_status"] = status
            row["passed"] = row["passed"] and status == frozen["required_status"]
        provenance_ok = provenance_ok and row["passed"]
        provenance.append(row)

    groups = []
    if provenance_ok:
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "0"
        for name, nodes in GATE_GROUPS.items():
            command = [sys.executable, "-m", "pytest", "-q", *nodes]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            groups.append(
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

    passed = provenance_ok and len(groups) == len(GATE_GROUPS) and all(
        row["passed"] for row in groups
    )
    source_paths = [Path(__file__), MANIFEST]
    out = {
        "status": "passed" if passed else "censored",
        "scope": manifest["scope"],
        "provenance": provenance,
        "gate_groups": groups,
        "gate_group_count": len(GATE_GROUPS),
        "gate_groups_executed": len(groups),
        "all_gates_passed": passed,
        "production_histories_generated": 0,
        "performance_evaluations": 0,
        "bootstrap_replicates": 0,
        "stochastic_pilot_authorized": passed,
        "stochastic_pilot_executed": False,
        "next_action": (
            "Register a tiny matched-history stochastic pilot under the translated D4 model."
            if passed
            else "Keep all stochastic history and schedule-performance work blocked."
        ),
        "source_sha256": {
            str(path.relative_to(ROOT)): digest(path) for path in source_paths
        },
    }
    RESULT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "groups": groups}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
