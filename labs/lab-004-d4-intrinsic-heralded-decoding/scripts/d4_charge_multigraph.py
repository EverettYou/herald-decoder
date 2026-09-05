"""Branch-labelled primitive charge multigraph and post-flux provenance.

The primitive L=2 quotient has parallel same-colour triangular edges.  Their
binary boundaries agree, but their opposite-colour centres and periodic
displacements differ.  This module retains those physical branches and maps
each production two-step union path to a unique branch before any endpoint
projection is taken.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pymatching
from numpy.typing import NDArray

from d4_charge import ChargeLattice, charge_chain_boundary
from d4_honeycomb import BLUE, GREEN, PeriodicHoneycomb
from d4_postflux import (
    PeriodicPostFluxRelations,
    infer_periodic_postflux_relations,
    periodic_local_neighborhood,
)


@dataclass(frozen=True)
class ChargeBranch:
    """One physical triangular edge in the primitive periodic quotient."""

    color: int
    branch_id: int
    endpoints: tuple[int, int]
    opposite_center: int
    displacement: tuple[int, int]
    honeycomb_edges: tuple[int, int]


@dataclass(frozen=True)
class BranchRelation:
    """One actual two-step union path and its unique charge branch."""

    color: int
    branch_id: int
    endpoints: tuple[int, int]
    opposite_center: int
    honeycomb_edges: tuple[int, int]


@dataclass(frozen=True)
class BranchPostFluxRelations:
    """Branch-resolved relations plus their endpoint-only projection."""

    active_vertices: tuple[int, ...]
    relations: tuple[BranchRelation, ...]

    @property
    def entanglement_pairs(self) -> tuple[tuple[int, int], ...]:
        return tuple(sorted({relation.endpoints for relation in self.relations}))


def _center_neighbor_coordinates(
    lattice: PeriodicHoneycomb,
    center: int,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    x, y = lattice.vertex_coordinate(center)
    center_color = int(lattice.vertex_colors[center])
    if center_color == GREEN:
        return (x, y), (x, y + 1), (x + 1, y)
    if center_color == BLUE:
        return (x, y), (x - 1, y), (x, y - 1)
    raise ValueError("center has invalid honeycomb colour")


def build_charge_branch_catalog(
    lattice: PeriodicHoneycomb,
    color: int,
) -> tuple[ChargeBranch, ...]:
    """Enumerate every same-colour triangular branch without deduplication."""

    if color not in (BLUE, GREEN):
        raise ValueError("color must be BLUE or GREEN")
    opposite = GREEN if color == BLUE else BLUE
    raw: list[
        tuple[tuple[int, int], int, tuple[int, int], tuple[int, int]]
    ] = []
    for center in range(opposite, lattice.vertex_count, 2):
        neighbors, edges = periodic_local_neighborhood(lattice, center)
        coordinates = _center_neighbor_coordinates(lattice, center)
        for first, second in ((0, 1), (1, 2), (2, 0)):
            left = int(neighbors[first])
            right = int(neighbors[second])
            dx = coordinates[second][0] - coordinates[first][0]
            dy = coordinates[second][1] - coordinates[first][1]
            path_edges = tuple(sorted((int(edges[first]), int(edges[second]))))
            if left > right:
                left, right = right, left
                dx, dy = -dx, -dy
            raw.append(((left, right), int(center), (int(dx), int(dy)), path_edges))
    ordered = sorted(raw)
    if len(ordered) != len(set(ordered)):
        raise RuntimeError("physical charge branches are not uniquely labelled")
    return tuple(
        ChargeBranch(
            color=color,
            branch_id=branch_id,
            endpoints=endpoints,
            opposite_center=center,
            displacement=displacement,
            honeycomb_edges=path_edges,
        )
        for branch_id, (endpoints, center, displacement, path_edges) in enumerate(
            ordered
        )
    )


def build_branch_charge_lattice(
    lattice: PeriodicHoneycomb,
    color: int,
) -> ChargeLattice:
    """Build a topology-preserving charge lattice with parallel columns."""

    branches = build_charge_branch_catalog(lattice, color)
    vertex_ids = np.arange(color, lattice.vertex_count, 2, dtype=np.int64)
    return ChargeLattice(
        color=color,
        honeycomb_vertex_count=lattice.vertex_count,
        vertex_ids=vertex_ids,
        edge_vertices=np.asarray(
            [
                (branch.endpoints[0] // 2, branch.endpoints[1] // 2)
                for branch in branches
            ],
            dtype=np.int64,
        ),
        edge_global_vertices=np.asarray(
            [branch.endpoints for branch in branches], dtype=np.int64
        ),
        edge_displacements=np.asarray(
            [branch.displacement for branch in branches], dtype=np.int64
        ),
        period_matrix=lattice.period_matrix.copy(),
    )


def branch_edge_wrap_sectors(
    lattice: PeriodicHoneycomb,
    color: int,
) -> tuple[tuple[int, int], ...]:
    """Return each branch's GF(2) torus crossing in a fixed vertex gauge.

    For a branch oriented from its smaller to larger global endpoint, subtract
    the stored representative-coordinate difference from its lifted primitive
    displacement.  The remainder is an integer torus period.  Its coefficients
    modulo two form a linear homology cochain on the multigraph.
    """

    periods = lattice.period_matrix
    a, b = (int(value) for value in periods[0])
    c, d = (int(value) for value in periods[1])
    determinant = a * d - b * c
    if determinant <= 0:
        raise ValueError("period matrix must have positive determinant")
    sectors = []
    for branch in build_charge_branch_catalog(lattice, color):
        left_coordinate = np.asarray(
            lattice.vertex_coordinate(branch.endpoints[0]), dtype=np.int64
        )
        right_coordinate = np.asarray(
            lattice.vertex_coordinate(branch.endpoints[1]), dtype=np.int64
        )
        residual = (
            np.asarray(branch.displacement, dtype=np.int64)
            - (right_coordinate - left_coordinate)
        )
        numerator = np.asarray(
            (
                d * int(residual[0]) - b * int(residual[1]),
                -c * int(residual[0]) + a * int(residual[1]),
            ),
            dtype=np.int64,
        )
        if np.any(numerator % determinant):
            raise ValueError("branch lift differs from representatives by a non-period")
        winding = numerator // determinant
        sectors.append((int(winding[0]) & 1, int(winding[1]) & 1))
    return tuple(sectors)


def branch_chain_sector(
    lattice: PeriodicHoneycomb,
    color: int,
    chain: NDArray[np.generic],
) -> tuple[int, int]:
    """Return the linear GF(2) homology of one closed branch chain."""

    charge_lattice = build_branch_charge_lattice(lattice, color)
    selected = np.asarray(chain, dtype=np.uint8)
    if selected.shape != (charge_lattice.edge_count,) or np.any(selected > 1):
        raise ValueError("branch chain must be binary with one value per edge")
    if np.any(charge_chain_boundary(charge_lattice, selected)):
        raise ValueError("branch homology requires a closed charge chain")
    first = 0
    second = 0
    for edge, sector in enumerate(branch_edge_wrap_sectors(lattice, color)):
        if selected[edge]:
            first ^= sector[0]
            second ^= sector[1]
    return first, second


def build_expanded_branch_matching(
    lattice: PeriodicHoneycomb,
    color: int,
    weights: NDArray[np.generic],
) -> pymatching.Matching:
    """Represent every physical branch as a private two-edge matching path."""

    charge_lattice = build_branch_charge_lattice(lattice, color)
    branch_weights = np.asarray(weights, dtype=np.float64)
    if branch_weights.shape != (charge_lattice.edge_count,):
        raise ValueError("weights must have one value per physical charge branch")
    if not np.all(np.isfinite(branch_weights)):
        raise ValueError("branch weights must be finite")
    matching = pymatching.Matching()
    for branch_id, (left, right) in enumerate(charge_lattice.edge_vertices):
        auxiliary = charge_lattice.vertex_count + branch_id
        half_weight = float(branch_weights[branch_id]) / 2.0
        matching.add_edge(
            int(left),
            auxiliary,
            fault_ids=branch_id,
            weight=half_weight,
        )
        matching.add_edge(
            auxiliary,
            int(right),
            weight=half_weight,
        )
    return matching


def expanded_charge_syndrome(
    lattice: ChargeLattice,
    syndrome: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Embed the measured charge syndrome with one zero per private auxiliary."""

    measured = np.asarray(syndrome, dtype=np.uint8)
    if measured.shape != (lattice.vertex_count,) or np.any(measured > 1):
        raise ValueError("charge syndrome must be binary on physical vertices")
    return np.concatenate(
        (measured, np.zeros(lattice.edge_count, dtype=np.uint8))
    )


