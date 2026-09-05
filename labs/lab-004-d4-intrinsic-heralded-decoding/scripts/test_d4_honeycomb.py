from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import (  # noqa: E402
    BLUE,
    GREEN,
    HORIZONTAL,
    VERTICAL,
    LogicalSectorPolicy,
    LogicalZSectorDescriptor,
    WindingParityRule,
    all_plus_logical_z_policy,
    generate_loop_constraints,
    paper_periodic_honeycomb,
    periodic_honeycomb,
)
from d4_observation import evaluate_observation  # noqa: E402


def _edge_mask_for_cycle(lattice, vertices: list[int]) -> np.ndarray:
    selected = np.zeros(lattice.edge_count, dtype=bool)
    for left, right in zip(vertices, vertices[1:] + vertices[:1]):
        selected[lattice.edge_between(left, right)] = True
    return selected


def _local_hexagon(lattice) -> tuple[np.ndarray, list[int]]:
    vertices = [
        lattice.vertex_id(0, 0, BLUE),
        lattice.vertex_id(0, 0, GREEN),
        lattice.vertex_id(1, 0, BLUE),
        lattice.vertex_id(1, -1, GREEN),
        lattice.vertex_id(1, -1, BLUE),
        lattice.vertex_id(0, -1, GREEN),
    ]
    return _edge_mask_for_cycle(lattice, vertices), vertices


def test_periodic_honeycomb_counts_and_degree() -> None:
    for size in (2, 3, 4):
        lattice = periodic_honeycomb(size)
        assert lattice.vertex_count == 2 * size * size
        assert lattice.edge_count == 3 * size * size
        degrees = np.bincount(
            lattice.edge_vertices.ravel(), minlength=lattice.vertex_count
        )
        assert np.all(degrees == 3)
        assert len({tuple(sorted(map(int, edge))) for edge in lattice.edge_vertices}) == (
            lattice.edge_count
        )


def test_paper_periodic_honeycomb_source_counts_and_degree() -> None:
    for size in (2, 3):
        lattice = paper_periodic_honeycomb(size)
        assert lattice.cell_count == 3 * size * size
        assert lattice.vertex_count == 6 * size * size
        assert lattice.edge_count == 9 * size * size
        assert round(np.linalg.det(lattice.period_matrix)) == 3 * size * size
        degrees = np.bincount(
            lattice.edge_vertices.ravel(), minlength=lattice.vertex_count
        )
        assert np.all(degrees == 3)


def test_paper_vertex_ids_are_periodic_under_both_source_periods() -> None:
    lattice = paper_periodic_honeycomb(3)
    first_period = lattice.period_matrix[:, 0]
    second_period = lattice.period_matrix[:, 1]
    for x, y in ((0, 0), (1, -2), (5, 4), (-3, 7)):
        for color in (BLUE, GREEN):
            reference = lattice.vertex_id(x, y, color)
            assert reference == lattice.vertex_id(
                x + int(first_period[0]), y + int(first_period[1]), color
            )
            assert reference == lattice.vertex_id(
                x + int(second_period[0]), y + int(second_period[1]), color
            )


def test_paper_supercell_vertex_map_is_complete_and_unique() -> None:
    lattice = paper_periodic_honeycomb(2)
    seen = {
        lattice.vertex_id(x, y, color)
        for x in range(-4, 5)
        for y in range(-4, 5)
        for color in (BLUE, GREEN)
    }
    assert seen == set(range(lattice.vertex_count))


def test_paper_supercell_lift_detects_two_independent_torus_directions() -> None:
    lattice = paper_periodic_honeycomb(2)
    analysis = generate_loop_constraints(
        lattice, np.ones(lattice.edge_count, dtype=bool)
    )
    assert len(analysis.components) == 1
    windings = np.asarray(analysis.components[0].winding_vectors, dtype=np.int64)
    assert np.linalg.matrix_rank(windings) == 2


def test_local_hexagon_gets_one_even_constraint_per_colour() -> None:
    lattice = periodic_honeycomb(3)
    selected, vertices = _local_hexagon(lattice)
    analysis = generate_loop_constraints(lattice, selected)
    assert len(analysis.components) == 1
    component = analysis.components[0]
    assert component.nonbranching_closed
    assert component.homologically_trivial
    assert component.vertices == tuple(sorted(vertices))
    assert len(analysis.constraints) == 2
    assert {constraint.label.rsplit("-", 1)[-1] for constraint in analysis.constraints} == {
        "blue",
        "green",
    }
    assert all(len(constraint.vertices) == 3 for constraint in analysis.constraints)


