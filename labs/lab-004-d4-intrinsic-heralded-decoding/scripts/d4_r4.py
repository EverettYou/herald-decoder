"""Exact conditioned logical-sector posterior for bounded D4 fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from math import log2

import numpy as np
from numpy.typing import NDArray

from d4_honeycomb import PeriodicHoneycomb
from d4_matching import classify_closed_chain
from d4_r3 import _supported_nonwinding_candidates, _validate_inputs


@dataclass(frozen=True)
class LogicalSectorEvidence:
    relative_windings: tuple[tuple[int, int], ...]
    candidate_count: int
    log2_evidence: float
    posterior_probability: float


@dataclass(frozen=True)
class ConditionedLogicalPosterior:
    sectors: tuple[LogicalSectorEvidence, ...]
    total_candidate_count: int
    log2_total_evidence: float
    conditional_entropy_bits: float
    bayes_logical_failure_probability: float
    top_two_log2_evidence_gap: float
    reference_error: NDArray[np.uint8]


def _logsumexp2(values: list[float]) -> float:
    maximum = max(values)
    return maximum + log2(sum(2.0 ** (value - maximum) for value in values))


def _relative_sector(
    lattice: PeriodicHoneycomb,
    reference: NDArray[np.uint8],
    candidate: NDArray[np.uint8],
) -> tuple[tuple[int, int], ...]:
    analysis = classify_closed_chain(lattice, reference ^ candidate)
    return tuple(
        sorted(
            {
                winding
                for component in analysis.components
                for winding in component.winding_vectors
            }
        )
    )


def exact_conditioned_logical_posterior(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    *,
    maximum_edges: int = 20,
    reference_error: NDArray[np.generic] | None = None,
) -> ConditionedLogicalPosterior:
    """Sum ``P(s|E)P(E)`` over every relative logical sector.

    The canonical reference is the lexicographically first compatible error
    chain.  Changing reference relabels sectors but does not change their
    evidence multiset, entropy, or Bayes risk.  This is the R4 operation that a
    configuration-MAP decoder cannot replace.
    """

    flux, charge = _validate_inputs(
        lattice, flux_syndrome, charge_outcomes, error_rate, maximum_edges
    )
    candidates, _ = _supported_nonwinding_candidates(
        lattice, flux, charge, error_rate
    )
    if not candidates:
        raise ValueError("observation has no supported nonwinding explanation")
    if reference_error is None:
        reference = candidates[0].error.copy()
    else:
        reference = np.asarray(reference_error, dtype=np.uint8)
        if reference.shape != (lattice.edge_count,) or np.any(reference > 1):
            raise ValueError("reference_error must be a binary edge chain")
        if not any(np.array_equal(reference, candidate.error) for candidate in candidates):
            raise ValueError("reference_error is not a compatible explanation")
        reference = reference.copy()
    grouped: dict[tuple[tuple[int, int], ...], list[float]] = {}
    for candidate in candidates:
        grouped.setdefault(
            _relative_sector(lattice, reference, candidate.error), []
        ).append(candidate.log2_joint_probability)
    sector_logs = {
        sector: _logsumexp2(values) for sector, values in grouped.items()
    }
    total_log = _logsumexp2(list(sector_logs.values()))
    sectors = tuple(
        LogicalSectorEvidence(
            sector,
            len(grouped[sector]),
            sector_logs[sector],
            2.0 ** (sector_logs[sector] - total_log),
        )
        for sector in sorted(grouped)
    )
    probabilities = [sector.posterior_probability for sector in sectors]
    entropy = -sum(
        probability * log2(probability)
        for probability in probabilities
        if probability > 0.0
    )
    ranked_logs = sorted(sector_logs.values(), reverse=True)
    gap = (
        float("inf")
        if len(ranked_logs) == 1
        else ranked_logs[0] - ranked_logs[1]
    )
    return ConditionedLogicalPosterior(
        sectors=sectors,
        total_candidate_count=len(candidates),
        log2_total_evidence=total_log,
        conditional_entropy_bits=entropy,
        bayes_logical_failure_probability=1.0 - max(probabilities),
        top_two_log2_evidence_gap=gap,
        reference_error=reference,
    )