def decode_expanded_branch_syndrome(
    honeycomb: PeriodicHoneycomb,
    color: int,
    syndrome: NDArray[np.generic],
    weights: NDArray[np.generic],
) -> tuple[NDArray[np.uint8], float]:
    """Decode on the expanded graph and return one physical branch mask."""

    charge_lattice = build_branch_charge_lattice(honeycomb, color)
    matching = build_expanded_branch_matching(honeycomb, color, weights)
    expanded = expanded_charge_syndrome(charge_lattice, syndrome)
    correction, objective = matching.decode(expanded, return_weight=True)
    correction = np.asarray(correction, dtype=np.uint8)
    if correction.shape != (charge_lattice.edge_count,):
        raise RuntimeError("expanded decoder returned the wrong fault-id shape")
    if not np.array_equal(
        charge_chain_boundary(charge_lattice, correction),
        np.asarray(syndrome, dtype=np.uint8),
    ):
        raise RuntimeError("expanded decoder returned the wrong physical boundary")
    return correction, float(objective)


def branch_catalog_index(
    catalog: tuple[ChargeBranch, ...],
) -> dict[tuple[int, tuple[int, int], tuple[int, int]], ChargeBranch]:
    """Index branches by centre, endpoints, and the actual honeycomb path."""

    index: dict[tuple[int, tuple[int, int], tuple[int, int]], ChargeBranch] = {}
    for branch in catalog:
        key = (branch.opposite_center, branch.endpoints, branch.honeycomb_edges)
        if key in index:
            raise RuntimeError("branch catalog contains duplicate provenance keys")
        index[key] = branch
    return index


