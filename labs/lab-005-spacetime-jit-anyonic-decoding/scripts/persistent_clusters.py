"""Persistent state over causal detector-cluster snapshots.

The tracker preserves raw event history, assigns stable identifiers, and
canonicalizes append-only component merges.  It deliberately does not support
deletion, retrospective record rewriting, or cluster splitting.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from detector_clusters import DetectorCluster, DetectorEvent, build_detector_clusters
from lyons_absorber import AbsorberGeometry
from schedule_state import Region, ScheduledCluster
from spacetime_record import CausalRecordPrefix


@dataclass(frozen=True)
class PersistentCluster:
    persistent_id: str
    snapshot: DetectorCluster
    merged_aliases: tuple[str, ...] = ()

    def to_scheduled_cluster(
        self, *, current_round: int, region: Region = "d_s3"
    ) -> ScheduledCluster:
        ephemeral = self.snapshot.to_scheduled_cluster(
            current_round=current_round, region=region
        )
        return ScheduledCluster(
            cluster_id=self.persistent_id,
            detector_vertices=ephemeral.detector_vertices,
            youngest_round=ephemeral.youngest_round,
            cube_size=ephemeral.cube_size,
            nearest_absorber_distance=ephemeral.nearest_absorber_distance,
            region=ephemeral.region,
        )


@dataclass(frozen=True)
class PersistentClusterEvent:
    round: int
    persistent_id: str
    action: Literal["create", "extend", "merge", "refresh"]
    new_event_ids: tuple[str, ...]
    merged_aliases: tuple[str, ...]


@dataclass
class PersistentClusterTracker:
    check_positions: tuple[tuple[int, ...], ...]
    connectivity_radius: int = 1
    known_events: dict[str, DetectorEvent] = field(default_factory=dict)
    event_origin: dict[str, str] = field(default_factory=dict)
    current_owner: dict[str, str] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    active: dict[str, PersistentCluster] = field(default_factory=dict)
    event_log: list[PersistentClusterEvent] = field(default_factory=list)
    last_round: int = -1
    next_identifier: int = 1

    def __post_init__(self) -> None:
        if self.connectivity_radius < 0:
            raise ValueError("connectivity radius must be nonnegative")

    def _allocate(self) -> str:
        identifier = f"pc{self.next_identifier:04d}"
        self.next_identifier += 1
        return identifier

    def canonical(self, identifier: str) -> str:
        seen: set[str] = set()
        while identifier in self.aliases:
            if identifier in seen:
                raise AssertionError("persistent cluster alias cycle")
            seen.add(identifier)
            identifier = self.aliases[identifier]
        return identifier

    def update(
        self,
        prefix: CausalRecordPrefix,
        *,
        geometry: AbsorberGeometry | None = None,
    ) -> tuple[PersistentCluster, ...]:
        if prefix.final_round < self.last_round:
            raise ValueError("persistent tracker cannot move backwards")
        snapshots = build_detector_clusters(
            prefix,
            check_positions=self.check_positions,
            geometry=None,
            connectivity_radius=self.connectivity_radius,
        )
        visible = {
            event.event_id: event
            for snapshot in snapshots
            for event in snapshot.events
        }
        missing = set(self.known_events).difference(visible)
        if missing:
            raise ValueError("causal detector history must be append-only")
        for event_id, prior in self.known_events.items():
            if visible[event_id] != prior:
                raise ValueError("previously observed detector event changed")

        owner_component_count: dict[str, int] = {}
        planned: list[
            tuple[DetectorCluster, str, tuple[str, ...], tuple[str, ...], str]
        ] = []
        for snapshot in snapshots:
            event_ids = tuple(event.event_id for event in snapshot.events)
            new_ids = tuple(event_id for event_id in event_ids if event_id not in self.known_events)
            prior_owners = tuple(
                sorted(
                    {
                        self.canonical(self.current_owner[event_id])
                        for event_id in event_ids
                        if event_id in self.current_owner
                    }
                )
            )
            for owner in prior_owners:
                owner_component_count[owner] = owner_component_count.get(owner, 0) + 1
            if not prior_owners:
                persistent_id = self._allocate()
                aliases: tuple[str, ...] = ()
                action = "create"
            elif len(prior_owners) == 1:
                persistent_id = prior_owners[0]
                aliases = ()
                action = "extend" if new_ids else "refresh"
            else:
                persistent_id = min(prior_owners)
                aliases = tuple(owner for owner in prior_owners if owner != persistent_id)
                action = "merge"
            planned.append((snapshot, persistent_id, aliases, new_ids, action))

        split = [owner for owner, count in owner_component_count.items() if count > 1]
        if split:
            raise ValueError("append-only fixed-radius clusters cannot split")

        for _, persistent_id, merged_aliases, _, _ in planned:
            for alias in merged_aliases:
                self.aliases[alias] = persistent_id
            if merged_aliases:
                merged_set = set(merged_aliases)
                for event_id, owner in tuple(self.current_owner.items()):
                    if self.canonical(owner) == persistent_id or owner in merged_set:
                        self.current_owner[event_id] = persistent_id

        next_active: dict[str, PersistentCluster] = {}
        for snapshot, persistent_id, merged_aliases, new_ids, action in planned:
            if geometry is not None:
                candidates: list[tuple[int, str]] = []
                for region in geometry.active(current_round=prefix.final_round):
                    if (
                        region.owner_cluster is not None
                        and self.canonical(region.owner_cluster) == persistent_id
                    ):
                        continue
                    if region.bounds.dimension != snapshot.bounds.dimension:
                        raise ValueError(
                            "active absorber dimension must match detector spacetime"
                        )
                    candidates.append(
                        (
                            snapshot.bounds.linf_distance(region.bounds),
                            region.absorber_id,
                        )
                    )
                candidates.sort()
                snapshot = replace(
                    snapshot,
                    nearest_absorber_distance=(
                        candidates[0][0] if candidates else None
                    ),
                    nearest_absorber_id=(candidates[0][1] if candidates else None),
                    absorber_link_candidates=tuple(
                        absorber_id
                        for distance, absorber_id in candidates
                        if distance <= 2 * snapshot.extent
                    ),
                )
            all_aliases = tuple(
                sorted(
                    {
                        alias
                        for alias in self.aliases
                        if self.canonical(alias) == persistent_id
                    }
                )
            )
            persistent = PersistentCluster(persistent_id, snapshot, all_aliases)
            if persistent_id in next_active:
                raise AssertionError("persistent identifier assigned to two components")
            next_active[persistent_id] = persistent
            for event in snapshot.events:
                if event.event_id not in self.known_events:
                    self.known_events[event.event_id] = event
                    self.event_origin[event.event_id] = persistent_id
                self.current_owner[event.event_id] = persistent_id
            self.event_log.append(
                PersistentClusterEvent(
                    prefix.final_round,
                    persistent_id,
                    action,
                    new_ids,
                    merged_aliases,
                )
            )

        if set(self.current_owner) != set(self.known_events):
            raise AssertionError("current ownership must cover every known event")
        self.active = next_active
        self.last_round = prefix.final_round
        return tuple(self.active[key] for key in sorted(self.active))
