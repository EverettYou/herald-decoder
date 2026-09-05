from __future__ import annotations

import inspect

import numpy as np
import pytest

from baseline_harness import InnerDecoderRequest, prefix_digest
from d4_projector_instrument import (
    CHARGE,
    FLUX,
    perfect_report,
    project_post_action_charge_state,
)
from d4_spatial_policy import paper_periodic_honeycomb
from d4_matching import edge_chain_boundary
from e1_schedule_integration import (
    E2PostFluxFixture,
    derive_round_local_e1_record,
    run_e2_completion_matrix,
    run_e1_policy_matrix,
)
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox
from spacetime_record import build_record_from_fault_masks


VERTICES = paper_periodic_honeycomb(2).vertex_count


def _visible_rows(*, future_herald: bool = False):
    syndrome = np.zeros((4, VERTICES), dtype=bool)
    syndrome[2, (0, 1)] = True
    syndrome[3] = syndrome[2]
    herald = np.zeros_like(syndrome)
    herald[2, (0, 2)] = True
    herald[3] = herald[2]
    if future_herald:
        herald[3, 4] = True
    return syndrome, herald


def _record(*, future_herald: bool = False, alternate_truth: bool = False):
    syndrome, herald = _visible_rows(future_herald=future_herald)
    if alternate_truth:
        return build_record_from_fault_masks(
            np.logical_not(syndrome),
            np.ones_like(syndrome),
            np.logical_not(herald),
            np.ones_like(herald),
        )
    return build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )


def _request(record, *, round_: int = 2, digest: str | None = None):
    prefix = record.causal_prefix(round_)
    return InnerDecoderRequest(
        branch="jit_lyons_brown",
        trial_id="i1-trial",
        prefix_digest=digest or prefix_digest(prefix),
        prefix=prefix,
        cluster_id="cluster-i1",
        event_ids=("event-i1",),
        noncausal=False,
    )


def test_i1_last_public_row_maps_flux_and_charge_membership_site_by_site() -> None:
    result = derive_round_local_e1_record(_request(_record()), size=2)
    labels = dict(result.reported_labels)

    assert result.trial_id == "i1-trial"
    assert result.round == 2
    assert len(labels) == VERTICES
    assert labels[0] == (CHARGE, FLUX)
    assert labels[1] == (FLUX,)
    assert labels[2] == (CHARGE,)
    assert all(labels[site] == () for site in range(3, VERTICES))


def test_i1_private_truth_decomposition_cannot_change_public_record() -> None:
    visible = derive_round_local_e1_record(_request(_record()), size=2)
    alternate = derive_round_local_e1_record(
        _request(_record(alternate_truth=True)), size=2
    )
    assert visible == alternate


def test_i1_future_only_public_change_cannot_change_earlier_record() -> None:
    base = derive_round_local_e1_record(_request(_record()), size=2)
    changed = derive_round_local_e1_record(
        _request(_record(future_herald=True)), size=2
    )
    assert base == changed


def test_i1_is_bound_to_prefix_and_rejects_wrong_spatial_shape() -> None:
    with pytest.raises(ValueError, match="bound to its causal prefix"):
        derive_round_local_e1_record(_request(_record(), digest="0" * 64), size=2)

    small = np.zeros((3, 1), dtype=bool)
    malformed = build_record_from_fault_masks(
        small, np.zeros_like(small), small, np.zeros_like(small)
    )
    with pytest.raises(ValueError, match="every D4 site"):
        derive_round_local_e1_record(_request(malformed, round_=1), size=2)


def test_i1_public_signature_has_no_history_or_truth_inputs_and_replays() -> None:
    assert tuple(inspect.signature(derive_round_local_e1_record).parameters) == (
        "request",
        "size",
    )
    request = _request(_record())
    first = derive_round_local_e1_record(request, size=2)
    second = derive_round_local_e1_record(request, size=2)
    assert first == second
    assert "truth" not in repr(inspect.signature(derive_round_local_e1_record))
    assert "history" not in repr(inspect.signature(derive_round_local_e1_record))


def test_i1_registered_scope_rejects_unverified_lattice_size() -> None:
    with pytest.raises(ValueError, match="bounded to paper L=2"):
        derive_round_local_e1_record(_request(_record()), size=3)


def _matrix_record(*, future_herald: bool = False, alternate_truth: bool = False):
    syndrome = np.zeros((4, VERTICES), dtype=bool)
    syndrome[1:, (0, 1)] = True
    herald = np.zeros_like(syndrome)
    herald[1:, (0, 2)] = True
    if future_herald:
        herald[3, 4] = True
    if alternate_truth:
        return build_record_from_fault_masks(
            np.logical_not(syndrome),
            np.ones_like(syndrome),
            np.logical_not(herald),
            np.ones_like(herald),
        )
    return build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )


def _matrix_geometry() -> AbsorberGeometry:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "i2-boundary",
            "spatial_boundary",
            SpacetimeBox((1, 0), (1, 3)),
            0,
        ),
        current_round=0,
    )
    return geometry


