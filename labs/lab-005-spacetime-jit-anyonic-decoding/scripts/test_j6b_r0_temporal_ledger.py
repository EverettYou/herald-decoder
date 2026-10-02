"""Four bounded deterministic temporal-ledger reconciliation fixtures."""

from __future__ import annotations

import hashlib

import numpy as np

from baseline_harness import InnerDecoderRequest, prefix_digest
from d4_integrated_history import (
    build_integrated_d4_history_from_draws,
    evaluate_history_matrix,
    evaluate_schedule_arm,
)
from d4_spatial_policy import paper_periodic_honeycomb
from e1_schedule_integration import E1PolicyDecoder
from generic_history import GenericNoiseParameters
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox


LATTICE = paper_periodic_honeycomb(2)
ZERO = GenericNoiseParameters(0.0, 0.0, 0.0, 0.0, 0.0)


def _key(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _history(odd_rounds: tuple[int, ...]):
    faults = np.zeros((4, LATTICE.edge_count), dtype=bool)
    syndrome_faults = np.zeros((5, LATTICE.vertex_count), dtype=bool)
    syndrome_faults[list(odd_rounds), 0] = True
    return build_integrated_d4_history_from_draws(
        trial_id="j6b-r0-deterministic",
        master_seed=1,
        parameters=ZERO,
        physical_key=_key("j6b-r0-physical"),
        first_observation_key=_key("j6b-r0-first"),
        second_exogenous_key=_key("j6b-r0-second"),
        transition_edge_faults=faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_uniforms=np.full((5, LATTICE.vertex_count), 0.5),
        first_observation_seeds=(10, 11, 12, 13, 14),
    )


def _call(decoder, history, round_index: int, *, cluster: str = "one"):
    prefix = history.record.causal_prefix(round_index)
    return decoder(
        InnerDecoderRequest(
            branch="jit_lyons_brown",
            trial_id=history.trial_id,
            prefix_digest=prefix_digest(prefix),
            prefix=prefix,
            cluster_id=cluster,
            event_ids=(cluster,),
            noncausal=False,
        )
    )


def _geometry() -> AbsorberGeometry:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "j6b-r0-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 4)), 0
        ),
        current_round=0,
    )
    return geometry


def test_odd_then_even() -> None:
    history = _history((1,))
    for mode in ("syndrome_only", "heralded"):
        decoder = E1PolicyDecoder(mode=mode)
        _call(decoder, history, 1)
        _call(decoder, history, 2)
        assert tuple(item.flux_action.status for item in decoder.invocations) == (
            "defer_temporal_boundary", "action"
        )
        row = evaluate_schedule_arm(
            history, mode=mode, branch="jit_lyons_brown",
            invocations=tuple(decoder.invocations),
        )
        assert row.status == "scored"
        assert row.denominator_included and not row.logical_failure
        assert row.invocation_count == 2 and row.unique_commit_count == 1
        assert row.commit_rounds == (2,)
        assert len(row.public_completion_digests) == 1


def test_persistent_odd() -> None:
    history = _history((1, 2))
    for mode in ("syndrome_only", "heralded"):
        decoder = E1PolicyDecoder(mode=mode)
        _call(decoder, history, 1)
        _call(decoder, history, 2)
        row = evaluate_schedule_arm(
            history, mode=mode, branch="jit_lyons_brown",
            invocations=tuple(decoder.invocations),
        )
        assert row.status == "failed_closed"
        assert row.denominator_included and row.logical_failure
        assert "unresolved_temporal_boundary_handoff" in (row.failure_reason or "")


def test_same_round_duplicates_and_conflict() -> None:
    history = _history((1,))
    decoder = E1PolicyDecoder(mode="heralded")
    _call(decoder, history, 1, cluster="first")
    _call(decoder, history, 1, cluster="second")
    _call(decoder, history, 2, cluster="later")
    row = evaluate_schedule_arm(
        history, mode="heralded", branch="jit_lyons_brown",
        invocations=tuple(decoder.invocations),
    )
    assert row.status == "scored"
    assert row.invocation_count == 3 and row.unique_commit_count == 1
    assert row.collapsed_duplicate_count == 1

    other = _history(())
    conflict = E1PolicyDecoder(mode="heralded")
    _call(conflict, other, 1, cluster="conflict")
    malformed = evaluate_schedule_arm(
        history, mode="heralded", branch="jit_lyons_brown",
        invocations=(decoder.invocations[0], conflict.invocations[0]),
    )
    assert malformed.status == "failed_closed"
    assert malformed.denominator_included and malformed.logical_failure
    assert "distinct full-snapshot actions" in (malformed.failure_reason or "")


def test_whole_matrix_replay() -> None:
    history = _history((1,))
    kwargs = {
        "check_positions": tuple((site,) for site in range(LATTICE.vertex_count)),
        "geometry": _geometry(),
    }
    first = evaluate_history_matrix(history, **kwargs)
    second = evaluate_history_matrix(history, **kwargs)
    assert first == second and len(first) == 8
    assert len({(row.mode, row.branch) for row in first}) == 8
    assert all(row.denominator_included for row in first)
    # No private source field is added to any public handoff or action.
    assert all("physical_key" not in str(row) for row in first)
