"""Exactly eight deterministic J6A public-path fixtures; no schedule arms."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from baseline_harness import InnerDecoderRequest, prefix_digest
from d4_projector_instrument import FLUX, typed_record_to_commit_request
from d4_spatial_policy import (
    D4SpatialCommitRequestV1,
    D4TemporalBoundaryActionV1,
    D4TemporalBoundaryHandoffV1,
    decode_flux_action,
    decode_temporal_boundary_handoff,
    paper_periodic_honeycomb,
)
from e1_schedule_integration import (
    E1PolicyDecoder, derive_round_local_e1_record, run_e1_policy_matrix,
)
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox
from spacetime_record import build_record_from_fault_masks


VERTICES = paper_periodic_honeycomb(2).vertex_count


def _record(rows: tuple[tuple[int, ...], ...], *, alternate_truth: bool = False):
    syndrome = np.zeros((len(rows), VERTICES), dtype=bool)
    for round_index, vertices in enumerate(rows):
        syndrome[round_index, list(vertices)] = True
    herald = np.zeros_like(syndrome)
    herald[:, 2] = True
    if alternate_truth:
        return build_record_from_fault_masks(
            np.logical_not(syndrome), np.ones_like(syndrome),
            np.logical_not(herald), np.ones_like(herald),
        )
    return build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )


def _request(record, round_index: int) -> InnerDecoderRequest:
    prefix = record.causal_prefix(round_index)
    return InnerDecoderRequest(
        branch="jit_lyons_brown",
        trial_id="j6a-fixed-fixture",
        prefix_digest=prefix_digest(prefix),
        prefix=prefix,
        cluster_id="j6a-cluster",
        event_ids=("j6a-event",),
        noncausal=False,
    )


def _invoke(record, round_index: int, *, mode: str = "heralded"):
    decoder = E1PolicyDecoder(mode=mode)
    response = decoder(_request(record, round_index))
    assert len(decoder.invocations) == 1
    invocation = decoder.invocations[0]
    assert response.correction_token == invocation.flux_action.action_digest
    return invocation


def _odd(invocation) -> tuple[D4TemporalBoundaryHandoffV1, D4TemporalBoundaryActionV1]:
    handoff = invocation.policy_request
    action = invocation.flux_action
    assert isinstance(handoff, D4TemporalBoundaryHandoffV1)
    assert isinstance(action, D4TemporalBoundaryActionV1)
    assert action.status == "defer_temporal_boundary"
    assert action.correction_edges == ()
    assert handoff.augmented_endpoint_count % 2 == 0
    assert handoff.odd_endpoints == tuple(
        site for site, labels in invocation.report.reported_labels if FLUX in labels
    )
    return handoff, action


def test_even_identity() -> None:
    record = _record(((), (0, 1)))
    request = _request(record, 1)
    report = derive_round_local_e1_record(request, size=2)
    for mode in ("syndrome_only", "heralded"):
        invocation = _invoke(record, 1, mode=mode)
        expected_request = typed_record_to_commit_request(
            report, request_id=invocation.policy_request.request_id,
            size=2, mode=mode, scheduler_prefix_digest=request.prefix_digest,
        )
        assert isinstance(invocation.policy_request, D4SpatialCommitRequestV1)
        assert invocation.policy_request.to_dict() == expected_request.to_dict()
        assert invocation.flux_action.to_dict() == decode_flux_action(expected_request).to_dict()


def test_odd_readout_snapshot() -> None:
    for mode in ("syndrome_only", "heralded"):
        invocation = _invoke(_record(((), (0,))), 1, mode=mode)
        handoff, action = _odd(invocation)
        assert handoff.odd_endpoints == (0,)
        assert handoff.temporal_boundary_labels == ("time:1:vertex:0",)
        assert handoff.augmented_endpoint_count == 2
        assert action.correction_edges == ()
        assert "physical" not in str(handoff.to_dict()).lower()
        assert "truth" not in str(action.to_dict()).lower()
    # The real scheduler must reach the same typed branch, not only a direct
    # callback constructed by the fixture.
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "j6a-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 1)), 0
        ),
        current_round=0,
    )
    matrix = run_e1_policy_matrix(
        trial_id="j6a-fixed-fixture", record=_record(((), (0,))),
        check_positions=tuple((site,) for site in range(VERTICES)),
        geometry=geometry, size=2,
    )
    assert any(
        isinstance(invocation.policy_request, D4TemporalBoundaryHandoffV1)
        for mode_run in matrix.modes for invocation in mode_run.invocations
    )


def test_odd_two_round_reconciliation() -> None:
    record = _record(((), (0,), (0, 1)))
    earlier = _invoke(record, 1)
    handoff, _ = _odd(earlier)
    frozen = handoff.to_dict()
    later = _invoke(record, 2)
    assert isinstance(later.policy_request, D4SpatialCommitRequestV1)
    assert later.flux_action.status == "action"
    assert later.policy_request.causal_prefix_digest != handoff.scheduler_prefix_digest
    assert later.flux_action.action_digest != earlier.flux_action.action_digest
    assert handoff.to_dict() == frozen


def test_odd_persistence() -> None:
    record = _record(((), (0,), (0,)))
    earlier = _invoke(record, 1)
    terminal = _invoke(record, 2)
    first, _ = _odd(earlier)
    last, action = _odd(terminal)
    assert first.handoff_digest != last.handoff_digest
    assert last.temporal_boundary_labels == ("time:2:vertex:0",)
    assert action.status == "defer_temporal_boundary"


def test_causal_future_extension() -> None:
    first = _invoke(_record(((), (0,), (0,))), 1)
    extended = _invoke(_record(((), (0,), (0, 1))), 1)
    assert first == extended


def test_truth_sidecar_invariance() -> None:
    rows = ((), (0,), (0,))
    for mode in ("syndrome_only", "heralded"):
        public = _invoke(_record(rows), 1, mode=mode)
        alternate = _invoke(_record(rows, alternate_truth=True), 1, mode=mode)
        assert public == alternate


def test_replay_and_vertex_permutation() -> None:
    base = _invoke(_record(((), (0, 2, 4))), 1)
    assert base == _invoke(_record(((), (0, 2, 4))), 1)
    rotated = _invoke(_record(((), (1, 3, 5))), 1)
    a, _ = _odd(base)
    b, _ = _odd(rotated)
    assert b.odd_endpoints == tuple(vertex + 1 for vertex in a.odd_endpoints)
    assert b.temporal_boundary_labels == tuple(
        f"time:1:vertex:{vertex + 1}" for vertex in a.odd_endpoints
    )


def test_malformed_or_unbound_token() -> None:
    invocation = _invoke(_record(((), (0,))), 1)
    handoff, _ = _odd(invocation)
    data = handoff.to_dict()
    for alteration in (
        {"scheduler_prefix_digest": "0" * 64},
        {"decision_round": 2},
        {"odd_endpoints": [0, 0, 0]},
        {"temporal_boundary_labels": ["unknown"]},
    ):
        malformed = {**data, **alteration}
        with pytest.raises(ValueError):
            D4TemporalBoundaryHandoffV1.from_dict(malformed, vertex_count=VERTICES)
    with pytest.raises(ValueError, match="not bound"):
        decode_temporal_boundary_handoff(
            handoff, vertex_count=VERTICES,
            expected_request_id=handoff.request_id,
            expected_scheduler_request_digest="0" * 64,
            expected_scheduler_prefix_digest=handoff.scheduler_prefix_digest,
            expected_e1_report_digest=handoff.e1_report_digest,
            expected_round=handoff.decision_round,
            expected_flux_vertices=handoff.odd_endpoints,
        )
    bad_action = replace(invocation.flux_action, correction_edges=(0,))
    with pytest.raises(ValueError, match="fabricates spatial correction"):
        bad_action.validate(handoff, vertex_count=VERTICES)