def _matrix(*, future_herald: bool = False, alternate_truth: bool = False):
    return run_e1_policy_matrix(
        trial_id="i2-trial",
        record=_matrix_record(
            future_herald=future_herald,
            alternate_truth=alternate_truth,
        ),
        check_positions=tuple((site,) for site in range(VERTICES)),
        geometry=_matrix_geometry(),
        size=2,
    )


def _cells(matrix):
    return {
        (mode_run.mode, invocation.branch): invocation
        for mode_run in matrix.modes
        for invocation in mode_run.invocations
    }


def _schedule_signature(mode_run):
    return tuple(
        (
            event.branch,
            event.round,
            event.cluster_id,
            event.action,
            event.history_digest,
            event.request_digest,
            event.prefix_final_round,
            event.noncausal,
        )
        for branch in mode_run.baseline.branches
        for event in branch.events
    )


def test_i2_executes_both_public_modes_across_all_four_schedules() -> None:
    matrix = _matrix()
    cells = _cells(matrix)
    assert set(cells) == {
        (mode, branch)
        for mode in ("syndrome_only", "heralded")
        for branch in (
            "immediate",
            "fixed_delay_1",
            "jit_lyons_brown",
            "offline_full_history",
        )
    }
    assert len(cells) == 8
    assert all(cell.flux_action.status == "action" for cell in cells.values())
    assert all(
        cell.policy_request.decision_round == cell.report.round
        for cell in cells.values()
    )
    lattice = paper_periodic_honeycomb(2)
    for cell in cells.values():
        correction = np.zeros(lattice.edge_count, dtype=np.uint8)
        correction[list(cell.flux_action.correction_edges)] = 1
        assert tuple(np.flatnonzero(edge_chain_boundary(lattice, correction))) == (
            cell.policy_request.flux_syndrome_vertices
        )


def test_i2_modes_share_trace_timing_scheduler_and_declared_information_budget() -> None:
    matrix = _matrix()
    syndrome_only, heralded = matrix.modes
    assert syndrome_only.baseline.history_digest == heralded.baseline.history_digest
    assert (
        syndrome_only.baseline.decoder_implementation_digest
        == heralded.baseline.decoder_implementation_digest
    )
    assert _schedule_signature(syndrome_only) == _schedule_signature(heralded)

    cells = _cells(matrix)
    for branch in (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    ):
        plain = cells[("syndrome_only", branch)]
        informed = cells[("heralded", branch)]
        assert plain.report == informed.report
        assert plain.schedule_request_digest == informed.schedule_request_digest
        assert plain.policy_request.initial_charge_measurements == ()
        assert informed.policy_request.initial_charge_measurements[0] == (0, 1)


def test_i3_multilabel_report_reaches_heralded_policy_without_coercion() -> None:
    cells = _cells(_matrix())
    for branch in (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    ):
        cell = cells[("heralded", branch)]
        labels = dict(cell.report.reported_labels)
        assert labels[0] == (CHARGE, FLUX)
        assert 0 in cell.policy_request.flux_syndrome_vertices
        assert (0, 1) in cell.policy_request.initial_charge_measurements


def test_i3_future_only_change_preserves_causal_policy_but_changes_offline() -> None:
    base = _cells(_matrix())
    changed = _cells(_matrix(future_herald=True))
    for mode in ("syndrome_only", "heralded"):
        for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
            assert base[(mode, branch)] == changed[(mode, branch)]
        assert base[(mode, "offline_full_history")].noncausal
        assert changed[(mode, "offline_full_history")].noncausal
        assert (
            base[(mode, "offline_full_history")].policy_request
            != changed[(mode, "offline_full_history")].policy_request
        )


def test_i3_private_truth_change_preserves_every_public_request_and_action() -> None:
    assert _matrix() == _matrix(alternate_truth=True)


@pytest.mark.parametrize("mode", ["syndrome_only", "heralded"])
def test_i3_odd_flux_membership_fails_closed(mode: str) -> None:
    syndrome = np.zeros((2, VERTICES), dtype=bool)
    syndrome[1, 0] = True
    herald = np.zeros_like(syndrome)
    record = build_record_from_fault_masks(
        syndrome, np.zeros_like(syndrome), herald, np.zeros_like(herald)
    )
    request = _request(record, round_=1)
    report = derive_round_local_e1_record(request, size=2)
    from d4_projector_instrument import typed_record_to_commit_request

    with pytest.raises(ValueError, match="even cardinality"):
        typed_record_to_commit_request(
            report,
            request_id=f"odd-{mode}",
            size=2,
            mode=mode,
            scheduler_prefix_digest=request.prefix_digest,
        )


def test_i3_offline_is_explicit_and_full_matrix_replay_is_bit_identical() -> None:
    first = _matrix()
    second = _matrix()
    assert first == second
    for mode_run in first.modes:
        offline = [
            item
            for item in mode_run.invocations
            if item.branch == "offline_full_history"
        ]
        assert len(offline) == 1
        assert offline[0].noncausal


