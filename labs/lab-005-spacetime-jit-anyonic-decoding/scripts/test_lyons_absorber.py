from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lyons_absorber import (  # noqa: E402
    AbsorberGeometry,
    AbsorbingRegion,
    LinkedCluster,
    LinkedClusterForest,
    NeutralityMeasurement,
    NeutralityMeasurementLog,
    SpacetimeBox,
    bind_nearest_absorber,
)
from schedule_state import ExplicitScheduleState, ScheduledCluster  # noqa: E402


def _region(
    absorber_id: str,
    kind: str,
    bounds: SpacetimeBox,
    round_: int,
    owner: str | None = None,
) -> AbsorbingRegion:
    return AbsorbingRegion(absorber_id, kind, bounds, round_, owner_cluster=owner)


def test_linf_nearest_absorber_binds_schedule_gate() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region("far", "spatial_boundary", SpacetimeBox((8, 8, 0), (8, 8, 4)), 0),
        current_round=0,
    )
    geometry.open(
        _region("near", "nonabelian_worldline", SpacetimeBox((5, 1, 0), (5, 1, 4)), 0),
        current_round=0,
    )
    cluster = ScheduledCluster("c0", (0,), 0, 1, 99, "d_s3")
    selected = bind_nearest_absorber(
        cluster,
        SpacetimeBox((1, 1, 2), (2, 2, 3)),
        geometry,
        current_round=3,
    )
    assert (selected, cluster.nearest_absorber_distance) == ("near", 3)


def test_terminated_absorber_is_not_a_future_distance_candidate() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region("short", "error_cluster", SpacetimeBox((3, 0, 0), (3, 0, 2)), 0),
        current_round=0,
    )
    geometry.open(
        _region("long", "spatial_boundary", SpacetimeBox((7, 0, 0), (7, 0, 8)), 0),
        current_round=0,
    )
    assert geometry.nearest_distance(
        SpacetimeBox((0, 0, 1), (0, 0, 1)), current_round=1
    ) == (3, "short")
    geometry.terminate("short", current_round=2)
    assert geometry.nearest_distance(
        SpacetimeBox((0, 0, 3), (0, 0, 3)), current_round=3
    ) == (7, "long")
    assert [event.action for event in geometry.event_log] == [
        "open",
        "open",
        "terminate",
    ]


def test_nearest_distance_can_exclude_own_absorbing_region() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region("own", "error_cluster", SpacetimeBox((0, 0), (1, 1)), 0, "c0"),
        current_round=0,
    )
    geometry.open(
        _region("boundary", "spatial_boundary", SpacetimeBox((5, 0), (5, 5)), 0),
        current_round=0,
    )
    distance = geometry.nearest_distance(
        SpacetimeBox((0, 0), (1, 1)), current_round=0, exclude_ids=("own",)
    )
    assert distance == (4, "boundary")


def test_link_forest_enforces_all_three_direct_link_restrictions() -> None:
    forest = LinkedClusterForest()
    for cluster in (
        LinkedCluster("small_a", 0),
        LinkedCluster("small_b", 0),
        LinkedCluster("medium", 1),
        LinkedCluster("large", 2),
    ):
        forest.register(cluster)
    forest.link("small_a", "medium")
    forest.link("medium", "large")
    with pytest.raises(ValueError, match="strictly larger"):
        forest.link("large", "medium")
    with pytest.raises(ValueError, match="only one larger"):
        forest.link("small_a", "large")
    with pytest.raises(ValueError, match="one direct child per level"):
        forest.link("small_b", "medium")


def test_neutrality_measurement_requires_active_owned_ungauged_region() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region(
            "u0",
            "ungauging_wall",
            SpacetimeBox((0, 0, 2), (2, 2, 4)),
            2,
            "c0",
        ),
        current_round=2,
    )
    schedule = ExplicitScheduleState("lyons_brown")
    cluster = ScheduledCluster("c0", (0,), 0, 1, 1, "d_z3", ungauged_at=2)
    schedule.register(cluster, current_round=2)
    log = NeutralityMeasurementLog()
    result = log.apply(
        NeutralityMeasurement("c0", "u0", 2, 0, 0),
        geometry=geometry,
        schedule=schedule,
        current_round=2,
    )
    assert result == "neutral"
    assert schedule.clusters["c0"].neutrality == "neutral"


def test_nonneutral_measurement_and_closed_region_rejection() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region(
            "u0",
            "ungauging_wall",
            SpacetimeBox((0, 0, 1), (1, 1, 3)),
            1,
            "c0",
        ),
        current_round=1,
    )
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 0, 1, 1, "d_z3", ungauged_at=1),
        current_round=1,
    )
    log = NeutralityMeasurementLog()
    assert log.apply(
        NeutralityMeasurement("c0", "u0", 1, 1, 0),
        geometry=geometry,
        schedule=schedule,
        current_round=1,
    ) == "nonneutral"
    geometry.terminate("u0", current_round=2)
    with pytest.raises(ValueError, match="active ungauged region"):
        log.apply(
            NeutralityMeasurement("c0", "u0", 2, 0, 0),
            geometry=geometry,
            schedule=schedule,
            current_round=2,
        )


def test_neutrality_rejects_future_round_and_wrong_owner() -> None:
    geometry = AbsorberGeometry()
    geometry.open(
        _region(
            "u0",
            "ungauging_wall",
            SpacetimeBox((0, 0, 1), (1, 1, 3)),
            1,
            "other",
        ),
        current_round=1,
    )
    schedule = ExplicitScheduleState("lyons_brown")
    schedule.register(
        ScheduledCluster("c0", (0,), 0, 1, 1, "d_z3", ungauged_at=1),
        current_round=1,
    )
    log = NeutralityMeasurementLog()
    with pytest.raises(ValueError, match="current round"):
        log.apply(
            NeutralityMeasurement("c0", "u0", 2, 0, 0),
            geometry=geometry,
            schedule=schedule,
            current_round=1,
        )
    with pytest.raises(ValueError, match="region owner"):
        log.apply(
            NeutralityMeasurement("c0", "u0", 1, 0, 0),
            geometry=geometry,
            schedule=schedule,
            current_round=1,
        )
