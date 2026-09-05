"""Tiny exhaustive reference for a fusion-constrained MAP decoder.

This is the R3.0 truth fixture used to validate a later MILP formulation.  It
enumerates physical red-X edge sets, enforces the observed flux boundary,
degree-two measurement support, and all generated fusion-parity constraints,
then maximizes ``P(s|E) P(E)`` under an iid Bernoulli prior.

It is deliberately not called Bayes-optimal logical decoding: a MAP error
configuration maximizes one term, whereas R4 must sum posterior mass over all
configurations in each logical sector.  Sector-dependent likelihoods of
winding error components are also censored rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp

from d4_honeycomb import PeriodicHoneycomb, generate_loop_constraints
from d4_matching import classify_closed_chain
from d4_observation import evaluate_observation
from d4_sampler import D4ObservationRecord


@dataclass(frozen=True)
class FusionConstrainedCandidate:
    error: NDArray[np.uint8]
    error_weight: int
    log2_conditional_probability: int
    log2_joint_probability: float


@dataclass(frozen=True)
class FusionConstrainedMapResult:
    maximizers: tuple[FusionConstrainedCandidate, ...]
    compatible_candidate_count: int
    censored_winding_candidate_count: int
    enumerated_candidate_count: int

    @property
    def maximum_log2_joint_probability(self) -> float:
        return self.maximizers[0].log2_joint_probability


@dataclass(frozen=True)
class HomologySectorOptimum:
    relative_windings: tuple[tuple[int, int], ...]
    maximizers: tuple[FusionConstrainedCandidate, ...]
    minimum_negative_log2_joint: float


@dataclass(frozen=True)
class FusionConstrainedMilpResult:
    """Finite one-hot MILP compilation of the exhaustive R3.0 support."""

    maximizers: tuple[FusionConstrainedCandidate, ...]
    minimum_negative_log2_joint: float
    solver_selected_error: NDArray[np.uint8]
    sector_optima: tuple[HomologySectorOptimum, ...]
    compatible_candidate_count: int


@dataclass(frozen=True)
class StructuralFusionMilpResult:
    """Direct edge-variable MILP with bounded fusion no-good cuts."""

    maximizers: tuple[FusionConstrainedCandidate, ...]
    minimum_negative_log2_joint: float
    solver_selected_error: NDArray[np.uint8]
    sector_optima: tuple[HomologySectorOptimum, ...]
    structurally_feasible_count: int
    fusion_no_good_count: int


@dataclass(frozen=True)
class ComponentAuxiliaryMilpResult:
    """Direct-edge MILP with structural trivial-loop fusion auxiliaries."""

    maximizers: tuple[FusionConstrainedCandidate, ...]
    minimum_negative_log2_joint: float
    solver_selected_error: NDArray[np.uint8]
    sector_optima: tuple[HomologySectorOptimum, ...]
    loop_auxiliary_count: int
    winding_no_good_count: int


@dataclass(frozen=True)
class R3RecordDecision:
    """Explicit split between terminal winding failure and recoverable record."""

    status: str
    logical_error: bool
    recovery: ComponentAuxiliaryMilpResult | None


def _supported_nonwinding_candidates(
    lattice: PeriodicHoneycomb,
    flux: NDArray[np.uint8],
    charge: NDArray[np.int64],
    error_rate: float,
) -> tuple[list[FusionConstrainedCandidate], int]:
    log_error = log2(error_rate)
    log_no_error = log2(1.0 - error_rate)
    compatible: list[FusionConstrainedCandidate] = []
    censored_winding = 0
    for mask in range(1 << lattice.edge_count):
        error = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        analysis = generate_loop_constraints(lattice, error.astype(bool))
        evaluation = evaluate_observation(
            lattice.edge_vertices,
            error,
            flux,
            charge,
            analysis.constraints,
        )
        if not evaluation.allowed or evaluation.log2_probability is None:
            continue
        has_winding = any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        )
        if has_winding:
            censored_winding += 1
            continue
        weight = int(error.sum())
        log_joint = (
            weight * log_error
            + (lattice.edge_count - weight) * log_no_error
            + evaluation.log2_probability
        )
        compatible.append(
            FusionConstrainedCandidate(
                error=error,
                error_weight=weight,
                log2_conditional_probability=evaluation.log2_probability,
                log2_joint_probability=log_joint,
            )
        )
    return compatible, censored_winding


def _validate_inputs(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    maximum_edges: int,
) -> tuple[NDArray[np.uint8], NDArray[np.int64]]:
    if lattice.edge_count > maximum_edges:
        raise ValueError("graph exceeds bounded exhaustive R3.0 limit")
    if not 0.0 < error_rate < 1.0:
        raise ValueError("error_rate must lie strictly between zero and one")
    flux = np.asarray(flux_syndrome, dtype=np.uint8)
    charge = np.asarray(charge_outcomes, dtype=np.int64)
    if flux.shape != (lattice.vertex_count,) or np.any(flux > 1):
        raise ValueError("flux_syndrome must be binary with one value per vertex")
    if charge.shape != (lattice.vertex_count,) or not np.isin(charge, (-1, 0, 1)).all():
        raise ValueError("charge_outcomes must be -1, 0, or 1 per vertex")
    return flux, charge


def exhaustive_fusion_constrained_map(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    *,
    maximum_edges: int = 20,
) -> FusionConstrainedMapResult:
    """Return every MAP edge set with a source-supported nonwinding likelihood."""

    flux, charge = _validate_inputs(
        lattice, flux_syndrome, charge_outcomes, error_rate, maximum_edges
    )
    compatible, censored_winding = _supported_nonwinding_candidates(
        lattice, flux, charge, error_rate
    )
    if not compatible:
        raise ValueError("observation has no supported nonwinding explanation")
    maximum = max(candidate.log2_joint_probability for candidate in compatible)
    maximizers = tuple(
        candidate
        for candidate in compatible
        if np.isclose(candidate.log2_joint_probability, maximum, rtol=0.0, atol=1e-12)
    )
    return FusionConstrainedMapResult(
        maximizers=maximizers,
        compatible_candidate_count=len(compatible),
        censored_winding_candidate_count=censored_winding,
        enumerated_candidate_count=1 << lattice.edge_count,
    )


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


def _solve_finite_milp(
    candidates: list[FusionConstrainedCandidate],
    edge_count: int,
    allowed: tuple[int, ...],
) -> tuple[int, float]:
    """Solve one finite support compilation with one-hot and explicit edge vars."""

    candidate_count = len(candidates)
    variable_count = candidate_count + edge_count
    objective = np.zeros(variable_count, dtype=np.float64)
    objective[:candidate_count] = [
        -candidate.log2_joint_probability for candidate in candidates
    ]
    matrix = np.zeros((1 + edge_count, variable_count), dtype=np.float64)
    matrix[0, :candidate_count] = 1.0
    for edge in range(edge_count):
        matrix[1 + edge, :candidate_count] = [
            -int(candidate.error[edge]) for candidate in candidates
        ]
        matrix[1 + edge, candidate_count + edge] = 1.0
    lower = np.zeros(variable_count, dtype=np.float64)
    upper = np.ones(variable_count, dtype=np.float64)
    allowed_set = set(allowed)
    for index in range(candidate_count):
        if index not in allowed_set:
            upper[index] = 0.0
    result = milp(
        objective,
        integrality=np.ones(variable_count, dtype=np.uint8),
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(
            matrix,
            np.concatenate(([1.0], np.zeros(edge_count))),
            np.concatenate(([1.0], np.zeros(edge_count))),
        ),
        options={"presolve": True},
    )
    if not result.success or result.x is None or result.fun is None:
        raise RuntimeError(f"finite R3 MILP failed: {result.message}")
    selected = int(np.argmax(result.x[:candidate_count]))
    return selected, float(result.fun)


def finite_support_fusion_constrained_milp(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    *,
    maximum_edges: int = 20,
) -> FusionConstrainedMilpResult:
    """Compile R3.0 support into a bounded exact one-hot integer program.

    The formulation retains explicit edge variables, but its fusion support is
    pre-enumerated into one-hot explanation variables.  It therefore validates
    solver objective, tie, and homology-sector plumbing only; it is not the
    future scalable structural MILP.
    """

    flux, charge = _validate_inputs(
        lattice, flux_syndrome, charge_outcomes, error_rate, maximum_edges
    )
    candidates, _ = _supported_nonwinding_candidates(
        lattice, flux, charge, error_rate
    )
    if not candidates:
        raise ValueError("observation has no supported nonwinding explanation")
    all_indices = tuple(range(len(candidates)))
    selected, minimum = _solve_finite_milp(candidates, lattice.edge_count, all_indices)
    maximizers = tuple(
        candidate
        for candidate in candidates
        if np.isclose(-candidate.log2_joint_probability, minimum, rtol=0.0, atol=1e-9)
    )
    reference = candidates[0].error
    sectors: dict[tuple[tuple[int, int], ...], list[int]] = {}
    for index, candidate in enumerate(candidates):
        sectors.setdefault(_relative_sector(lattice, reference, candidate.error), []).append(index)
    sector_optima = []
    for sector, indices in sorted(sectors.items()):
        _, sector_minimum = _solve_finite_milp(
            candidates, lattice.edge_count, tuple(indices)
        )
        sector_optima.append(
            HomologySectorOptimum(
                relative_windings=sector,
                maximizers=tuple(
                    candidates[index]
                    for index in indices
                    if np.isclose(
                        -candidates[index].log2_joint_probability,
                        sector_minimum,
                        rtol=0.0,
                        atol=1e-9,
                    )
                ),
                minimum_negative_log2_joint=sector_minimum,
            )
        )
    return FusionConstrainedMilpResult(
        maximizers=maximizers,
        minimum_negative_log2_joint=minimum,
        solver_selected_error=candidates[selected].error,
        sector_optima=tuple(sector_optima),
        compatible_candidate_count=len(candidates),
    )


def _mask(chain: NDArray[np.uint8]) -> int:
    return sum(int(bit) << edge for edge, bit in enumerate(chain))


def _structural_support_partition(
    lattice: PeriodicHoneycomb,
    flux: NDArray[np.uint8],
    charge: NDArray[np.int64],
    error_rate: float,
) -> tuple[list[FusionConstrainedCandidate], list[NDArray[np.uint8]]]:
    """Enumerate only to compile bounded fusion cuts and validate feasibility."""

    log_error = log2(error_rate)
    log_no_error = log2(1.0 - error_rate)
    measured = charge != -1
    compatible: list[FusionConstrainedCandidate] = []
    forbidden: list[NDArray[np.uint8]] = []
    for mask in range(1 << lattice.edge_count):
        error = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        degrees = np.bincount(
            lattice.edge_vertices[error.astype(bool)].ravel(),
            minlength=lattice.vertex_count,
        )
        if not np.array_equal(degrees % 2, flux) or not np.array_equal(
            degrees == 2, measured
        ):
            continue
        analysis = generate_loop_constraints(lattice, error.astype(bool))
        evaluation = evaluate_observation(
            lattice.edge_vertices,
            error,
            flux,
            charge,
            analysis.constraints,
        )
        has_winding = any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        )
        if not evaluation.allowed or evaluation.log2_probability is None or has_winding:
            forbidden.append(error)
            continue
        weight = int(error.sum())
        compatible.append(
            FusionConstrainedCandidate(
                error,
                weight,
                evaluation.log2_probability,
                weight * log_error
                + (lattice.edge_count - weight) * log_no_error
                + evaluation.log2_probability,
            )
        )
    return compatible, forbidden


def _solve_structural_milp(
    lattice: PeriodicHoneycomb,
    flux: NDArray[np.uint8],
    charge: NDArray[np.int64],
    error_rate: float,
    conditional_log2_probability: int,
    forbidden: list[NDArray[np.uint8]],
) -> tuple[NDArray[np.uint8], float]:
    edge_count = lattice.edge_count
    vertex_count = lattice.vertex_count
    variable_count = edge_count + vertex_count
    objective = np.zeros(variable_count, dtype=np.float64)
    objective[:edge_count] = -(
        log2(error_rate) - log2(1.0 - error_rate)
    )
    rows = []
    lower = []
    upper = []
    for vertex in range(vertex_count):
        row = np.zeros(variable_count, dtype=np.float64)
        incident = np.flatnonzero(np.any(lattice.edge_vertices == vertex, axis=1))
        row[incident] = 1.0
        row[edge_count + vertex] = -2.0
        rows.append(row)
        lower.append(float(flux[vertex]))
        upper.append(float(flux[vertex]))
    for chain in forbidden:
        row = np.zeros(variable_count, dtype=np.float64)
        ones = np.flatnonzero(chain)
        zeros = np.flatnonzero(1 - chain)
        row[ones] = -1.0
        row[zeros] = 1.0
        rows.append(row)
        lower.append(float(1 - len(ones)))
        upper.append(np.inf)
    bound_lower = np.zeros(variable_count, dtype=np.float64)
    bound_upper = np.ones(variable_count, dtype=np.float64)
    for vertex in range(vertex_count):
        auxiliary = edge_count + vertex
        if charge[vertex] != -1:
            bound_lower[auxiliary] = bound_upper[auxiliary] = 1.0
        elif flux[vertex] == 0:
            bound_lower[auxiliary] = bound_upper[auxiliary] = 0.0
    result = milp(
        objective,
        integrality=np.ones(variable_count, dtype=np.uint8),
        bounds=Bounds(bound_lower, bound_upper),
        constraints=LinearConstraint(
            np.asarray(rows), np.asarray(lower), np.asarray(upper)
        ),
        options={"presolve": True},
    )
    if not result.success or result.x is None or result.fun is None:
        raise RuntimeError(f"structural R3 MILP failed: {result.message}")
    selected = np.rint(result.x[:edge_count]).astype(np.uint8)
    constant = (
        -edge_count * log2(1.0 - error_rate) - conditional_log2_probability
    )
    return selected, float(result.fun + constant)


def structural_fusion_constrained_milp(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    *,
    maximum_edges: int = 20,
) -> StructuralFusionMilpResult:
    """Solve a bounded direct-edge MILP with exact fusion no-good cuts.

    Boundary and measurement support are structural degree/parity equations.
    Fusion-incompatible structurally feasible chains are excluded by bounded
    no-good cuts.  The present objective requires a constant Appendix-A
    conditional log-likelihood over compatible chains and fails closed when
    that condition is absent; structurally encoding a varying constraint count
    is the next R3 gate.
    """

    flux, charge = _validate_inputs(
        lattice, flux_syndrome, charge_outcomes, error_rate, maximum_edges
    )
    compatible, fusion_forbidden = _structural_support_partition(
        lattice, flux, charge, error_rate
    )
    if not compatible:
        raise ValueError("observation has no supported nonwinding explanation")
    conditional_values = {
        candidate.log2_conditional_probability for candidate in compatible
    }
    if len(conditional_values) != 1:
        raise ValueError(
            "structural R3 objective requires varying-likelihood auxiliaries"
        )
    conditional = next(iter(conditional_values))
    selected, minimum = _solve_structural_milp(
        lattice,
        flux,
        charge,
        error_rate,
        conditional,
        fusion_forbidden,
    )
    maximizers = tuple(
        candidate
        for candidate in compatible
        if np.isclose(
            -candidate.log2_joint_probability, minimum, rtol=0.0, atol=1e-9
        )
    )
    if not any(np.array_equal(selected, candidate.error) for candidate in maximizers):
        raise RuntimeError("structural MILP selected a nonoptimal explanation")
    reference = compatible[0].error
    sectors: dict[tuple[tuple[int, int], ...], list[FusionConstrainedCandidate]] = {}
    for candidate in compatible:
        sectors.setdefault(
            _relative_sector(lattice, reference, candidate.error), []
        ).append(candidate)
    sector_optima = []
    all_structural = [candidate.error for candidate in compatible] + fusion_forbidden
    for sector, members in sorted(sectors.items()):
        member_masks = {_mask(candidate.error) for candidate in members}
        sector_forbidden = fusion_forbidden + [
            chain for chain in all_structural if _mask(chain) not in member_masks
        ]
        _, sector_minimum = _solve_structural_milp(
            lattice,
            flux,
            charge,
            error_rate,
            conditional,
            sector_forbidden,
        )
        sector_optima.append(
            HomologySectorOptimum(
                sector,
                tuple(
                    candidate
                    for candidate in members
                    if np.isclose(
                        -candidate.log2_joint_probability,
                        sector_minimum,
                        rtol=0.0,
                        atol=1e-9,
                    )
                ),
                sector_minimum,
            )
        )
    return StructuralFusionMilpResult(
        maximizers,
        minimum,
        selected,
        tuple(sector_optima),
        len(compatible) + len(fusion_forbidden),
        len(fusion_forbidden),
    )


def _bounded_trivial_loop_catalog(
    lattice: PeriodicHoneycomb,
) -> list[tuple[NDArray[np.uint8], tuple, NDArray[np.int64]]]:
    """Enumerate primitive isolated-loop components, not full explanations."""

    catalog = []
    for mask in range(1 << lattice.edge_count):
        chain = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        analysis = generate_loop_constraints(lattice, chain.astype(bool))
        if (
            len(analysis.components) != 1
            or not analysis.components[0].nonbranching_closed
            or not analysis.components[0].homologically_trivial
            or len(analysis.constraints) != 2
        ):
            continue
        vertices = np.unique(lattice.edge_vertices[np.flatnonzero(chain)])
        incident = np.flatnonzero(
            np.any(np.isin(lattice.edge_vertices, vertices), axis=1)
        )
        external = np.asarray(
            sorted(set(int(edge) for edge in incident) - set(np.flatnonzero(chain))),
            dtype=np.int64,
        )
        catalog.append((chain, analysis.constraints, external))
    return catalog


def geometry_trivial_loop_catalog(
    lattice: PeriodicHoneycomb,
    *,
    maximum_cycle_length: int | None = None,
    cycle_limit: int = 100_000,
) -> list[tuple[NDArray[np.uint8], tuple, NDArray[np.int64]]]:
    """Generate isolated trivial-loop components from simple graph cycles.

    This replaces the ``2**E`` edge-subset scan used by the R3.3 validation
    fixture.  Cycles are generated directly by DFS, deduplicated by edge mask,
    and then source-filtered for homological triviality and the expected two
    colour constraints.  Length and count guards keep the operation bounded.
    """

    if cycle_limit <= 0:
        raise ValueError("cycle_limit must be positive")
    limit = (
        lattice.vertex_count
        if maximum_cycle_length is None
        else int(maximum_cycle_length)
    )
    if limit < 3:
        raise ValueError("maximum_cycle_length must be at least three")
    adjacency: list[list[tuple[int, int]]] = [
        [] for _ in range(lattice.vertex_count)
    ]
    for edge, (left, right) in enumerate(lattice.edge_vertices):
        adjacency[int(left)].append((int(right), edge))
        adjacency[int(right)].append((int(left), edge))
    for neighbors in adjacency:
        neighbors.sort()
    masks: set[int] = set()
    for start in range(lattice.vertex_count):
        visited = {start}

        def walk(vertex: int, path_edges: tuple[int, ...]) -> None:
            for neighbor, edge in adjacency[vertex]:
                if neighbor == start:
                    if len(path_edges) >= 2:
                        mask = 1 << edge
                        for selected_edge in path_edges:
                            mask |= 1 << selected_edge
                        masks.add(mask)
                        if len(masks) > cycle_limit:
                            raise ValueError("geometry cycle limit exceeded")
                    continue
                if (
                    neighbor < start
                    or neighbor in visited
                    or len(path_edges) + 1 >= limit
                ):
                    continue
                visited.add(neighbor)
                walk(neighbor, path_edges + (edge,))
                visited.remove(neighbor)

        walk(start, ())
    catalog = []
    for mask in sorted(masks):
        chain = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        analysis = generate_loop_constraints(lattice, chain.astype(bool))
        if (
            len(analysis.components) != 1
            or not analysis.components[0].nonbranching_closed
            or not analysis.components[0].homologically_trivial
            or len(analysis.constraints) != 2
        ):
            continue
        vertices = np.unique(lattice.edge_vertices[np.flatnonzero(chain)])
        incident = np.flatnonzero(
            np.any(np.isin(lattice.edge_vertices, vertices), axis=1)
        )
        external = np.asarray(
            sorted(set(int(edge) for edge in incident) - set(np.flatnonzero(chain))),
            dtype=np.int64,
        )
        catalog.append((chain, analysis.constraints, external))
    return catalog


def _structurally_feasible_winding_chains(
    lattice: PeriodicHoneycomb,
    flux: NDArray[np.uint8],
    charge: NDArray[np.int64],
) -> list[NDArray[np.uint8]]:
    measured = charge != -1
    result = []
    for mask in range(1 << lattice.edge_count):
        chain = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        degrees = np.bincount(
            lattice.edge_vertices[chain.astype(bool)].ravel(),
            minlength=lattice.vertex_count,
        )
        if not np.array_equal(degrees % 2, flux) or not np.array_equal(
            degrees == 2, measured
        ):
            continue
        analysis = generate_loop_constraints(lattice, chain.astype(bool))
        if any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        ):
            result.append(chain)
    return result


def _solve_component_auxiliary_milp(
    lattice: PeriodicHoneycomb,
    flux: NDArray[np.uint8],
    charge: NDArray[np.int64],
    error_rate: float,
    catalog: list[tuple[NDArray[np.uint8], tuple, NDArray[np.int64]]],
    forbidden: list[NDArray[np.uint8]],
) -> tuple[NDArray[np.uint8], float]:
    edge_count = lattice.edge_count
    vertex_count = lattice.vertex_count
    loop_count = len(catalog)
    variable_count = edge_count + vertex_count + loop_count
    objective = np.zeros(variable_count, dtype=np.float64)
    objective[:edge_count] = -(
        log2(error_rate) - log2(1.0 - error_rate)
    )
    objective[edge_count + vertex_count :] = -2.0
    rows: list[NDArray[np.float64]] = []
    lower: list[float] = []
    upper: list[float] = []
    for vertex in range(vertex_count):
        row = np.zeros(variable_count, dtype=np.float64)
        incident = np.flatnonzero(np.any(lattice.edge_vertices == vertex, axis=1))
        row[incident] = 1.0
        row[edge_count + vertex] = -2.0
        rows.append(row)
        lower.append(float(flux[vertex]))
        upper.append(float(flux[vertex]))
    bound_lower = np.zeros(variable_count, dtype=np.float64)
    bound_upper = np.ones(variable_count, dtype=np.float64)
    for vertex in range(vertex_count):
        auxiliary = edge_count + vertex
        if charge[vertex] != -1:
            bound_lower[auxiliary] = bound_upper[auxiliary] = 1.0
        elif flux[vertex] == 0:
            bound_lower[auxiliary] = bound_upper[auxiliary] = 0.0
    for loop_index, (chain, constraints, external) in enumerate(catalog):
        auxiliary = edge_count + vertex_count + loop_index
        selected = np.flatnonzero(chain)
        for edge in selected:
            row = np.zeros(variable_count, dtype=np.float64)
            row[auxiliary] = 1.0
            row[edge] = -1.0
            rows.append(row)
            lower.append(-np.inf)
            upper.append(0.0)
        for edge in external:
            row = np.zeros(variable_count, dtype=np.float64)
            row[auxiliary] = 1.0
            row[int(edge)] = 1.0
            rows.append(row)
            lower.append(-np.inf)
            upper.append(1.0)
        row = np.zeros(variable_count, dtype=np.float64)
        row[auxiliary] = 1.0
        row[selected] = -1.0
        row[external] = 1.0
        rows.append(row)
        lower.append(float(1 - len(selected)))
        upper.append(np.inf)
        if any(
            int(np.sum(charge[list(constraint.vertices)])) % 2
            != constraint.required_parity
            for constraint in constraints
        ):
            bound_upper[auxiliary] = 0.0
    for chain in forbidden:
        row = np.zeros(variable_count, dtype=np.float64)
        ones = np.flatnonzero(chain)
        zeros = np.flatnonzero(1 - chain)
        row[ones] = -1.0
        row[zeros] = 1.0
        rows.append(row)
        lower.append(float(1 - len(ones)))
        upper.append(np.inf)
    result = milp(
        objective,
        integrality=np.ones(variable_count, dtype=np.uint8),
        bounds=Bounds(bound_lower, bound_upper),
        constraints=LinearConstraint(
            np.asarray(rows), np.asarray(lower), np.asarray(upper)
        ),
        options={"presolve": True},
    )
    if not result.success or result.x is None or result.fun is None:
        raise RuntimeError(f"component-auxiliary R3 MILP failed: {result.message}")
    selected = np.rint(result.x[:edge_count]).astype(np.uint8)
    internal_count = int(np.sum(charge != -1))
    constant = -edge_count * log2(1.0 - error_rate) + internal_count
    return selected, float(result.fun + constant)


def component_auxiliary_fusion_milp(
    lattice: PeriodicHoneycomb,
    flux_syndrome: NDArray[np.generic],
    charge_outcomes: NDArray[np.generic],
    error_rate: float,
    *,
    maximum_edges: int = 20,
) -> ComponentAuxiliaryMilpResult:
    """Encode trivial-loop fusion parity and likelihood without fusion no-goods."""

    flux, charge = _validate_inputs(
        lattice, flux_syndrome, charge_outcomes, error_rate, maximum_edges
    )
    compatible, _ = _supported_nonwinding_candidates(
        lattice, flux, charge, error_rate
    )
    if not compatible:
        raise ValueError("observation has no supported nonwinding explanation")
    catalog = geometry_trivial_loop_catalog(lattice)
    winding_forbidden = _structurally_feasible_winding_chains(
        lattice, flux, charge
    )
    selected, minimum = _solve_component_auxiliary_milp(
        lattice,
        flux,
        charge,
        error_rate,
        catalog,
        winding_forbidden,
    )
    maximizers = tuple(
        candidate
        for candidate in compatible
        if np.isclose(
            -candidate.log2_joint_probability, minimum, rtol=0.0, atol=1e-9
        )
    )
    if not any(np.array_equal(selected, candidate.error) for candidate in maximizers):
        raise RuntimeError("component-auxiliary MILP disagrees with R3.0")
    reference = compatible[0].error
    sectors: dict[tuple[tuple[int, int], ...], list[FusionConstrainedCandidate]] = {}
    for candidate in compatible:
        sectors.setdefault(
            _relative_sector(lattice, reference, candidate.error), []
        ).append(candidate)
    sector_optima = []
    for sector, members in sorted(sectors.items()):
        member_masks = {_mask(candidate.error) for candidate in members}
        sector_forbidden = winding_forbidden + [
            candidate.error
            for candidate in compatible
            if _mask(candidate.error) not in member_masks
        ]
        _, sector_minimum = _solve_component_auxiliary_milp(
            lattice,
            flux,
            charge,
            error_rate,
            catalog,
            sector_forbidden,
        )
        sector_optima.append(
            HomologySectorOptimum(
                sector,
                tuple(
                    candidate
                    for candidate in members
                    if np.isclose(
                        -candidate.log2_joint_probability,
                        sector_minimum,
                        rtol=0.0,
                        atol=1e-9,
                    )
                ),
                sector_minimum,
            )
        )
    return ComponentAuxiliaryMilpResult(
        maximizers,
        minimum,
        selected,
        tuple(sector_optima),
        len(catalog),
        len(winding_forbidden),
    )


def decode_observation_record_r3(
    lattice: PeriodicHoneycomb,
    observation: D4ObservationRecord,
    error_rate: float,
    *,
    maximum_edges: int = 20,
) -> R3RecordDecision:
    """Apply the researcher-approved terminal winding gate before R3 recovery.

    A record with any nontrivial winding component is a logical failure
    relative to the unknown ground-state sector and never receives an invented
    sector-dependent charge likelihood.  Only sampled nonwinding records enter
    the component-auxiliary MAP solver.
    """

    if observation.size != lattice.size:
        raise ValueError("observation and lattice sizes disagree")
    if observation.winding_components or observation.status == "logical_failure":
        if not observation.logical_error or not observation.winding_components:
            raise ValueError("inconsistent terminal winding record")
        return R3RecordDecision("terminal_winding_logical_failure", True, None)
    if observation.status != "sampled" or observation.logical_error:
        raise ValueError("R3 requires a sampled nonwinding observation")
    if observation.charge_outcomes is None:
        raise ValueError("sampled observation lacks charge outcomes")
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(observation.flux_vertices)] = 1
    recovery = component_auxiliary_fusion_milp(
        lattice,
        flux,
        np.asarray(observation.charge_outcomes, dtype=np.int64),
        error_rate,
        maximum_edges=maximum_edges,
    )
    return R3RecordDecision("recovered_nonwinding", False, recovery)
