"""Versioned R1 sampler for the single-colour D4 observation channel."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray

from d4_honeycomb import (
    LogicalSectorPolicy,
    PeriodicHoneycomb,
    generate_loop_constraints,
    periodic_honeycomb,
)
from d4_observation import evaluate_observation


SCHEMA_VERSION = 3


@dataclass(frozen=True)
class D4ObservationRecord:
    schema_version: int
    lattice: str
    size: int
    error_rate: float | None
    seed: int
    status: str
    logical_error: bool
    logical_sector_required: bool
    logical_sector_label: str | None
    error_edges: tuple[int, ...]
    flux_vertices: tuple[int, ...]
    charge_outcomes: tuple[int, ...] | None
    constraint_labels: tuple[str, ...]
    log2_conditional_probability: int | None
    winding_components: tuple[tuple[tuple[int, int], ...], ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _record_from_error_edges(
    lattice: PeriodicHoneycomb,
    error_edges: NDArray[np.generic],
    *,
    seed: int,
    error_rate: float | None,
    logical_sector: LogicalSectorPolicy | None,
) -> D4ObservationRecord:
    selected = np.asarray(error_edges, dtype=np.bool_)
    if selected.shape != (lattice.edge_count,):
        raise ValueError("error_edges must have one value per lattice edge")
    analysis = generate_loop_constraints(lattice, selected, logical_sector)
    winding_components = tuple(
        component.winding_vectors
        for component in analysis.components
        if component.nonbranching_closed and not component.homologically_trivial
    )

    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    flux = (degrees % 2).astype(np.bool_)
    error_indices = tuple(int(edge) for edge in np.flatnonzero(selected))
    flux_vertices = tuple(int(vertex) for vertex in np.flatnonzero(flux))

    if winding_components and logical_sector is None:
        return D4ObservationRecord(
            schema_version=SCHEMA_VERSION,
            lattice="periodic_coloured_honeycomb",
            size=lattice.size,
            error_rate=error_rate,
            seed=seed,
            status="logical_failure",
            logical_error=True,
            logical_sector_required=False,
            logical_sector_label=None,
            error_edges=error_indices,
            flux_vertices=flux_vertices,
            charge_outcomes=None,
            constraint_labels=tuple(
                constraint.label for constraint in analysis.constraints
            ),
            log2_conditional_probability=None,
            winding_components=winding_components,
        )

    rng = np.random.default_rng(seed)
    internal_vertices = np.flatnonzero(degrees == 2)
    # Only a non-vacuum e charge is a public herald.  Do not expose whether a
    # zero arose from a hidden degree-two fusion or from no fusion at all.
    charge = np.zeros(lattice.vertex_count, dtype=np.int64)
    charge[internal_vertices] = rng.integers(0, 2, size=len(internal_vertices))

    # The generated relations have disjoint support by connected component and
    # colour.  Reserve one deterministic pivot per relation and set it from the
    # sampled outcomes on the other vertices, yielding a uniform sample over
    # the allowed affine parity subspace without rejection.
    pivots: set[int] = set()
    for constraint in analysis.constraints:
        pivot = max(constraint.vertices)
        if pivot in pivots:
            raise ValueError("constraint generator produced dependent pivots")
        pivots.add(pivot)
        other_parity = sum(
            int(charge[vertex])
            for vertex in constraint.vertices
            if vertex != pivot
        ) % 2
        charge[pivot] = constraint.required_parity ^ other_parity

    evaluation = evaluate_observation(
        lattice.edge_vertices,
        selected,
        flux,
        charge,
        analysis.constraints,
    )
    if not evaluation.allowed or evaluation.log2_probability is None:
        raise AssertionError(f"sampler produced invalid support: {evaluation.reason}")

    return D4ObservationRecord(
        schema_version=SCHEMA_VERSION,
        lattice="periodic_coloured_honeycomb",
        size=lattice.size,
        error_rate=error_rate,
        seed=seed,
        status="sampled",
        logical_error=bool(winding_components),
        logical_sector_required=False,
        logical_sector_label=(logical_sector.label if logical_sector else None),
        error_edges=error_indices,
        flux_vertices=flux_vertices,
        charge_outcomes=tuple(int(value) for value in charge),
        constraint_labels=tuple(constraint.label for constraint in analysis.constraints),
        log2_conditional_probability=evaluation.log2_probability,
        winding_components=winding_components,
    )


def observation_from_error_edges(
    lattice: PeriodicHoneycomb,
    error_edges: NDArray[np.generic],
    *,
    seed: int,
    logical_sector: LogicalSectorPolicy | None = None,
) -> D4ObservationRecord:
    """Sample the fusion record conditional on one fixed physical error set.

    The primary ground-state contract is sector agnostic: any physical winding
    component acts nontrivially on the initial logical sector and is returned
    immediately as ``logical_failure``.  Supplying an explicit sector policy
    remains available only for bounded likelihood diagnostics; such a sampled
    winding record still has ``logical_error=True``.
    """

    return _record_from_error_edges(
        lattice,
        error_edges,
        seed=seed,
        error_rate=None,
        logical_sector=logical_sector,
    )


def sample_observation(
    size: int,
    error_rate: float,
    seed: int,
    logical_sector: LogicalSectorPolicy | None = None,
) -> D4ObservationRecord:
    """Draw E~Bernoulli(p), then sample or explicitly flag its fusion record."""

    if not 0.0 <= error_rate <= 1.0:
        raise ValueError("error_rate must lie in [0, 1]")
    lattice = periodic_honeycomb(size)
    error_rng = np.random.default_rng(seed)
    error_edges = error_rng.random(lattice.edge_count) < error_rate
    # Derive an independent deterministic stream for the conditional fusion
    # sample so changing its implementation cannot silently change E.
    charge_seed = int(np.random.SeedSequence([seed, 0xD4]).generate_state(1)[0])
    return _record_from_error_edges(
        lattice,
        error_edges,
        seed=charge_seed,
        error_rate=error_rate,
        logical_sector=logical_sector,
    )
