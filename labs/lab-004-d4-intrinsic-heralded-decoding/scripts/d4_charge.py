"""Second-stage Abelian charge recovery for the D4 decoder.

After a homologically trivial red-X physical/correction union has removed all
m-fluxes, Appendix A permits any effective same-colour Pauli-Z string that
pairs the measured e-charges along that union.  All such choices are
homologically equivalent.  This module constructs one deterministic spanning-
forest representative, decodes its boundary by unit-weight MWPM on the blue or
green triangular star sublattice, and classifies the symmetric-difference
residual on the torus.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pymatching
from numpy.typing import NDArray

from d4_honeycomb import BLUE, GREEN, PeriodicHoneycomb
from d4_postflux import PeriodicPostFluxRelations, periodic_local_neighborhood


@dataclass(frozen=True)
class ChargeLattice:
    """One same-colour triangular sublattice of honeycomb stars."""

    color: int
    honeycomb_vertex_count: int
    vertex_ids: NDArray[np.int64]
    edge_vertices: NDArray[np.int64]
    edge_global_vertices: NDArray[np.int64]
    edge_displacements: NDArray[np.int64]
    period_matrix: NDArray[np.int64]

    @property
    def vertex_count(self) -> int:
        return len(self.vertex_ids)

    @property
    def edge_count(self) -> int:
        return len(self.edge_vertices)

    def local_vertex(self, global_vertex: int) -> int:
        global_vertex = int(global_vertex)
        if (
            global_vertex < 0
            or global_vertex >= self.honeycomb_vertex_count
            or global_vertex % 2 != self.color
        ):
            raise ValueError("global vertex does not belong to charge colour")
        return global_vertex // 2

    def edge_between_global(self, left: int, right: int) -> int:
        pair = tuple(sorted((int(left), int(right))))
        matches = np.flatnonzero(
            (self.edge_global_vertices[:, 0] == pair[0])
            & (self.edge_global_vertices[:, 1] == pair[1])
        )
        if len(matches) != 1:
            raise ValueError("expected one same-colour charge edge")
        return int(matches[0])


@dataclass(frozen=True)
class ChargeResidualAnalysis:
    """Homology of a closed triangular-lattice charge residual."""

    component_windings: tuple[tuple[tuple[int, int], ...], ...]

    @property
    def logical_error(self) -> bool:
        return any(windings for windings in self.component_windings)


@dataclass(frozen=True)
class ChargeColorRecoveryResult:
    """Truth-referenced effective-error and MWPM recovery for one colour."""

    color: int
    syndrome: NDArray[np.uint8]
    effective_error: NDArray[np.uint8]
    correction: NDArray[np.uint8]
    residual: NDArray[np.uint8]
    residual_analysis: ChargeResidualAnalysis
    objective_weight: float

    @property
    def logical_error(self) -> bool:
        return self.residual_analysis.logical_error


@dataclass(frozen=True)
class D4ChargeRecoveryResult:
    """Second-stage recovery result for blue and green e-charges."""

    blue: ChargeColorRecoveryResult
    green: ChargeColorRecoveryResult

    @property
    def logical_error(self) -> bool:
        return self.blue.logical_error or self.green.logical_error


@dataclass(frozen=True)
class PublicChargeColorAction:
    """One colour's decoder action computed from the public charge record."""

    color: int
    syndrome: NDArray[np.uint8]
    correction: NDArray[np.uint8]
    objective_weight: float


@dataclass(frozen=True)
class D4PublicChargeAction:
    """Relation-free blue/green charge actions chosen from public data only."""

    blue: PublicChargeColorAction
    green: PublicChargeColorAction


