from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from schedule_state import (  # noqa: E402
    DeferredMeasurementRecord,
    ExplicitScheduleState,
    ScheduledCluster,
)
from spacetime_record import build_record_from_fault_masks  # noqa: E402


def _detector_prefix() -> tuple[DeferredMeasurementRecord, np.ndarray]:
    truth = np.asarray([[0, 0], [1, 0]], dtype=bool)
    herald = np.zeros((2, 0), dtype=bool)
    record = build_record_from_fault_masks(
        truth, np.zeros_like(truth), herald, herald
    )
    return DeferredMeasurementRecord.from_prefix(record.causal_prefix(1)), truth[1]


def test_deferred_measurement_reversal_moves_detector_to_next_round() -> None:
    record, raw_latest = _detector_prefix()
    assert record.detectors[:, 0].tolist() == [True]
    record.defer_current(cluster_id="c0", current_round=1, vertices=(0,))
    assert record.detectors[:, 0].tolist() == [False]
    record.append_round(raw_latest)
    assert record.detectors[:, 0].tolist() == [False, True]
    assert record.event_log[0].action == "reverse_latest_readout"


def test_deferred_record_rejects_past_or_absent_detector_event() -> None:
    record, _ = _detector_prefix()
    with pytest.raises(ValueError, match="latest detector round"):
        record.defer_current(cluster_id="c0", current_round=0, vertices=(0,))
    with pytest.raises(ValueError, match="current detector event"):
        record.defer_current(cluster_id="c1", current_round=1, vertices=(1,))


def test_jing_branch_retains_then_commits_without_record_reversal() -> None:
    schedule = ExplicitScheduleState("jing_ilp")
    schedule.register(
        ScheduledCluster("c0", (0,), 0, 2, 9, "d_s3"), current_round=0
    )
    assert schedule.step(current_round=1)[0].action == "defer"
    assert schedule.step(current_round=2)[0].action == "commit"
    assert schedule.clusters == {}
    assert [event.action for event in schedule.event_log] == ["defer", "commit"]


def test_lyons_branch_defer_ungauge_wait_and_neutral_regauge() -> None:
    record, raw_latest = _detector_prefix()
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 1, 1, 1, "d_s3"), current_round=1
    )
    assert schedule.step(current_round=1, record=record)[0].action == "defer"
    record.append_round(raw_latest)
    assert schedule.step(current_round=2, record=record)[0].action == "ungauge"
    assert schedule.clusters["c0"].region == "d_z3"
    schedule.set_neutrality("c0", "neutral")
    assert schedule.step(current_round=2, record=record)[0].action == "defer"
    record.append_round(raw_latest)
    final = schedule.step(current_round=3, record=record)[0]
    assert final.action == "correct_regauge"
    assert final.region_after == "d_s3"
    assert schedule.clusters == {}


def test_lyons_boundary_ungauges_and_nonneutral_cluster_defers() -> None:
    truth = np.asarray([[0], [1], [0]], dtype=bool)
    herald = np.zeros((3, 0), dtype=bool)
    base = build_record_from_fault_masks(
        truth, np.zeros_like(truth), herald, herald
    )
    record = DeferredMeasurementRecord.from_prefix(base.causal_prefix(2))
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 1, 1, 1, "boundary"), current_round=2
    )
    first = schedule.step(current_round=2, record=record)[0]
    assert (first.action, first.region_before, first.region_after) == (
        "ungauge",
        "boundary",
        "d_z3",
    )
    schedule.set_neutrality("c0", "nonneutral")
    # The ungauging boundary resets age, so the cluster first defers by age.
    assert schedule.step(current_round=2, record=record)[0].action == "defer"
    record.append_round(np.asarray([0], dtype=bool))
    nonneutral = schedule.step(current_round=3, record=record)[0]
    assert nonneutral.action == "defer_nonneutral"
    assert schedule.clusters["c0"].region == "d_z3"


def test_schedule_rejects_future_registration_and_branch_record_mismatch() -> None:
    schedule = ExplicitScheduleState("lyons_brown")
    with pytest.raises(ValueError, match="causally available"):
        schedule.register(
            ScheduledCluster("c0", (0,), 2, 1, 1, "d_s3"), current_round=1
        )
    schedule.register(
        ScheduledCluster("c0", (0,), 1, 1, 1, "d_s3"), current_round=1
    )
    with pytest.raises(ValueError, match="current decoder record"):
        schedule.step(current_round=1)