def infer_branch_postflux_relations(
    lattice: PeriodicHoneycomb,
    physical_edges: NDArray[np.generic],
    correction_edges: NDArray[np.generic],
    catalogs: dict[int, tuple[ChargeBranch, ...]] | None = None,
) -> BranchPostFluxRelations:
    """Map every actual two-step union path to one physical charge branch."""

    physical = np.asarray(physical_edges, dtype=np.bool_)
    correction = np.asarray(correction_edges, dtype=np.bool_)
    if physical.shape != (lattice.edge_count,):
        raise ValueError("physical_edges must have one value per lattice edge")
    if correction.shape != (lattice.edge_count,):
        raise ValueError("correction_edges must have one value per lattice edge")
    branch_catalogs = catalogs or {
        color: build_charge_branch_catalog(lattice, color)
        for color in (BLUE, GREEN)
    }
    indexes = {
        color: branch_catalog_index(branch_catalogs[color])
        for color in (BLUE, GREEN)
    }
    union = physical | correction
    adjacency: list[list[tuple[int, int]]] = [
        [] for _ in range(lattice.vertex_count)
    ]
    for edge in np.flatnonzero(union):
        left, right = (int(value) for value in lattice.edge_vertices[edge])
        adjacency[left].append((right, int(edge)))
        adjacency[right].append((left, int(edge)))
    unseen = {vertex for vertex, neighbors in enumerate(adjacency) if neighbors}
    active: set[int] = set()
    resolved: dict[tuple[int, int], BranchRelation] = {}
    while unseen:
        root = min(unseen)
        stack = [root]
        component: set[int] = set()
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            unseen.discard(vertex)
            stack.extend(neighbor for neighbor, _ in adjacency[vertex])
        active.update(component)
        for target_color in (BLUE, GREEN):
            target_vertices = {
                vertex
                for vertex in component
                if int(lattice.vertex_colors[vertex]) == target_color
            }
            for center in sorted(component - target_vertices):
                neighbors = sorted(
                    (neighbor, edge)
                    for neighbor, edge in adjacency[center]
                    if neighbor in target_vertices
                )
                for (left, left_edge), (right, right_edge) in combinations(
                    neighbors, 2
                ):
                    endpoints = tuple(sorted((int(left), int(right))))
                    path_edges = tuple(sorted((int(left_edge), int(right_edge))))
                    key = (int(center), endpoints, path_edges)
                    matches = [indexes[target_color][key]] if key in indexes[target_color] else []
                    if len(matches) != 1:
                        raise ValueError(
                            "two-step union relation has zero or multiple physical branches"
                        )
                    branch = matches[0]
                    relation = BranchRelation(
                        color=target_color,
                        branch_id=branch.branch_id,
                        endpoints=endpoints,
                        opposite_center=int(center),
                        honeycomb_edges=path_edges,
                    )
                    relation_key = (target_color, branch.branch_id)
                    if relation_key in resolved and resolved[relation_key] != relation:
                        raise RuntimeError("branch id has inconsistent relation provenance")
                    resolved[relation_key] = relation
    return BranchPostFluxRelations(
        active_vertices=tuple(sorted(active)),
        relations=tuple(
            sorted(
                resolved.values(),
                key=lambda relation: (relation.color, relation.branch_id),
            )
        ),
    )


def validate_endpoint_projection(
    lattice: PeriodicHoneycomb,
    physical_edges: NDArray[np.generic],
    correction_edges: NDArray[np.generic],
    enriched: BranchPostFluxRelations,
) -> tuple[bool, PeriodicPostFluxRelations]:
    """Check that forgetting branch labels exactly recovers production pairs."""

    endpoint = infer_periodic_postflux_relations(
        lattice, physical_edges, correction_edges
    )
    agrees = (
        enriched.active_vertices == endpoint.active_vertices
        and enriched.entanglement_pairs == endpoint.entanglement_pairs
    )
    return agrees, endpoint
