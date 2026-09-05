"""Published D4 practical-matching graph and edge-weight rule.

Jing et al. use unit weights for the unheralded baseline and
``w_e = 1 - n_e K`` for the intrinsically heralded decoder, where ``n_e`` is
the number of measured intermediate Abelian charges adjacent to edge ``e``.
They set ``K`` to three times the total number of honeycomb edges, equal to
``27 L^2`` in their nine-edge-per-unit-cell normalization.  Expressing the
rule as ``3 * edge_count`` avoids silently identifying a primitive honeycomb
cell with the paper's larger three-colour kagome unit cell.  These are matching
objective weights, not probabilities or posterior LLRs inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pymatching
from numpy.typing import NDArray

from d4_honeycomb import ConstraintAnalysis, PeriodicHoneycomb, generate_loop_constraints


@dataclass(frozen=True)
class D4MatchingResult:
    correction: NDArray[np.uint8]
    objective_weight: float


@dataclass(frozen=True)
class D4FluxRecoveryResult:
    """Truth-referenced audit of the first stage of the published decoder.

    The decoder itself consumes only the measured flux syndrome and edge
    weights. ``physical_error`` is supplied solely by a simulation fixture so
    the recovery can be scored. Pauli-X operators compose over GF(2), so the
    post-recovery operator is the symmetric difference (XOR). Appendix A uses
    a different object for the first logical decision: the Boolean union of
    physical and correction strings, because both rounds contribute to the
    post-flux stabilizer-entanglement history. These objects must not be
    conflated.

    This object deliberately stops before the paper's second, charge-recovery
    stage.  Constructing the effective blue/green Pauli-Z strings requires the
    source's post-flux DSU rules and must not be guessed from the honeycomb
    incidence graph.
    """

    syndrome: NDArray[np.uint8]
    correction: NDArray[np.uint8]
    residual: NDArray[np.uint8]
    residual_analysis: ConstraintAnalysis
    physical_correction_union: NDArray[np.uint8]
    union_analysis: ConstraintAnalysis
    objective_weight: float
    logical_error: bool


def d4_check_matrix(lattice: PeriodicHoneycomb) -> NDArray[np.uint8]:
    """Return the vertex-edge incidence matrix over GF(2)."""

    check = np.zeros(
        (lattice.vertex_count, lattice.edge_count), dtype=np.uint8
    )
    for edge, (left, right) in enumerate(lattice.edge_vertices):
        check[int(left), edge] = 1
        check[int(right), edge] = 1
    return check


def edge_chain_boundary(
    lattice: PeriodicHoneycomb,
    edge_chain: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Return the GF(2) endpoint syndrome of one binary edge chain."""

    chain = np.asarray(edge_chain, dtype=np.uint8)
    if chain.shape != (lattice.edge_count,) or np.any(chain > 1):
        raise ValueError("edge_chain must be binary with one value per edge")
    return np.asarray((d4_check_matrix(lattice) @ chain) % 2, dtype=np.uint8)


