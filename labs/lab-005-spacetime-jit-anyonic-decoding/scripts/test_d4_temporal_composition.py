from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_spatial_policy import (  # noqa: E402
    MODEL_ID,
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    canonical_digest,
    decode_charge_action,
    decode_flux_action,
)
from d4_honeycomb import paper_periodic_honeycomb  # noqa: E402
from d4_temporal_composition import (  # noqa: E402
    advance_round,
    commit_flux,
    open_temporal_state,
    score_frozen_transition,
    supply_post_flux,
)


def _request(mode: str, prefix_digest: str) -> D4SpatialCommitRequestV1:
    return D4SpatialCommitRequestV1.from_dict(
        {
            "schema_version": 1,
            "request_id": f"e0-{mode}",
            "model_id": MODEL_ID,
            "size": 2,
            "mode": mode,
            "decision_round": 1,
            "committed_through_round": 1,
            "flux_syndrome_vertices": [0, 1],
            "initial_charge_measurements": (
                [] if mode == "syndrome_only" else [{"vertex": 0, "outcome": 1}]
            ),
            "causal_prefix_digest": prefix_digest,
        }
    )


def _empty_post(request, flux):
    unsigned = {
        "request_id": request.request_id,
        "action_digest": flux.action_digest,
        "observation_round": 1,
        "measurement_layout": {"active_vertices": [], "entanglement_pairs": []},
        "charge_measurements": [],
    }
    return D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=paper_periodic_honeycomb(2).vertex_count,
    )


def _complete(mode: str = "syndrome_only"):
    state = open_temporal_state(
        trial_id=f"trial-{mode}",
        size=2,
        mode=mode,
        initial_round=0,
        causal_prefix_digest="0" * 64,
    )
    state = advance_round(state, next_round=1, causal_prefix_digest="1" * 64)
    request = _request(mode, "1" * 64)
    state = commit_flux(state, request)
    post = _empty_post(request, state.flux_action)
    return supply_post_flux(state, post), request, post


@pytest.mark.parametrize("mode", ["syndrome_only", "heralded"])
def test_perfect_temporal_actions_equal_direct_spatial_policy(mode: str) -> None:
    state, request, post = _complete(mode)
    direct_flux = decode_flux_action(request)
    direct_charge = decode_charge_action(request, direct_flux, post)
    assert state.commit_request == request
    assert state.flux_action == direct_flux
    assert state.post_flux_observation == post
    assert state.charge_action == direct_charge


def test_no_action_carry_forward_and_post_flux_order_are_causal() -> None:
    state = open_temporal_state(
        trial_id="carry",
        size=2,
        mode="syndrome_only",
        initial_round=0,
        causal_prefix_digest="0" * 64,
    )
    state = advance_round(state, next_round=1, causal_prefix_digest="1" * 64)
    assert state.phase == "observing"
    assert [event.kind for event in state.events] == ["open", "advance"]
    request = _request("syndrome_only", "1" * 64)
    post = _empty_post(request, decode_flux_action(request))
    with pytest.raises(ValueError, match="previously bound"):
        supply_post_flux(state, post)
    committed = commit_flux(state, request)
    with pytest.raises(ValueError, match="pending"):
        advance_round(committed, next_round=2, causal_prefix_digest="2" * 64)


def test_completed_transition_advances_to_third_causal_round() -> None:
    complete, _, _ = _complete()
    advanced = advance_round(
        complete, next_round=2, causal_prefix_digest="2" * 64
    )
    assert advanced.current_round == 2
    assert advanced.phase == "observing"
    assert advanced.commit_request is None
    assert advanced.flux_action is None
    assert [event.kind for event in advanced.events] == [
        "open",
        "advance",
        "commit_flux",
        "complete_charge",
        "advance",
    ]


def test_public_state_has_deterministic_digest_and_no_truth_fields() -> None:
    first, _, _ = _complete("heralded")
    second, _, _ = _complete("heralded")
    assert first == second
    assert first.state_digest == second.state_digest
    payload = json.dumps(first.public_dict(), sort_keys=True).lower()
    for forbidden in (
        "physical_error",
        "future",
        "logical_failure",
        "truth",
        "random_seed",
    ):
        assert forbidden not in payload


def test_private_scorer_requires_completed_frozen_public_transition() -> None:
    observing = open_temporal_state(
        trial_id="score",
        size=2,
        mode="syndrome_only",
        initial_round=0,
        causal_prefix_digest="0" * 64,
    )
    with pytest.raises(ValueError, match="completed frozen"):
        score_frozen_transition(observing, logical_failure_truth=False)
    complete, _, _ = _complete()
    digest_before = complete.state_digest
    score = score_frozen_transition(complete, logical_failure_truth=True)
    assert score.state_digest == digest_before
    assert score.logical_failure
    assert complete.state_digest == digest_before


def test_temporal_commit_rejects_mismatched_round_mode_or_prefix() -> None:
    state = open_temporal_state(
        trial_id="reject",
        size=2,
        mode="syndrome_only",
        initial_round=0,
        causal_prefix_digest="0" * 64,
    )
    state = advance_round(state, next_round=1, causal_prefix_digest="1" * 64)
    with pytest.raises(ValueError, match="does not match"):
        commit_flux(state, _request("syndrome_only", "2" * 64))
    with pytest.raises(ValueError, match="does not match"):
        commit_flux(state, _request("heralded", "1" * 64))
