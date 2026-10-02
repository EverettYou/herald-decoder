"""Registered four-cell, deterministic feedback-interface counterfactual.

The correction-sensitive kernel is stipulated for an interface test. It is not
a D4 fusion law or a schedule-performance model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from d4_projector_instrument import (
    CHARGE,
    FLUX,
    VACUUM,
    project_hidden_state,
    project_post_action_charge_state,
)


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6c-action-feedback-counterfactual-2026-09-24.json"
RESULT = LAB / "results/j6c-action-feedback-counterfactual-2026-09-24.json"
LABELS = (VACUUM, FLUX, CHARGE)


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def action_from_causal_record(first_record: list[int], arm: str) -> str:
    """The fixed policy arm may use round 0 only; future and truth are absent."""
    require(first_record == [1, 1], "unexpected round-0 public record")
    require(arm in ("defer", "commit"), "unknown action arm")
    return arm


def bound_second_record(action: str, action_digest: str, hidden_label: str) -> dict:
    require(action == "commit", "E2 exists only after a commit")
    require(hidden_label in (VACUUM, CHARGE), "E2 must be charge/vacuum")
    projected = project_post_action_charge_state(
        trial_id="j6c-post-flux", round=0, charge_labels={0: hidden_label},
        bound_action_digest=action_digest,
    )
    require(projected.bound_action_digest == action_digest, "private E2 binding drift")
    return {
        "round": 0,
        "charge_vacuum_bits": [int(hidden_label == CHARGE), int(hidden_label == VACUUM)],
        "bound_action_digest": action_digest,
    }


def check_second_binding(second_record: dict, action_digest: str) -> None:
    require(second_record["bound_action_digest"] == action_digest,
            "second record is bound to a different public action")


def kernel(model: str, action: str, fixture: dict) -> dict[str, int]:
    require(not fixture["between_round_fault"], "registered zero-fault fixture changed")
    require(fixture["second_charge_outcome"] == VACUUM,
            "registered vacuum E2 outcome changed")
    next_label = FLUX
    if model == "action_feedback_fixture" and action == "commit":
        next_label = VACUUM
    require(model in ("no_feedback_null", "action_feedback_fixture"),
            "unregistered model")
    weights = {label: int(label == next_label) for label in LABELS}
    require(all(weight >= 0 for weight in weights.values()), "negative kernel weight")
    require(sum(weights.values()) == 1, "categorical kernel is not normalized")
    return weights


def run_cell(contract: dict, model: str, arm: str, *, perturb_future: bool = False) -> dict:
    scope = contract["fixed_scope"]
    fixture = scope["exogenous_fixture"]
    require(not fixture["first_report_fault"] and not fixture["second_report_fault"],
            "registered perfect-readout fixture changed")
    projection = scope["public_label_projection"]
    hidden0 = project_hidden_state(
        trial_id="j6c-fixed-exogenous", round=0, true_labels={0: FLUX},
    )
    first0 = list(projection[FLUX])
    action = action_from_causal_record(first0, arm)
    action_digest = digest({"round": 0, "action": action, "first_record": first0})

    second = None
    if action == "commit":
        second = bound_second_record(
            action, action_digest, fixture["second_charge_outcome"]
        )
        check_second_binding(second, action_digest)

    weights = kernel(model, action, fixture)
    next_label = next(label for label, probability in weights.items() if probability == 1)
    hidden1 = project_hidden_state(
        trial_id="j6c-fixed-exogenous", round=1, true_labels={0: next_label},
        previous=hidden0,
        bound_action_digest=action_digest if model == "action_feedback_fixture" else None,
    )
    first1 = list(projection[next_label])
    if perturb_future:
        first1[0] ^= 1
    relative_winding = bool(fixture["relative_winding"])
    terminal_nonvacuum = next_label != VACUUM
    private_score = terminal_nonvacuum or relative_winding
    public = {
        "round0_first_record": first0,
        "round0_action": action,
        "round0_action_digest": action_digest,
        "round0_second_record": second,
        "round1_first_record": first1,
    }
    require(set(public) == {
        "round0_first_record", "round0_action", "round0_action_digest",
        "round0_second_record", "round1_first_record",
    }, "public field-set drift")
    return {
        "model": model,
        "arm": arm,
        "public": public,
        "private_diagnostic": {
            "terminal_label": next_label,
            "hidden_state_digest": hidden1.state_update_digest,
            "terminal_nonvacuum": terminal_nonvacuum,
            "relative_winding": relative_winding,
            "boolean_union_failure": private_score,
        },
        "kernel": weights,
    }


def validate(contract: dict) -> dict:
    upstream_path = LAB / contract["research_basis"]["upstream_review"]
    require(file_hash(upstream_path) == contract["research_basis"]["upstream_sha256"],
            "upstream model-sufficiency review hash drift")
    upstream = json.loads(upstream_path.read_text())
    require(upstream["status"] == "passed_structural_model_limit_only",
            "upstream review is not accepted")
    require(contract["budget"]["deterministic_cells"] == 4,
            "registered cell count changed")
    keys = contract["fixed_scope"]["exogenous_keys"]
    require(len(keys) == 3 and len(set(keys.values())) == 3 and
            all(len(value) == 64 for value in keys.values()), "exogenous key drift")

    cells = [run_cell(contract, model, action)
             for model in contract["fixed_scope"]["models"]
             for action in contract["fixed_scope"]["actions"]]
    require(len(cells) == 4, "four-cell matrix incomplete")
    by_key = {(cell["model"], cell["arm"]): cell for cell in cells}
    first0 = {tuple(cell["public"]["round0_first_record"]) for cell in cells}
    require(first0 == {(1, 1)}, "round-0 public records differ")
    require(all(cell == run_cell(contract, cell["model"], cell["arm"])
                for cell in cells), "exact replay failed")

    for cell in cells:
        perturbed = run_cell(contract, cell["model"], cell["arm"], perturb_future=True)
        for name in ("round0_first_record", "round0_action", "round0_action_digest",
                     "round0_second_record"):
            require(perturbed["public"][name] == cell["public"][name],
                    f"future-only perturbation changed causal field {name}")
        require(perturbed["public"]["round1_first_record"] !=
                cell["public"]["round1_first_record"],
                "future-only perturbation did not alter round-1 record")
        require(cell["private_diagnostic"]["boolean_union_failure"] == (
            cell["private_diagnostic"]["terminal_nonvacuum"] or
            cell["private_diagnostic"]["relative_winding"]
        ), "private union score drift")
        public_text = json.dumps(cell["public"], sort_keys=True)
        require(not any(term in public_text for term in (
            "terminal_label", "hidden_state", "fault", "relative_winding",
            "private", "support", "pairing", "kernel",
        )), "public record leaks private diagnostics")

    for model in contract["fixed_scope"]["models"]:
        deferred = by_key[(model, "defer")]
        committed = by_key[(model, "commit")]
        require(deferred["public"]["round0_second_record"] is None,
                "defer unexpectedly measured E2")
        require(committed["public"]["round0_second_record"]["charge_vacuum_bits"] == [0, 1],
                "commit E2 full-binary record drift")
        wrong_digest = "0" * 64
        require(wrong_digest != committed["public"]["round0_action_digest"],
                "wrong-digest negative control is not wrong")
        try:
            check_second_binding(committed["public"]["round0_second_record"], wrong_digest)
        except AssertionError:
            pass
        else:
            raise AssertionError("wrong action digest passed E2 binding")

    null_defer = by_key[("no_feedback_null", "defer")]
    null_commit = by_key[("no_feedback_null", "commit")]
    feedback_defer = by_key[("action_feedback_fixture", "defer")]
    feedback_commit = by_key[("action_feedback_fixture", "commit")]
    require(null_defer["private_diagnostic"]["hidden_state_digest"] ==
            null_commit["private_diagnostic"]["hidden_state_digest"],
            "no-feedback hidden state depends on action")
    require(null_defer["public"]["round1_first_record"] ==
            null_commit["public"]["round1_first_record"],
            "no-feedback first record depends on action")
    require(feedback_defer["private_diagnostic"]["hidden_state_digest"] !=
            feedback_commit["private_diagnostic"]["hidden_state_digest"],
            "feedback hidden state failed to depend on action")
    require(feedback_defer["public"]["round1_first_record"] !=
            feedback_commit["public"]["round1_first_record"],
            "feedback future first record failed to depend on action")
    require(feedback_defer["private_diagnostic"]["terminal_label"] == FLUX and
            feedback_commit["private_diagnostic"]["terminal_label"] == VACUUM,
            "feedback fixture private labels drifted")

    return {
        "cells": cells,
        "checks": {
            "four_registered_cells": True,
            "three_matched_exogenous_keys": True,
            "categorical_kernel_normalized": True,
            "round0_public_and_policy_causal": True,
            "action_bound_full_binary_E2_and_wrong_digest_rejection": True,
            "future_only_perturbation_preserves_prior_action_and_E2": True,
            "null_action_to_future_path_absent": True,
            "fixture_action_to_future_path_present": True,
            "private_boolean_union_and_public_nonleak": True,
            "exact_replay": True,
        },
    }


def main() -> int:
    started = time.process_time()
    require(not RESULT.exists(), "J6C result already exists; no silent rerun")
    contract = json.loads(CONTRACT.read_text())
    result = {
        "schema_version": 1,
        "contract_sha256": file_hash(CONTRACT),
        "runner_sha256": file_hash(Path(__file__)),
        "status": "censored",
        "reason": None,
        "new_stochastic_histories": 0,
        "new_performance_arm_evaluations": 0,
        "new_bootstrap_replicates": 0,
        "claim_boundary": contract["claim_boundary"],
    }
    try:
        result.update(validate(contract))
        result["status"] = "passed_deterministic_interface_only"
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}:{exc}"
    result["cpu_seconds"] = round(time.process_time() - started, 6)
    if result["cpu_seconds"] > contract["budget"]["max_cpu_seconds"]:
        result["status"] = "censored"
        result["reason"] = "registered CPU budget exceeded"
        result.pop("cells", None)
        result.pop("checks", None)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "reason": result["reason"],
                      "cpu_seconds": result["cpu_seconds"]}))
    return 0 if result["status"] == "passed_deterministic_interface_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
