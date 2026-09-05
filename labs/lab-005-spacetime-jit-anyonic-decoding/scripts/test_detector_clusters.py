from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from detector_clusters import build_detector_clusters  # noqa: E402
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox  # noqa: E402
from schedule_state import DeferredMeasurementRecord, ExplicitScheduleState  # noqa: E402
from spacetime_record import CausalRecordPrefix, build_record_from_fault_masks  # noqa: E402


def _prefix(detectors: list[list[int]], *, final_round: int) -> CausalRecordPrefix:
    detector_array = np.asarray(detectors, dtype=bool)
    checks = detector_array.shape[1]
    return CausalRecordPrefix(
        final_round=final_round,
        syndrome_readout=np.zeros((final_round + 1, checks), dtype=bool),
        syndrome_detectors=detector_array,
        herald_readout=np.zeros((final_round + 1, 0), dtype=bool),
    )


def test_causal_prefix_builds_deterministic_spacetime_components() -> None:
    prefix = _prefix([[1, 1, 0], [0, 1, 0], [0, 0, 1]], final_round=3)
    clusters = build_detector_clusters(
        prefix, check_positions=((0,), (1,), (5,)), connectivity_radius=1
    )
    assert [cluster.cluster_id for cluster in clusters] == [
        "cluster:d1:c0",
        "cluster:d3:c2",
    ]
    assert [event.event_id for event in clusters[0].events] == [
        "d1:c0",
        "d1:c1",
        "d2:c1",
    ]


def test_cluster_summaries_report_age_extent_and_symmetric_separation() -> None:
    prefix = _prefix([[1, 0, 0], [0, 0, 0], [0, 1, 1], [0, 0, 0]], final_round=4)
    clusters = build_detector_clusters(
        prefix, check_positions=((0,), (4,), (5,)), connectivity_radius=1
    )
    first, second = clusters
    assert (first.oldest_round, first.youngest_round, first.age, first.extent) == (1, 1, 3, 1)
    assert (second.oldest_round, second.youngest_round, second.age, second.extent) == (3, 3, 1, 2)
    assert first.nearest_cluster_distance == second.nearest_cluster_distance == 4


def test_active_absorbers_supply_distance_and_geometric_link_candidates() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "near", "spatial_boundary", SpacetimeBox((3, 0), (3, 5)), 0
        ),
        current_round=0,
    )
    geometry.open(
        AbsorbingRegion(
            "far", "spatial_boundary", SpacetimeBox((8, 0), (8, 5)), 0
        ),
        current_round=0,
    )
    cluster = build_detector_clusters(
        _prefix([[1]], final_round=1),
        check_positions=((0,),),
        geometry=geometry,
    )[0]
    assert (cluster.nearest_absorber_distance, cluster.nearest_absorber_id) == (3, "near")
    assert cluster.absorber_link_candidates == ()

    broad = build_detector_clusters(
        _prefix([[1, 1]], final_round=1),
        check_positions=((0,), (1,)),
        geometry=geometry,
    )[0]
    assert broad.extent == 2
    assert broad.absorber_link_candidates == ("near",)


def test_terminated_and_owned_absorbers_are_excluded() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "owned", "error_cluster", SpacetimeBox((0, 0), (0, 3)), 0,
            owner_cluster="cluster:d1:c0",
        ),
        current_round=0,
    )
    geometry.open(
        AbsorbingRegion(
            "closed", "spatial_boundary", SpacetimeBox((2, 0), (2, 3)), 0
        ),
        current_round=0,
    )
    geometry.open(
        AbsorbingRegion(
            "active", "spatial_boundary", SpacetimeBox((5, 0), (5, 3)), 0
        ),
        current_round=0,
    )
    geometry.terminate("closed", current_round=1)
    cluster = build_detector_clusters(
        _prefix([[1], [0]], final_round=2),
        check_positions=((0,),),
        geometry=geometry,
    )[0]
    assert (cluster.nearest_absorber_distance, cluster.nearest_absorber_id) == (5, "active")


def test_schedule_handoff_requires_current_frontier_and_active_absorber() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "boundary", "spatial_boundary", SpacetimeBox((4, 0), (4, 4)), 0
        ),
        current_round=0,
    )
    old, current = build_detector_clusters(
        _prefix([[1, 0], [0, 1]], final_round=2),
        check_positions=((0,), (3,)),
        geometry=geometry,
        connectivity_radius=0,
    )
    with pytest.raises(ValueError, match="current-frontier"):
        old.to_scheduled_cluster(current_round=2)
    scheduled = current.to_scheduled_cluster(current_round=2)
    assert scheduled.detector_vertices == (1,)
    assert scheduled.nearest_absorber_distance == 1


def test_causal_cluster_handoff_drives_public_defer_step() -> None:
    syndrome_truth = np.asarray([[0], [1]], dtype=bool)
    herald = np.zeros((2, 0), dtype=bool)
    record = build_record_from_fault_masks(
        syndrome_truth, np.zeros_like(syndrome_truth), herald, herald
    )
    prefix = record.causal_prefix(1)
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "boundary", "spatial_boundary", SpacetimeBox((3, 0), (3, 3)), 0
        ),
        current_round=0,
    )
    cluster = build_detector_clusters(
        prefix, check_positions=((0,),), geometry=geometry
    )[0]
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(cluster.to_scheduled_cluster(current_round=1), current_round=1)
    decoder_record = DeferredMeasurementRecord.from_prefix(prefix)
    transition = schedule.step(current_round=1, record=decoder_record)[0]
    assert (transition.action, transition.required_age) == ("defer", 3)
    assert decoder_record.detectors[0, 0] == 0


def test_invalid_prefix_and_coordinate_contracts_are_rejected() -> None:
    bad = _prefix([[1]], final_round=1)
    with pytest.raises(ValueError, match="one declared position"):
        build_detector_clusters(bad, check_positions=((0,), (1,)))
    with pytest.raises(ValueError, match="unique"):
        build_detector_clusters(
            _prefix([[1, 0]], final_round=1), check_positions=((0,), (0,))
        )
    malformed = CausalRecordPrefix(
        final_round=2,
        syndrome_readout=np.zeros((2, 1), dtype=bool),
        syndrome_detectors=np.zeros((1, 1), dtype=bool),
        herald_readout=np.zeros((2, 0), dtype=bool),
    )
    with pytest.raises(ValueError, match="extends beyond"):
        build_detector_clusters(malformed, check_positions=((0,),))
