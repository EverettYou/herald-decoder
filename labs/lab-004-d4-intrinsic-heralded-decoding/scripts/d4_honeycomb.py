"""Periodic coloured honeycomb topology and R1 loop-constraint generator."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

import numpy as np
from numpy.typing import NDArray

from d4_observation import ParityConstraint


BLUE = 0
GREEN = 1
HORIZONTAL = (1, 0)
VERTICAL = (0, 1)


@dataclass(frozen=True)
class PeriodicHoneycomb:
    size: int
    macro_basis: NDArray[np.int64]
    residue_vectors: NDArray[np.int64]
    edge_vertices: NDArray[np.int64]
    blue_to_green_displacements: NDArray[np.int64]
    vertex_colors: NDArray[np.int8]

    @property
    def cell_count(self) -> int:
        return self.size * self.size * len(self.residue_vectors)

    @property
    def vertex_count(self) -> int:
        return 2 * self.cell_count

    @property
    def edge_count(self) -> int:
        return 3 * self.cell_count

    @property
    def period_matrix(self) -> NDArray[np.int64]:
        """Primitive-coordinate torus periods, stored as matrix columns."""

        return self.size * self.macro_basis

    def _reduce_cell(self, x: int, y: int) -> tuple[int, int, int]:
        """Reduce a primitive cell coordinate to macrocell and coset indices."""

        a, b = (int(value) for value in self.macro_basis[0])
        c, d = (int(value) for value in self.macro_basis[1])
        determinant = a * d - b * c
        if determinant <= 0:
            raise ValueError("macro basis must have positive determinant")
        for residue_index, residue in enumerate(self.residue_vectors):
            dx = x - int(residue[0])
            dy = y - int(residue[1])
            numerator_u = d * dx - b * dy
            numerator_v = -c * dx + a * dy
            if numerator_u % determinant == 0 and numerator_v % determinant == 0:
                return (
                    (numerator_u // determinant) % self.size,
                    (numerator_v // determinant) % self.size,
                    residue_index,
                )
        raise ValueError("primitive coordinate is absent from quotient cosets")

    def vertex_id(self, x: int, y: int, color: int) -> int:
        if color not in (BLUE, GREEN):
            raise ValueError("color must be BLUE or GREEN")
        macro_x, macro_y, residue = self._reduce_cell(x, y)
        cell = (
            (macro_y * self.size + macro_x) * len(self.residue_vectors) + residue
        )
        return 2 * cell + color

    def vertex_coordinate(self, vertex: int) -> tuple[int, int]:
        """Return the stored primitive-cell representative of one vertex."""

        vertex = int(vertex)
        if vertex < 0 or vertex >= self.vertex_count:
            raise ValueError("vertex is out of range")
        cell = vertex // 2
        residue_count = len(self.residue_vectors)
        residue_index = cell % residue_count
        macro_cell = cell // residue_count
        macro_x = macro_cell % self.size
        macro_y = macro_cell // self.size
        coordinate = (
            self.macro_basis
            @ np.array((macro_x, macro_y), dtype=np.int64)
            + self.residue_vectors[residue_index]
        )
        return int(coordinate[0]), int(coordinate[1])

    def edge_between(self, left: int, right: int) -> int:
        matches = np.flatnonzero(
            ((self.edge_vertices[:, 0] == left) & (self.edge_vertices[:, 1] == right))
            | ((self.edge_vertices[:, 0] == right) & (self.edge_vertices[:, 1] == left))
        )
        if len(matches) != 1:
            raise ValueError(f"expected one edge between {left} and {right}")
        return int(matches[0])


@dataclass(frozen=True)
class ErrorComponent:
    vertices: tuple[int, ...]
    edges: tuple[int, ...]
    nonbranching_closed: bool
    winding_vectors: tuple[tuple[int, int], ...]

    @property
    def homologically_trivial(self) -> bool:
        return not self.winding_vectors


@dataclass(frozen=True)
class ConstraintAnalysis:
    constraints: tuple[ParityConstraint, ...]
    components: tuple[ErrorComponent, ...]


@dataclass(frozen=True)
class WindingParityRule:
    """Charge-parity rule for one primitive winding direction and colour.

    ``required_parity=None`` means that the protected logical sector imposes
    no parity constraint on this branch.  This explicit third state matters:
    Appendix A distinguishes an unconstrained charge colour from even parity.
    """

    winding_direction: tuple[int, int]
    color: int
    required_parity: int | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "winding_direction", _primitive_winding(self.winding_direction)
        )
        if self.color not in (BLUE, GREEN):
            raise ValueError("color must be BLUE or GREEN")
        if self.required_parity not in (0, 1, None):
            raise ValueError("required_parity must be 0, 1, or None")


@dataclass(frozen=True)
class LogicalSectorPolicy:
    """Explicit winding-parity semantics for one protected logical sector.

    This is deliberately a representation, not a claim that every abstract
    policy labels a physical D4 ground state.  The source-faithful mapping from
    protected logical operators to these rules is a separate verification gate.
    """

    label: str
    rules: tuple[WindingParityRule, ...]

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("logical-sector label must be nonempty")
        keys = [(rule.winding_direction, rule.color) for rule in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("logical-sector policy contains duplicate rules")

    def required_parity(
        self, winding_direction: tuple[int, int], color: int
    ) -> int | None:
        key = (_primitive_winding(winding_direction), color)
        for rule in self.rules:
            if (rule.winding_direction, rule.color) == key:
                return rule.required_parity
        raise ValueError(
            f"logical-sector policy {self.label!r} lacks rule for {key}"
        )


@dataclass(frozen=True)
class LogicalZSectorDescriptor:
    """Logical-Z information relevant to one red-X error channel.

    The four entries are eigenvalues of the blue/green logical Z strings in
    the horizontal/vertical directions.  ``None`` means the state is not a
    definite eigenstate of that logical Z (for example, the source's vertical
    blue-X eigenstate leaves horizontal blue-Z parity unconstrained).

    Red logical-Z data are absent because red X errors create intermediate
    blue and green charges only.  This descriptor does not validate whether an
    arbitrary four-entry assignment is one of the 22 physical D4 ground
    states; it only implements the source's parity/eigenvalue correspondence.
    """

    label: str
    blue_horizontal: int | None
    green_horizontal: int | None
    blue_vertical: int | None
    green_vertical: int | None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("logical-sector label must be nonempty")
        for value in (
            self.blue_horizontal,
            self.green_horizontal,
            self.blue_vertical,
            self.green_vertical,
        ):
            if value not in (-1, 1, None):
                raise ValueError("logical-Z eigenvalues must be -1, +1, or None")

    def to_policy(self) -> LogicalSectorPolicy:
        """Map Z=+1/-1/indefinite to even/odd/unconstrained parity."""

        values = (
            (HORIZONTAL, BLUE, self.blue_horizontal),
            (HORIZONTAL, GREEN, self.green_horizontal),
            (VERTICAL, BLUE, self.blue_vertical),
            (VERTICAL, GREEN, self.green_vertical),
        )
        return LogicalSectorPolicy(
            self.label,
            tuple(
                WindingParityRule(
                    direction,
                    color,
                    None if eigenvalue is None else (1 - eigenvalue) // 2,
                )
                for direction, color, eigenvalue in values
            ),
        )


def all_plus_logical_z_policy() -> LogicalSectorPolicy:
    """Return the all-logical-Z=+1 sector prepared in Iqbal et al.

    Jing et al. do not specify this as their threshold-simulation sector.  It
    is exposed only as a source-backed candidate for a declared reproduction.
    """

    return LogicalZSectorDescriptor(
        label="iqbal-all-logical-z-plus",
        blue_horizontal=1,
        green_horizontal=1,
        blue_vertical=1,
        green_vertical=1,
    ).to_policy()


def _periodic_honeycomb_from_quotient(
    size: int,
    macro_basis: NDArray[np.int64],
    residue_vectors: NDArray[np.int64],
) -> PeriodicHoneycomb:
    """Build a honeycomb quotient from primitive-coordinate representatives."""

    if size < 2:
        raise ValueError("size must be at least 2 to avoid parallel-edge degeneracy")
    basis = np.asarray(macro_basis, dtype=np.int64)
    residues = np.asarray(residue_vectors, dtype=np.int64)
    if basis.shape != (2, 2):
        raise ValueError("macro_basis must be a 2x2 integer matrix")
    if residues.ndim != 2 or residues.shape[1] != 2 or len(residues) == 0:
        raise ValueError("residue_vectors must have shape (n, 2)")
    determinant = int(basis[0, 0] * basis[1, 1] - basis[0, 1] * basis[1, 0])
    if determinant <= 0 or determinant != len(residues):
        raise ValueError("residues must enumerate a positive-determinant quotient")

    cell_count = size * size * len(residues)
    vertex_colors = np.tile(np.array([BLUE, GREEN], dtype=np.int8), cell_count)
    edge_vertices: list[tuple[int, int]] = []
    displacements: list[tuple[int, int]] = []

    lattice_shell = PeriodicHoneycomb(
        size=size,
        macro_basis=basis,
        residue_vectors=residues,
        edge_vertices=np.empty((0, 2), dtype=np.int64),
        blue_to_green_displacements=np.empty((0, 2), dtype=np.int64),
        vertex_colors=vertex_colors,
    )

    # Each blue vertex connects to green vertices in its own cell, the cell to
    # the left, and the cell below.  The unwrapped displacement is retained so
    # a lifted graph traversal can detect torus winding.
    for macro_y in range(size):
        for macro_x in range(size):
            macro_coordinate = basis @ np.array([macro_x, macro_y], dtype=np.int64)
            for residue in residues:
                x, y = (int(value) for value in macro_coordinate + residue)
                blue = lattice_shell.vertex_id(x, y, BLUE)
                for dx, dy in ((0, 0), (-1, 0), (0, -1)):
                    green = lattice_shell.vertex_id(x + dx, y + dy, GREEN)
                    edge_vertices.append((blue, green))
                    displacements.append((dx, dy))

    return PeriodicHoneycomb(
        size=size,
        macro_basis=basis,
        residue_vectors=residues,
        edge_vertices=np.asarray(edge_vertices, dtype=np.int64),
        blue_to_green_displacements=np.asarray(displacements, dtype=np.int64),
        vertex_colors=vertex_colors,
    )


def periodic_honeycomb(size: int) -> PeriodicHoneycomb:
    """Return a primitive-cell LxL honeycomb fixture with 3L^2 edges."""

    return _periodic_honeycomb_from_quotient(
        size,
        np.eye(2, dtype=np.int64),
        np.array(((0, 0),), dtype=np.int64),
    )


def paper_periodic_honeycomb(size: int) -> PeriodicHoneycomb:
    """Return the source-normalized determinant-three periodic honeycomb.

    The conventional colour-compatible basis ``(1,1), (-1,2)`` contains
    three primitive honeycomb cells.  Repeating it ``size`` times in each
    direction therefore gives the paper normalization: ``6L^2`` affected
    blue/green vertices, ``9L^2`` red-qubit edges, and ``K=3E=27L^2``.
    The primitive constructor remains available only for tiny exhaustive
    semantic tests whose ``size`` must not be interpreted as the paper's L.
    """

    return _periodic_honeycomb_from_quotient(
        size,
        np.array(((1, -1), (1, 2)), dtype=np.int64),
        np.array(((0, 0), (1, 0), (2, 0)), dtype=np.int64),
    )


def _canonical_winding(
    vector: NDArray[np.int64], period_matrix: NDArray[np.int64]
) -> tuple[int, int]:
    a, b = (int(value) for value in period_matrix[0])
    c, d = (int(value) for value in period_matrix[1])
    determinant = a * d - b * c
    numerator = np.array(
        (d * int(vector[0]) - b * int(vector[1]),
         -c * int(vector[0]) + a * int(vector[1])),
        dtype=np.int64,
    )
    if determinant <= 0 or np.any(numerator % determinant):
        raise ValueError("lift inconsistency is not an integer torus winding")
    winding = numerator // determinant
    first_nonzero = next((int(value) for value in winding if value), 0)
    if first_nonzero < 0:
        winding = -winding
    return int(winding[0]), int(winding[1])


def _primitive_winding(vector: tuple[int, int]) -> tuple[int, int]:
    x, y = (int(value) for value in vector)
    divisor = gcd(abs(x), abs(y))
    if divisor == 0:
        raise ValueError("winding direction must be nonzero")
    x //= divisor
    y //= divisor
    if x < 0 or (x == 0 and y < 0):
        x, y = -x, -y
    return x, y


def generate_loop_constraints(
    lattice: PeriodicHoneycomb,
    error_edges: NDArray[np.generic],
    logical_sector: LogicalSectorPolicy | None = None,
) -> ConstraintAnalysis:
    """Generate colour constraints for closed nonbranching loops.

    Appendix A assigns one even-parity relation per colour to every isolated,
    nonbranching, homologically trivial error loop.  Branched or open
    components receive no loop relation here.  Nontrivial loops are identified
    but receive no constraint unless an explicit logical-sector policy is
    supplied.  A policy must cover both colours for the loop's primitive
    winding direction; a missing or ambiguous rule is rejected rather than
    guessed.
    """

    selected = np.asarray(error_edges, dtype=np.bool_)
    if selected.shape != (lattice.edge_count,):
        raise ValueError("error_edges must have one value per lattice edge")

    adjacency: list[list[int]] = [[] for _ in range(lattice.vertex_count)]
    for edge in np.flatnonzero(selected):
        left, right = lattice.edge_vertices[edge]
        adjacency[int(left)].append(int(edge))
        adjacency[int(right)].append(int(edge))

    components: list[ErrorComponent] = []
    constraints: list[ParityConstraint] = []
    unseen = {vertex for vertex, edges in enumerate(adjacency) if edges}
    component_index = 0
    while unseen:
        root = min(unseen)
        stack = [root]
        vertices: set[int] = set()
        edges: set[int] = set()
        lift: dict[int, NDArray[np.int64]] = {root: np.zeros(2, dtype=np.int64)}
        windings: set[tuple[int, int]] = set()

        while stack:
            vertex = stack.pop()
            if vertex in vertices:
                continue
            vertices.add(vertex)
            unseen.discard(vertex)
            for edge in adjacency[vertex]:
                edges.add(edge)
                blue, green = (int(value) for value in lattice.edge_vertices[edge])
                if vertex == blue:
                    neighbor = green
                    delta = lattice.blue_to_green_displacements[edge]
                else:
                    neighbor = blue
                    delta = -lattice.blue_to_green_displacements[edge]
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

        ordered_vertices = tuple(sorted(vertices))
        ordered_edges = tuple(sorted(edges))
        nonbranching_closed = all(len(adjacency[v]) == 2 for v in vertices)
        component = ErrorComponent(
            vertices=ordered_vertices,
            edges=ordered_edges,
            nonbranching_closed=nonbranching_closed,
            winding_vectors=tuple(sorted(windings)),
        )
        components.append(component)

        if component.nonbranching_closed and component.homologically_trivial:
            for color, name in ((BLUE, "blue"), (GREEN, "green")):
                color_vertices = tuple(
                    vertex
                    for vertex in component.vertices
                    if int(lattice.vertex_colors[vertex]) == color
                )
                if not color_vertices:
                    raise ValueError("closed honeycomb loop lacks one colour")
                constraints.append(
                    ParityConstraint(
                        color_vertices,
                        required_parity=0,
                        label=f"component-{component_index}-{name}",
                    )
                )
        elif component.nonbranching_closed and logical_sector is not None:
            directions = {
                _primitive_winding(winding)
                for winding in component.winding_vectors
            }
            if len(directions) != 1:
                raise ValueError(
                    "winding component has multiple independent directions; "
                    "no source-backed parity rule is implemented"
                )
            direction = next(iter(directions))
            for color, name in ((BLUE, "blue"), (GREEN, "green")):
                required_parity = logical_sector.required_parity(direction, color)
                if required_parity is None:
                    continue
                color_vertices = tuple(
                    vertex
                    for vertex in component.vertices
                    if int(lattice.vertex_colors[vertex]) == color
                )
                if not color_vertices:
                    raise ValueError("closed honeycomb loop lacks one colour")
                constraints.append(
                    ParityConstraint(
                        color_vertices,
                        required_parity=required_parity,
                        label=(
                            f"component-{component_index}-{name}-winding-"
                            f"{direction[0]}-{direction[1]}"
                        ),
                    )
                )
        component_index += 1

    return ConstraintAnalysis(tuple(constraints), tuple(components))
