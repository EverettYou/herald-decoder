"""Contract tests for the narrow J6P fixed-path public adapter."""

import json

import pytest

from j6p_fixed_path_e2_adapter import (
    LAW, bound_action_digest, first_prefix_digest, provide_fixed_path_e2,
)
from run_j6p_first_record_aware_e2_adapter import run


def _call():
    law = json.loads(LAW.read_text())
    first = next(row["first_public"] for row in law["public_law_rows"]
                 if row["first_public"]["charge"][1] == 0)
    prefix = first_prefix_digest("fixture", 0, first)
    return dict(trial_id="fixture", decision_round=0, first_public=first,
                first_digest=prefix, correction_edges=(0, 4),
                action_digest=bound_action_digest("fixture", 0, prefix, (0, 4)),
                second_exogenous_bit=0)


def test_registered_matrix_and_controls_pass():
    result = run()
    assert result["valid_case_count"] == 12
    assert all(result["invalid_control_results"].values())
    assert result["stochastic_histories"] == result["schedule_arm_evaluations"] == 0


def test_first_record_and_action_binding_fail_closed():
    call = _call()
    for changed in (
        {**call, "first_digest": "0" * 64},
        {**call, "action_digest": "0" * 64},
        {**call, "correction_edges": (0,)},
        {**call, "decision_round": 1},
        {**call, "second_exogenous_bit": True},
        {**call, "future_public_record": call["first_public"]},
    ):
        with pytest.raises((ValueError, TypeError)):
            provide_fixed_path_e2(**changed)


def test_public_completion_is_whitelisted_and_replays():
    call = _call()
    first = provide_fixed_path_e2(**call)
    assert first == provide_fixed_path_e2(**call)
    assert set(first) == {"trial_id", "decision_round", "first_prefix_digest",
                          "public_action_red_edge_ids", "action_digest",
                          "second_public", "completion_digest"}
    assert set(first["second_public"]) == {"flux", "charge", "vacuum"}
    assert not any("physical" in key or "private" in key or "coin" in key
                   for key in first)