def build_charge_lattice(
    honeycomb: PeriodicHoneycomb,
    color: int,
) -> ChargeLattice:
    """Construct the periodic same-colour triangular star lattice."""

    if color not in (BLUE, GREEN):
        raise ValueError("color must be BLUE or GREEN")
    opposite = GREEN if color == BLUE else BLUE
    vertex_ids = np.arange(color, honeycomb.vertex_count, 2, dtype=np.int64)
    records: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    for center in range(opposite, honeycomb.vertex_count, 2):
        neighbors, _ = periodic_local_neighborhood(honeycomb, center)
        x, y = honeycomb.vertex_coordinate(center)
        if opposite == GREEN:
            coordinates = ((x, y), (x, y + 1), (x + 1, y))
        else:
            coordinates = ((x, y), (x - 1, y), (x, y - 1))
        for first, second in ((0, 1), (1, 2), (2, 0)):
            global_left = int(neighbors[first])
            global_right = int(neighbors[second])
            dx = coordinates[second][0] - coordinates[first][0]
            dy = coordinates[second][1] - coordinates[first][1]
            if global_left > global_right:
                global_left, global_right = global_right, global_left
                dx, dy = -dx, -dy
            key = (global_left, global_right)
            if key in records:
                raise ValueError("duplicate edge in charge lattice construction")
            records[key] = (global_left // 2, global_right // 2, dx, dy)
    ordered = sorted(records.items())
    edge_global = np.asarray([key for key, _ in ordered], dtype=np.int64)
    edge_vertices = np.asarray(
        [(value[0], value[1]) for _, value in ordered], dtype=np.int64
    )
    displacements = np.asarray(
        [(value[2], value[3]) for _, value in ordered], dtype=np.int64
    )
    return ChargeLattice(
        color=color,
        honeycomb_vertex_count=honeycomb.vertex_count,
        vertex_ids=vertex_ids,
        edge_vertices=edge_vertices,
        edge_global_vertices=edge_global,
        edge_displacements=displacements,
        period_matrix=honeycomb.period_matrix.copy(),
    )


def charge_check_matrix(lattice: ChargeLattice) -> NDArray[np.uint8]:
    check = np.zeros((lattice.vertex_count, lattice.edge_count), dtype=np.uint8)
    for edge, (left, right) in enumerate(lattice.edge_vertices):
        check[int(left), edge] = 1
        check[int(right), edge] = 1
    return check


def charge_chain_boundary(
    lattice: ChargeLattice,
    chain: NDArray[np.generic],
) -> NDArray[np.uint8]:
    selected = np.asarray(chain, dtype=np.uint8)
    if selected.shape != (lattice.edge_count,) or np.any(selected > 1):
        raise ValueError("charge chain must be binary with one value per edge")
    return np.asarray((charge_check_matrix(lattice) @ selected) % 2, dtype=np.uint8)


def effective_error_from_relations(
    lattice: ChargeLattice,
    relation_pairs: tuple[tuple[int, int], ...],
    charge_outcomes: NDArray[np.generic],
    active_vertices: tuple[int, ...] | None = None,
) -> NDArray[np.uint8]:
    """Choose a deterministic forest string with the measured charge boundary.

    ``active_vertices`` is explicit for production union components because a
    component may contain only one star of a given colour.  Such a singleton
    has no relation edge but still carries the source's even-parity constraint.
    The optional default preserves the small direct fixtures, where activity
    is exactly the set of relation endpoints.
    """

    charge = np.asarray(charge_outcomes, dtype=np.int64)
    if charge.shape != (lattice.honeycomb_vertex_count,):
        raise ValueError("charge_outcomes must have one value per honeycomb vertex")
    pairs = tuple(tuple(sorted((int(left), int(right)))) for left, right in relation_pairs)
    if len(pairs) != len(set(pairs)):
        raise ValueError("relation_pairs must be unique")
    pair_vertices = {vertex for pair in pairs for vertex in pair}
    active = pair_vertices if active_vertices is None else {
        int(vertex) for vertex in active_vertices
    }
    if not pair_vertices <= active:
        raise ValueError("relation pair endpoints must be active")
    adjacency: dict[int, list[int]] = {vertex: [] for vertex in active}
    for vertex in active:
        lattice.local_vertex(vertex)
    for left, right in pairs:
        lattice.local_vertex(left)
        lattice.local_vertex(right)
        lattice.edge_between_global(left, right)
        adjacency[left].append(right)
        adjacency[right].append(left)
    target_vertices = set(int(vertex) for vertex in lattice.vertex_ids)
    if any(charge[vertex] not in (0, 1) for vertex in active):
        raise ValueError("active same-colour charge outcomes must be binary")
    if any(charge[vertex] != -1 for vertex in target_vertices - active):
        raise ValueError("inactive same-colour charge outcomes must be -1")

    selected = np.zeros(lattice.edge_count, dtype=np.uint8)
    unseen = set(active)
    while unseen:
        root = min(unseen)
        parent: dict[int, int | None] = {root: None}
        order = [root]
        for vertex in order:
            unseen.discard(vertex)
            for neighbor in sorted(adjacency[vertex]):
                if neighbor not in parent:
                    parent[neighbor] = vertex
                    order.append(neighbor)
        parity = {vertex: int(charge[vertex]) for vertex in order}
        for vertex in reversed(order[1:]):
            ancestor = parent[vertex]
            if ancestor is None:
                raise RuntimeError("non-root tree vertex lacks a parent")
            if parity[vertex]:
                selected[lattice.edge_between_global(vertex, ancestor)] ^= 1
                parity[ancestor] ^= 1
        if parity[root]:
            raise ValueError("relation component has odd measured charge parity")

    expected = np.zeros(lattice.vertex_count, dtype=np.uint8)
    for vertex in active:
        expected[lattice.local_vertex(vertex)] = int(charge[vertex])
    if not np.array_equal(charge_chain_boundary(lattice, selected), expected):
        raise RuntimeError("constructed effective error has the wrong charge boundary")
    return selected


def decode_charge_syndrome(
    lattice: ChargeLattice,
    syndrome: NDArray[np.generic],
) -> tuple[NDArray[np.uint8], float]:
    detectors = np.asarray(syndrome, dtype=np.uint8)
    if detectors.shape != (lattice.vertex_count,) or np.any(detectors > 1):
        raise ValueError("charge syndrome must be binary with one value per vertex")
    if int(np.sum(detectors)) % 2:
        raise ValueError("periodic charge syndrome must have even parity")
    matching = pymatching.Matching.from_check_matrix(
        charge_check_matrix(lattice),
        weights=np.ones(lattice.edge_count, dtype=np.float64),
    )
    correction, weight = matching.decode(detectors, return_weight=True)
    correction = np.asarray(correction, dtype=np.uint8)
    if not np.array_equal(charge_chain_boundary(lattice, correction), detectors):
        raise RuntimeError("charge MWPM correction does not reproduce syndrome")
    return correction, float(weight)


def public_postflux_charge_record(
    internal_outcomes: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Project simulator sentinels to the full binary decoder-visible record."""

    internal = np.asarray(internal_outcomes, dtype=np.int64)
    if internal.ndim != 1 or np.any(~np.isin(internal, (-1, 0, 1))):
        raise ValueError("internal outcomes must be a one-dimensional -1/0/1 record")
    return np.asarray(np.maximum(internal, 0), dtype=np.uint8)


def _public_color_action(
    honeycomb: PeriodicHoneycomb,
    public_record: NDArray[np.uint8],
    color: int,
) -> PublicChargeColorAction:
    lattice = build_charge_lattice(honeycomb, color)
    syndrome = np.asarray(
        [public_record[int(vertex)] for vertex in lattice.vertex_ids],
        dtype=np.uint8,
    )
    correction, weight = decode_charge_syndrome(lattice, syndrome)
    return PublicChargeColorAction(
        color=color,
        syndrome=syndrome,
        correction=correction,
        objective_weight=weight,
    )


def decode_public_postflux_charges(
    honeycomb: PeriodicHoneycomb,
    public_charge_outcomes: NDArray[np.generic],
) -> D4PublicChargeAction:
    """Choose both charge corrections from the full public binary record.

    This is the online decoder boundary.  It intentionally accepts neither
    post-flux relations nor an active-support mask.
    """

    public = np.asarray(public_charge_outcomes, dtype=np.uint8)
    if public.shape != (honeycomb.vertex_count,) or np.any(public > 1):
        raise ValueError("public charge outcomes must be binary on every star")
    return D4PublicChargeAction(
        blue=_public_color_action(honeycomb, public, BLUE),
        green=_public_color_action(honeycomb, public, GREEN),
    )


def _canonical_winding(
    vector: NDArray[np.int64], period_matrix: NDArray[np.int64]
) -> tuple[int, int]:
    a, b = (int(value) for value in period_matrix[0])
    c, d = (int(value) for value in period_matrix[1])
    determinant = a * d - b * c
    numerator = np.array(
        (
            d * int(vector[0]) - b * int(vector[1]),
            -c * int(vector[0]) + a * int(vector[1]),
        ),
        dtype=np.int64,
    )
    if determinant <= 0 or np.any(numerator % determinant):
        raise ValueError("charge lift inconsistency is not a torus winding")
    winding = numerator // determinant
    first_nonzero = next((int(value) for value in winding if value), 0)
    if first_nonzero < 0:
        winding = -winding
    return int(winding[0]), int(winding[1])


def classify_closed_charge_chain(
    lattice: ChargeLattice,
    chain: NDArray[np.generic],
) -> ChargeResidualAnalysis:
    selected = np.asarray(chain, dtype=np.uint8)
    if np.any(charge_chain_boundary(lattice, selected)):
        raise ValueError("charge recovery residual must be closed")
    adjacency: list[list[int]] = [[] for _ in range(lattice.vertex_count)]
    for edge in np.flatnonzero(selected):
        left, right = lattice.edge_vertices[edge]
        adjacency[int(left)].append(int(edge))
        adjacency[int(right)].append(int(edge))
    unseen = {vertex for vertex, edges in enumerate(adjacency) if edges}
    component_windings: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        root = min(unseen)
        stack = [root]
        visited: set[int] = set()
        lift = {root: np.zeros(2, dtype=np.int64)}
        windings: set[tuple[int, int]] = set()
        while stack:
            vertex = stack.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            unseen.discard(vertex)
            for edge in adjacency[vertex]:
                left, right = (int(value) for value in lattice.edge_vertices[edge])
                if vertex == left:
                    neighbor = right
                    delta = lattice.edge_displacements[edge]
                else:
                    neighbor = left
                    delta = -lattice.edge_displacements[edge]
                proposed = lift[vertex] + delta
                if neighbor in lift:
                    discrepancy = proposed - lift[neighbor]
                    if np.any(discrepancy):
                        windings.add(
                            _canonical_winding(discrepancy, lattice.period_matrix)
                        )
                else:
                    lift[neighbor] = proposed
                    stack.append(neighbor)
        component_windings.append(tuple(sorted(windings)))
    return ChargeResidualAnalysis(tuple(component_windings))


def _score_charge_color_action(
    lattice: ChargeLattice,
    relation_pairs: tuple[tuple[int, int], ...],
    internal_charge_outcomes: NDArray[np.generic],
    active_vertices: tuple[int, ...],
    action: PublicChargeColorAction,
) -> ChargeColorRecoveryResult:
    effective = effective_error_from_relations(
        lattice, relation_pairs, internal_charge_outcomes, active_vertices
    )
    syndrome = charge_chain_boundary(lattice, effective)
    if action.color != lattice.color or not np.array_equal(action.syndrome, syndrome):
        raise ValueError("public charge action is not bound to this measured record")
    if not np.array_equal(
        charge_chain_boundary(lattice, action.correction), syndrome
    ):
        raise ValueError("public charge correction does not reproduce the record")
    residual = effective ^ action.correction
    analysis = classify_closed_charge_chain(lattice, residual)
    return ChargeColorRecoveryResult(
        color=lattice.color,
        syndrome=syndrome,
        effective_error=effective,
        correction=action.correction,
        residual=residual,
        residual_analysis=analysis,
        objective_weight=action.objective_weight,
    )


def score_public_postflux_charge_action(
    honeycomb: PeriodicHoneycomb,
    relations: PeriodicPostFluxRelations,
    public_charge_outcomes: NDArray[np.generic],
    action: D4PublicChargeAction,
    *,
    flux_components_homologically_trivial: bool,
) -> D4ChargeRecoveryResult:
    """Score a public action against private action-conditioned simulator truth."""

    if not flux_components_homologically_trivial:
        raise ValueError("charge recovery requires homologically trivial flux union")
    public = np.asarray(public_charge_outcomes, dtype=np.uint8)
    if public.shape != (honeycomb.vertex_count,) or np.any(public > 1):
        raise ValueError("public charge outcomes must be binary on every star")
    active = set(relations.active_vertices)
    inactive = set(range(honeycomb.vertex_count)) - active
    if any(public[vertex] for vertex in inactive):
        raise ValueError("public charge record is nonzero outside private support")
    internal = np.asarray(public, dtype=np.int64)
    internal[list(inactive)] = -1
    pairs_by_color: dict[int, list[tuple[int, int]]] = {BLUE: [], GREEN: []}
    for left, right in relations.entanglement_pairs:
        left_color = int(honeycomb.vertex_colors[left])
        right_color = int(honeycomb.vertex_colors[right])
        if left_color != right_color:
            raise ValueError("post-flux relation must join same-colour stars")
        pairs_by_color[left_color].append((left, right))
    blue_lattice = build_charge_lattice(honeycomb, BLUE)
    green_lattice = build_charge_lattice(honeycomb, GREEN)
    return D4ChargeRecoveryResult(
        blue=_score_charge_color_action(
            blue_lattice,
            tuple(pairs_by_color[BLUE]),
            internal,
            tuple(
                sorted(
                    vertex
                    for vertex in active
                    if int(honeycomb.vertex_colors[vertex]) == BLUE
                )
            ),
            action.blue,
        ),
        green=_score_charge_color_action(
            green_lattice,
            tuple(pairs_by_color[GREEN]),
            internal,
            tuple(
                sorted(
                    vertex
                    for vertex in active
                    if int(honeycomb.vertex_colors[vertex]) == GREEN
                )
            ),
            action.green,
        ),
    )


def recover_postflux_charges(
    honeycomb: PeriodicHoneycomb,
    relations: PeriodicPostFluxRelations,
    charge_outcomes: NDArray[np.generic],
    *,
    flux_components_homologically_trivial: bool,
) -> D4ChargeRecoveryResult:
    """Compatibility wrapper with a relation-free online action boundary."""

    public = public_postflux_charge_record(charge_outcomes)
    action = decode_public_postflux_charges(honeycomb, public)
    return score_public_postflux_charge_action(
        honeycomb,
        relations,
        public,
        action,
        flux_components_homologically_trivial=flux_components_homologically_trivial,
    )
