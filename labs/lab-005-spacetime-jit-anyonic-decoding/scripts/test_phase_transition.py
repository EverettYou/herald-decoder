from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lyons_absorber import AbsorberGeometry, NeutralityMeasurement, SpacetimeBox  # noqa: E402
from phase_transition import FusionOutcome, PhaseTransitionAdapter  # noqa: E402
from schedule_state import (  # noqa: E402
    DeferredMeasurementRecord,
    ExplicitScheduleState,
    ScheduleTransition,
    ScheduledCluster,
)
from spacetime_record import build_record_from_fault_masks  # noqa: E402


def _transition(
    action: str,
    *,
    round_: int = 2,
    before: str = "d_s3",
    after: str = "d_z3",
    neutrality: str = "unknown",
) -> ScheduleTransition:
    return ScheduleTransition(
        "lyons_brown", "c0", round_, action, before, after, 1, 1, neutrality
    )


def _ungauged_schedule(neutrality: str = "unknown") -> ExplicitScheduleState:
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 1, 1, 1, "d_z3", neutrality, 2),
        current_round=2,
    )
    return schedule


def test_ungauge_opens_owned_region_and_preserves_supplied_outcome() -> None:
    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    outcome = FusionOutcome(1, 0, "e-sector")
    state = adapter.ungauge(
        _transition("ungauge"),
        bounds=SpacetimeBox((0, 0, 2), (2, 2, 5)),
        supplied_outcome=outcome,
        geometry=geometry,
        current_round=2,
    )
    assert state.d_s3_outcome is outcome
    assert state.d_z3_outcome is outcome
    assert geometry.regions[state.region_id].owner_cluster == "c0"
    assert geometry.regions[state.region_id].active_at(2)
    assert adapter.event_log[0].action == "ungauge_preserve"


def test_neutral_record_then_regauge_terminates_region_once() -> None:
    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    state = adapter.ungauge(
        _transition("ungauge"),
        bounds=SpacetimeBox((0, 0, 2), (2, 2, 4)),
        supplied_outcome=FusionOutcome(0, 0),
        geometry=geometry,
        current_round=2,
    )
    schedule = _ungauged_schedule()
    assert adapter.measure(
        NeutralityMeasurement("c0", state.region_id, 2, 0, 0),
        schedule=schedule,
        geometry=geometry,
        current_round=2,
    ) == "neutral"
    adapter.apply_schedule_transition(
        _transition(
            "correct_regauge",
            round_=3,
            before="d_z3",
            after="d_s3",
            neutrality="neutral",
        ),
        geometry=geometry,
        current_round=3,
    )
    assert state.closed_round == 3
    assert not geometry.regions[state.region_id].active_at(3)
    with pytest.raises(ValueError, match="already closed"):
        adapter.apply_schedule_transition(
            _transition(
                "correct_regauge",
                round_=3,
                before="d_z3",
                after="d_s3",
                neutrality="neutral",
            ),
            geometry=geometry,
            current_round=3,
        )


def test_nonneutral_deferral_keeps_region_active() -> None:
    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    state = adapter.ungauge(
        _transition("ungauge"),
        bounds=SpacetimeBox((0, 0, 2), (2, 2, 5)),
        supplied_outcome=FusionOutcome(0, 1, "m-sector"),
        geometry=geometry,
        current_round=2,
    )
    schedule = _ungauged_schedule()
    adapter.measure(
        NeutralityMeasurement("c0", state.region_id, 2, 0, 1),
        schedule=schedule,
        geometry=geometry,
        current_round=2,
    )
    adapter.apply_schedule_transition(
        _transition(
            "defer_nonneutral",
            round_=3,
            before="d_z3",
            after="d_z3",
            neutrality="nonneutral",
        ),
        geometry=geometry,
        current_round=3,
    )
    assert state.closed_round is None
    assert geometry.regions[state.region_id].active_at(3)


def test_measurement_must_match_preserved_deterministic_outcome() -> None:
    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    state = adapter.ungauge(
        _transition("ungauge"),
        bounds=SpacetimeBox((0, 0, 2), (1, 1, 4)),
        supplied_outcome=FusionOutcome(1, 0, "e-sector"),
        geometry=geometry,
        current_round=2,
    )
    with pytest.raises(ValueError, match="disagrees with supplied outcome"):
        adapter.measure(
            NeutralityMeasurement("c0", state.region_id, 2, 0, 0),
            schedule=_ungauged_schedule(),
            geometry=geometry,
            current_round=2,
        )


def test_invalid_phase_order_and_duplicate_region_are_rejected() -> None:
    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    with pytest.raises(ValueError, match="only a Lyons-Brown ungauge"):
        adapter.ungauge(
            _transition("defer"),
            bounds=SpacetimeBox((0, 0), (1, 1)),
            supplied_outcome=FusionOutcome(0, 0),
            geometry=geometry,
            current_round=2,
        )
    adapter.ungauge(
        _transition("ungauge"),
        bounds=SpacetimeBox((0, 0), (1, 1)),
        supplied_outcome=FusionOutcome(0, 0),
        geometry=geometry,
        current_round=2,
    )
    with pytest.raises(ValueError, match="only one phase-transition region"):
        adapter.ungauge(
            _transition("ungauge"),
            bounds=SpacetimeBox((0, 0), (1, 1)),
            supplied_outcome=FusionOutcome(0, 0),
            geometry=geometry,
            current_round=2,
        )


def test_public_schedule_trace_drives_lifecycle_without_truth_access() -> None:
    truth = np.asarray([[0], [1], [1]], dtype=bool)
    herald = np.zeros((3, 0), dtype=bool)
    base = build_record_from_fault_masks(
        truth, np.zeros_like(truth), herald, herald
    )
    record = DeferredMeasurementRecord.from_prefix(base.causal_prefix(2))
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 1, 1, 1, "d_s3"), current_round=2
    )
    ungauge = schedule.step(current_round=2, record=record)[0]
    assert ungauge.action == "ungauge"

    geometry = AbsorberGeometry()
    adapter = PhaseTransitionAdapter()
    state = adapter.ungauge(
        ungauge,
        bounds=SpacetimeBox((0, 0, 2), (1, 1, 4)),
        supplied_outcome=FusionOutcome(0, 0),
        geometry=geometry,
        current_round=2,
    )
    adapter.measure(
        NeutralityMeasurement("c0", state.region_id, 2, 0, 0),
        schedule=schedule,
        geometry=geometry,
        current_round=2,
    )
    record.append_round(np.asarray([1], dtype=bool))
    regauge = schedule.step(current_round=3, record=record)[0]
    assert regauge.action == "correct_regauge"
    adapter.apply_schedule_transition(
        regauge, geometry=geometry, current_round=3
    )
    assert [event.action for event in adapter.event_log] == [
        "ungauge_preserve",
        "measure_neutrality",
        "correct_regauge",
    ]
    assert not geometry.regions[state.region_id].active_at(3)
