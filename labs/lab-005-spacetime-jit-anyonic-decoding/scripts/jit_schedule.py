"""Causal cluster-age gate for the just-in-time ILP decoder.

This implements the commit/defer predicate in Algorithm 1 of Jing et al.
(2026).  The inner ILP supplies disconnected inferred clusters; this state
machine owns only the bounding-cube age gate and unresolved-defect
bookkeeping.  It does not implement the fuller Lyons--Brown absorber-distance,
measurement-reversal, D(S3)/D(Z3) boundary, ungauging, neutrality, or re-gauging
state machine.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Defect:
    defect_id: str
    position: tuple[int, ...]
    time: int


@dataclass(frozen=True)
class CorrectionElement:
    position: tuple[int, ...]
    time: int


@dataclass(frozen=True)
class InferredCluster:
    cluster_id: str
    defect_ids: tuple[str, ...]
    correction_elements: tuple[CorrectionElement, ...] = ()


@dataclass(frozen=True)
class JitDecision:
    cluster_id: str
    action: str
    cube_size: int
    youngest_time: int
    current_time: int


@dataclass
class JitStateMachine:
    unresolved: dict[str, Defect] = field(default_factory=dict)
    event_log: list[JitDecision] = field(default_factory=list)
    last_time: int = -1

    def _validate_time(self, current_time: int) -> None:
        if current_time < self.last_time:
            raise ValueError("a causal scheduler cannot move backwards in time")

    def add_defects(self, defects: tuple[Defect, ...], *, current_time: int) -> None:
        self._validate_time(current_time)
        new_ids = tuple(defect.defect_id for defect in defects)
        if len(new_ids) != len(set(new_ids)):
            raise ValueError("new defect identifiers must be unique")
        for defect in defects:
            if defect.time < 0 or defect.time > current_time:
                raise ValueError("a causal scheduler cannot register a future defect")
            if defect.defect_id in self.unresolved:
                raise ValueError("defect identifiers must be unique while unresolved")
        self.last_time = current_time
        for defect in defects:
            self.unresolved[defect.defect_id] = defect

    @staticmethod
    def _cube_size(
        defects: tuple[Defect, ...],
        correction_elements: tuple[CorrectionElement, ...],
    ) -> int:
        points = [defect.position + (defect.time,) for defect in defects]
        points.extend(element.position + (element.time,) for element in correction_elements)
        if not points:
            raise ValueError("a cluster must contain at least one spacetime element")
        dimension = len(points[0])
        if any(len(point) != dimension for point in points):
            raise ValueError("cluster elements must share one spacetime dimension")
        return max(
            max(point[axis] for point in points) - min(point[axis] for point in points) + 1
            for axis in range(dimension)
        )

    def step(
        self,
        *,
        current_time: int,
        clusters: tuple[InferredCluster, ...],
    ) -> tuple[JitDecision, ...]:
        self._validate_time(current_time)
        cluster_ids = tuple(cluster.cluster_id for cluster in clusters)
        if len(cluster_ids) != len(set(cluster_ids)):
            raise ValueError("cluster identifiers must be unique at one time step")
        flattened = tuple(
            defect_id for cluster in clusters for defect_id in cluster.defect_ids
        )
        if len(flattened) != len(set(flattened)):
            raise ValueError("one defect cannot belong to two inferred clusters")
        if set(flattened) != set(self.unresolved):
            raise ValueError("clusters must partition every unresolved defect")
        decisions: list[JitDecision] = []
        for cluster in clusters:
            if not cluster.defect_ids:
                raise ValueError("an inferred cluster must contain a defect")
            if len(set(cluster.defect_ids)) != len(cluster.defect_ids):
                raise ValueError("a cluster cannot repeat a defect")
            defects = tuple(self.unresolved[item] for item in cluster.defect_ids)
            elements = tuple(cluster.correction_elements)
            if any(element.time < 0 or element.time > current_time for element in elements):
                raise ValueError("a causal scheduler cannot inspect a future correction string")
            cube_size = self._cube_size(defects, elements)
            youngest_time = max(
                [defect.time for defect in defects]
                + [element.time for element in elements]
            )
            action = "defer" if youngest_time > current_time - cube_size else "commit"
            decision = JitDecision(
                cluster_id=cluster.cluster_id,
                action=action,
                cube_size=cube_size,
                youngest_time=youngest_time,
                current_time=current_time,
            )
            decisions.append(decision)
        self.event_log.extend(decisions)
        for cluster, decision in zip(clusters, decisions, strict=True):
            if decision.action == "commit":
                for defect_id in cluster.defect_ids:
                    del self.unresolved[defect_id]
        self.last_time = current_time
        return tuple(decisions)