def _e2_postflux_provider(invocation):
    hidden = project_post_action_charge_state(
        trial_id="i2-trial",
        round=invocation.report.round,
        charge_labels={0: CHARGE, 2: CHARGE},
        bound_action_digest=invocation.flux_action.action_digest,
    )
    return E2PostFluxFixture(
        record=perfect_report(hidden),
        active_vertices=(0, 2),
        entanglement_pairs=((0, 2),),
    )


def _e2_matrix(*, future_herald: bool = False, alternate_truth: bool = False):
    return run_e2_completion_matrix(
        trial_id="i2-trial",
        record=_matrix_record(
            future_herald=future_herald,
            alternate_truth=alternate_truth,
        ),
        check_positions=tuple((site,) for site in range(VERTICES)),
        geometry=_matrix_geometry(),
        postflux_provider=_e2_postflux_provider,
        size=2,
    )


def _e2_cells(matrix):
    return {(cell.mode, cell.branch): cell for cell in matrix.cells}


def test_e2b_completes_both_modes_across_all_schedules_with_matched_design() -> None:
    cells = _e2_cells(_e2_matrix())
    branches = (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    )
    assert set(cells) == {
        (mode, branch)
        for mode in ("syndrome_only", "heralded")
        for branch in branches
    }
    assert all(cell.charge_action.status == "action" for cell in cells.values())
    assert all(cell.charge_action.blue_correction_edges for cell in cells.values())
    for branch in branches:
        plain = cells[("syndrome_only", branch)]
        heralded = cells[("heralded", branch)]
        assert plain.postflux_observation.active_vertices == (
            heralded.postflux_observation.active_vertices
        )
        assert plain.postflux_observation.entanglement_pairs == (
            heralded.postflux_observation.entanglement_pairs
        )
        assert plain.postflux_record.reported_labels == (
            heralded.postflux_record.reported_labels
        )
        assert plain.flux_action.action_digest != heralded.flux_action.action_digest
        assert plain.postflux_record.bound_action_digest == plain.flux_action.action_digest
        assert (
            heralded.postflux_record.bound_action_digest
            == heralded.flux_action.action_digest
        )


def test_e2b_next_round_attaches_only_after_public_charge_completion() -> None:
    cells = _e2_cells(_e2_matrix())
    assert any(cell.advanced_state_digest is not None for cell in cells.values())
    assert any(cell.advanced_state_digest is None for cell in cells.values())
    for cell in cells.values():
        assert len(cell.completion_state_digest) == 64
        if cell.next_round is None:
            assert cell.advanced_state_digest is None
        else:
            assert cell.next_round == cell.policy_request.decision_round + 1
            assert len(cell.advanced_state_digest) == 64


def test_e2c_future_only_change_preserves_causal_completed_transitions() -> None:
    base = _e2_cells(_e2_matrix())
    changed = _e2_cells(_e2_matrix(future_herald=True))
    for mode in ("syndrome_only", "heralded"):
        for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
            left = base[(mode, branch)]
            right = changed[(mode, branch)]
            assert left.policy_request == right.policy_request
            assert left.flux_action == right.flux_action
            assert left.postflux_record == right.postflux_record
            assert left.postflux_observation == right.postflux_observation
            assert left.charge_action == right.charge_action
            assert left.completion_state_digest == right.completion_state_digest
        assert base[(mode, "offline_full_history")].noncausal
        assert changed[(mode, "offline_full_history")].noncausal
        assert (
            base[(mode, "offline_full_history")].completion_state_digest
            != changed[(mode, "offline_full_history")].completion_state_digest
        )


def test_e2c_private_truth_change_and_replay_preserve_every_public_cell() -> None:
    first = _e2_matrix()
    assert first == _e2_matrix(alternate_truth=True)
    assert first == _e2_matrix()


def test_e2c_parity_inconsistent_postflux_support_fails_closed() -> None:
    def odd_provider(invocation):
        hidden = project_post_action_charge_state(
            trial_id="i2-trial",
            round=invocation.report.round,
            charge_labels={0: CHARGE},
            bound_action_digest=invocation.flux_action.action_digest,
        )
        return E2PostFluxFixture(
            record=perfect_report(hidden),
            active_vertices=(0,),
            entanglement_pairs=(),
        )

    with pytest.raises(ValueError, match="parity support"):
        run_e2_completion_matrix(
            trial_id="i2-trial",
            record=_matrix_record(),
            check_positions=tuple((site,) for site in range(VERTICES)),
            geometry=_matrix_geometry(),
            postflux_provider=odd_provider,
            size=2,
        )


def test_e2_public_runner_signature_requires_external_postflux_provider() -> None:
    assert set(inspect.signature(run_e2_completion_matrix).parameters) == {
        "trial_id",
        "record",
        "check_positions",
        "geometry",
        "postflux_provider",
        "size",
        "connectivity_radius",
    }
