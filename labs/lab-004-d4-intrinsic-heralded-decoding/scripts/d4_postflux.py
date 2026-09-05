"""Post-flux e-charge constraint accumulation for the D4 decoder.

Appendix A describes local stabilizer rules that entangle same-colour star
measurements after the physical and corrective red-X strings are combined.
The published simulations accumulate those local relations with a disjoint-set
union (DSU). This module implements the accumulation layer and the source's
seven-row diagram lookup. The diagram lookup is diagnostic only: integration
on 2026-08-28 showed that reflected MWPM configurations are not uniquely
covered by those masks. Production uses the source's global invariant of one
blue and one green parity component per connected physical/correction union.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray

from d4_honeycomb import BLUE, GREEN, PeriodicHoneycomb


@dataclass(frozen=True)
class PostFluxConstraintAnalysis:
    """Connected measurement constraints after flux correction."""

    components: tuple[tuple[int, ...], ...]
    charge_parities: tuple[int, ...]
    allowed: bool


class LocalArm(IntEnum):
    """The three neighboring-star directions in Appendix A's rule table."""

    TOP = 0
    BOTTOM_LEFT = 1
    BOTTOM_RIGHT = 2


@dataclass(frozen=True)
class PostFluxLocalRule:
    """One canonical row of Appendix A's seven-row local rule table."""

    row: int
    physical_mask: int
    correction_mask: int
    measured_after_error: bool
    entangled_arms: tuple[LocalArm, ...]


@dataclass(frozen=True)
class PeriodicLocalRuleApplication:
    """One source-table rule applied to an actual periodic neighborhood."""

    row: int
    center_vertex: int
    neighbor_vertices: tuple[int, int, int]
    edge_indices: tuple[int, int, int]
    physical_mask: int
    correction_mask: int
    entanglement_pairs: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class PeriodicPostFluxRelations:
    """Active post-flux stars and their same-colour parity relations."""

    applications: tuple[PeriodicLocalRuleApplication, ...]
    active_vertices: tuple[int, ...]
    entanglement_pairs: tuple[tuple[int, int], ...]


def _mask(*arms: LocalArm) -> int:
    return sum(1 << int(arm) for arm in arms)


