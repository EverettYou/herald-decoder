"""Public D4 likelihood factor ledgers for the Lab 004 R6A exact gate.

This module does not run belief propagation.  It separates the validated D4
conditional likelihood into local observation-support factors and optional
closed-loop parity factors for one latent edge assignment.  The public record
contains only flux and charge observations; component and winding information
is derived internally from the candidate assignment and is never serialized as
decoder input.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import prod
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from d4_honeycomb import PeriodicHoneycomb, generate_loop_constraints
from d4_r3 import geometry_trivial_loop_catalog


FORBIDDEN_PUBLIC_FIELDS = frozenset(
    {
        "error_edges",
        "physical_error",
        "components",
        "winding_components",
        "logical_sector",
        "logical_error",
        "constraint_labels",
        "relations",
        "postflux_relations",
        "truth",
    }
)


@dataclass(frozen=True)
class PublicD4Observation:
    """Observation-only first-stage D4 record."""

    flux_syndrome: tuple[int, ...]
    charge_outcomes: tuple[int, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "PublicD4Observation":
        forbidden = FORBIDDEN_PUBLIC_FIELDS.intersection(payload)
        if forbidden:
            raise ValueError(
                "public D4 observation contains forbidden hidden fields: "
                + ", ".join(sorted(forbidden))
            )
        allowed = {"flux_syndrome", "charge_outcomes"}
        unknown = set(payload).difference(allowed)
        if unknown:
            raise ValueError(
                "public D4 observation contains unknown fields: "
                + ", ".join(sorted(unknown))
            )
        if set(payload) != allowed:
            raise ValueError("public D4 observation requires flux_syndrome and charge_outcomes")
        return cls(
            tuple(int(value) for value in payload["flux_syndrome"]),  # type: ignore[arg-type]
            tuple(int(value) for value in payload["charge_outcomes"]),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, list[int]]:
        return {
            "flux_syndrome": list(self.flux_syndrome),
            "charge_outcomes": list(self.charge_outcomes),
        }


@dataclass(frozen=True)
class LocalObservationFactor:
    vertex: int
    incident_edges: tuple[int, ...]
    observed_flux: int
    observed_charge: int
    value: float
    reason: str | None = None


@dataclass(frozen=True)
class PublicParityFactor:
    vertices: tuple[int, ...]
    required_parity: int
    value: float
    label: str


@dataclass(frozen=True)
class D4FactorLedger:
    """Product decomposition for one candidate edge assignment."""

    branch: str
    status: str
    probability: float
    internal_vertex_count: int
    local_factors: tuple[LocalObservationFactor, ...]
    parity_factors: tuple[PublicParityFactor, ...]
    reason: str | None = None

    def diagnostic_dict(self) -> dict[str, object]:
        """Serialize an audit ledger that is explicitly not decoder-visible.

        Parity scopes are derived while evaluating a latent candidate and can
        reveal candidate component structure.  The complete R6A matrix must
        decide whether they admit a fixed public auxiliary representation;
        until then this ledger is analysis evidence, not a BP request.
        """

        return {
            "decoder_visible": False,
            "branch": self.branch,
            "status": self.status,
            "probability": self.probability,
            "internal_vertex_count": self.internal_vertex_count,
            "local_factors": [asdict(factor) for factor in self.local_factors],
            "parity_factors": [asdict(factor) for factor in self.parity_factors],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FixedCycleFactorSpec:
    """One geometry-fixed cycle activation scope."""

    cycle_edges: tuple[int, ...]
    boundary_edges: tuple[int, ...]
    blue_vertices: tuple[int, ...]
    green_vertices: tuple[int, ...]


@dataclass(frozen=True)
class FixedCycleFactorLedger:
    status: str
    probability: float
    internal_vertex_count: int
    active_cycle_count: int
    catalog_cycle_count: int
    reason: str | None = None


@dataclass(frozen=True)
class LocalSpinFactorLedger:
    """Exact contraction of the fixed local auxiliary-spin graph."""

    status: str
    probability: float
    internal_vertex_count: int
    closed_component_count: int
    colour_partitions: tuple[int, int]
    reason: str | None = None


@dataclass(frozen=True)
class LocalEdgeFlowFactorLedger:
    """Exact contraction of the nonnegative local edge-flow graph."""

    status: str
    probability: float
    internal_vertex_count: int
    closed_component_count: int
    colour_partitions: tuple[float, float]
    reason: str | None = None


def build_fixed_cycle_factor_catalog(
    lattice: PeriodicHoneycomb,
) -> tuple[FixedCycleFactorSpec, ...]:
    """Build a candidate-independent catalog from fixed lattice geometry."""

    catalog = []
    for chain, constraints, boundary_edges in geometry_trivial_loop_catalog(lattice):
        cycle_edges = tuple(int(edge) for edge in np.flatnonzero(chain))
        by_label = {constraint.label.rsplit("-", 1)[-1]: constraint for constraint in constraints}
        catalog.append(
            FixedCycleFactorSpec(
                cycle_edges=cycle_edges,
                boundary_edges=tuple(int(edge) for edge in boundary_edges),
                blue_vertices=tuple(int(vertex) for vertex in by_label["blue"].vertices),
                green_vertices=tuple(int(vertex) for vertex in by_label["green"].vertices),
            )
        )
    return tuple(catalog)


def fixed_cycle_factor_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
    catalog: tuple[FixedCycleFactorSpec, ...],
) -> FixedCycleFactorLedger:
    """Evaluate the fixed cycle-activation factor graph for one candidate.

    The catalog is public fixed geometry.  Candidate component structure is not
    serialized: each factor computes activation from its own latent cycle and
    boundary edge variables.
    """

    selected, flux, charge = _validated_inputs(lattice, candidate_error_edges, observation)
    local_factors, internal_count = _local_factor_ledger(lattice, selected, flux, charge)
    local_product = float(prod(factor.value for factor in local_factors))
    if local_product == 0.0:
        reason = next((factor.reason for factor in local_factors if factor.value == 0), None)
        return FixedCycleFactorLedger("forbidden", 0.0, internal_count, 0, len(catalog), reason)
    analysis = generate_loop_constraints(lattice, selected)
    if any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    ):
        return FixedCycleFactorLedger(
            "terminal_winding", 0.0, internal_count, 0, len(catalog),
            "ground-state-relative winding logical failure",
        )

    multiplier = 1.0
    active_count = 0
    for factor in catalog:
        active = all(selected[edge] for edge in factor.cycle_edges) and not any(
            selected[edge] for edge in factor.boundary_edges
        )
        if not active:
            continue
        active_count += 1
        for vertices in (factor.blue_vertices, factor.green_vertices):
            if sum(int(charge[vertex]) for vertex in vertices) % 2:
                return FixedCycleFactorLedger(
                    "forbidden", 0.0, internal_count, active_count, len(catalog),
                    "active fixed-cycle parity constraint violated",
                )
            multiplier *= 2.0
    return FixedCycleFactorLedger(
        "allowed", local_product * multiplier, internal_count, active_count, len(catalog)
    )


def explicit_local_spin_partition(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
    colour: int,
) -> int:
    """Sum one colour's fixed local factors over all binary vertex spins.

    This exponential routine is an independent small-graph control, not a
    decoder implementation.  Selected edges enforce equal endpoint spins.
    Vertices whose selected degree is not two pin their spin to +1; a
    degree-two vertex of ``colour`` contributes its public charge exponent.
    """

    if colour not in (0, 1):
        raise ValueError("colour must be 0 or 1")
    selected, _flux, charge = _validated_inputs(
        lattice, candidate_error_edges, observation
    )
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    total = 0
    for mask in range(1 << lattice.vertex_count):
        spins = np.asarray(
            [1 if (mask >> vertex) & 1 else -1 for vertex in range(lattice.vertex_count)],
            dtype=np.int8,
        )
        selected_endpoints = lattice.edge_vertices[selected]
        if len(selected_endpoints) and np.any(
            spins[selected_endpoints[:, 0]] != spins[selected_endpoints[:, 1]]
        ):
            continue
        if np.any(spins[degrees != 2] != 1):
            continue
        term = 1
        for vertex in np.flatnonzero(
            (degrees == 2) & (lattice.vertex_colors == colour)
        ):
            term *= int(spins[vertex]) ** int(charge[vertex])
        total += term
    return int(total)


def local_spin_factor_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
) -> LocalSpinFactorLedger:
    """Contract the fixed bounded-arity auxiliary-spin likelihood graph.

    The contraction is evaluated componentwise for speed.  It is algebraically
    identical to summing :func:`explicit_local_spin_partition` independently
    for the two charge colours.  Component labels are an internal contraction
    strategy, not decoder-visible inputs or factor specifications.
    """

    selected, flux, charge = _validated_inputs(lattice, candidate_error_edges, observation)
    local_factors, internal_count = _local_factor_ledger(lattice, selected, flux, charge)
    local_product = float(prod(factor.value for factor in local_factors))
    if local_product == 0.0:
        reason = next((factor.reason for factor in local_factors if factor.value == 0), None)
        return LocalSpinFactorLedger(
            "forbidden", 0.0, internal_count, 0, (0, 0), reason
        )

    analysis = generate_loop_constraints(lattice, selected)
    if any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    ):
        return LocalSpinFactorLedger(
            "terminal_winding",
            0.0,
            internal_count,
            0,
            (0, 0),
            "ground-state-relative winding logical failure",
        )

    closed_components = tuple(
        component for component in analysis.components if component.nonbranching_closed
    )
    partitions = [1, 1]
    for component in closed_components:
        for colour in (0, 1):
            parity = sum(
                int(charge[vertex])
                for vertex in component.vertices
                if int(lattice.vertex_colors[vertex]) == colour
            ) % 2
            if parity:
                partitions[colour] = 0
            elif partitions[colour]:
                partitions[colour] *= 2

    multiplier = partitions[0] * partitions[1]
    if multiplier == 0:
        return LocalSpinFactorLedger(
            "forbidden",
            0.0,
            internal_count,
            len(closed_components),
            (partitions[0], partitions[1]),
            "local auxiliary-spin parity partition vanishes",
        )
    return LocalSpinFactorLedger(
        "allowed",
        local_product * float(multiplier),
        internal_count,
        len(closed_components),
        (partitions[0], partitions[1]),
    )


def explicit_local_edge_flow_partition(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
    colour: int,
) -> float:
    """Sum one colour's nonnegative local factors over binary edge flows.

    Unselected physical edges pin their flow bit to zero.  At selected degree
    two, the two incident flow bits have XOR equal to the observed charge bit
    for the matching vertex colour (and zero otherwise).  Other vertices leave
    incident selected flow bits unconstrained and contribute ``2**(-d/2)``.
    This exponential implementation is only a small-graph exactness control.
    """

    if colour not in (0, 1):
        raise ValueError("colour must be 0 or 1")
    selected, _flux, charge = _validated_inputs(
        lattice, candidate_error_edges, observation
    )
    incident = tuple(
        tuple(int(edge) for edge in np.flatnonzero(np.any(lattice.edge_vertices == vertex, axis=1)))
        for vertex in range(lattice.vertex_count)
    )
    total = 0.0
    for mask in range(1 << lattice.edge_count):
        flow = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)], dtype=np.int8
        )
        if np.any(flow[~selected]):
            continue
        term = 1.0
        for vertex, vertex_edges in enumerate(incident):
            selected_edges = tuple(edge for edge in vertex_edges if selected[edge])
            degree = len(selected_edges)
            if degree == 2:
                required = (
                    int(charge[vertex])
                    if int(lattice.vertex_colors[vertex]) == colour
                    else 0
                )
                if int(flow[selected_edges[0]] ^ flow[selected_edges[1]]) != required:
                    term = 0.0
                    break
            else:
                term *= 2.0 ** (-degree / 2.0)
        total += term
    return total


def local_edge_flow_factor_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
    *,
    terminal_winding: bool = True,
) -> LocalEdgeFlowFactorLedger:
    """Contract the exact nonnegative bounded-arity edge-flow graph.

    ``terminal_winding=False`` contracts the local graph literally, including
    winding degree-two components.  The default applies the separate
    ground-state-relative terminal policy used by Lab 004.
    """

    selected, flux, charge = _validated_inputs(lattice, candidate_error_edges, observation)
    local_factors, internal_count = _local_factor_ledger(lattice, selected, flux, charge)
    local_product = float(prod(factor.value for factor in local_factors))
    if local_product == 0.0:
        reason = next((factor.reason for factor in local_factors if factor.value == 0), None)
        return LocalEdgeFlowFactorLedger(
            "forbidden", 0.0, internal_count, 0, (0.0, 0.0), reason
        )

    analysis = generate_loop_constraints(lattice, selected)
    if terminal_winding and any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    ):
        return LocalEdgeFlowFactorLedger(
            "terminal_winding",
            0.0,
            internal_count,
            0,
            (0.0, 0.0),
            "ground-state-relative winding logical failure",
        )

    closed_components = tuple(
        component for component in analysis.components if component.nonbranching_closed
    )
    partitions = [1.0, 1.0]
    for component in closed_components:
        for colour in (0, 1):
            parity = sum(
                int(charge[vertex])
                for vertex in component.vertices
                if int(lattice.vertex_colors[vertex]) == colour
            ) % 2
            if parity:
                partitions[colour] = 0.0
            elif partitions[colour]:
                partitions[colour] *= 2.0

    multiplier = partitions[0] * partitions[1]
    if multiplier == 0.0:
        return LocalEdgeFlowFactorLedger(
            "forbidden",
            0.0,
            internal_count,
            len(closed_components),
            (partitions[0], partitions[1]),
            "nonnegative local edge-flow parity partition vanishes",
        )
    return LocalEdgeFlowFactorLedger(
        "allowed",
        local_product * multiplier,
        internal_count,
        len(closed_components),
        (partitions[0], partitions[1]),
    )


def _validated_inputs(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
) -> tuple[NDArray[np.bool_], NDArray[np.int64], NDArray[np.int64]]:
    selected = np.asarray(candidate_error_edges, dtype=np.bool_)
    if selected.shape != (lattice.edge_count,):
        raise ValueError("candidate_error_edges must have one value per lattice edge")
    flux = np.asarray(observation.flux_syndrome, dtype=np.int64)
    charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    if flux.shape != (lattice.vertex_count,) or charge.shape != (lattice.vertex_count,):
        raise ValueError("public D4 arrays must have one value per lattice vertex")
    if not np.isin(flux, (0, 1)).all():
        raise ValueError("flux_syndrome values must be binary")
    if not np.isin(charge, (-1, 0, 1)).all():
        raise ValueError("charge_outcomes values must be -1, 0, or 1")
    return selected, flux, charge


def _local_factor_ledger(
    lattice: PeriodicHoneycomb,
    selected: NDArray[np.bool_],
    flux: NDArray[np.int64],
    charge: NDArray[np.int64],
) -> tuple[tuple[LocalObservationFactor, ...], int]:
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    incident = tuple(
        tuple(int(edge) for edge in np.flatnonzero(np.any(lattice.edge_vertices == vertex, axis=1)))
        for vertex in range(lattice.vertex_count)
    )
    factors: list[LocalObservationFactor] = []
    legacy_support_revealed = bool(np.any(charge == -1))
    internal_count = 0
    for vertex, degree in enumerate(degrees):
        expected_flux = int(degree % 2)
        internal = int(degree) == 2
        if internal:
            internal_count += 1
        expected_measured = internal
        observed_measured = int(charge[vertex]) != -1
        value = 0.5 if internal else 1.0
        reason = None
        if int(flux[vertex]) != expected_flux:
            value = 0.0
            reason = "flux syndrome is not boundary(E)"
        elif legacy_support_revealed and observed_measured != expected_measured:
            value = 0.0
            reason = "charge measurement support is not degree-two support"
        elif not legacy_support_revealed and int(charge[vertex]) == 1 and not internal:
            value = 0.0
            reason = "e-charge herald is not degree-two support"
        factors.append(
            LocalObservationFactor(
                vertex=vertex,
                incident_edges=incident[vertex],
                observed_flux=int(flux[vertex]),
                observed_charge=int(charge[vertex]),
                value=value,
                reason=reason,
            )
        )
    return tuple(factors), internal_count


def factorized_observation_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
    *,
    include_parity: bool,
) -> D4FactorLedger:
    """Evaluate F1 or F2 for one latent candidate and one public observation.

    F1 includes only local flux/degree support.  F2 additionally derives the
    independent trivial-loop parity relations from the candidate assignment
    and evaluates them against the public charge outcomes.  A nontrivial
    nonbranching loop is a terminal logical branch under the resolved Lab 004
    ground-state-relative contract and is not assigned an observation weight.
    This is an exact diagnostic ledger; candidate-dependent parity scopes are
    not yet a fixed decoder-visible factor graph.
    """

    selected, flux, charge = _validated_inputs(
        lattice, candidate_error_edges, observation
    )
    local_factors, internal_count = _local_factor_ledger(
        lattice, selected, flux, charge
    )
    branch = "F2-support-plus-parity" if include_parity else "F1-local-support"
    local_product = float(prod(factor.value for factor in local_factors))
    local_failure = next((factor.reason for factor in local_factors if factor.value == 0), None)
    if local_product == 0.0:
        return D4FactorLedger(
            branch,
            "forbidden",
            0.0,
            internal_count,
            local_factors,
            (),
            local_failure,
        )

    analysis = generate_loop_constraints(lattice, selected)
    if any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    ):
        return D4FactorLedger(
            branch,
            "terminal_winding",
            0.0,
            internal_count,
            local_factors,
            (),
            "ground-state-relative winding logical failure",
        )

    parity_factors: list[PublicParityFactor] = []
    if include_parity:
        for constraint in analysis.constraints:
            observed_parity = sum(int(charge[vertex]) for vertex in constraint.vertices) % 2
            value = 2.0 if observed_parity == constraint.required_parity else 0.0
            parity_factors.append(
                PublicParityFactor(
                    vertices=constraint.vertices,
                    required_parity=constraint.required_parity,
                    value=value,
                    label=constraint.label,
                )
            )
    parity_product = float(prod(factor.value for factor in parity_factors))
    probability = local_product * parity_product
    if probability == 0.0:
        return D4FactorLedger(
            branch,
            "forbidden",
            0.0,
            internal_count,
            local_factors,
            tuple(parity_factors),
            "independent loop-parity constraint violated",
        )
    return D4FactorLedger(
        branch,
        "allowed",
        probability,
        internal_count,
        local_factors,
        tuple(parity_factors),
    )


def f1_local_support_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
) -> D4FactorLedger:
    return factorized_observation_weight(
        lattice, candidate_error_edges, observation, include_parity=False
    )


def f2_support_plus_parity_weight(
    lattice: PeriodicHoneycomb,
    candidate_error_edges: NDArray[np.generic],
    observation: PublicD4Observation,
) -> D4FactorLedger:
    return factorized_observation_weight(
        lattice, candidate_error_edges, observation, include_parity=True
    )
