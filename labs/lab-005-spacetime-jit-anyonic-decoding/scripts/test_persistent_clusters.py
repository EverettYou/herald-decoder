from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox  # noqa: E402
from persistent_clusters import PersistentClusterTracker  # noqa: E402
from schedule_state import DeferredMeasurementRecord, ExplicitScheduleState  # noqa: E402
from spacetime_record import CausalRecordPrefix, build_record_from_fault_masks  # noqa: E402


def _prefix(detectors: list[list[int]]) -> CausalRecordPrefix:
    values = np.asarray(detectors, dtype=bool)
    rounds, checks = values.shape
    return CausalRecordPrefix(
        final_round=rounds,
        syndrome_readout=np.zeros((rounds + 1, checks), dtype=bool),
        syndrome_detectors=values,
        herald_readout=np.zeros((rounds + 1, 0), dtype=bool),
    )


def test_single_component_retains_identifier_when_extended() -> None:
    tracker = PersistentClusterTracker(((0,), (1,)))
    first = tracker.update(_prefix([[1, 0]]))[0]
    second = tracker.update(_prefix([[1, 0], [0, 1]]))[0]
    assert first.persistent_id == second.persistent_id == "pc0001"
    assert tracker.event_origin == {"d1:c0": "pc0001", "d2:c1": "pc0001"}
    assert [event.action for event in tracker.event_log] == ["create", "extend"]


def test_disconnected_new_component_gets_new_persistent_identifier() -> None:
    tracker = PersistentClusterTracker(((0,), (5,)))
    tracker.update(_prefix([[1, 0]]))
    clusters = tracker.update(_prefix([[1, 0], [0, 1]]))
    assert [cluster.persistent_id for cluster in clusters] == ["pc0001", "pc0002"]
    assert tracker.event_origin["d2:c1"] == "pc0002"


def test_bridge_event_merges_components_into_earliest_id_with_alias() -> None:
    tracker = PersistentClusterTracker(((0,), (1,), (2,)))
    initial = tracker.update(_prefix([[1, 0, 1]]))
    assert [cluster.persistent_id for cluster in initial] == ["pc0001", "pc0002"]
    merged = tracker.update(_prefix([[1, 0, 1], [0, 1, 0]]))
    assert [cluster.persistent_id for cluster in merged] == ["pc0001"]
    assert merged[0].merged_aliases == ("pc0002",)
    assert tracker.canonical("pc0002") == "pc0001"
    assert tracker.event_origin["d1:c2"] == "pc0002"
    assert set(tracker.current_owner.values()) == {"pc0001"}
    assert tracker.event_log[-1].action == "merge"


def test_removed_or_changed_historical_event_is_rejected() -> None:
    tracker = PersistentClusterTracker(((0,), (1,)))
    tracker.update(_prefix([[1, 0]]))
    with pytest.raises(ValueError, match="append-only"):
        tracker.update(_prefix([[0, 0], [0, 1]]))

    changed_positions = PersistentClusterTracker(((0,), (1,)))
    changed_positions.update(_prefix([[1, 0]]))
    changed_positions.check_positions = ((3,), (1,))
    with pytest.raises(ValueError, match="changed"):
        changed_positions.update(_prefix([[1, 0], [0, 1]]))


def test_idempotent_refresh_does_not_duplicate_event_origin() -> None:
    tracker = PersistentClusterTracker(((0,),))
    tracker.update(_prefix([[1]]))
    tracker.update(_prefix([[1]]))
    assert tracker.event_origin == {"d1:c0": "pc0001"}
    assert tracker.event_log[-1].action == "refresh"


def test_absorber_candidates_refresh_as_lifecycle_changes() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "near", "spatial_boundary", SpacetimeBox((2, 0), (2, 3)), 0
        ),
        current_round=0,
    )
    tracker = PersistentClusterTracker(((0,),))
    first = tracker.update(_prefix([[1]]), geometry=geometry)[0]
    assert first.snapshot.absorber_link_candidates == ("near",)
    geometry.open(
        AbsorbingRegion(
            "owned", "error_cluster", SpacetimeBox((0, 0), (0, 3)), 1,
            owner_cluster="pc0001",
        ),
        current_round=1,
    )
    owned_excluded = tracker.update(_prefix([[1]]), geometry=geometry)[0]
    assert owned_excluded.snapshot.nearest_absorber_id == "near"
    geometry.terminate("near", current_round=2)
    second = tracker.update(_prefix([[1], [0]]), geometry=geometry)[0]
    assert second.persistent_id == first.persistent_id
    assert second.snapshot.absorber_link_candidates == ()
    assert second.snapshot.nearest_absorber_id is None


def test_persistent_identifier_drives_current_frontier_schedule_handoff() -> None:
    truth = np.asarray([[0], [1]], dtype=bool)
    herald = np.zeros((2, 0), dtype=bool)
    record = build_record_from_fault_masks(
        truth, np.zeros_like(truth), herald, herald
    )
    prefix = record.causal_prefix(1)
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "boundary", "spatial_boundary", SpacetimeBox((3, 0), (3, 3)), 0
        ),
        current_round=0,
    )
    tracker = PersistentClusterTracker(((0,),))
    tracked = tracker.update(prefix, geometry=geometry)[0]
    scheduled = tracked.to_scheduled_cluster(current_round=1)
    assert scheduled.cluster_id == "pc0001"
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(scheduled, current_round=1)
    decoder_record = DeferredMeasurementRecord.from_prefix(prefix)
    transition = schedule.step(current_round=1, record=decoder_record)[0]
    assert (transition.cluster_id, transition.action) == ("pc0001", "defer")
