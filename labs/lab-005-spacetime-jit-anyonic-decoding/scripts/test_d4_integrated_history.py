from __future__ import annotations

from dataclasses import replace
import inspect

import numpy as np
import pytest

from d4_integrated_history import (
    build_integrated_d4_history_from_draws,
    derive_private_score,
    evaluate_history_matrix,
    provide_action_conditioned_second_record,
    terminal_arm_row,
)
from d4_charge import decode_public_postflux_charges
from d4_spatial_policy import paper_periodic_honeycomb
from e1_schedule_integration import run_e1_policy_matrix
from generic_history import GenericNoiseParameters
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox


PARAMETERS = GenericNoiseParameters(0.0, 0.0, 0.0, 0.0, 0.0)


def _key(label: str) -> str:
    import hashlib

    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _history(
    *,
    transition_edges: tuple[int, ...] = (),
    syndrome_fault: tuple[int, int] | None = None,
):
    lattice = paper_periodic_honeycomb(2)
    faults = np.zeros((4, lattice.edge_count), dtype=bool)
    faults[0, list(transition_edges)] = True
    syndrome_faults = np.zeros((5, lattice.vertex_count), dtype=bool)
    if syndrome_fault is not None:
        syndrome_faults[syndrome_fault] = True
    return build_integrated_d4_history_from_draws(
        trial_id="j6-fixture",
        master_seed=1,
        parameters=PARAMETERS,
        physical_key=_key("physical"),
        first_observation_key=_key("first"),
        second_exogenous_key=_key("second"),
        transition_edge_faults=faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_uniforms=np.full((5, lattice.vertex_count), 0.5),
        first_observation_seeds=(10, 11, 12, 13, 14),
    )


def _geometry() -> AbsorberGeometry:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "j6-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 4)), 0
        ),
        current_round=0,
    )
    return geometry


def _invocations(history):
    lattice = paper_periodic_honeycomb(2)
    matrix = run_e1_policy_matrix(
        trial_id=history.trial_id,
        record=history.record,
        check_positions=tuple((site,) for site in range(lattice.vertex_count)),
        geometry=_geometry(),
        size=2,
    )
    return tuple(
        invocation for mode in matrix.modes for invocation in mode.invocations
    )


def test_zero_history_has_five_bound_rounds_and_no_private_public_fields() -> None:
    history = _history()
    assert len(history.hidden_projector_states) == 5
    assert not np.any(history.record.syndrome_readout)
    assert not np.any(history.record.herald_readout)
    transcript = history.public_transcript()
    text = repr(transcript)
    assert "physical_edge" not in text
    assert "hidden" not in text
    assert "winding" not in text
    assert "truth" not in text


def test_all_eight_schedule_mode_cells_complete_and_score_without_loss() -> None:
    history = _history(transition_edges=(0,))
    rows = []
    for invocation in _invocations(history):
        completion = provide_action_conditioned_second_record(history, invocation)
        score = derive_private_score(history, invocation, completion)
        rows.append((invocation.mode, invocation.branch, completion, score))
    assert len(rows) == 8
    assert len({(mode, branch) for mode, branch, _, _ in rows}) == 8
    assert all(len(completion.public_charge_record) == 24 for _, _, completion, _ in rows)
    assert all(set(completion.public_charge_record) <= {0, 1} for _, _, completion, _ in rows)
    assert not any(score.logical_failure for _, _, _, score in rows)
    assert rows == [
        (
            invocation.mode,
            invocation.branch,
            provide_action_conditioned_second_record(history, invocation),
            derive_private_score(
                history,
                invocation,
                provide_action_conditioned_second_record(history, invocation),
            ),
        )
        for invocation in _invocations(history)
    ]


def test_second_record_is_action_bound_and_charge_action_is_relation_free() -> None:
    history = _history(transition_edges=(2, 5, 8, 12, 17, 24, 30, 34))
    invocations = _invocations(history)
    invocation = next(item for item in invocations if item.report.round >= 1)
    completion = provide_action_conditioned_second_record(history, invocation)
    assert len(completion.public_charge_record) == 24
    assert tuple(inspect.signature(decode_public_postflux_charges).parameters) == (
        "honeycomb",
        "public_charge_outcomes",
    )
    public_text = repr(completion.public_dict())
    assert "active_vertices" not in public_text
    assert "entanglement_pairs" not in public_text
    assert "internal" not in public_text
    wrong = replace(completion, flux_action_digest="0" * 64)
    with pytest.raises(ValueError, match="not bound"):
        derive_private_score(history, invocation, wrong)


