"""Exact completeness audit for the registered E3 repeated-D4 kernel.

This module does not construct a stochastic history.  It inventories the
verified public/private interfaces and runs only exact normalization and
signature checks needed to decide whether they already define

    P(X[t+1], O[t+1] | X[t], F[t], A[t]).

Missing factors remain missing; the audit never fills them with an implicit
memoryless or independence assumption.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Literal

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LAB004_SCRIPTS = ROOT / "labs" / "lab-004-d4-intrinsic-heralded-decoding" / "scripts"
for path in (str(Path(__file__).resolve().parent), str(LAB004_SCRIPTS)):
    if path not in sys.path:
        sys.path.insert(0, path)

from d4_projector_instrument import (  # noqa: E402
    CHARGE,
    FLUX,
    REGISTERED_LABELS,
    project_hidden_state,
    project_post_action_charge_state,
    report_distribution,
)
from d4_recovery import decode_and_score_flux_recovery  # noqa: E402
from d4_sampler import observation_from_error_edges  # noqa: E402
from d4_temporal_composition import score_frozen_transition  # noqa: E402
from e1_schedule_integration import run_e2_completion_matrix  # noqa: E402
from generic_history import GenericNoiseParameters, herald_confusion_matrix  # noqa: E402


FactorStatus = Literal["complete", "partial", "localized_only", "missing"]


@dataclass(frozen=True)
class KernelFactorAudit:
    factor: str
    status: FactorStatus
    supported_parts: tuple[str, ...]
    missing_parts: tuple[str, ...]
    exact_checks: tuple[str, ...]
    scientific_boundary: str


def _parameters(function: Any) -> tuple[str, ...]:
    return tuple(inspect.signature(function).parameters)


def _e1_report_normalization() -> dict[str, float]:
    sums: dict[str, float] = {}
    for true_label in REGISTERED_LABELS:
        law = report_distribution(
            true_label,
            false_negative=0.13,
            false_positive={FLUX: 0.07, CHARGE: 0.11},
        )
        raw_sum = float(sum(law.values()))
        if not np.isclose(raw_sum, 1.0):
            raise AssertionError(f"E1 report law is not normalized for {true_label}")
        sums[true_label] = 1.0
    return sums


def _generic_report_normalization() -> tuple[float, ...]:
    matrix = herald_confusion_matrix(
        GenericNoiseParameters(
            p_data=0.03,
            p_syndrome=0.05,
            p_fp=0.07,
            p_fn=0.11,
            p_confuse=0.13,
        )
    )
    sums = tuple(float(value) for value in matrix.sum(axis=1))
    if not np.allclose(sums, 1.0):
        raise AssertionError("generic categorical report matrix is not normalized")
    return sums


def build_transition_kernel_audit() -> dict[str, Any]:
    """Return the complete registered K1-K4 source/interface audit."""

    signatures = {
        "static_spatial_observation": _parameters(observation_from_error_edges),
        "hidden_projector_update": _parameters(project_hidden_state),
        "post_action_projector_update": _parameters(project_post_action_charge_state),
        "e2_completion_runner": _parameters(run_e2_completion_matrix),
        "single_flux_truth_scorer": _parameters(decode_and_score_flux_recovery),
        "frozen_transition_scorer": _parameters(score_frozen_transition),
    }
    e1_sums = _e1_report_normalization()
    generic_sums = _generic_report_normalization()

    k1 = KernelFactorAudit(
        factor="K1-physical-state-evolution",
        status="missing",
        supported_parts=(
            "generic binary edge-fault increments and cumulative syndrome identity",
            "static D4 fusion record conditional on one supplied physical edge chain",
            "deterministic hidden projector digest chaining for externally supplied true labels",
        ),
        missing_parts=(
            "a normalized law for the next true D4 projector state given the previous state and a data-fault increment",
            "a physical residual-state update after applying a public correction",
            "a proof that previous fusion/projector information may be discarded between rounds",
        ),
        exact_checks=(
            "observation_from_error_edges has no previous-state or public-action input",
            "project_hidden_state requires externally supplied true_labels and defines no probability law",
        ),
        scientific_boundary="Independent per-round fusion resampling would be a new model assumption, not a consequence of the current source or interface.",
    )
    k2 = KernelFactorAudit(
        factor="K2-public-measurement-kernel",
        status="localized_only",
        supported_parts=(
            "normalized local E1 false-positive/false-negative report law",
            "normalized generic none/blue/green confusion matrix",
            "typed multi-label reports with a perfect-report limit",
            "localized Jing-2025 five-star time-like-herald fixture",
        ),
        missing_parts=(
            "a joint multisite repeated D4 true-outcome distribution",
            "cross-round correlations induced by noncommuting/quasi-stabilizer state update",
            "a derived identification between the generic categorical G law and D4 species reports",
        ),
        exact_checks=(
            f"E1 row sums={tuple(e1_sums[label] for label in REGISTERED_LABELS)}",
            f"generic categorical row sums={generic_sums}",
        ),
        scientific_boundary="Normalized classical corruption after a supplied truth record does not define the missing truth-record dynamics.",
    )
    k3 = KernelFactorAudit(
        factor="K3-action-conditioned-postflux-kernel",
        status="missing",
        supported_parts=(
            "E2 exact action/report digest binding and temporal order",
            "single-shot Lab-004 post-flux relations and parity-supported charge sampler on private truth",
            "deterministic projector update when post-action charge labels are externally supplied",
        ),
        missing_parts=(
            "a repeated-state law mapping the pre-action physical/projector state and flux action to the next physical state",
            "a normalized public charge/vacuum report law derived from that updated state",
        ),
        exact_checks=(
            "run_e2_completion_matrix requires an external postflux_provider",
            "project_post_action_charge_state requires external charge_labels",
        ),
        scientific_boundary="E2 validates consumption and binding of a physical report; it does not generate that report.",
    )
    k4 = KernelFactorAudit(
        factor="K4-private-logical-scorer",
        status="partial",
        supported_parts=(
            "ground-state-relative homology scoring for one supplied spatial physical chain and correction",
            "truth exclusion from the public decoder",
            "private score attachment only after a frozen E2 completion",
        ),
        missing_parts=(
            "a canonical accumulated spacetime residual that composes multiple data-fault increments and applied two-stage corrections",
            "a derivation that the single-shot union/homology criterion is sufficient for that accumulated state",
        ),
        exact_checks=(
            "decode_and_score_flux_recovery consumes one physical_error chain",
            "score_frozen_transition consumes an externally supplied logical_failure_truth boolean",
        ),
        scientific_boundary="The existing scorer can audit a single completed spatial cycle but cannot derive repeated-history logical truth from public state alone.",
    )

    factors = (k1, k2, k3, k4)
    if any(factor.status == "complete" for factor in factors):
        raise AssertionError("the registered audit expects no fully complete K1-K4 factor")
    if "postflux_provider" not in signatures["e2_completion_runner"]:
        raise AssertionError("E2 runner no longer exposes its physical-provider boundary")
    if "logical_failure_truth" not in signatures["frozen_transition_scorer"]:
        raise AssertionError("private scorer no longer exposes its truth-side boundary")

    payload = {
        "schema_version": 1,
        "status": "incomplete",
        "question": "Do current components define a normalized causal repeated D4 transition kernel and private logical scorer?",
        "answer": "No. Classical report kernels and single-cycle scoring are available, but cross-round hidden-state evolution and action-conditioned physical post-flux generation are not specified.",
        "factors": [asdict(factor) for factor in factors],
        "interface_signatures": {key: list(value) for key, value in signatures.items()},
        "normalization": {
            "e1_local_report_row_sums": e1_sums,
            "generic_categorical_row_sums": list(generic_sums),
        },
        "earliest_missing_dependency": "K1-physical-state-evolution",
        "dependent_missing_dependency": "K3-action-conditioned-postflux-kernel",
        "partially_available": [
            "K2 normalized classical report layers on externally supplied truth",
            "K4 single-cycle private homology scoring",
        ],
        "unresolved_physical_models": [
            "explicit phenomenological Markov transition on a declared hidden D4 state",
            "stateful projector or density-operator evolution",
            "ancilla/circuit-derived repeated extraction channel",
        ],
        "bounded_checks_can_discriminate_models": False,
        "sampling": 0,
        "prohibited_next_steps": [
            "independent per-round fusion resampling",
            "stochastic schedule pilot",
            "logical-error-rate or threshold estimation",
        ],
    }
    return json.loads(json.dumps(payload, sort_keys=True))