def test_winding_loop_is_detected_and_not_given_even_constraints() -> None:
    size = 3
    lattice = periodic_honeycomb(size)
    selected = np.zeros(lattice.edge_count, dtype=bool)
    for y in range(size):
        pairs = (
            (lattice.vertex_id(0, y, BLUE), lattice.vertex_id(0, y, GREEN)),
            (lattice.vertex_id(0, y, BLUE), lattice.vertex_id(0, y - 1, GREEN)),
        )
        for left, right in pairs:
            selected[lattice.edge_between(left, right)] = True
    analysis = generate_loop_constraints(lattice, selected)
    assert len(analysis.components) == 1
    component = analysis.components[0]
    assert component.nonbranching_closed
    assert not component.homologically_trivial
    assert any(winding[1] != 0 for winding in component.winding_vectors)
    assert analysis.constraints == ()


def test_horizontal_winding_loop_uses_its_own_sector_rules() -> None:
    size = 3
    lattice = periodic_honeycomb(size)
    selected = np.zeros(lattice.edge_count, dtype=bool)
    for x in range(size):
        pairs = (
            (lattice.vertex_id(x, 0, BLUE), lattice.vertex_id(x, 0, GREEN)),
            (lattice.vertex_id(x, 0, BLUE), lattice.vertex_id(x - 1, 0, GREEN)),
        )
        for left, right in pairs:
            selected[lattice.edge_between(left, right)] = True
    policy = LogicalSectorPolicy(
        "horizontal-odd-blue",
        (
            WindingParityRule((2, 0), BLUE, 1),
            WindingParityRule((1, 0), GREEN, 0),
        ),
    )
    analysis = generate_loop_constraints(lattice, selected, policy)
    assert len(analysis.components) == 1
    assert analysis.components[0].winding_vectors
    assert [constraint.required_parity for constraint in analysis.constraints] == [
        1,
        0,
    ]


def test_logical_z_eigenvalues_map_to_source_parity_semantics() -> None:
    minus_z_policy = LogicalZSectorDescriptor(
        label="appendix-a-horizontal-blue-minus-z",
        blue_horizontal=-1,
        green_horizontal=1,
        blue_vertical=1,
        green_vertical=1,
    ).to_policy()
    assert minus_z_policy.required_parity(HORIZONTAL, BLUE) == 1
    assert minus_z_policy.required_parity(HORIZONTAL, GREEN) == 0

    # A vertical blue logical-X eigenstate has no definite horizontal blue-Z
    # eigenvalue in the source example, hence no horizontal blue constraint.
    x_policy = LogicalZSectorDescriptor(
        label="appendix-a-vertical-blue-x",
        blue_horizontal=None,
        green_horizontal=None,
        blue_vertical=None,
        green_vertical=None,
    ).to_policy()
    assert x_policy.required_parity(HORIZONTAL, BLUE) is None


def test_iqbal_all_logical_z_plus_candidate_is_even_in_both_directions() -> None:
    policy = all_plus_logical_z_policy()
    assert policy.label == "iqbal-all-logical-z-plus"
    for direction in (HORIZONTAL, VERTICAL):
        for color in (BLUE, GREEN):
            assert policy.required_parity(direction, color) == 0


def test_logical_z_descriptor_rejects_non_eigenvalues() -> None:
    with np.testing.assert_raises_regex(ValueError, "eigenvalues"):
        LogicalZSectorDescriptor("invalid", 0, 1, 1, 1)


def test_branched_component_has_no_loop_constraint() -> None:
    lattice = periodic_honeycomb(3)
    blue = lattice.vertex_id(0, 0, BLUE)
    selected = np.zeros(lattice.edge_count, dtype=bool)
    selected[np.flatnonzero(np.any(lattice.edge_vertices == blue, axis=1))] = True
    analysis = generate_loop_constraints(lattice, selected)
    assert len(analysis.components) == 1
    assert not analysis.components[0].nonbranching_closed
    assert analysis.constraints == ()


def test_generated_hexagon_constraints_normalize_eq_a12_likelihood() -> None:
    lattice = periodic_honeycomb(3)
    selected, vertices = _local_hexagon(lattice)
    analysis = generate_loop_constraints(lattice, selected)
    flux = np.zeros(lattice.vertex_count, dtype=bool)
    total_probability = 0.0
    allowed_count = 0
    for bits in itertools.product((0, 1), repeat=len(vertices)):
        charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
        charge[vertices] = bits
        result = evaluate_observation(
            lattice.edge_vertices,
            selected,
            flux,
            charge,
            analysis.constraints,
        )
        total_probability += result.probability
        allowed_count += int(result.allowed)
    assert allowed_count == 16
    assert total_probability == 1.0