def test_private_score_is_derived_and_detects_terminal_residual() -> None:
    history = _history(transition_edges=(0,))
    invocation = next(item for item in _invocations(history) if item.report.round >= 1)
    completion = provide_action_conditioned_second_record(history, invocation)
    score = derive_private_score(history, invocation, completion)
    assert "logical_failure_truth" not in inspect.signature(derive_private_score).parameters
    assert score.logical_failure == (
        score.physical_winding
        or score.union_winding
        or score.terminal_residual
        or score.charge_winding
    )


def test_unconditional_terminal_row_retains_missing_and_malformed_arms_as_failures() -> None:
    history = _history(transition_edges=(0,))
    invocation = _invocations(history)[0]
    missing = terminal_arm_row(
        history, invocation, None, failure_reason="timeout"
    )
    assert missing.denominator_included
    assert missing.logical_failure
    assert missing.status == "failed_closed"
    completion = provide_action_conditioned_second_record(history, invocation)
    malformed = replace(completion, flux_action_digest="0" * 64)
    retained = terminal_arm_row(history, invocation, malformed)
    assert retained.denominator_included
    assert retained.logical_failure
    assert retained.status == "failed_closed"


def test_zero_event_history_exposes_missing_arm_level_success_path() -> None:
    history = _history()
    lattice = paper_periodic_honeycomb(2)
    rows = evaluate_history_matrix(
        history,
        check_positions=tuple((site,) for site in range(lattice.vertex_count)),
        geometry=_geometry(),
    )
    assert len(rows) == 8
    assert all(row.status == "scored" for row in rows)
    assert all(row.invocation_count == 0 for row in rows)
    assert all(row.unique_commit_count == 0 for row in rows)
    assert not any(row.logical_failure for row in rows)


def test_multicluster_fixture_repeats_full_snapshot_action_per_cluster() -> None:
    history = _history(transition_edges=(0, 1))
    immediate = tuple(
        invocation
        for invocation in _invocations(history)
        if invocation.mode == "syndrome_only" and invocation.branch == "immediate"
    )
    assert len(immediate) == 2
    assert (
        immediate[0].policy_request.flux_syndrome_vertices
        == immediate[1].policy_request.flux_syndrome_vertices
    )
    assert immediate[0].flux_action.correction_edges == immediate[1].flux_action.correction_edges
    lattice = paper_periodic_honeycomb(2)
    rows = evaluate_history_matrix(
        history,
        check_positions=tuple((site,) for site in range(lattice.vertex_count)),
        geometry=_geometry(),
    )
    assert len(rows) == 8
    row = next(
        item
        for item in rows
        if item.mode == "syndrome_only" and item.branch == "immediate"
    )
    assert row.status == "scored"
    assert row.invocation_count == 2
    assert row.unique_commit_count == 1
    assert row.collapsed_duplicate_count == 1


def test_zero_single_and_multicluster_matrices_replay_exactly_eight_rows() -> None:
    lattice = paper_periodic_honeycomb(2)
    for edges in ((), (0,), (0, 1)):
        history = _history(transition_edges=edges)
        first = evaluate_history_matrix(
            history,
            check_positions=tuple(
                (site,) for site in range(lattice.vertex_count)
            ),
            geometry=_geometry(),
        )
        second = evaluate_history_matrix(
            history,
            check_positions=tuple(
                (site,) for site in range(lattice.vertex_count)
            ),
            geometry=_geometry(),
        )
        assert len(first) == 8
        assert first == second
        assert all(row.denominator_included for row in first)


def test_odd_noisy_syndrome_handoff_retains_all_eight_denominator_rows() -> None:
    history = _history(syndrome_fault=(1, 0))
    lattice = paper_periodic_honeycomb(2)
    rows = evaluate_history_matrix(
        history,
        check_positions=tuple((site,) for site in range(lattice.vertex_count)),
        geometry=_geometry(),
    )
    assert len(rows) == 8
    assert all(row.denominator_included for row in rows)
    for row in rows:
        if row.branch == "immediate":
            assert row.status == "failed_closed"
            assert row.logical_failure
            assert "unresolved_temporal_boundary_handoff" in (row.failure_reason or "")
        else:
            assert row.status == "scored"
