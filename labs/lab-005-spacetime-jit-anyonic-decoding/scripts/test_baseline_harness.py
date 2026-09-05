from __future__ import annotations

from dataclasses import fields
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline_harness import (  # noqa: E402
    DeterministicInnerDecoder,
    InnerDecoderRequest,
    run_shared_history_baselines,
    visible_history_digest,
)
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox  # noqa: E402
from spacetime_record import build_record_from_fault_masks  # noqa: E402


def _history():
    syndrome = np.asarray([[0], [1], [1], [1]], dtype=bool)
    herald = np.zeros((4, 1), dtype=bool)
    return build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )


def _geometry() -> AbsorberGeometry:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "boundary",
            "spatial_boundary",
            SpacetimeBox((2, 0), (2, 3)),
            0,
        ),
        current_round=0,
    )
    return geometry


def _future_counterfactual(last_herald: int):
    syndrome = np.asarray([[0], [1], [1], [1]], dtype=bool)
    herald = np.asarray([[0], [0], [0], [last_herald]], dtype=bool)
    return build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )


def _near_geometry() -> AbsorberGeometry:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "near-boundary",
            "spatial_boundary",
            SpacetimeBox((1, 0), (1, 3)),
            0,
        ),
        current_round=0,
    )
    return geometry


def _run_counterfactual(last_herald: int):
    decoder = DeterministicInnerDecoder()
    result = run_shared_history_baselines(
        trial_id="counterfactual",
        record=_future_counterfactual(last_herald),
        check_positions=((0,),),
        geometry=_near_geometry(),
        decoder=decoder,
    )
    return result, {request.branch: request for request in decoder.requests}


def _run():
    decoder = DeterministicInnerDecoder()
    result = run_shared_history_baselines(
        trial_id="trial-0",
        record=_history(),
        check_positions=((0,),),
        geometry=_geometry(),
        decoder=decoder,
    )
    return result, decoder


def test_registered_branch_matrix_has_expected_invocation_timing() -> None:
    result, _ = _run()
    by_branch = {branch.branch: branch for branch in result.branches}
    assert tuple(by_branch) == (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    )
    assert [event.round for event in by_branch["immediate"].events] == [1]
    assert [event.round for event in by_branch["fixed_delay_1"].events] == [2]
    assert [event.action for event in by_branch["jit_lyons_brown"].events] == [
        "defer",
        "defer",
        "invoke",
    ]
    assert [event.round for event in by_branch["jit_lyons_brown"].events] == [1, 2, 3]
    assert [event.round for event in by_branch["offline_full_history"].events] == [3]


def test_all_branches_share_history_and_decoder_implementation() -> None:
    result, decoder = _run()
    assert {branch.history_digest for branch in result.branches} == {
        result.history_digest
    }
    assert result.decoder_version == decoder.version
    assert result.decoder_implementation_digest == decoder.implementation_digest
    assert len(decoder.requests) == 4
    assert {branch.history_digest for branch in result.branches} == {
        result.history_digest
    }


def test_causal_prefixes_stop_at_invocation_and_offline_is_explicit() -> None:
    _, decoder = _run()
    requests = {request.branch: request for request in decoder.requests}
    assert requests["immediate"].prefix.final_round == 1
    assert requests["fixed_delay_1"].prefix.final_round == 2
    assert requests["jit_lyons_brown"].prefix.final_round == 3
    assert requests["offline_full_history"].prefix.final_round == 3
    assert not any(
        requests[branch].noncausal
        for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown")
    )
    assert requests["offline_full_history"].noncausal
    assert requests["immediate"].prefix.syndrome_readout.shape[0] == 2


def test_request_schema_excludes_truth_fault_and_logical_fields() -> None:
    names = {item.name for item in fields(InnerDecoderRequest)}
    forbidden = {
        "history_digest",
        "truth",
        "faults",
        "logical",
        "syndrome_truth",
        "herald_truth",
    }
    assert not names.intersection(forbidden)
    _, decoder = _run()
    for request in decoder.requests:
        assert set(vars(request.prefix)) == {
            "final_round",
            "syndrome_readout",
            "syndrome_detectors",
            "herald_readout",
        }


def test_future_only_change_preserves_every_causal_callback_output() -> None:
    base_run, base = _run_counterfactual(0)
    future_run, future = _run_counterfactual(1)

    assert base_run.history_digest != future_run.history_digest
    for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
        assert base[branch].prefix.final_round < 3
        assert base[branch].prefix_digest == future[branch].prefix_digest
        assert base[branch].request_digest == future[branch].request_digest

    base_events = {
        event.branch: event
        for branch in base_run.branches
        for event in branch.events
        if event.action == "invoke"
    }
    future_events = {
        event.branch: event
        for branch in future_run.branches
        for event in branch.events
        if event.action == "invoke"
    }
    for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
        assert base_events[branch].response_digest == future_events[branch].response_digest

    assert base["offline_full_history"].noncausal
    assert future["offline_full_history"].noncausal
    assert base["offline_full_history"].prefix.final_round == 3
    assert future["offline_full_history"].prefix.final_round == 3
    assert (
        base["offline_full_history"].request_digest
        != future["offline_full_history"].request_digest
    )
    assert (
        base_events["offline_full_history"].response_digest
        != future_events["offline_full_history"].response_digest
    )


def test_visible_history_digest_ignores_private_truth_decomposition() -> None:
    visible = np.asarray([[0], [1], [1], [1]], dtype=bool)
    herald_visible = np.asarray([[0], [1], [0], [1]], dtype=bool)
    record_a = build_record_from_fault_masks(
        visible,
        np.zeros_like(visible),
        herald_visible,
        np.zeros_like(herald_visible),
    )
    record_b = build_record_from_fault_masks(
        np.logical_not(visible),
        np.ones_like(visible),
        np.logical_not(herald_visible),
        np.ones_like(herald_visible),
    )
    assert np.array_equal(record_a.syndrome_readout, record_b.syndrome_readout)
    assert np.array_equal(record_a.herald_readout, record_b.herald_readout)
    assert visible_history_digest(record_a) == visible_history_digest(record_b)


def test_deterministic_replay_is_bit_identical() -> None:
    first, _ = _run()
    second, _ = _run()
    assert first == second


def test_jit_branch_requires_active_absorber_and_trial_id() -> None:
    with pytest.raises(ValueError, match="nonempty trial"):
        run_shared_history_baselines(
            trial_id="",
            record=_history(),
            check_positions=((0,),),
            geometry=_geometry(),
            decoder=DeterministicInnerDecoder(),
        )
    with pytest.raises(ValueError, match="active nearest absorber"):
        run_shared_history_baselines(
            trial_id="trial-0",
            record=_history(),
            check_positions=((0,),),
            geometry=AbsorberGeometry(),
            decoder=DeterministicInnerDecoder(),
        )
