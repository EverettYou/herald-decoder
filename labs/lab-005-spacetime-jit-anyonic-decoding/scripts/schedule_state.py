"""Explicit bounded schedule state for Jing and Lyons--Brown branches.

This module keeps two source-derived abstractions separate:

* ``jing_ilp`` retains unresolved defects until the Algorithm-1 bounding-cube
  age gate commits them.
* ``lyons_brown`` propagates a deferred detector by reversing the latest
  decoder-side readout, then tracks D(S3), ungauged D(Z3), and boundary state.

The implementation is an abstract deterministic fixture.  It does not model
microscopic ungauging circuits, infer neutrality, or claim fault tolerance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from spacetime_record import CausalRecordPrefix


BoolArray = NDArray[np.bool_]
ScheduleBranch = Literal["jing_ilp", "lyons_brown"]
Region = Literal["d_s3", "d_z3", "boundary"]
Neutrality = Literal["unknown", "neutral", "nonneutral"]


@dataclass(frozen=True)
class DeferredRecordEvent:
    cluster_id: str
    round: int
    vertices: tuple[int, ...]
    action: str = "reverse_latest_readout"


@dataclass
class DeferredMeasurementRecord:
    """Mutable decoder-side record used only to propagate deferred events."""

    syndrome_readout: BoolArray
    expected_syndrome_changes: BoolArray
    event_log: list[DeferredRecordEvent] = field(default_factory=list)

    @classmethod
    def from_prefix(
        cls,
        prefix: CausalRecordPrefix,
        *,
        expected_syndrome_changes: NDArray[np.generic] | None = None,
    ) -> "DeferredMeasurementRecord":
        readout = np.asarray(prefix.syndrome_readout, dtype=np.bool_).copy()
        detector_rows = readout.shape[0] - 1
        if expected_syndrome_changes is None:
            expected = np.zeros((detector_rows, readout.shape[1]), dtype=np.bool_)
        else:
            expected = np.asarray(expected_syndrome_changes, dtype=np.bool_).copy()
            if expected.shape != (detector_rows, readout.shape[1]):
                raise ValueError("expected syndrome changes have the wrong prefix shape")
        record = cls(readout, expected)
        if not np.array_equal(record.detectors, prefix.syndrome_detectors):
            raise ValueError("prefix detectors disagree with supplied expected changes")
        return record

    @property
    def final_round(self) -> int:
        return int(self.syndrome_readout.shape[0] - 1)

    @property
    def detector_count(self) -> int:
        return int(self.syndrome_readout.shape[1])

    @property
    def detectors(self) -> BoolArray:
        return (
            self.syndrome_readout[1:]
            ^ self.syndrome_readout[:-1]
            ^ self.expected_syndrome_changes
        )

    def defer_current(
        self, *, cluster_id: str, current_round: int, vertices: tuple[int, ...]
    ) -> DeferredRecordEvent:
        """Reverse current readouts so visible detector events move forward."""

        if current_round != self.final_round or current_round == 0:
            raise ValueError("defer propagation must act on the latest detector round")
        selected = tuple(int(vertex) for vertex in vertices)
        if selected != tuple(sorted(set(selected))):
            raise ValueError("deferred detector vertices must be sorted and unique")
        if any(vertex < 0 or vertex >= self.detector_count for vertex in selected):
            raise ValueError("deferred detector vertex is out of range")
        row = self.detectors[current_round - 1]
        if any(not row[vertex] for vertex in selected):
            raise ValueError("a deferred vertex must carry a current detector event")
        self.syndrome_readout[current_round, list(selected)] ^= True
        if any(self.detectors[current_round - 1, vertex] for vertex in selected):
            raise AssertionError("defer propagation did not clear the current event")
        event = DeferredRecordEvent(cluster_id, current_round, selected)
        self.event_log.append(event)
        return event

    def append_round(
        self,
        syndrome_readout: NDArray[np.generic],
        *,
        expected_syndrome_change: NDArray[np.generic] | None = None,
    ) -> None:
        row = np.asarray(syndrome_readout, dtype=np.bool_)
        if row.shape != (self.detector_count,):
            raise ValueError("new syndrome readout has the wrong width")
        change = (
            np.zeros(self.detector_count, dtype=np.bool_)
            if expected_syndrome_change is None
            else np.asarray(expected_syndrome_change, dtype=np.bool_)
        )
        if change.shape != (self.detector_count,):
            raise ValueError("expected syndrome change has the wrong width")
        self.syndrome_readout = np.vstack((self.syndrome_readout, row))
        self.expected_syndrome_changes = np.vstack(
            (self.expected_syndrome_changes, change)
        )


@dataclass
class ScheduledCluster:
    cluster_id: str
    detector_vertices: tuple[int, ...]
    youngest_round: int
    cube_size: int
    nearest_absorber_distance: int
    region: Region
    neutrality: Neutrality = "unknown"
    ungauged_at: int | None = None


@dataclass(frozen=True)
class ScheduleTransition:
    branch: ScheduleBranch
    cluster_id: str
    round: int
    action: str
    region_before: Region
    region_after: Region
    age: int
    required_age: int
    neutrality: Neutrality


@dataclass
class ExplicitScheduleState:
    branch: ScheduleBranch
    clusters: dict[str, ScheduledCluster] = field(default_factory=dict)
    event_log: list[ScheduleTransition] = field(default_factory=list)
    last_round: int = -1

    def __post_init__(self) -> None:
        if self.branch not in ("jing_ilp", "lyons_brown"):
            raise ValueError("unknown schedule branch")

    def register(self, cluster: ScheduledCluster, *, current_round: int) -> None:
        if current_round < self.last_round:
            raise ValueError("a causal schedule cannot move backwards")
        if cluster.cluster_id in self.clusters or not cluster.cluster_id:
            raise ValueError("cluster identifier must be new and nonempty")
        if cluster.youngest_round < 0 or cluster.youngest_round > current_round:
            raise ValueError("cluster youngest round must be causally available")
        if cluster.cube_size <= 0 or cluster.nearest_absorber_distance <= 0:
            raise ValueError("cluster size and absorber distance must be positive")
        if cluster.region not in ("d_s3", "d_z3", "boundary"):
            raise ValueError("unknown cluster region")
        if cluster.neutrality not in ("unknown", "neutral", "nonneutral"):
            raise ValueError("unknown neutrality label")
        vertices = cluster.detector_vertices
        if vertices != tuple(sorted(set(vertices))) or not vertices:
            raise ValueError("cluster detector vertices must be nonempty, sorted, unique")
        occupied = {
            vertex
            for active in self.clusters.values()
            for vertex in active.detector_vertices
        }
        if occupied.intersection(vertices):
            raise ValueError("active clusters cannot share detector vertices")
        self.clusters[cluster.cluster_id] = cluster
        self.last_round = current_round

    def set_neutrality(self, cluster_id: str, neutrality: Neutrality) -> None:
        if neutrality not in ("neutral", "nonneutral"):
            raise ValueError("neutrality observation must be neutral or nonneutral")
        cluster = self.clusters[cluster_id]
        if cluster.region != "d_z3":
            raise ValueError("neutrality is observable only in the ungauged region")
        cluster.neutrality = neutrality

    def step(
        self,
        *,
        current_round: int,
        record: DeferredMeasurementRecord | None = None,
    ) -> tuple[ScheduleTransition, ...]:
        if current_round < self.last_round:
            raise ValueError("a causal schedule cannot move backwards")
        if self.branch == "lyons_brown":
            if record is None or record.final_round != current_round:
                raise ValueError("Lyons-Brown steps require the current decoder record")

        planned: list[tuple[ScheduledCluster, ScheduleTransition, bool]] = []
        deferred_vertices: set[int] = set()
        for cluster_id in sorted(self.clusters):
            cluster = self.clusters[cluster_id]
            region_before = cluster.region
            reference_round = (
                cluster.ungauged_at
                if cluster.region == "d_z3" and cluster.ungauged_at is not None
                else cluster.youngest_round
            )
            age = current_round - reference_round
            required_age = (
                cluster.cube_size
                if self.branch == "jing_ilp"
                else cluster.nearest_absorber_distance
            )
            propagate = False
            if age < required_age:
                action = "defer"
                region_after = cluster.region
                propagate = self.branch == "lyons_brown"
            elif self.branch == "jing_ilp":
                action = "commit"
                region_after = cluster.region
            elif cluster.region in ("d_s3", "boundary"):
                action = "ungauge"
                region_after = "d_z3"
            elif cluster.neutrality == "neutral":
                action = "correct_regauge"
                region_after = "d_s3"
            elif cluster.neutrality == "nonneutral":
                action = "defer_nonneutral"
                region_after = "d_z3"
                propagate = True
            else:
                action = "await_neutrality"
                region_after = "d_z3"

            if propagate:
                overlap = deferred_vertices.intersection(cluster.detector_vertices)
                if overlap:
                    raise ValueError("deferred clusters cannot share detector vertices")
                deferred_vertices.update(cluster.detector_vertices)
            transition = ScheduleTransition(
                branch=self.branch,
                cluster_id=cluster.cluster_id,
                round=current_round,
                action=action,
                region_before=region_before,
                region_after=region_after,
                age=age,
                required_age=required_age,
                neutrality=cluster.neutrality,
            )
            planned.append((cluster, transition, propagate))

        if record is not None and deferred_vertices:
            if current_round == 0:
                raise ValueError("cannot propagate a detector before the first transition")
            if any(
                vertex < 0 or vertex >= record.detector_count
                for vertex in deferred_vertices
            ):
                raise ValueError("deferred detector vertex is out of range")
            current_detectors = record.detectors[current_round - 1]
            if any(not current_detectors[vertex] for vertex in deferred_vertices):
                raise ValueError("every propagated vertex must carry a current event")
        if record is not None:
            for cluster, _, propagate in planned:
                if propagate:
                    record.defer_current(
                        cluster_id=cluster.cluster_id,
                        current_round=current_round,
                        vertices=cluster.detector_vertices,
                    )

        for cluster, transition, _ in planned:
            self.event_log.append(transition)
            if transition.action == "ungauge":
                cluster.region = "d_z3"
                cluster.ungauged_at = current_round
                cluster.neutrality = "unknown"
            elif transition.action in ("commit", "correct_regauge"):
                del self.clusters[cluster.cluster_id]
        self.last_round = current_round
        return tuple(transition for _, transition, _ in planned)
