"""Deterministic phase-transition lifecycle around the abstract JIT schedule.

The adapter records a supplied fusion outcome, labels its preservation across
an abstract D(S3)-to-D(Z3) transition, binds a measured neutrality record, and
terminates the associated absorber on a neutral re-gauging transition.  It is
not a microscopic implementation of gauging or ungauging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from lyons_absorber import (
    AbsorberGeometry,
    AbsorbingRegion,
    NeutralityMeasurement,
    NeutralityMeasurementLog,
    SpacetimeBox,
)
from schedule_state import ExplicitScheduleState, Neutrality, ScheduleTransition


@dataclass(frozen=True)
class FusionOutcome:
    """Explicit deterministic fixture value, not an inferred hidden state."""

    e_parity: int
    m_parity: int
    species_label: str = "vacuum"

    def __post_init__(self) -> None:
        if self.e_parity not in (0, 1) or self.m_parity not in (0, 1):
            raise ValueError("fusion outcome parities must be binary")
        if not self.species_label:
            raise ValueError("fusion outcome requires a nonempty species label")

    @property
    def neutrality(self) -> Neutrality:
        return "neutral" if (self.e_parity, self.m_parity) == (0, 0) else "nonneutral"


@dataclass
class UngaugedRegionState:
    cluster_id: str
    region_id: str
    opened_round: int
    d_s3_outcome: FusionOutcome
    d_z3_outcome: FusionOutcome
    measured_neutrality: Neutrality = "unknown"
    closed_round: int | None = None


@dataclass(frozen=True)
class PhaseLifecycleEvent:
    cluster_id: str
    region_id: str
    round: int
    action: Literal[
        "ungauge_preserve",
        "measure_neutrality",
        "defer_nonneutral",
        "correct_regauge",
    ]
    neutrality: Neutrality


@dataclass
class PhaseTransitionAdapter:
    """Transactional deterministic lifecycle for one region per cluster."""

    regions: dict[str, UngaugedRegionState] = field(default_factory=dict)
    event_log: list[PhaseLifecycleEvent] = field(default_factory=list)
    neutrality_log: NeutralityMeasurementLog = field(
        default_factory=NeutralityMeasurementLog
    )
    last_round: int = -1

    def _check_clock(self, current_round: int) -> None:
        if current_round < self.last_round:
            raise ValueError("phase lifecycle cannot move backwards")

    def ungauge(
        self,
        transition: ScheduleTransition,
        *,
        bounds: SpacetimeBox,
        supplied_outcome: FusionOutcome,
        geometry: AbsorberGeometry,
        current_round: int,
    ) -> UngaugedRegionState:
        self._check_clock(current_round)
        if transition.round != current_round:
            raise ValueError("ungauge transition must belong to the current round")
        if transition.branch != "lyons_brown" or transition.action != "ungauge":
            raise ValueError("only a Lyons-Brown ungauge transition may open a region")
        if transition.region_before not in ("d_s3", "boundary") or transition.region_after != "d_z3":
            raise ValueError("ungauge transition must enter D(Z3) from D(S3) or boundary")
        if transition.cluster_id in self.regions:
            raise ValueError("a cluster can have only one phase-transition region")
        region_id = f"ungauged:{transition.cluster_id}"
        geometry.open(
            AbsorbingRegion(
                absorber_id=region_id,
                kind="ungauging_wall",
                bounds=bounds,
                opened_round=current_round,
                owner_cluster=transition.cluster_id,
            ),
            current_round=current_round,
        )
        state = UngaugedRegionState(
            cluster_id=transition.cluster_id,
            region_id=region_id,
            opened_round=current_round,
            d_s3_outcome=supplied_outcome,
            d_z3_outcome=supplied_outcome,
        )
        if state.d_s3_outcome != state.d_z3_outcome:
            raise AssertionError("fusion outcome was not preserved by ungauging")
        self.regions[transition.cluster_id] = state
        self.event_log.append(
            PhaseLifecycleEvent(
                transition.cluster_id,
                region_id,
                current_round,
                "ungauge_preserve",
                "unknown",
            )
        )
        self.last_round = current_round
        return state

    def measure(
        self,
        measurement: NeutralityMeasurement,
        *,
        schedule: ExplicitScheduleState,
        geometry: AbsorberGeometry,
        current_round: int,
    ) -> Neutrality:
        self._check_clock(current_round)
        state = self.regions[measurement.cluster_id]
        if measurement.region_id != state.region_id:
            raise ValueError("neutrality record is bound to the wrong phase region")
        if (measurement.e_parity, measurement.m_parity) != (
            state.d_z3_outcome.e_parity,
            state.d_z3_outcome.m_parity,
        ):
            raise ValueError("deterministic neutrality record disagrees with supplied outcome")
        neutrality = self.neutrality_log.apply(
            measurement,
            geometry=geometry,
            schedule=schedule,
            current_round=current_round,
        )
        if state.measured_neutrality != "unknown":
            raise ValueError("phase region already has a neutrality record")
        state.measured_neutrality = neutrality
        self.event_log.append(
            PhaseLifecycleEvent(
                state.cluster_id,
                state.region_id,
                current_round,
                "measure_neutrality",
                neutrality,
            )
        )
        self.last_round = current_round
        return neutrality

    def apply_schedule_transition(
        self,
        transition: ScheduleTransition,
        *,
        geometry: AbsorberGeometry,
        current_round: int,
    ) -> None:
        self._check_clock(current_round)
        if transition.round != current_round or transition.branch != "lyons_brown":
            raise ValueError("phase action must be a current Lyons-Brown transition")
        state = self.regions[transition.cluster_id]
        if state.closed_round is not None:
            raise ValueError("phase region is already closed")
        if transition.action == "defer_nonneutral":
            if state.measured_neutrality != "nonneutral" or transition.neutrality != "nonneutral":
                raise ValueError("non-neutral deferral requires a matching measured record")
            if not geometry.regions[state.region_id].active_at(current_round):
                raise ValueError("non-neutral deferral requires an active ungauged region")
            action = "defer_nonneutral"
        elif transition.action == "correct_regauge":
            if state.measured_neutrality != "neutral" or transition.neutrality != "neutral":
                raise ValueError("re-gauging requires a matching neutral record")
            geometry.terminate(state.region_id, current_round=current_round)
            state.closed_round = current_round
            action = "correct_regauge"
        else:
            raise ValueError("transition is not a phase-lifecycle completion action")
        self.event_log.append(
            PhaseLifecycleEvent(
                state.cluster_id,
                state.region_id,
                current_round,
                action,
                state.measured_neutrality,
            )
        )
        self.last_round = current_round