def compose_edge_chains(
    lattice: PeriodicHoneycomb,
    *edge_chains: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Compose Pauli edge strings as their GF(2) symmetric difference."""

    result = np.zeros(lattice.edge_count, dtype=np.uint8)
    for edge_chain in edge_chains:
        chain = np.asarray(edge_chain, dtype=np.uint8)
        if chain.shape != (lattice.edge_count,) or np.any(chain > 1):
            raise ValueError("each edge chain must be binary with one value per edge")
        result ^= chain
    return result


def physical_correction_union(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    correction: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Return the source's Boolean physical/correction string union.

    Unlike Pauli composition, an edge present in both inputs remains present:
    the union records the two-round stabilizer history used by Appendix A's
    post-flux parity constraints and logical-error criterion.
    """

    selected: list[NDArray[np.uint8]] = []
    for chain in (physical_error, correction):
        value = np.asarray(chain, dtype=np.uint8)
        if value.shape != (lattice.edge_count,) or np.any(value > 1):
            raise ValueError("physical and correction chains must be binary")
        selected.append(value)
    return np.asarray(selected[0] | selected[1], dtype=np.uint8)


def classify_physical_correction_union(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    correction: NDArray[np.generic],
) -> ConstraintAnalysis:
    """Classify connected components of the Appendix-A Boolean union."""

    union = physical_correction_union(lattice, physical_error, correction)
    return generate_loop_constraints(lattice, union.astype(bool))


def classify_closed_chain(
    lattice: PeriodicHoneycomb,
    edge_chain: NDArray[np.generic],
) -> ConstraintAnalysis:
    """Classify connected components of a closed recovery residual.

    The universal-cover traversal in ``generate_loop_constraints`` records a
    nonzero winding vector for every homologically nontrivial component,
    including branched closed components.  Open chains are rejected because a
    logical-recovery score is meaningful only after syndrome cancellation.
    """

    chain = np.asarray(edge_chain, dtype=np.uint8)
    if np.any(edge_chain_boundary(lattice, chain)):
        raise ValueError("recovery residual must be a closed edge chain")
    return generate_loop_constraints(lattice, chain.astype(bool))


def syndrome_only_weights(lattice: PeriodicHoneycomb) -> NDArray[np.float64]:
    """Return the paper's unit-weight unheralded matching objective."""

    return np.ones(lattice.edge_count, dtype=np.float64)


def published_herald_weights(
    lattice: PeriodicHoneycomb,
    charge_outcomes: NDArray[np.generic],
    *,
    forcing_scale: float | None = None,
) -> NDArray[np.float64]:
    """Return ``1 - n_e K`` using measured charge-one endpoints.

    Charge records use ``-1`` for unmeasured, ``0`` for vacuum, and ``1`` for
    an Abelian charge.  Only measured charge-one outcomes contribute to
    ``n_e``.  The optional scale exists for bounded semantic tests.  By
    default, ``K=3E`` where ``E`` is the actual honeycomb edge count; this is
    the invariant source rule and equals ``27 L^2`` only on a source-normalized
    lattice with ``9 L^2`` edges.
    """

    charge = np.asarray(charge_outcomes, dtype=np.int64)
    if charge.shape != (lattice.vertex_count,):
        raise ValueError("charge_outcomes must have one value per vertex")
    if not np.all(np.isin(charge, (-1, 0, 1))):
        raise ValueError("charge outcomes must be -1, 0, or 1")
    scale = (
        3.0 * lattice.edge_count
        if forcing_scale is None
        else float(forcing_scale)
    )
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("forcing_scale must be finite and positive")
    adjacent_charges = np.sum(
        charge[lattice.edge_vertices] == 1,
        axis=1,
        dtype=np.int64,
    )
    return 1.0 - scale * adjacent_charges.astype(np.float64)


def decode_flux_syndrome(
    lattice: PeriodicHoneycomb,
    syndrome: NDArray[np.generic],
    edge_weights: NDArray[np.generic],
) -> D4MatchingResult:
    """Decode one even flux syndrome with PyMatching on the periodic graph."""

    detectors = np.asarray(syndrome, dtype=np.uint8)
    if detectors.shape != (lattice.vertex_count,):
        raise ValueError("syndrome must have one value per vertex")
    if np.any(detectors > 1):
        raise ValueError("syndrome must be binary")
    if int(np.sum(detectors)) % 2:
        raise ValueError("periodic honeycomb syndrome must have even parity")
    weights = np.asarray(edge_weights, dtype=np.float64)
    if weights.shape != (lattice.edge_count,) or not np.all(np.isfinite(weights)):
        raise ValueError("edge_weights must be finite with one value per edge")

    matching = pymatching.Matching.from_check_matrix(
        d4_check_matrix(lattice),
        weights=weights,
    )
    correction, objective_weight = matching.decode(
        detectors, return_weight=True
    )
    correction = np.asarray(correction, dtype=np.uint8)
    if not np.array_equal(
        (d4_check_matrix(lattice) @ correction) % 2,
        detectors,
    ):
        raise AssertionError("PyMatching correction does not reproduce syndrome")
    return D4MatchingResult(correction, float(objective_weight))
