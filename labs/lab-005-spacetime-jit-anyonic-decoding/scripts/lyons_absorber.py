"""Deterministic absorber geometry for the Lyons--Brown schedule preflight.

This module implements only the source-level geometry and measurement
interfaces needed to test the just-in-time state machine:

* inclusive integer spacetime boxes with the L-infinity metric;
* explicit absorber opening and termination;
* the three direct-link restrictions of Lyons--Brown Theorem 4; and
* a recorded D(Z3) neutrality measurement which can update schedule state.

It does not implement microscopic gauging circuits, derive detector clusters
from circuit noise, or reproduce the paper's threshold theorem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from schedule_state import ExplicitScheduleState, Neutrality, ScheduledCluster


AbsorberKind = Literal[
    "spatial_boundary",
    "temporal_boundary",
    "nonabelian_worldline",
    "error_cluster",
    "ungauging_wall",
    "gauging_wall",
]


@dataclass(frozen=True)
class SpacetimeBox:
    """Inclusive integer box; all coordinates, including time, are explicit."""

    lower: tuple[int, ...]
    upper: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.lower or len(self.lower) != len(self.upper):
            raise ValueError("box bounds must have the same nonzero dimension")
        if any(lo > hi for lo, hi in zip(self.lower, self.upper, strict=True)):
            raise ValueError("box lower bound cannot exceed its upper bound")

    @property
    def dimension(self) -> int:
        return len(self.lower)

    def linf_distance(self, other: "SpacetimeBox") -> int:
        """Minimum L-infinity distance between two inclusive boxes."""

        if self.dimension != other.dimension:
            raise ValueError("L-infinity distance requires equal dimensions")
        gaps = (
            max(lo_a - hi_b, lo_b - hi_a, 0)
            for lo_a, hi_a, lo_b, hi_b in zip(
                self.lower,
                self.upper,
                other.lower,
                other.upper,
                strict=True,
            )
        )
        return max(gaps)


@dataclass
class AbsorbingRegion:
    absorber_id: str
    kind: AbsorberKind
    bounds: SpacetimeBox
    opened_round: int
    closed_round: int | None = None
    owner_cluster: str | None = None

    def active_at(self, current_round: int) -> bool:
        return self.opened_round <= current_round and (
            self.closed_round is None or current_round < self.closed_round
        )


@dataclass(frozen=True)
class AbsorberLifecycleEvent:
    absorber_id: str
    round: int
    action: Literal["open", "terminate"]


@dataclass
class AbsorberGeometry:
    """Causal registry of active absorbing regions."""

    regions: dict[str, AbsorbingRegion] = field(default_factory=dict)
    event_log: list[AbsorberLifecycleEvent] = field(default_factory=list)
    last_round: int = -1

    def open(self, region: AbsorbingRegion, *, current_round: int) -> None:
        if current_round < self.last_round:
            raise ValueError("absorber lifecycle cannot move backwards")
        if not region.absorber_id or region.absorber_id in self.regions:
            raise ValueError("absorber identifier must be new and nonempty")
        if region.opened_round != current_round or region.opened_round < 0:
            raise ValueError("absorber must open at the current causal round")
        if region.closed_round is not None:
            raise ValueError("a newly opened absorber cannot already be terminated")
        self.regions[region.absorber_id] = region
        self.event_log.append(
            AbsorberLifecycleEvent(region.absorber_id, current_round, "open")
        )
        self.last_round = current_round

    def terminate(self, absorber_id: str, *, current_round: int) -> None:
        if current_round < self.last_round:
            raise ValueError("absorber lifecycle cannot move backwards")
        region = self.regions[absorber_id]
        if not region.active_at(current_round):
            raise ValueError("only an active absorber can be terminated")
        region.closed_round = current_round
        self.event_log.append(
            AbsorberLifecycleEvent(absorber_id, current_round, "terminate")
        )
        self.last_round = current_round

    def active(self, *, current_round: int) -> tuple[AbsorbingRegion, ...]:
        if current_round < 0:
            raise ValueError("current round must be nonnegative")
        return tuple(
            self.regions[key]
            for key in sorted(self.regions)
            if self.regions[key].active_at(current_round)
        )

    def nearest_distance(
        self,
        cluster_bounds: SpacetimeBox,
        *,
        current_round: int,
        exclude_ids: tuple[str, ...] = (),
    ) -> tuple[int, str]:
        excluded = set(exclude_ids)
        candidates = [
            region
            for region in self.active(current_round=current_round)
            if region.absorber_id not in excluded
        ]
        if not candidates:
            raise ValueError("no active absorber is available for this cluster")
        if any(region.bounds.dimension != cluster_bounds.dimension for region in candidates):
            raise ValueError("all active absorber boxes must match cluster dimension")
        ranked = sorted(
            (cluster_bounds.linf_distance(region.bounds), region.absorber_id)
            for region in candidates
        )
        return ranked[0]


def bind_nearest_absorber(
    cluster: ScheduledCluster,
    cluster_bounds: SpacetimeBox,
    geometry: AbsorberGeometry,
    *,
    current_round: int,
    exclude_ids: tuple[str, ...] = (),
) -> str:
    """Populate the schedule gate from explicit active absorber geometry."""

    distance, absorber_id = geometry.nearest_distance(
        cluster_bounds,
        current_round=current_round,
        exclude_ids=exclude_ids,
    )
    if distance <= 0:
        raise ValueError("a scheduled cluster must be separated from its absorber")
    cluster.nearest_absorber_distance = distance
    return absorber_id


@dataclass(frozen=True)
class LinkedCluster:
    cluster_id: str
    level: int

    def __post_init__(self) -> None:
        if not self.cluster_id or self.level < 0:
            raise ValueError("linked cluster needs a nonempty id and nonnegative level")


@dataclass
class LinkedClusterForest:
    """Theorem-4 direct-link invariants, independent of cluster discovery."""

    clusters: dict[str, LinkedCluster] = field(default_factory=dict)
    parent: dict[str, str] = field(default_factory=dict)

    def register(self, cluster: LinkedCluster) -> None:
        if cluster.cluster_id in self.clusters:
            raise ValueError("linked cluster identifier must be unique")
        self.clusters[cluster.cluster_id] = cluster

    def link(self, child_id: str, parent_id: str) -> None:
        child = self.clusters[child_id]
        parent = self.clusters[parent_id]
        if child.level >= parent.level:
            raise ValueError("a direct link must point to a strictly larger cluster")
        if child_id in self.parent:
            raise ValueError("a cluster can be directly linked to only one larger cluster")
        if any(
            existing_parent == parent_id
            and self.clusters[existing_child].level == child.level
            for existing_child, existing_parent in self.parent.items()
        ):
            raise ValueError("an absorber can have only one direct child per level")
        cursor = parent_id
        while cursor in self.parent:
            cursor = self.parent[cursor]
            if cursor == child_id:
                raise ValueError("direct links cannot form a cycle")
        self.parent[child_id] = parent_id


@dataclass(frozen=True)
class NeutralityMeasurement:
    cluster_id: str
    region_id: str
    round: int
    e_parity: int
    m_parity: int

    def __post_init__(self) -> None:
        if self.round < 0 or self.e_parity not in (0, 1) or self.m_parity not in (0, 1):
            raise ValueError("neutrality measurement needs a causal round and binary parities")

    @property
    def neutrality(self) -> Neutrality:
        return "neutral" if (self.e_parity, self.m_parity) == (0, 0) else "nonneutral"


@dataclass
class NeutralityMeasurementLog:
    """Validate a local D(Z3) readout before updating schedule state."""

    measurements: list[NeutralityMeasurement] = field(default_factory=list)

    def apply(
        self,
        measurement: NeutralityMeasurement,
        *,
        geometry: AbsorberGeometry,
        schedule: ExplicitScheduleState,
        current_round: int,
    ) -> Neutrality:
        if measurement.round != current_round:
            raise ValueError("neutrality measurement must belong to the current round")
        region = geometry.regions[measurement.region_id]
        if region.kind != "ungauging_wall" or not region.active_at(current_round):
            raise ValueError("neutrality is measurable only in an active ungauged region")
        if region.owner_cluster != measurement.cluster_id:
            raise ValueError("neutrality measurement must match the region owner")
        cluster = schedule.clusters[measurement.cluster_id]
        if cluster.region != "d_z3" or cluster.ungauged_at is None:
            raise ValueError("schedule cluster is not in the ungauged D(Z3) phase")
        if current_round < cluster.ungauged_at:
            raise ValueError("neutrality measurement cannot precede ungauging")
        schedule.set_neutrality(measurement.cluster_id, measurement.neutrality)
        self.measurements.append(measurement)
        return measurement.neutrality
