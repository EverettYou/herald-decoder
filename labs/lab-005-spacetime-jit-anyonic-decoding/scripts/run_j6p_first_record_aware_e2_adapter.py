"""Deterministic 12-cell and invalid-input matrix for the fixed J6P adapter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from j6p_fixed_path_e2_adapter import (
    LAW, bound_action_digest, first_prefix_digest, provide_fixed_path_e2,
)


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6p-first-record-aware-e2-adapter-2026-09-25.json"
RESULT = LAB / "results/j6p-first-record-aware-e2-adapter-2026-09-25.json"
OLD_CALLER = LAB / "scripts/d4_integrated_history.py"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected(fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
    except (ValueError, TypeError, KeyError):
        return True
    return False


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pinned = {
        "j6o_result": file_hash(LAW) == contract["pinned_inputs"]["j6o_result_sha256"],
        "frozen_integrated_history": file_hash(OLD_CALLER) ==
        contract["pinned_inputs"]["frozen_integrated_history_sha256"],
    }
    assert all(pinned.values()), pinned
    law = json.loads(LAW.read_text())
    first_records = {row["first_public"]["charge"][1]: row["first_public"]
                     for row in law["public_law_rows"]}
    assert set(first_records) == {0, 1}
    actions = {"defer": (), "partial": (0,), "matched": (0, 4)}
    rows = []
    for first_bit in (0, 1):
        first = first_records[first_bit]
        prefix = first_prefix_digest("fixed-j6p-trial", 0, first)
        for action_name, edges in actions.items():
            action = bound_action_digest("fixed-j6p-trial", 0, prefix, edges)
            for coin in (0, 1):
                kwargs = dict(trial_id="fixed-j6p-trial", decision_round=0,
                              first_public=first, first_digest=prefix,
                              correction_edges=edges, action_digest=action,
                              second_exogenous_bit=coin)
                completed = provide_fixed_path_e2(**kwargs)
                assert completed == provide_fixed_path_e2(**kwargs)
                assert set(completed) == {"trial_id", "decision_round",
                                          "first_prefix_digest", "public_action_red_edge_ids",
                                          "action_digest", "second_public", "completion_digest"}
                assert completed["first_prefix_digest"] == prefix
                assert completed["action_digest"] == action
                assert completed["public_action_red_edge_ids"] == list(edges)
                if action_name == "defer":
                    assert completed["second_public"] is None
                else:
                    assert set(completed["second_public"]) == {"flux", "charge", "vacuum"}
                    assert all(len(bits) == 24 for bits in completed["second_public"].values())
                rows.append({"first_green_bit": first_bit, "action": action_name,
                             "second_exogenous_bit_private": coin,
                             "public_completion": completed})
    assert len(rows) == 12
    for first_bit in (0, 1):
        for action_name in ("partial", "matched"):
            actual = [row["public_completion"]["second_public"] for row in rows
                      if row["first_green_bit"] == first_bit and row["action"] == action_name]
            expected = [row["second_public"] for row in law["public_law_rows"]
                        if row["action"] == action_name
                        and row["first_public"]["charge"][1] == first_bit]
            assert sorted(actual, key=lambda record: record["charge"]) == \
                   sorted(expected, key=lambda record: record["charge"])
    first = first_records[0]
    prefix = first_prefix_digest("fixed-j6p-trial", 0, first)
    action = bound_action_digest("fixed-j6p-trial", 0, prefix, (0, 4))
    valid = dict(trial_id="fixed-j6p-trial", decision_round=0,
                 first_public=first, first_digest=prefix,
                 correction_edges=(0, 4), action_digest=action,
                 second_exogenous_bit=0)
    changed = {key: value.copy() for key, value in first.items()}
    changed["charge"][1] = 1
    changed["vacuum"][1] = 0
    invalid = {
        "first_record_bit_tamper_stale_digest": rejected(
            provide_fixed_path_e2, **{**valid, "first_public": changed}),
        "first_digest_tamper": rejected(
            provide_fixed_path_e2, **{**valid, "first_digest": "0" * 64}),
        "action_digest_swap": rejected(
            provide_fixed_path_e2, **{**valid, "action_digest": "0" * 64}),
        "unsupported_action": rejected(
            provide_fixed_path_e2, **{**valid, "correction_edges": (4,)}),
        "invalid_coin": rejected(
            provide_fixed_path_e2, **{**valid, "second_exogenous_bit": 2}),
        "private_support_in_first_record": rejected(
            provide_fixed_path_e2,
            **{**valid, "first_public": {**first, "physical_error_edges": [0, 4]}}),
        "future_only_field_injection": rejected(
            provide_fixed_path_e2, **{**valid, "future_public_record": first}),
        "malformed_binary_first_record": rejected(
            provide_fixed_path_e2,
            **{**valid, "first_public": {**first, "charge": [2] + first["charge"][1:]}}),
    }
    assert all(invalid.values()), invalid
    assert file_hash(OLD_CALLER) == contract["pinned_inputs"]["frozen_integrated_history_sha256"]
    assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_fixed_path_first_record_aware_adapter_only",
        "contract_sha256": file_hash(CONTRACT),
        "pinned_input_checks": pinned,
        "valid_case_count": len(rows),
        "invalid_control_results": invalid,
        "valid_rows": rows,
        "checks": {"first_record_required": True,
                   "action_bound_to_first_prefix": True,
                   "j6o_conditional_law_enumerated": True,
                   "defer_has_no_e2": True,
                   "public_fields_whitelisted": True,
                   "exact_replay": True,
                   "old_five_round_caller_byte_identical": True},
        "inference_boundary": "Fixed one-geometry public E2 adapter only. Not integrated into or a replacement for the general phenomenological five-round caller; no general D4 action-conditioned kernel, noisy history, schedule risk or threshold is established.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.process_time() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