# Transcription of the table on Appendix A p. 13.  The diagrams use one
# vertical top arm and two diagonal bottom arms.  Rows are stored in the order
# printed.  All but row 6 entangle the top and bottom-right neighboring stars;
# row 6 entangles all three.  Rotations are generated algorithmically below.
POSTFLUX_LOCAL_RULES = (
    PostFluxLocalRule(
        1,
        _mask(),
        _mask(LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
        False,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        2,
        _mask(LocalArm.TOP),
        _mask(LocalArm.BOTTOM_RIGHT),
        False,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        3,
        _mask(LocalArm.BOTTOM_RIGHT),
        _mask(LocalArm.TOP, LocalArm.BOTTOM_LEFT, LocalArm.BOTTOM_RIGHT),
        False,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        4,
        _mask(LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
        _mask(),
        True,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        5,
        _mask(LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
        _mask(LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
        True,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        6,
        _mask(LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
        _mask(LocalArm.TOP, LocalArm.BOTTOM_LEFT),
        True,
        (LocalArm.TOP, LocalArm.BOTTOM_LEFT, LocalArm.BOTTOM_RIGHT),
    ),
    PostFluxLocalRule(
        7,
        _mask(LocalArm.TOP, LocalArm.BOTTOM_LEFT, LocalArm.BOTTOM_RIGHT),
        _mask(LocalArm.BOTTOM_RIGHT),
        False,
        (LocalArm.TOP, LocalArm.BOTTOM_RIGHT),
    ),
)


def rotate_arm_mask(mask: int, rotation: int) -> int:
    """Rotate a three-arm incidence mask counterclockwise by 0, 1, or 2."""

    if mask < 0 or mask >= 8:
        raise ValueError("arm mask must be a three-bit integer")
    turns = int(rotation) % 3
    result = 0
    for arm in LocalArm:
        if mask & (1 << int(arm)):
            result |= 1 << ((int(arm) + turns) % 3)
    return result


def reflect_arm_mask(mask: int) -> int:
    """Reflect a three-arm mask by exchanging bottom-left and bottom-right."""

    if mask < 0 or mask >= 8:
        raise ValueError("arm mask must be a three-bit integer")
    return (mask & 0b001) | ((mask & 0b010) << 1) | ((mask & 0b100) >> 1)


def _reflect_arm(arm: LocalArm) -> LocalArm:
    if arm == LocalArm.BOTTOM_LEFT:
        return LocalArm.BOTTOM_RIGHT
    if arm == LocalArm.BOTTOM_RIGHT:
        return LocalArm.BOTTOM_LEFT
    return LocalArm.TOP


def lookup_postflux_local_rule(
    physical_mask: int,
    correction_mask: int,
    measured_after_error: bool,
) -> tuple[int, tuple[LocalArm, ...]]:
    """Return the printed row and rotated entangled-neighbor directions.

    Only the seven source rows and their three lattice rotations are accepted
    in this canonical table frame.  The periodic adapter handles the mirrored
    green-centered frame explicitly; admitting both chiralities here would be
    ambiguous for rows whose reflected images share masks but entangle
    different neighbor pairs.
    """

    if physical_mask < 0 or physical_mask >= 8:
        raise ValueError("physical_mask must be a three-bit integer")
    if correction_mask < 0 or correction_mask >= 8:
        raise ValueError("correction_mask must be a three-bit integer")
    matches: list[tuple[int, tuple[LocalArm, ...]]] = []
    for rule in POSTFLUX_LOCAL_RULES:
        if rule.measured_after_error != bool(measured_after_error):
            continue
        for rotation in range(3):
            if (
                rotate_arm_mask(rule.physical_mask, rotation) == physical_mask
                and rotate_arm_mask(rule.correction_mask, rotation)
                == correction_mask
            ):
                arms = tuple(
                    LocalArm((int(arm) + rotation) % 3)
                    for arm in rule.entangled_arms
                )
                matches.append((rule.row, arms))
    if len(matches) != 1:
        raise ValueError(
            "local physical/correction configuration is not one unique "
            "Appendix-A rule"
        )
    return matches[0]


def local_entanglement_pairs(
    neighbor_vertices: tuple[int, int, int],
    physical_mask: int,
    correction_mask: int,
    measured_after_error: bool,
) -> tuple[tuple[int, int], ...]:
    """Translate one accepted local rule into DSU union operations."""

    if len(neighbor_vertices) != 3 or len(set(neighbor_vertices)) != 3:
        raise ValueError("neighbor_vertices must contain three distinct vertices")
    _, arms = lookup_postflux_local_rule(
        physical_mask,
        correction_mask,
        measured_after_error,
    )
    anchor = neighbor_vertices[int(arms[0])]
    return tuple(
        (anchor, neighbor_vertices[int(arm)])
        for arm in arms[1:]
    )


def periodic_local_neighborhood(
    lattice: PeriodicHoneycomb,
    center_vertex: int,
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Return actual neighbors and incident edges in source arm order.

    Use primitive honeycomb basis vectors ``a1=(sqrt(3)/2, 3/2)`` and
    ``a2=(-sqrt(3)/2, 3/2)``, with the green sublattice displaced vertically
    above blue.  For a blue center, the same, x-1, and y-1 cells are top,
    bottom-left, and bottom-right.  For a green center, the globally drawn
    left/right arms exchange under sublattice inversion: same, y+1, and x+1.
    This ordering supports exact fixtures for the printed source diagrams. It
    is not a complete production inference rule for arbitrary matched strings;
    ``infer_periodic_postflux_relations`` implements the global union invariant.
    """

    center = int(center_vertex)
    if center < 0 or center >= lattice.vertex_count:
        raise ValueError("center_vertex is out of range")
    x, y = lattice.vertex_coordinate(center)
    color = int(lattice.vertex_colors[center])
    if color == BLUE:
        opposite = GREEN
        coordinates = ((x, y), (x - 1, y), (x, y - 1))
    elif color == GREEN:
        opposite = BLUE
        coordinates = ((x, y), (x, y + 1), (x + 1, y))
    else:
        raise ValueError("center vertex has invalid honeycomb colour")
    neighbors = tuple(
        lattice.vertex_id(nx, ny, opposite) for nx, ny in coordinates
    )
    if len(set(neighbors)) != 3:
        raise ValueError("periodic neighborhood has degenerate arm vertices")
    edges = tuple(lattice.edge_between(center, neighbor) for neighbor in neighbors)
    if len(set(edges)) != 3:
        raise ValueError("periodic neighborhood has degenerate arm edges")
    return neighbors, edges


def _edge_selection_to_arm_mask(
    edge_selection: NDArray[np.generic],
    edge_indices: tuple[int, int, int],
    edge_count: int,
) -> int:
    selected = np.asarray(edge_selection, dtype=np.bool_)
    if selected.shape != (edge_count,):
        raise ValueError("edge selection must have one value per lattice edge")
    return sum(
        (1 << arm) if selected[edge] else 0
        for arm, edge in enumerate(edge_indices)
    )


def apply_periodic_postflux_local_rule(
    lattice: PeriodicHoneycomb,
    center_vertex: int,
    physical_edges: NDArray[np.generic],
    correction_edges: NDArray[np.generic],
    measured_after_error: bool,
) -> PeriodicLocalRuleApplication:
    """Map one printed Appendix-A diagram fixture onto periodic edges.

    This fail-closed helper audits the canonical rows and rotations. It must
    not be used as the production relation inference for arbitrary MWPM output.
    """

    neighbors, edges = periodic_local_neighborhood(lattice, center_vertex)
    physical_mask = _edge_selection_to_arm_mask(
        physical_edges, edges, lattice.edge_count
    )
    correction_mask = _edge_selection_to_arm_mask(
        correction_edges, edges, lattice.edge_count
    )
    center_color = int(lattice.vertex_colors[int(center_vertex)])
    canonical_physical = (
        reflect_arm_mask(physical_mask) if center_color == GREEN else physical_mask
    )
    canonical_correction = (
        reflect_arm_mask(correction_mask)
        if center_color == GREEN
        else correction_mask
    )
    row, canonical_arms = lookup_postflux_local_rule(
        canonical_physical,
        canonical_correction,
        measured_after_error,
    )
    actual_arms = tuple(
        _reflect_arm(arm) if center_color == GREEN else arm
        for arm in canonical_arms
    )
    anchor = neighbors[int(actual_arms[0])]
    pairs = tuple((anchor, neighbors[int(arm)]) for arm in actual_arms[1:])
    return PeriodicLocalRuleApplication(
        row=row,
        center_vertex=int(center_vertex),
        neighbor_vertices=neighbors,
        edge_indices=edges,
        physical_mask=physical_mask,
        correction_mask=correction_mask,
        entanglement_pairs=pairs,
    )


def collect_periodic_postflux_relations(
    lattice: PeriodicHoneycomb,
    center_vertices: tuple[int, ...],
    physical_edges: NDArray[np.generic],
    correction_edges: NDArray[np.generic],
    measured_after_error: tuple[bool, ...],
) -> PeriodicPostFluxRelations:
    """Collect actual local-rule outputs for a bounded post-flux component.

    The caller explicitly supplies the centers whose local configurations are
    part of the source transformation.  This function does not reinterpret an
    unlisted or inactive lattice neighborhood as a rule: every supplied center
    is looked up fail-closed, and only vertices touched by a resulting
    stabilizer relation enter the DSU active set.
    """

    centers = tuple(int(center) for center in center_vertices)
    measured = tuple(bool(value) for value in measured_after_error)
    if len(centers) != len(set(centers)):
        raise ValueError("center_vertices must be unique")
    if len(centers) != len(measured):
        raise ValueError("measured_after_error must have one value per center")
    applications = tuple(
        apply_periodic_postflux_local_rule(
            lattice,
            center,
            physical_edges,
            correction_edges,
            measured_flag,
        )
        for center, measured_flag in zip(centers, measured)
    )
    pairs = tuple(
        sorted(
            {
                tuple(sorted((int(left), int(right))))
                for application in applications
                for left, right in application.entanglement_pairs
            }
        )
    )
    active = tuple(sorted({vertex for pair in pairs for vertex in pair}))
    return PeriodicPostFluxRelations(applications, active, pairs)


def infer_periodic_postflux_relations(
    lattice: PeriodicHoneycomb,
    physical_edges: NDArray[np.generic],
    correction_edges: NDArray[np.generic],
) -> PeriodicPostFluxRelations:
    """Build the production DSU relations from connected union components.

    Appendix A states the invariant needed by the decoder directly: every
    connected component of the physical/correction union gives one blue and
    one green parity component.  The printed seven-row table is a local
    stabilizer derivation, but its canonical diagrams do not enumerate the
    mirrored matched-string configurations needed by an arbitrary periodic
    MWPM output.  Production therefore constructs the same-colour connectivity
    invariant without guessing missing reflected rows: every two-step path
    through an opposite-colour center becomes a triangular-lattice relation.
    """

    physical = np.asarray(physical_edges, dtype=np.bool_)
    correction = np.asarray(correction_edges, dtype=np.bool_)
    if physical.shape != (lattice.edge_count,):
        raise ValueError("physical_edges must have one value per lattice edge")
    if correction.shape != (lattice.edge_count,):
        raise ValueError("correction_edges must have one value per lattice edge")
    union = physical | correction
    adjacency: list[list[int]] = [[] for _ in range(lattice.vertex_count)]
    for edge in np.flatnonzero(union):
        left, right = (int(value) for value in lattice.edge_vertices[edge])
        adjacency[left].append(right)
        adjacency[right].append(left)
    unseen = {vertex for vertex, neighbors in enumerate(adjacency) if neighbors}
    active: set[int] = set()
    pairs: set[tuple[int, int]] = set()
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
            stack.extend(adjacency[vertex])
        active.update(component)
        for target_color in (BLUE, GREEN):
            target_vertices = {
                vertex
                for vertex in component
                if int(lattice.vertex_colors[vertex]) == target_color
            }
            candidates: set[tuple[int, int]] = set()
            for center in component:
                if int(lattice.vertex_colors[center]) == target_color:
                    continue
                same_color_neighbors = sorted(
                    neighbor
                    for neighbor in adjacency[center]
                    if neighbor in target_vertices
                )
                for first_index, first in enumerate(same_color_neighbors):
                    for second in same_color_neighbors[first_index + 1 :]:
                        candidates.add((first, second))
            if len(target_vertices) > 1:
                reached = {min(target_vertices)}
                frontier = list(reached)
                candidate_adjacency = {vertex: [] for vertex in target_vertices}
                for left, right in candidates:
                    candidate_adjacency[left].append(right)
                    candidate_adjacency[right].append(left)
                for vertex in frontier:
                    for neighbor in candidate_adjacency[vertex]:
                        if neighbor not in reached:
                            reached.add(neighbor)
                            frontier.append(neighbor)
                if reached != target_vertices:
                    raise RuntimeError(
                        "union component did not induce connected same-colour "
                        "charge relations"
                    )
            pairs.update(candidates)
    return PeriodicPostFluxRelations(
        applications=(),
        active_vertices=tuple(sorted(active)),
        entanglement_pairs=tuple(sorted(pairs)),
    )


class _DisjointSet:
    def __init__(self, vertices: tuple[int, ...]) -> None:
        self.parent = {vertex: vertex for vertex in vertices}
        self.rank = {vertex: 0 for vertex in vertices}

    def find(self, vertex: int) -> int:
        parent = self.parent[vertex]
        if parent != vertex:
            self.parent[vertex] = self.find(parent)
        return self.parent[vertex]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def accumulate_postflux_constraints(
    vertex_count: int,
    active_vertices: tuple[int, ...],
    entanglement_pairs: tuple[tuple[int, int], ...],
    charge_outcomes: NDArray[np.generic],
) -> PostFluxConstraintAnalysis:
    """Accumulate local same-colour entanglement relations with a DSU.

    ``active_vertices`` are the star measurements participating in the
    physical-error/correction component.  ``entanglement_pairs`` are the local
    stabilizer relations supplied by the Appendix-A lookup.  On a
    homologically trivial component, every resulting DSU component has even
    measured e-charge parity.

    Charge outcomes use ``-1`` outside the active set and binary values on the
    active set, matching the Lab 004 observation schema.
    """

    if vertex_count <= 0:
        raise ValueError("vertex_count must be positive")
    active = tuple(int(vertex) for vertex in active_vertices)
    if len(active) != len(set(active)):
        raise ValueError("active_vertices must be unique")
    if any(vertex < 0 or vertex >= vertex_count for vertex in active):
        raise ValueError("active vertex is out of range")
    active_set = set(active)

    charge = np.asarray(charge_outcomes, dtype=np.int64)
    if charge.shape != (vertex_count,):
        raise ValueError("charge_outcomes must have one value per vertex")
    if any(charge[vertex] not in (0, 1) for vertex in active):
        raise ValueError("active charge outcomes must be binary")
    inactive = np.ones(vertex_count, dtype=bool)
    inactive[list(active)] = False
    if np.any(charge[inactive] != -1):
        raise ValueError("inactive charge outcomes must be -1")

    dsu = _DisjointSet(active)
    for left, right in entanglement_pairs:
        left = int(left)
        right = int(right)
        if left not in active_set or right not in active_set:
            raise ValueError("entanglement-pair endpoints must be active")
        dsu.union(left, right)

    grouped: dict[int, list[int]] = {}
    for vertex in active:
        grouped.setdefault(dsu.find(vertex), []).append(vertex)
    components = tuple(
        sorted(tuple(sorted(vertices)) for vertices in grouped.values())
    )
    parities = tuple(
        int(np.sum(charge[list(component)], dtype=np.int64) % 2)
        for component in components
    )
    return PostFluxConstraintAnalysis(
        components=components,
        charge_parities=parities,
        allowed=all(parity == 0 for parity in parities),
    )


def evaluate_eq_a13_three_star_fixture(
    star_1_charge: int,
    star_3_charge: int,
) -> PostFluxConstraintAnalysis:
    """Evaluate the exact three-star stabilizer fixture in Eqs. A13-A14.

    After the physical and corrective red-X strings remove both fluxes, the
    source derives a product stabilizer on same-colour stars 1 and 3.  Their
    second-round charge outcomes must therefore be equal, equivalently even
    in parity.  Star 2 is the opposite colour and belongs to its own colour
    analysis, so it is not inserted into this fixture's active set.
    """

    charge = np.full(3, -1, dtype=np.int64)
    charge[0] = int(star_1_charge)
    charge[2] = int(star_3_charge)
    return accumulate_postflux_constraints(
        vertex_count=3,
        active_vertices=(0, 2),
        entanglement_pairs=((0, 2),),
        charge_outcomes=charge,
    )
