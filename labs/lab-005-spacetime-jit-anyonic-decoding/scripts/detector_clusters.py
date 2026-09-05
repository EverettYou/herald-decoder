"""Causal snapshot construction of detector clusters for Lab 005.

The registered preflight treats detector events as integer spacetime points
and forms connected components under a bounded L-infinity adjacency rule.  It
reports geometry needed by the abstract schedule but does not claim that this
snapshot rule is a unique or optimal reconstruction of the Lyons--Brown
persistent cluster process.
"""

from __future__ import annotations

from dataclasses import dataclass

from lyons_absorber import AbsorberGeometry, SpacetimeBox
from schedule_state import Region, ScheduledCluster
from spacetime_record import CausalRecordPrefix


@dataclass(frozen=True, order=True)
class DetectorEvent:
    event_id: str
    check_index: int
    position: tuple[int, ...]
    round: int

    @property
    def spacetime_position(self) -> tuple[int, ...]:
        return self.position + (self.round,)


@dataclass(frozen=True)
class DetectorCluster:
    cluster_id: str
    events: tuple[DetectorEvent, ...]
    bounds: SpacetimeBox
    oldest_round: int
    youngest_round: int
    age: int
    extent: int
    nearest_cluster_distance: int | None
    nearest_absorber_distance: int | None
    nearest_absorber_id: str | None
    absorber_link_candidates: tuple[str, ...]

    def current_vertices(self, *, current_round: int) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    event.check_index
                    for event in self.events
                    if event.round == current_round
                }
            )
        )

    def to_scheduled_cluster(
        self, *, current_round: int, region: Region = "d_s3"
    ) -> ScheduledCluster:
        vertices = self.current_vertices(current_round=current_round)
        if not vertices:
            raise ValueError("schedule handoff requires a current-frontier event")
        if self.nearest_absorber_distance is None:
            raise ValueError("schedule handoff requires an active absorber distance")
        if self.nearest_absorber_distance <= 0:
            raise ValueError("an overlapping absorber requires merge or phase handling")
        return ScheduledCluster(
            cluster_id=self.cluster_id,
            detector_vertices=vertices,
            youngest_round=self.youngest_round,
            cube_size=self.extent,
            nearest_absorber_distance=self.nearest_absorber_distance,
            region=region,
        )


def _linf_points(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    if len(left) != len(right):
        raise ValueError("spacetime points must share one dimension")
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def _validate_prefix(prefix: CausalRecordPrefix) -> None:
    if prefix.final_round < 0:
        raise ValueError("causal prefix final round must be nonnegative")
    if prefix.syndrome_readout.ndim != 2 or prefix.syndrome_detectors.ndim != 2:
        raise ValueError("causal syndrome arrays must be rank two")
    if prefix.syndrome_readout.shape[0] != prefix.final_round + 1:
        raise ValueError("causal syndrome readout extends beyond its final round")
    if prefix.syndrome_detectors.shape != (
        prefix.final_round,
        prefix.syndrome_readout.shape[1],
    ):
        raise ValueError("causal detector shape disagrees with the prefix horizon")
    if prefix.herald_readout.ndim != 2 or prefix.herald_readout.shape[0] != prefix.final_round + 1:
        raise ValueError("causal herald readout extends beyond its final round")


def build_detector_clusters(
    prefix: CausalRecordPrefix,
    *,
    check_positions: tuple[tuple[int, ...], ...],
    geometry: AbsorberGeometry | None = None,
    connectivity_radius: int = 1,
) -> tuple[DetectorCluster, ...]:
    """Build deterministic connected components from one causal snapshot."""

    _validate_prefix(prefix)
    if connectivity_radius < 0:
        raise ValueError("connectivity radius must be nonnegative")
    checks = prefix.syndrome_detectors.shape[1]
    if len(check_positions) != checks:
        raise ValueError("one declared position is required for each detector check")
    if not check_positions or not check_positions[0]:
        raise ValueError("check positions require a nonzero spatial dimension")
    spatial_dimension = len(check_positions[0])
    if any(len(position) != spatial_dimension for position in check_positions):
        raise ValueError("all check positions must share one dimension")
    if len(set(check_positions)) != len(check_positions):
        raise ValueError("check positions must be unique")

    events: list[DetectorEvent] = []
    for detector_row in range(prefix.final_round):
        event_round = detector_row + 1
        for check_index in range(checks):
            if bool(prefix.syndrome_detectors[detector_row, check_index]):
                events.append(
                    DetectorEvent(
                        event_id=f"d{event_round}:c{check_index}",
                        check_index=check_index,
                        position=tuple(int(value) for value in check_positions[check_index]),
                        round=event_round,
                    )
                )
    if not events:
        return ()

    parent = list(range(len(events)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            return
        smaller, larger = sorted((root_left, root_right))
        parent[larger] = smaller

    for left in range(len(events)):
        for right in range(left + 1, len(events)):
            if _linf_points(
                events[left].spacetime_position,
                events[right].spacetime_position,
            ) <= connectivity_radius:
                union(left, right)

    components: dict[int, list[DetectorEvent]] = {}
    for index, event in enumerate(events):
        components.setdefault(find(index), []).append(event)

    provisional: list[tuple[str, tuple[DetectorEvent, ...], SpacetimeBox, int]] = []
    for members in components.values():
        ordered = tuple(sorted(members))
        points = tuple(event.spacetime_position for event in ordered)
        lower = tuple(min(point[axis] for point in points) for axis in range(spatial_dimension + 1))
        upper = tuple(max(point[axis] for point in points) for axis in range(spatial_dimension + 1))
        bounds = SpacetimeBox(lower, upper)
        extent = max(hi - lo + 1 for lo, hi in zip(lower, upper, strict=True))
        provisional.append((f"cluster:{ordered[0].event_id}", ordered, bounds, extent))
    provisional.sort(key=lambda item: item[0])

    clusters: list[DetectorCluster] = []
    for index, (cluster_id, members, bounds, extent) in enumerate(provisional):
        other_distances = [
            bounds.linf_distance(other_bounds)
            for other_index, (_, _, other_bounds, _) in enumerate(provisional)
            if other_index != index
        ]
        nearest_cluster = min(other_distances) if other_distances else None
        nearest_absorber_distance: int | None = None
        nearest_absorber_id: str | None = None
        link_candidates: tuple[str, ...] = ()
        if geometry is not None:
            candidates = []
            for region in geometry.active(current_round=prefix.final_round):
                if region.owner_cluster == cluster_id:
                    continue
                if region.bounds.dimension != bounds.dimension:
                    raise ValueError("active absorber dimension must match detector spacetime")
                candidates.append((bounds.linf_distance(region.bounds), region.absorber_id))
            candidates.sort()
            if candidates:
                nearest_absorber_distance, nearest_absorber_id = candidates[0]
                link_candidates = tuple(
                    absorber_id
                    for distance, absorber_id in candidates
                    if distance <= 2 * extent
                )
        oldest = min(event.round for event in members)
        youngest = max(event.round for event in members)
        clusters.append(
            DetectorCluster(
                cluster_id=cluster_id,
                events=members,
                bounds=bounds,
                oldest_round=oldest,
                youngest_round=youngest,
                age=prefix.final_round - youngest,
                extent=extent,
                nearest_cluster_distance=nearest_cluster,
                nearest_absorber_distance=nearest_absorber_distance,
                nearest_absorber_id=nearest_absorber_id,
                absorber_link_candidates=link_candidates,
            )
        )
    return tuple(clusters)
