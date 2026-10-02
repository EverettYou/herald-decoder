"""Integrated phenomenological D4 histories for the bounded J6 preflight.

The public scheduler sees only a causal binary syndrome/signal record.  After
one public flux action, this module privately constructs the corresponding
post-flux relations, emits a full-binary public charge record, obtains the
relation-free public charge action, and derives the Boolean-union loss from
the hidden physical history.  No public method exposes support, relations,
effective strings, or logical truth.

This is the researcher-approved phenomenological/projector-level D4
translation.  It is not an ancilla-level extraction circuit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import numpy as np
from numpy.typing import NDArray

from baseline_harness import visible_history_digest
from d4_projector_instrument import CHARGE, FLUX, VACUUM, HiddenProjectorStateV1, project_hidden_state
from d4_spatial_policy import (
    D4FluxActionV1,
    D4TemporalBoundaryActionV1,
    D4TemporalBoundaryHandoffV1,
    canonical_digest,
    paper_periodic_honeycomb,
)
from e1_schedule_integration import E1PolicyInvocation, run_e1_policy_matrix
from generic_history import GenericNoiseParameters
from spacetime_record import SpacetimeRecord, build_record_from_fault_masks

# d4_spatial_policy installs the frozen Lab 004 script directory on sys.path.
from d4_charge import decode_public_postflux_charges, score_public_postflux_charge_action
from d4_honeycomb import BLUE, all_plus_logical_z_policy, generate_loop_constraints
from d4_matching import edge_chain_boundary, physical_correction_union
from d4_pipeline import sample_postflux_charge_outcomes
from d4_postflux import infer_periodic_postflux_relations
from d4_sampler import observation_from_error_edges


BoolArray = NDArray[np.bool_]
FloatArray = NDArray[np.float64]
UIntArray = NDArray[np.uint8]
StringArray = NDArray[np.str_]
_HEX = frozenset("0123456789abcdef")


def _freeze(value: NDArray[np.generic]) -> NDArray[np.generic]:
    result = np.array(value, copy=True)
    result.setflags(write=False)
    return result


def _key(name: str, value: str) -> str:
    text = str(value)
    if len(text) != 64 or any(character not in _HEX for character in text):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _has_winding(lattice: Any, edges: NDArray[np.generic]) -> bool:
    analysis = generate_loop_constraints(lattice, np.asarray(edges, dtype=np.bool_))
    return any(component.winding_vectors for component in analysis.components)


def _categorical_truth(lattice: Any, signal: BoolArray) -> StringArray:
    result = np.full(signal.shape, "none", dtype="<U5")
    for site in np.flatnonzero(signal):
        result[int(site)] = "blue" if int(lattice.vertex_colors[int(site)]) == BLUE else "green"
    return result


def _categorical_readout(
    truth: StringArray,
    uniforms: FloatArray,
    parameters: GenericNoiseParameters,
) -> StringArray:
    if uniforms.shape != truth.shape or np.any((uniforms < 0.0) | (uniforms >= 1.0)):
        raise ValueError("herald uniforms must match truth and lie in [0,1)")
    result = np.array(truth, copy=True)
    none = truth == "none"
    false_positive = none & (uniforms >= 1.0 - parameters.p_fp)
    result[false_positive & (uniforms < 1.0 - parameters.p_fp / 2.0)] = "blue"
    result[false_positive & (uniforms >= 1.0 - parameters.p_fp / 2.0)] = "green"
    for source, other in (("blue", "green"), ("green", "blue")):
        selected = truth == source
        false_negative = selected & (uniforms < parameters.p_fn)
        confused = selected & ~false_negative & (
            uniforms < parameters.p_fn + parameters.p_confuse
        )
        result[false_negative] = "none"
        result[confused] = other
    return result


@dataclass(frozen=True)
class IntegratedD4HistoryV1:
    """One immutable five-round history with public and private partitions."""

    trial_id: str
    master_seed: int
    size: int
    parameters: GenericNoiseParameters
    physical_key: str
    first_observation_key: str
    second_exogenous_key: str
    transition_edge_faults: BoolArray
    physical_edge_states: BoolArray
    hidden_projector_states: tuple[HiddenProjectorStateV1, ...]
    public_herald_truth: StringArray
    public_herald_readout: StringArray
    record: SpacetimeRecord
    history_digest: str
    private_physical_digest: str

    def __post_init__(self) -> None:
        lattice = paper_periodic_honeycomb(self.size)
        if not self.trial_id or self.size != 2 or self.record.readout_rounds != 5:
            raise ValueError("J6 histories require a nonempty trial, paper L=2, and five rounds")
        if self.transition_edge_faults.shape != (4, lattice.edge_count):
            raise ValueError("J6 requires four between-round edge-fault rows")
        if self.physical_edge_states.shape != (5, lattice.edge_count):
            raise ValueError("physical edge states must cover all five rounds")
        if len(self.hidden_projector_states) != 5:
            raise ValueError("hidden projector trajectory must cover all five rounds")
        if self.public_herald_truth.shape != (5, lattice.vertex_count):
            raise ValueError("categorical herald truth has the wrong shape")
        if self.public_herald_readout.shape != self.public_herald_truth.shape:
            raise ValueError("categorical herald readout has the wrong shape")
        for name in ("physical_key", "first_observation_key", "second_exogenous_key"):
            _key(name, getattr(self, name))
        if self.history_digest != visible_history_digest(self.record):
            raise ValueError("visible history digest does not match the public record")
        for name in (
            "transition_edge_faults",
            "physical_edge_states",
            "public_herald_truth",
            "public_herald_readout",
        ):
            object.__setattr__(self, name, _freeze(getattr(self, name)))

    def public_transcript(self) -> dict[str, Any]:
        """Return the complete public first record without truth sidecars."""

        return {
            "trial_id": self.trial_id,
            "history_digest": self.history_digest,
            "syndrome_readout": self.record.syndrome_readout.astype(int).tolist(),
            "syndrome_detectors": self.record.syndrome_detectors.astype(int).tolist(),
            "herald_readout": self.public_herald_readout.tolist(),
        }


@dataclass(frozen=True)
class ActionConditionedSecondRecordV1:
    """Public completion plus an opaque private-generation binding."""

    trial_id: str
    decision_round: int
    flux_action_digest: str
    public_charge_record: tuple[int, ...]
    public_charge_action: dict[str, tuple[int, ...]]
    public_completion_digest: str
    private_binding_digest: str
    _physical_edges: tuple[int, ...]
    _flux_correction_edges: tuple[int, ...]
    _active_vertices: tuple[int, ...]
    _entanglement_pairs: tuple[tuple[int, int], ...]
    _internal_second_record: tuple[int, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "decision_round": self.decision_round,
            "flux_action_digest": self.flux_action_digest,
            "public_charge_record": list(self.public_charge_record),
            "public_charge_action": {
                color: list(edges) for color, edges in self.public_charge_action.items()
            },
            "public_completion_digest": self.public_completion_digest,
        }


@dataclass(frozen=True)
class DerivedPrivateScoreV1:
    trial_id: str
    public_completion_digest: str
    physical_winding: bool
    union_winding: bool
    terminal_residual: bool
    charge_winding: bool
    logical_failure: bool
    scoring_digest: str


@dataclass(frozen=True)
class J6TerminalArmRowV1:
    """One unconditional denominator row; failures cannot disappear."""

    trial_id: str
    mode: str
    branch: str
    status: str
    denominator_included: bool
    logical_failure: bool
    public_completion_digest: str | None
    private_scoring_digest: str | None
    failure_reason: str | None


@dataclass(frozen=True)
class J6ArmEvaluationV1:
    """One unconditional arm row after cumulative-frame composition."""

    trial_id: str
    mode: str
    branch: str
    status: str
    denominator_included: bool
    logical_failure: bool
    invocation_count: int
    unique_commit_count: int
    collapsed_duplicate_count: int
    commit_rounds: tuple[int, ...]
    public_completion_digests: tuple[str, ...]
    physical_winding: bool
    union_winding: bool
    charge_winding: bool
    terminal_residual: bool
    failure_reason: str | None


def build_integrated_d4_history_from_draws(
    *,
    trial_id: str,
    master_seed: int,
    parameters: GenericNoiseParameters,
    physical_key: str,
    first_observation_key: str,
    second_exogenous_key: str,
    transition_edge_faults: NDArray[np.generic],
    syndrome_measurement_faults: NDArray[np.generic],
    herald_uniforms: NDArray[np.generic],
    first_observation_seeds: tuple[int, ...],
) -> IntegratedD4HistoryV1:
    """Compose one deterministic D4 history from explicit independent draws."""

    if not trial_id or len(first_observation_seeds) != 5:
        raise ValueError("trial_id and five first-observation seeds are required")
    lattice = paper_periodic_honeycomb(2)
    faults = np.asarray(transition_edge_faults, dtype=np.bool_)
    syndrome_faults = np.asarray(syndrome_measurement_faults, dtype=np.bool_)
    uniforms = np.asarray(herald_uniforms, dtype=np.float64)
    if faults.shape != (4, lattice.edge_count):
        raise ValueError("transition_edge_faults must have shape (4, edge_count)")
    if syndrome_faults.shape != (5, lattice.vertex_count):
        raise ValueError("syndrome faults must have shape (5, vertex_count)")
    if uniforms.shape != (5, lattice.vertex_count):
        raise ValueError("herald uniforms must have shape (5, vertex_count)")

    physical = np.zeros((5, lattice.edge_count), dtype=np.bool_)
    for round_index in range(1, 5):
        physical[round_index] = physical[round_index - 1] ^ faults[round_index - 1]

    syndrome_truth = np.zeros((5, lattice.vertex_count), dtype=np.bool_)
    signal_truth = np.zeros_like(syndrome_truth)
    categorical_truth = np.full((5, lattice.vertex_count), "none", dtype="<U5")
    hidden: list[HiddenProjectorStateV1] = []
    prior: HiddenProjectorStateV1 | None = None
    sector = all_plus_logical_z_policy()
    for round_index in range(5):
        chain = physical[round_index].astype(np.uint8)
        syndrome_truth[round_index] = edge_chain_boundary(lattice, chain).astype(bool)
        observation = observation_from_error_edges(
            lattice,
            chain,
            seed=int(first_observation_seeds[round_index]),
            logical_sector=sector,
        )
        if observation.charge_outcomes is None:
            raise RuntimeError("sector-declared D4 first observation lacks charge outcomes")
        signal_truth[round_index] = np.asarray(observation.charge_outcomes, dtype=np.bool_)
        categorical_truth[round_index] = _categorical_truth(
            lattice, signal_truth[round_index]
        )
        labels = {
            site: (
                FLUX
                if syndrome_truth[round_index, site]
                else CHARGE
                if signal_truth[round_index, site]
                else VACUUM
            )
            for site in range(lattice.vertex_count)
        }
        prior = project_hidden_state(
            trial_id=trial_id,
            round=round_index,
            true_labels=labels,
            previous=prior,
        )
        hidden.append(prior)

    categorical_readout = _categorical_readout(categorical_truth, uniforms, parameters)
    signal_readout = categorical_readout != "none"
    record = build_record_from_fault_masks(
        syndrome_truth,
        syndrome_faults,
        signal_truth,
        signal_truth ^ signal_readout,
    )
    private_payload = {
        "trial_id": trial_id,
        "physical_key": _key("physical_key", physical_key),
        "first_observation_key": _key("first_observation_key", first_observation_key),
        "transition_edge_faults": faults.astype(int).tolist(),
        "physical_edge_states": physical.astype(int).tolist(),
        "hidden_state_digests": [state.state_update_digest for state in hidden],
    }
    return IntegratedD4HistoryV1(
        trial_id=trial_id,
        master_seed=int(master_seed),
        size=2,
        parameters=parameters,
        physical_key=physical_key,
        first_observation_key=first_observation_key,
        second_exogenous_key=_key("second_exogenous_key", second_exogenous_key),
        transition_edge_faults=faults,
        physical_edge_states=physical,
        hidden_projector_states=tuple(hidden),
        public_herald_truth=categorical_truth,
        public_herald_readout=categorical_readout,
        record=record,
        history_digest=visible_history_digest(record),
        private_physical_digest=_digest(private_payload),
    )


def generate_integrated_d4_history(
    *, trial_id: str, master_seed: int, parameters: GenericNoiseParameters
) -> IntegratedD4HistoryV1:
    """Sample the frozen J6 channel; production callers remain separately gated."""

    lattice = paper_periodic_honeycomb(2)
    streams = np.random.SeedSequence(int(master_seed)).spawn(4)
    physical_rng, syndrome_rng, herald_rng, observation_rng = (
        np.random.default_rng(stream) for stream in streams
    )
    keys = tuple(
        _digest({"protocol": "j6-matched-key-v1", "master_seed": int(master_seed), "tag": tag})
        for tag in ("physical", "first_observation", "second_exogenous")
    )
    return build_integrated_d4_history_from_draws(
        trial_id=trial_id,
        master_seed=int(master_seed),
        parameters=parameters,
        physical_key=keys[0],
        first_observation_key=keys[1],
        second_exogenous_key=keys[2],
        transition_edge_faults=(
            physical_rng.random((4, lattice.edge_count)) < parameters.p_data
        ),
        syndrome_measurement_faults=(
            syndrome_rng.random((5, lattice.vertex_count)) < parameters.p_syndrome
        ),
        herald_uniforms=herald_rng.random((5, lattice.vertex_count)),
        first_observation_seeds=tuple(
            int(value)
            for value in observation_rng.integers(0, 2**32, size=5, dtype=np.uint64)
        ),
    )


def provide_action_conditioned_second_record(
    history: IntegratedD4HistoryV1,
    invocation: E1PolicyInvocation,
) -> ActionConditionedSecondRecordV1:
    """Generate the R6AF full-binary second record under one realized action."""

    if invocation.flux_action.status == "defer_temporal_boundary":
        raise ValueError("unresolved_temporal_boundary_handoff: no physical action")
    if invocation.report.trial_id != history.trial_id:
        raise ValueError("flux action belongs to another history")
    round_index = int(invocation.report.round)
    if not 0 <= round_index < history.record.readout_rounds:
        raise ValueError("flux action round is outside the hidden history")
    lattice = paper_periodic_honeycomb(history.size)
    invocation.flux_action.validate(edge_count=lattice.edge_count)
    if invocation.flux_action.request_id != invocation.policy_request.request_id:
        raise ValueError("flux action is not bound to its policy request")

    physical = history.physical_edge_states[round_index].astype(np.uint8)
    correction = np.zeros(lattice.edge_count, dtype=np.uint8)
    correction[list(invocation.flux_action.correction_edges)] = 1
    relations = infer_periodic_postflux_relations(lattice, physical, correction)
    second_seed = int(
        _digest(
            {
                "second_exogenous_key": history.second_exogenous_key,
                "flux_action_digest": invocation.flux_action.action_digest,
                "decision_round": round_index,
            }
        )[:16],
        16,
    )
    internal = sample_postflux_charge_outcomes(
        lattice.vertex_count, relations, seed=second_seed
    )
    public = np.maximum(internal, 0).astype(np.uint8)
    charge_action = decode_public_postflux_charges(lattice, public)
    public_action = {
        "blue": tuple(int(edge) for edge in np.flatnonzero(charge_action.blue.correction)),
        "green": tuple(int(edge) for edge in np.flatnonzero(charge_action.green.correction)),
    }
    public_payload = {
        "trial_id": history.trial_id,
        "decision_round": round_index,
        "flux_action_digest": invocation.flux_action.action_digest,
        "public_charge_record": public.astype(int).tolist(),
        "public_charge_action": {
            color: list(edges) for color, edges in public_action.items()
        },
    }
    private_payload = {
        "private_physical_digest": history.private_physical_digest,
        "flux_action_digest": invocation.flux_action.action_digest,
        "active_vertices": list(relations.active_vertices),
        "entanglement_pairs": [list(pair) for pair in relations.entanglement_pairs],
        "internal_second_record": internal.astype(int).tolist(),
    }
    return ActionConditionedSecondRecordV1(
        trial_id=history.trial_id,
        decision_round=round_index,
        flux_action_digest=invocation.flux_action.action_digest,
        public_charge_record=tuple(int(value) for value in public),
        public_charge_action=public_action,
        public_completion_digest=canonical_digest(public_payload),
        private_binding_digest=_digest(private_payload),
        _physical_edges=tuple(int(edge) for edge in np.flatnonzero(physical)),
        _flux_correction_edges=invocation.flux_action.correction_edges,
        _active_vertices=relations.active_vertices,
        _entanglement_pairs=relations.entanglement_pairs,
        _internal_second_record=tuple(int(value) for value in internal),
    )


def derive_private_score(
    history: IntegratedD4HistoryV1,
    invocation: E1PolicyInvocation,
    completion: ActionConditionedSecondRecordV1,
) -> DerivedPrivateScoreV1:
    """Derive winding/residual loss; no logical label is accepted as input."""

    if completion.trial_id != history.trial_id or invocation.report.trial_id != history.trial_id:
        raise ValueError("private score inputs do not share one history")
    if completion.flux_action_digest != invocation.flux_action.action_digest:
        raise ValueError("second record is not bound to this flux action")
    if completion.decision_round != invocation.report.round:
        raise ValueError("second record is not bound to this decision round")
    lattice = paper_periodic_honeycomb(history.size)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[list(completion._physical_edges)] = 1
    expected_physical = history.physical_edge_states[completion.decision_round].astype(np.uint8)
    if not np.array_equal(physical, expected_physical):
        raise ValueError("private completion is not bound to the hidden physical state")
    correction = np.zeros(lattice.edge_count, dtype=np.uint8)
    correction[list(completion._flux_correction_edges)] = 1
    if tuple(np.flatnonzero(correction)) != invocation.flux_action.correction_edges:
        raise ValueError("private completion correction does not match the public action")

    union = physical_correction_union(lattice, physical, correction)
    physical_winding = _has_winding(lattice, physical)
    union_winding = _has_winding(lattice, union)
    terminal_residual = bool(np.any(edge_chain_boundary(lattice, physical ^ correction)))

    charge_winding = False
    if not union_winding:
        relations = infer_periodic_postflux_relations(lattice, physical, correction)
        if (
            relations.active_vertices != completion._active_vertices
            or relations.entanglement_pairs != completion._entanglement_pairs
        ):
            raise ValueError("private relation support does not replay")
        public = np.asarray(completion.public_charge_record, dtype=np.uint8)
        action = decode_public_postflux_charges(lattice, public)
        expected_action = {
            "blue": tuple(int(edge) for edge in np.flatnonzero(action.blue.correction)),
            "green": tuple(int(edge) for edge in np.flatnonzero(action.green.correction)),
        }
        if expected_action != completion.public_charge_action:
            raise ValueError("public charge action does not replay from the public record")
        recovered = score_public_postflux_charge_action(
            lattice,
            relations,
            public,
            action,
            flux_components_homologically_trivial=True,
        )
        charge_winding = bool(recovered.logical_error)

    logical_failure = bool(
        physical_winding or union_winding or terminal_residual or charge_winding
    )
    payload = {
        "trial_id": history.trial_id,
        "public_completion_digest": completion.public_completion_digest,
        "private_binding_digest": completion.private_binding_digest,
        "physical_winding": physical_winding,
        "union_winding": union_winding,
        "terminal_residual": terminal_residual,
        "charge_winding": charge_winding,
        "logical_failure": logical_failure,
    }
    return DerivedPrivateScoreV1(
        trial_id=history.trial_id,
        public_completion_digest=completion.public_completion_digest,
        physical_winding=physical_winding,
        union_winding=union_winding,
        terminal_residual=terminal_residual,
        charge_winding=charge_winding,
        logical_failure=logical_failure,
        scoring_digest=_digest(payload),
    )


def terminal_arm_row(
    history: IntegratedD4HistoryV1,
    invocation: E1PolicyInvocation,
    completion: ActionConditionedSecondRecordV1 | None,
    *,
    failure_reason: str | None = None,
) -> J6TerminalArmRowV1:
    """Return exactly one row and count any missing/malformed completion as loss."""

    if completion is None:
        reason = str(failure_reason or "missing_completion")
        return J6TerminalArmRowV1(
            trial_id=history.trial_id,
            mode=invocation.mode,
            branch=invocation.branch,
            status="failed_closed",
            denominator_included=True,
            logical_failure=True,
            public_completion_digest=None,
            private_scoring_digest=None,
            failure_reason=reason,
        )
    try:
        score = derive_private_score(history, invocation, completion)
    except (AssertionError, RuntimeError, ValueError) as error:
        return J6TerminalArmRowV1(
            trial_id=history.trial_id,
            mode=invocation.mode,
            branch=invocation.branch,
            status="failed_closed",
            denominator_included=True,
            logical_failure=True,
            public_completion_digest=completion.public_completion_digest,
            private_scoring_digest=None,
            failure_reason=f"{type(error).__name__}:{error}",
        )
    return J6TerminalArmRowV1(
        trial_id=history.trial_id,
        mode=invocation.mode,
        branch=invocation.branch,
        status="scored",
        denominator_included=True,
        logical_failure=score.logical_failure,
        public_completion_digest=completion.public_completion_digest,
        private_scoring_digest=score.scoring_digest,
        failure_reason=None,
    )


def _canonical_cumulative_invocations(
    invocations: tuple[E1PolicyInvocation, ...],
    *,
    vertex_count: int,
) -> tuple[tuple[E1PolicyInvocation, ...], int]:
    """Collapse repeated cluster callbacks that decode one full public snapshot.

    The spatial action is an absolute cumulative Pauli-frame estimate at its
    decision round, not an incremental correction.  Therefore one canonical
    action is retained per round and a later round supersedes the earlier
    frame.  Distinct actions at one round fail closed rather than being
    silently combined.
    """

    by_round: dict[int, list[E1PolicyInvocation]] = {}
    for invocation in invocations:
        by_round.setdefault(int(invocation.report.round), []).append(invocation)
    canonical: list[E1PolicyInvocation] = []
    collapsed = 0
    for round_index in sorted(by_round):
        group = by_round[round_index]
        signatures = set()
        for item in group:
            request = item.policy_request
            action = item.flux_action
            if isinstance(request, D4TemporalBoundaryHandoffV1):
                if not isinstance(action, D4TemporalBoundaryActionV1):
                    raise ValueError("temporal handoff has no bound defer action")
                action.validate(request, vertex_count=vertex_count)
                visible = tuple(
                    site for site, labels in item.report.reported_labels if FLUX in labels
                )
                if (
                    request.scheduler_request_digest != item.schedule_request_digest
                    or request.e1_report_digest != item.report.report_digest
                    or request.decision_round != item.report.round
                    or request.odd_endpoints != visible
                ):
                    raise ValueError("temporal handoff is not bound to its public callback")
                signatures.add(
                    ("defer", item.report.report_digest, request.odd_endpoints,
                     request.temporal_boundary_labels)
                )
            else:
                if not isinstance(action, D4FluxActionV1):
                    raise ValueError("spatial request has no physical flux action")
                signatures.add(
                    ("action", request.flux_syndrome_vertices,
                     request.initial_charge_measurements, action.correction_edges)
                )
        if len(signatures) != 1:
            raise ValueError(
                "same-round cluster callbacks produced distinct full-snapshot actions"
            )
        canonical.append(
            min(group, key=lambda item: item.schedule_request_digest)
        )
        collapsed += len(group) - 1
    return tuple(canonical), collapsed


def evaluate_schedule_arm(
    history: IntegratedD4HistoryV1,
    *,
    mode: str,
    branch: str,
    invocations: tuple[E1PolicyInvocation, ...],
) -> J6ArmEvaluationV1:
    """Produce exactly one unconditional row for zero, one, or many callbacks."""

    if mode not in ("syndrome_only", "heralded"):
        raise ValueError("unsupported J6 public mode")
    if branch not in (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    ):
        raise ValueError("unsupported J6 schedule branch")
    if any(
        invocation.mode != mode or invocation.branch != branch
        for invocation in invocations
    ):
        raise ValueError("arm invocations do not match their mode/branch key")

    lattice = paper_periodic_honeycomb(history.size)
    try:
        canonical, collapsed = _canonical_cumulative_invocations(
            invocations, vertex_count=lattice.vertex_count
        )
        completions: list[ActionConditionedSecondRecordV1] = []
        scores: list[DerivedPrivateScoreV1] = []
        physical_commits: list[E1PolicyInvocation] = []
        pending_handoff = False
        for invocation in canonical:
            if isinstance(invocation.flux_action, D4TemporalBoundaryActionV1):
                # No action-conditioned second observation exists for a defer.
                # A later full-snapshot physical action may supersede the
                # ledger; a terminal unresolved ledger remains a failure.
                pending_handoff = True
                continue
            pending_handoff = False
            physical_commits.append(invocation)
            completion = provide_action_conditioned_second_record(
                history, invocation
            )
            completions.append(completion)
            scores.append(derive_private_score(history, invocation, completion))
        if pending_handoff:
            raise ValueError("unresolved_temporal_boundary_handoff")

        final_physical = history.physical_edge_states[-1].astype(np.uint8)
        final_correction = np.zeros(lattice.edge_count, dtype=np.uint8)
        if physical_commits:
            final_correction[list(physical_commits[-1].flux_action.correction_edges)] = 1
        final_union = physical_correction_union(
            lattice, final_physical, final_correction
        )
        physical_winding = any(
            _has_winding(lattice, row) for row in history.physical_edge_states
        )
        union_winding = bool(
            any(score.union_winding for score in scores)
            or _has_winding(lattice, final_union)
        )
        charge_winding = any(score.charge_winding for score in scores)
        terminal_residual = bool(
            np.any(
                edge_chain_boundary(
                    lattice, final_physical ^ final_correction
                )
            )
        )
        logical_failure = bool(
            physical_winding
            or union_winding
            or charge_winding
            or terminal_residual
        )
        return J6ArmEvaluationV1(
            trial_id=history.trial_id,
            mode=mode,
            branch=branch,
            status="scored",
            denominator_included=True,
            logical_failure=logical_failure,
            invocation_count=len(invocations),
            unique_commit_count=len(physical_commits),
            collapsed_duplicate_count=collapsed,
            commit_rounds=tuple(item.report.round for item in physical_commits),
            public_completion_digests=tuple(
                item.public_completion_digest for item in completions
            ),
            physical_winding=physical_winding,
            union_winding=union_winding,
            charge_winding=charge_winding,
            terminal_residual=terminal_residual,
            failure_reason=None,
        )
    except (AssertionError, RuntimeError, ValueError) as error:
        return J6ArmEvaluationV1(
            trial_id=history.trial_id,
            mode=mode,
            branch=branch,
            status="failed_closed",
            denominator_included=True,
            logical_failure=True,
            invocation_count=len(invocations),
            unique_commit_count=0,
            collapsed_duplicate_count=0,
            commit_rounds=(),
            public_completion_digests=(),
            physical_winding=False,
            union_winding=False,
            charge_winding=False,
            terminal_residual=True,
            failure_reason=f"{type(error).__name__}:{error}",
        )


def evaluate_history_matrix(
    history: IntegratedD4HistoryV1,
    *,
    check_positions: tuple[tuple[int, ...], ...],
    geometry: Any,
    connectivity_radius: int = 1,
) -> tuple[J6ArmEvaluationV1, ...]:
    """Run both modes and four schedules and return exactly eight arm rows."""

    try:
        matrix = run_e1_policy_matrix(
            trial_id=history.trial_id,
            record=history.record,
            check_positions=check_positions,
            geometry=geometry,
            size=history.size,
            connectivity_radius=connectivity_radius,
        )
    except (AssertionError, RuntimeError, ValueError) as error:
        # Noisy measurement records may lie outside the static periodic
        # decoder's admissible domain (for example, an odd instantaneous
        # syndrome).  The registered unconditional denominator retains such
        # a decoder abort as one logical failure in every affected arm.
        reason = f"schedule_matrix_{type(error).__name__}:{error}"
        return tuple(
            J6ArmEvaluationV1(
                trial_id=history.trial_id,
                mode=mode,
                branch=branch,
                status="failed_closed",
                denominator_included=True,
                logical_failure=True,
                invocation_count=0,
                unique_commit_count=0,
                collapsed_duplicate_count=0,
                commit_rounds=(),
                public_completion_digests=(),
                physical_winding=False,
                union_winding=False,
                charge_winding=False,
                terminal_residual=True,
                failure_reason=reason,
            )
            for mode in ("syndrome_only", "heralded")
            for branch in (
                "immediate",
                "fixed_delay_1",
                "jit_lyons_brown",
                "offline_full_history",
            )
        )
    rows: list[J6ArmEvaluationV1] = []
    for mode_run in matrix.modes:
        for branch in (
            "immediate",
            "fixed_delay_1",
            "jit_lyons_brown",
            "offline_full_history",
        ):
            arm_invocations = tuple(
                item for item in mode_run.invocations if item.branch == branch
            )
            rows.append(
                evaluate_schedule_arm(
                    history,
                    mode=mode_run.mode,
                    branch=branch,
                    invocations=arm_invocations,
                )
            )
    if len(rows) != 8 or len({(row.mode, row.branch) for row in rows}) != 8:
        raise AssertionError("J6 matrix must emit exactly eight unique arm rows")
    return tuple(rows)
