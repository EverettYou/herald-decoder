"""Validated local support and likelihood core for the Lab 004 D4 record.

For the single-colour red-X channel in Jing et al., the red m-flux syndrome
must equal the boundary of the error subgraph.  Intermediate blue/green star
measurements occur only at degree-two vertices of that subgraph; odd-degree
vertices host m-fluxes and are not measured.  If C independent parity
constraints are satisfied, Appendix A gives

    P(s | E) = 2 ** (C - N_internal),

where N_internal is the number of measured intermediate stars.  This is the
first equality in Eq. A12 and avoids relying on a geometry-specific rewrite in
terms of error length, Y intersections, and flux count.

This module validates an externally supplied constraint list.  Constructing
the complete periodic-honeycomb constraint/homology list is the next R1 gate;
it is intentionally not guessed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp2
from typing import Iterable

import numpy as np
from numpy.typing import NDArray


BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int_]


@dataclass(frozen=True)
class ParityConstraint:
    """One independent parity relation among measured charge outcomes."""

    vertices: tuple[int, ...]
    required_parity: int = 0
    label: str = ""

    def __post_init__(self) -> None:
        if not self.vertices:
            raise ValueError("a parity constraint must contain vertices")
        if len(set(self.vertices)) != len(self.vertices):
            raise ValueError("constraint vertices must be unique")
        if self.required_parity not in (0, 1):
            raise ValueError("required_parity must be 0 or 1")


@dataclass(frozen=True)
class D4ObservationEvaluation:
    allowed: bool
    probability: float
    log2_probability: int | None
    internal_vertices: tuple[int, ...]
    reason: str | None = None


def _incidence_matrix(edge_vertices: NDArray[np.generic]) -> BoolArray:
    endpoints = np.asarray(edge_vertices, dtype=np.int64)
    if endpoints.ndim != 2 or endpoints.shape[1] != 2:
        raise ValueError("edge_vertices must have shape (edges, 2)")
    if endpoints.size and endpoints.min() < 0:
        raise ValueError("vertex ids must be nonnegative")
    if any(left == right for left, right in endpoints):
        raise ValueError("self-loop edges are not supported")
    vertex_count = int(endpoints.max()) + 1 if endpoints.size else 0
    incidence = np.zeros((endpoints.shape[0], vertex_count), dtype=np.bool_)
    for edge, (left, right) in enumerate(endpoints):
        incidence[edge, left] = True
        incidence[edge, right] = True
    return incidence


def evaluate_observation(
    edge_vertices: NDArray[np.generic],
    error_edges: NDArray[np.generic],
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    constraints: Iterable[ParityConstraint] = (),
) -> D4ObservationEvaluation:
    """Validate support and evaluate P(s|E) for supplied independent constraints.

    The production record is a binary e-charge herald: 1 for a matching
    Abelian e charge and 0 otherwise.  A vacuum fusion result must not reveal
    the hidden degree-two support.  The old -1/0/1 representation remains
    accepted only to audit preserved historical artifacts.
    """

    incidence = _incidence_matrix(edge_vertices)
    selected = np.asarray(error_edges, dtype=np.bool_)
    if selected.shape != (incidence.shape[0],):
        raise ValueError("error_edges must have one value per edge")
    flux = np.asarray(flux_syndrome, dtype=np.bool_)
    charge = np.asarray(charge_outcomes, dtype=np.int64)
    vertex_count = incidence.shape[1]
    if flux.shape != (vertex_count,) or charge.shape != (vertex_count,):
        raise ValueError("syndrome arrays must have one value per vertex")
    if not np.isin(charge, (-1, 0, 1)).all():
        raise ValueError("charge outcomes must be -1, 0, or 1")

    degrees = incidence[selected].sum(axis=0, dtype=np.int64)
    expected_flux = (degrees % 2).astype(np.bool_)
    internal = degrees == 2
    internal_vertices = tuple(int(v) for v in np.flatnonzero(internal))

    if not np.array_equal(flux, expected_flux):
        return D4ObservationEvaluation(
            False, 0.0, None, internal_vertices, "flux syndrome is not boundary(E)"
        )
    legacy_support_revealed = bool(np.any(charge == -1))
    if legacy_support_revealed and np.any((charge != -1) != internal):
        return D4ObservationEvaluation(False, 0.0, None, internal_vertices,
                                       "charge measurements do not match degree-two internal support")
    if not legacy_support_revealed and np.any((charge == 1) & ~internal):
        return D4ObservationEvaluation(False, 0.0, None, internal_vertices,
                                       "e-charge herald occurs away from degree-two support")

    checked_constraints = tuple(constraints)
    for constraint in checked_constraints:
        vertices = np.asarray(constraint.vertices, dtype=np.int64)
        if np.any(vertices < 0) or np.any(vertices >= vertex_count):
            raise ValueError("constraint references an unknown vertex")
        if not internal[vertices].all():
            raise ValueError("constraint references an unmeasured vertex")
        observed_parity = int(charge[vertices].sum() % 2)
        if observed_parity != constraint.required_parity:
            return D4ObservationEvaluation(
                False,
                0.0,
                None,
                internal_vertices,
                f"parity constraint violated: {constraint.label or constraint.vertices}",
            )

    log2_probability = len(checked_constraints) - len(internal_vertices)
    return D4ObservationEvaluation(
        True,
        exp2(log2_probability),
        log2_probability,
        internal_vertices,
    )
