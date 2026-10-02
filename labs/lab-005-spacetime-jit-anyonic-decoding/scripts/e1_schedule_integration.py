"""Causal translation from one schedule callback to a typed E1 public record.

This module implements only the registered I1 observation adapter.  It does
not invoke the D4 policy, compare schedule branches, or produce performance
data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

import numpy as np

from baseline_harness import (
    BaselineRun,
    InnerDecoderRequest,
    InnerDecoderResponse,
    prefix_digest,
    run_shared_history_baselines,
)
from d4_projector_instrument import (
    CHARGE,
    FLUX,
    SCHEMA_VERSION,
    PublicReportedRecordV1,
    typed_postflux_record_to_observation,
    typed_record_to_commit_request,
)
from d4_spatial_policy import (
    D4ChargeActionV1,
    D4FluxActionV1,
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    D4TemporalBoundaryActionV1,
    D4TemporalBoundaryHandoffV1,
    canonical_digest,
    decode_flux_action,
    decode_temporal_boundary_handoff,
    paper_periodic_honeycomb,
)
from d4_temporal_composition import (
    PerfectD4TemporalStateV1,
    advance_round,
    commit_flux,
    open_temporal_state,
    supply_post_flux,
)
from lyons_absorber import AbsorberGeometry
from spacetime_record import SpacetimeRecord


Mode = Literal["syndrome_only", "heralded"]


def derive_round_local_e1_record(
    request: InnerDecoderRequest,
    *,
    size: int,
) -> PublicReportedRecordV1:
    """Translate the final public row of a schedule callback into E1 labels.

    Syndrome membership maps to ``m_flux`` and herald membership maps to
    ``e_charge`` independently, so one site may carry both public labels.  The
    complete history and all private truth/fault fields are intentionally
    unavailable to this function.
    """

    if size != 2:
        raise ValueError("the registered I1 adapter is bounded to paper L=2")
    if not request.trial_id:
        raise ValueError("schedule request trial_id must be nonempty")
    prefix = request.prefix
    if request.prefix_digest != prefix_digest(prefix):
        raise ValueError("schedule request is not bound to its causal prefix")

    vertex_count = paper_periodic_honeycomb(size).vertex_count
    expected_readout_shape = (prefix.final_round + 1, vertex_count)
    expected_detector_shape = (prefix.final_round, vertex_count)
    if prefix.final_round < 0:
        raise ValueError("causal prefix round must be nonnegative")
    if np.asarray(prefix.syndrome_readout).shape != expected_readout_shape:
        raise ValueError("syndrome readout must cover every D4 site through the round")
    if np.asarray(prefix.herald_readout).shape != expected_readout_shape:
        raise ValueError("herald readout must cover every D4 site through the round")
    if np.asarray(prefix.syndrome_detectors).shape != expected_detector_shape:
        raise ValueError("syndrome detectors do not match the causal prefix horizon")

    flux_row = np.asarray(prefix.syndrome_readout[-1], dtype=np.bool_)
    charge_row = np.asarray(prefix.herald_readout[-1], dtype=np.bool_)
    reports = tuple(
        (
            site,
            tuple(
                label
                for label, present in ((CHARGE, charge_row[site]), (FLUX, flux_row[site]))
                if bool(present)
            ),
        )
        for site in range(vertex_count)
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "trial_id": request.trial_id,
        "round": prefix.final_round,
        "reported_labels": [
            {"site": site, "labels": list(labels)} for site, labels in reports
        ],
        "bound_action_digest": None,
    }
    return PublicReportedRecordV1(
        schema_version=SCHEMA_VERSION,
        trial_id=request.trial_id,
        round=prefix.final_round,
        reported_labels=reports,
        bound_action_digest=None,
        report_digest=canonical_digest(payload),
    )


@dataclass(frozen=True)
class E1PolicyInvocation:
    mode: Mode
    branch: str
    noncausal: bool
    schedule_request_digest: str
    report: PublicReportedRecordV1
    policy_request: D4SpatialCommitRequestV1 | D4TemporalBoundaryHandoffV1
    flux_action: D4FluxActionV1 | D4TemporalBoundaryActionV1


@dataclass
class E1PolicyDecoder:
    """Actual stage-1 D4 policy callback used by the I2/I3 matrix."""

    mode: Mode
    size: int = 2
    version: str = "d4-stage1-e1-integration-v2"
    requests: list[InnerDecoderRequest] = field(default_factory=list)
    invocations: list[E1PolicyInvocation] = field(default_factory=list)

    @property
    def implementation_digest(self) -> str:
        return canonical_digest(
            {
                "protocol": "lab005-d4-stage1-e1-integration-v1",
                "class": type(self).__name__,
                "version": self.version,
            }
        )

    def __call__(self, request: InnerDecoderRequest) -> InnerDecoderResponse:
        self.requests.append(request)
        report = derive_round_local_e1_record(request, size=self.size)
        policy_request_id = canonical_digest(
            {
                "protocol": "lab005-d4-stage1-request-v1",
                "schedule_request_digest": request.request_digest,
                "mode": self.mode,
            }
        )
        flux_vertices = tuple(
            site for site, labels in report.reported_labels if FLUX in labels
        )
        if len(flux_vertices) % 2:
            vertex_count = paper_periodic_honeycomb(self.size).vertex_count
            handoff = D4TemporalBoundaryHandoffV1.from_public(
                request_id=policy_request_id,
                decision_round=report.round,
                scheduler_request_digest=request.request_digest,
                scheduler_prefix_digest=request.prefix_digest,
                e1_report_digest=report.report_digest,
                flux_vertices=flux_vertices,
                vertex_count=vertex_count,
            )
            # The public spatial policy receives the augmented request and
            # validates its binding before emitting a no-physics defer action.
            policy_request = D4TemporalBoundaryHandoffV1.from_dict(
                handoff.to_dict(), vertex_count=vertex_count
            )
            action = decode_temporal_boundary_handoff(
                policy_request,
                vertex_count=vertex_count,
                expected_request_id=policy_request_id,
                expected_scheduler_request_digest=request.request_digest,
                expected_scheduler_prefix_digest=request.prefix_digest,
                expected_e1_report_digest=report.report_digest,
                expected_round=report.round,
                expected_flux_vertices=flux_vertices,
            )
        else:
            policy_request = typed_record_to_commit_request(
                report,
                request_id=policy_request_id,
                size=self.size,
                mode=self.mode,
                scheduler_prefix_digest=request.prefix_digest,
            )
            action = decode_flux_action(policy_request)
        self.invocations.append(
            E1PolicyInvocation(
                mode=self.mode,
                branch=request.branch,
                noncausal=request.noncausal,
                schedule_request_digest=request.request_digest,
                report=report,
                policy_request=policy_request,
                flux_action=action,
            )
        )
        return InnerDecoderResponse(
            decoder_version=self.version,
            implementation_digest=self.implementation_digest,
            request_digest=request.request_digest,
            correction_token=action.action_digest,
        )


@dataclass(frozen=True)
class E1ModeRun:
    mode: Mode
    baseline: BaselineRun
    invocations: tuple[E1PolicyInvocation, ...]


@dataclass(frozen=True)
class E1PolicyMatrixRun:
    trial_id: str
    history_digest: str
    modes: tuple[E1ModeRun, ...]


def run_e1_policy_matrix(
    *,
    trial_id: str,
    record: SpacetimeRecord,
    check_positions: tuple[tuple[int, ...], ...],
    geometry: AbsorberGeometry,
    size: int = 2,
    connectivity_radius: int = 1,
) -> E1PolicyMatrixRun:
    """Run both actual stage-1 policy modes over all four schedule branches."""

    mode_runs: list[E1ModeRun] = []
    for mode in ("syndrome_only", "heralded"):
        decoder = E1PolicyDecoder(mode=mode, size=size)
        baseline = run_shared_history_baselines(
            trial_id=trial_id,
            record=record,
            check_positions=check_positions,
            geometry=geometry,
            decoder=decoder,
            connectivity_radius=connectivity_radius,
        )
        mode_runs.append(E1ModeRun(mode, baseline, tuple(decoder.invocations)))

    history_digests = {run.baseline.history_digest for run in mode_runs}
    if len(history_digests) != 1:
        raise AssertionError("policy modes did not share one visible history")
    return E1PolicyMatrixRun(
        trial_id=trial_id,
        history_digest=history_digests.pop(),
        modes=tuple(mode_runs),
    )


@dataclass(frozen=True)
class E2PostFluxFixture:
    """Public output of an external physical post-action adapter."""

    record: PublicReportedRecordV1
    active_vertices: tuple[int, ...]
    entanglement_pairs: tuple[tuple[int, int], ...]


PostFluxProvider = Callable[[E1PolicyInvocation], E2PostFluxFixture]


@dataclass(frozen=True)
class E2CompletionCell:
    mode: Mode
    branch: str
    noncausal: bool
    policy_request: D4SpatialCommitRequestV1
    flux_action: D4FluxActionV1
    postflux_record: PublicReportedRecordV1
    postflux_observation: D4PostFluxObservationV1
    charge_action: D4ChargeActionV1
    completion_state_digest: str
    next_round: int | None
    advanced_state_digest: str | None


@dataclass(frozen=True)
class E2CompletionMatrixRun:
    trial_id: str
    history_digest: str
    e1_matrix: E1PolicyMatrixRun
    cells: tuple[E2CompletionCell, ...]


def _next_policy_prefix_digest(
    *,
    invocation: E1PolicyInvocation,
    record: SpacetimeRecord,
    size: int,
) -> tuple[int, str] | None:
    next_round = invocation.report.round + 1
    if next_round >= record.readout_rounds:
        return None
    prefix = record.causal_prefix(next_round)
    request = InnerDecoderRequest(
        branch=invocation.branch,  # type: ignore[arg-type]
        trial_id=invocation.report.trial_id,
        prefix_digest=prefix_digest(prefix),
        prefix=prefix,
        cluster_id="e2-next-round",
        event_ids=(),
        noncausal=invocation.noncausal,
    )
    next_report = derive_round_local_e1_record(request, size=size)
    next_policy = typed_record_to_commit_request(
        next_report,
        request_id=canonical_digest(
            {
                "protocol": "lab005-d4-e2-next-round-v1",
                "prior_action_digest": invocation.flux_action.action_digest,
                "next_round": next_round,
                "mode": invocation.mode,
            }
        ),
        size=size,
        mode=invocation.mode,
        scheduler_prefix_digest=request.prefix_digest,
    )
    return next_round, next_policy.causal_prefix_digest


def run_e2_completion_matrix(
    *,
    trial_id: str,
    record: SpacetimeRecord,
    check_positions: tuple[tuple[int, ...], ...],
    geometry: AbsorberGeometry,
    postflux_provider: PostFluxProvider,
    size: int = 2,
    connectivity_radius: int = 1,
) -> E2CompletionMatrixRun:
    """Complete all registered E1 cells through public charge recovery."""

    e1_matrix = run_e1_policy_matrix(
        trial_id=trial_id,
        record=record,
        check_positions=check_positions,
        geometry=geometry,
        size=size,
        connectivity_radius=connectivity_radius,
    )
    cells: list[E2CompletionCell] = []
    layouts: dict[str, tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = {}
    report_rules: dict[str, tuple[tuple[int, tuple[str, ...]], ...]] = {}

    for mode_run in e1_matrix.modes:
        for invocation in mode_run.invocations:
            if isinstance(invocation.policy_request, D4TemporalBoundaryHandoffV1):
                raise ValueError(
                    "unresolved_temporal_boundary_handoff: no physical post-flux stage"
                )
            state = open_temporal_state(
                trial_id=trial_id,
                size=size,
                mode=invocation.mode,
                initial_round=invocation.report.round,
                causal_prefix_digest=invocation.policy_request.causal_prefix_digest,
            )
            committed = commit_flux(state, invocation.policy_request)
            if committed.flux_action != invocation.flux_action:
                raise AssertionError("E2 did not preserve the exact E1 flux action")

            fixture = postflux_provider(invocation)
            layout = (fixture.active_vertices, fixture.entanglement_pairs)
            prior_layout = layouts.setdefault(invocation.branch, layout)
            if prior_layout != layout:
                raise AssertionError("public modes did not share one measurement layout")
            prior_rule = report_rules.setdefault(
                invocation.branch, fixture.record.reported_labels
            )
            if prior_rule != fixture.record.reported_labels:
                raise AssertionError("public modes did not share one report rule")

            observation = typed_postflux_record_to_observation(
                fixture.record,
                request=invocation.policy_request,
                flux_action=invocation.flux_action,
                active_vertices=fixture.active_vertices,
                entanglement_pairs=fixture.entanglement_pairs,
            )
            completed = supply_post_flux(committed, observation)
            next_prefix = _next_policy_prefix_digest(
                invocation=invocation,
                record=record,
                size=size,
            )
            advanced: PerfectD4TemporalStateV1 | None = None
            if next_prefix is not None:
                next_round, next_digest = next_prefix
                advanced = advance_round(
                    completed,
                    next_round=next_round,
                    causal_prefix_digest=next_digest,
                )
            cells.append(
                E2CompletionCell(
                    mode=invocation.mode,
                    branch=invocation.branch,
                    noncausal=invocation.noncausal,
                    policy_request=invocation.policy_request,
                    flux_action=invocation.flux_action,
                    postflux_record=fixture.record,
                    postflux_observation=observation,
                    charge_action=completed.charge_action,
                    completion_state_digest=completed.state_digest,
                    next_round=None if next_prefix is None else next_prefix[0],
                    advanced_state_digest=(
                        None if advanced is None else advanced.state_digest
                    ),
                )
            )

    if len(cells) != 8:
        raise AssertionError("E2 completion matrix must contain eight cells")
    return E2CompletionMatrixRun(
        trial_id=trial_id,
        history_digest=e1_matrix.history_digest,
        e1_matrix=e1_matrix,
        cells=tuple(cells),
    )
