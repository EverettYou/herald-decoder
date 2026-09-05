"""Perfect-measurement temporal composition for the Lab 005 D4 branch.

This module wraps the verified observation-only Lab 004 spatial policy in a
small causal state machine.  It introduces no noisy readout model and never
constructs a measurement from a hidden physical chain.  A physical adapter
must still supply every post-action observation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping

from d4_spatial_policy import (
    DecoderMode,
    D4ChargeActionV1,
    D4FluxActionV1,
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    canonical_digest,
    decode_charge_action,
    decode_flux_action,
)


TemporalPhase = Literal["observing", "awaiting_post_flux", "complete"]


@dataclass(frozen=True)
class TemporalEventV1:
    sequence: int
    round: int
    kind: str
    payload_digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "round": self.round,
            "kind": self.kind,
            "payload_digest": self.payload_digest,
        }


@dataclass(frozen=True)
class PerfectD4TemporalStateV1:
    schema_version: int
    trial_id: str
    size: int
    mode: DecoderMode
    current_round: int
    causal_prefix_digest: str
    phase: TemporalPhase
    commit_request: D4SpatialCommitRequestV1 | None = None
    flux_action: D4FluxActionV1 | None = None
    post_flux_observation: D4PostFluxObservationV1 | None = None
    charge_action: D4ChargeActionV1 | None = None
    events: tuple[TemporalEventV1, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_id": self.trial_id,
            "size": self.size,
            "mode": self.mode,
            "current_round": self.current_round,
            "causal_prefix_digest": self.causal_prefix_digest,
            "phase": self.phase,
            "commit_request": (
                None if self.commit_request is None else self.commit_request.to_dict()
            ),
            "flux_action": None if self.flux_action is None else self.flux_action.to_dict(),
            "post_flux_observation": (
                None
                if self.post_flux_observation is None
                else self.post_flux_observation.to_dict()
            ),
            "charge_action": (
                None if self.charge_action is None else self.charge_action.to_dict()
            ),
            "events": [event.to_dict() for event in self.events],
        }

    @property
    def state_digest(self) -> str:
        return canonical_digest(self.public_dict())


def _event(state: PerfectD4TemporalStateV1, kind: str, payload: Mapping[str, Any]) -> TemporalEventV1:
    return TemporalEventV1(
        sequence=len(state.events),
        round=state.current_round,
        kind=kind,
        payload_digest=canonical_digest(payload),
    )


def open_temporal_state(
    *,
    trial_id: str,
    size: int,
    mode: DecoderMode,
    initial_round: int,
    causal_prefix_digest: str,
) -> PerfectD4TemporalStateV1:
    if not trial_id or size != 2 or mode not in ("syndrome_only", "heralded"):
        raise ValueError("E0 supports a nonempty trial on the registered L=2 modes")
    if initial_round < 0 or len(causal_prefix_digest) != 64:
        raise ValueError("invalid initial round or causal prefix digest")
    state = PerfectD4TemporalStateV1(
        schema_version=1,
        trial_id=trial_id,
        size=size,
        mode=mode,
        current_round=initial_round,
        causal_prefix_digest=causal_prefix_digest,
        phase="observing",
    )
    return replace(
        state,
        events=(
            _event(
                state,
                "open",
                {"causal_prefix_digest": causal_prefix_digest, "phase": "observing"},
            ),
        ),
    )


def advance_round(
    state: PerfectD4TemporalStateV1,
    *,
    next_round: int,
    causal_prefix_digest: str,
) -> PerfectD4TemporalStateV1:
    if state.phase == "awaiting_post_flux":
        raise ValueError("cannot advance while a bound post-flux observation is pending")
    if next_round != state.current_round + 1 or len(causal_prefix_digest) != 64:
        raise ValueError("temporal prefixes must advance by exactly one round")
    advanced = replace(
        state,
        current_round=next_round,
        causal_prefix_digest=causal_prefix_digest,
        phase="observing",
        commit_request=None,
        flux_action=None,
        post_flux_observation=None,
        charge_action=None,
    )
    return replace(
        advanced,
        events=state.events
        + (
            _event(
                advanced,
                "advance",
                {"causal_prefix_digest": causal_prefix_digest, "phase": "observing"},
            ),
        ),
    )


def commit_flux(
    state: PerfectD4TemporalStateV1,
    request: D4SpatialCommitRequestV1,
) -> PerfectD4TemporalStateV1:
    if state.phase != "observing":
        raise ValueError("a flux action may be committed only from observing state")
    if (
        request.size != state.size
        or request.mode != state.mode
        or request.decision_round != state.current_round
        or request.causal_prefix_digest != state.causal_prefix_digest
    ):
        raise ValueError("spatial commit request does not match the temporal state")
    action = decode_flux_action(request)
    committed = replace(
        state,
        phase="awaiting_post_flux",
        commit_request=request,
        flux_action=action,
    )
    return replace(
        committed,
        events=state.events
        + (_event(committed, "commit_flux", action.to_dict()),),
    )


def supply_post_flux(
    state: PerfectD4TemporalStateV1,
    observation: D4PostFluxObservationV1,
) -> PerfectD4TemporalStateV1:
    if (
        state.phase != "awaiting_post_flux"
        or state.commit_request is None
        or state.flux_action is None
    ):
        raise ValueError("post-flux observation requires a previously bound flux action")
    action = decode_charge_action(state.commit_request, state.flux_action, observation)
    complete = replace(
        state,
        current_round=max(state.current_round, observation.observation_round),
        phase="complete",
        post_flux_observation=observation,
        charge_action=action,
    )
    return replace(
        complete,
        events=state.events
        + (_event(complete, "complete_charge", action.to_dict()),),
    )


@dataclass(frozen=True)
class PrivateFrozenTransitionScoreV1:
    state_digest: str
    scorer_version: str
    logical_failure: bool
    scoring_digest: str


def score_frozen_transition(
    state: PerfectD4TemporalStateV1,
    *,
    logical_failure_truth: bool,
) -> PrivateFrozenTransitionScoreV1:
    """Score only a completed public transition in a private sidecar."""

    if state.phase != "complete" or state.charge_action is None:
        raise ValueError("private scoring requires a completed frozen transition")
    payload = {
        "state_digest": state.state_digest,
        "scorer_version": "e0-private-truth-fixture-v1",
        "logical_failure": bool(logical_failure_truth),
    }
    return PrivateFrozenTransitionScoreV1(
        state_digest=state.state_digest,
        scorer_version="e0-private-truth-fixture-v1",
        logical_failure=bool(logical_failure_truth),
        scoring_digest=canonical_digest(payload),
    )
