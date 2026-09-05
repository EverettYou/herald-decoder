from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_postflux import (  # noqa: E402
    POSTFLUX_LOCAL_RULES,
    LocalArm,
    accumulate_postflux_constraints,
    apply_periodic_postflux_local_rule,
    collect_periodic_postflux_relations,
    evaluate_eq_a13_three_star_fixture,
    infer_periodic_postflux_relations,
    local_entanglement_pairs,
    lookup_postflux_local_rule,
    periodic_local_neighborhood,
    reflect_arm_mask,
    rotate_arm_mask,
)
from d4_matching import published_herald_weights, syndrome_only_weights  # noqa: E402
from d4_recovery import decode_and_score_flux_recovery  # noqa: E402
from d4_sampler import observation_from_error_edges  # noqa: E402


def test_eq_a13_fixture_allows_exactly_equal_star_outcomes() -> None:
    allowed = []
    for star_1 in (0, 1):
        for star_3 in (0, 1):
            result = evaluate_eq_a13_three_star_fixture(star_1, star_3)
            allowed.append((star_1, star_3, result.allowed))
            assert result.components == ((0, 2),)
            assert result.charge_parities == ((star_1 + star_3) % 2,)
    assert allowed == [
        (0, 0, True),
        (0, 1, False),
        (1, 0, False),
        (1, 1, True),
    ]


def test_dsu_accumulates_transitive_local_relations() -> None:
    charge = np.array([1, 1, 0, 0, -1], dtype=np.int64)
    result = accumulate_postflux_constraints(
        5,
        (0, 1, 2, 3),
        ((0, 1), (2, 3), (1, 2)),
        charge,
    )
    assert result.components == ((0, 1, 2, 3),)
    assert result.charge_parities == (0,)
    assert result.allowed


def test_disconnected_components_receive_independent_even_constraints() -> None:
    charge = np.array([1, 1, 1, 0], dtype=np.int64)
    result = accumulate_postflux_constraints(
        4,
        (0, 1, 2, 3),
        ((0, 1), (2, 3)),
        charge,
    )
    assert result.components == ((0, 1), (2, 3))
    assert result.charge_parities == (0, 1)
    assert not result.allowed


def test_postflux_accumulator_fails_closed_on_schema_mismatch() -> None:
    with np.testing.assert_raises_regex(ValueError, "inactive"):
        accumulate_postflux_constraints(
            3,
            (0, 2),
            ((0, 2),),
            np.array([0, 0, 0], dtype=np.int64),
        )
    with np.testing.assert_raises_regex(ValueError, "must be active"):
        accumulate_postflux_constraints(
            3,
            (0, 2),
            ((0, 1),),
            np.array([0, -1, 0], dtype=np.int64),
        )


def test_all_seven_printed_local_rules_are_transcribed_exactly() -> None:
    assert [rule.row for rule in POSTFLUX_LOCAL_RULES] == list(range(1, 8))
    assert [rule.measured_after_error for rule in POSTFLUX_LOCAL_RULES] == [
        False,
        False,
        False,
        True,
        True,
        True,
        False,
    ]
    for rule in POSTFLUX_LOCAL_RULES:
        row, arms = lookup_postflux_local_rule(
            rule.physical_mask,
            rule.correction_mask,
            rule.measured_after_error,
        )
        assert row == rule.row
        assert arms == rule.entangled_arms
    assert POSTFLUX_LOCAL_RULES[5].entangled_arms == (
        LocalArm.TOP,
        LocalArm.BOTTOM_LEFT,
        LocalArm.BOTTOM_RIGHT,
    )
    assert all(
        len(rule.entangled_arms) == 2
        for rule in POSTFLUX_LOCAL_RULES
        if rule.row != 6
    )


def test_local_rule_matrix_covers_all_21_canonical_rotations() -> None:
    seen: set[tuple[int, int, bool]] = set()
    for rule in POSTFLUX_LOCAL_RULES:
        for rotation in range(3):
            key = (
                rotate_arm_mask(rule.physical_mask, rotation),
                rotate_arm_mask(rule.correction_mask, rotation),
                rule.measured_after_error,
            )
            assert key not in seen
            seen.add(key)
            row, _ = lookup_postflux_local_rule(*key)
            assert row == rule.row
    assert len(seen) == 21


def test_local_rules_emit_pair_or_three_way_dsu_relations() -> None:
    neighbors = (10, 11, 12)
    for rule in POSTFLUX_LOCAL_RULES:
        pairs = local_entanglement_pairs(
            neighbors,
            rule.physical_mask,
            rule.correction_mask,
            rule.measured_after_error,
        )
        assert len(pairs) == (2 if rule.row == 6 else 1)
        touched = set(sum((list(pair) for pair in pairs), []))
        assert len(touched) == (3 if rule.row == 6 else 2)


def test_unlisted_local_configuration_fails_closed() -> None:
    with np.testing.assert_raises_regex(ValueError, "not one unique"):
        lookup_postflux_local_rule(0, 0, False)
    with np.testing.assert_raises_regex(ValueError, "not one unique"):
        lookup_postflux_local_rule(
            0,
            1 << int(LocalArm.TOP),
            False,
        )


def test_reflected_diagram_masks_do_not_define_a_unique_completion() -> None:
    row3 = POSTFLUX_LOCAL_RULES[2]
    _, reflected_mask_match = lookup_postflux_local_rule(
        reflect_arm_mask(row3.physical_mask),
        reflect_arm_mask(row3.correction_mask),
        row3.measured_after_error,
    )
    geometrically_reflected_output = tuple(
        LocalArm.BOTTOM_RIGHT
        if arm == LocalArm.BOTTOM_LEFT
        else LocalArm.BOTTOM_LEFT
        if arm == LocalArm.BOTTOM_RIGHT
        else LocalArm.TOP
        for arm in row3.entangled_arms
    )
    assert reflected_mask_match != geometrically_reflected_output


def _selection_from_mask(
    edge_count: int,
    edge_indices: tuple[int, int, int],
    mask: int,
) -> np.ndarray:
    selected = np.zeros(edge_count, dtype=bool)
    for arm, edge in enumerate(edge_indices):
        selected[edge] = bool(mask & (1 << arm))
    return selected


def test_periodic_geometry_orders_both_colours_without_reflection() -> None:
    lattice = paper_periodic_honeycomb(3)
    x, y = 2, -1
    blue = lattice.vertex_id(x, y, BLUE)
    green = lattice.vertex_id(x, y, GREEN)
    blue_neighbors, blue_edges = periodic_local_neighborhood(lattice, blue)
    green_neighbors, green_edges = periodic_local_neighborhood(lattice, green)
    assert blue_neighbors == (
        lattice.vertex_id(x, y, GREEN),
        lattice.vertex_id(x - 1, y, GREEN),
        lattice.vertex_id(x, y - 1, GREEN),
    )
    assert green_neighbors == (
        lattice.vertex_id(x, y, BLUE),
        lattice.vertex_id(x, y + 1, BLUE),
        lattice.vertex_id(x + 1, y, BLUE),
    )
    assert set(blue_edges) == set(
        np.flatnonzero(np.any(lattice.edge_vertices == blue, axis=1))
    )
    assert set(green_edges) == set(
        np.flatnonzero(np.any(lattice.edge_vertices == green, axis=1))
    )


def test_periodic_geometry_covers_every_source_supercell_neighborhood() -> None:
    lattice = paper_periodic_honeycomb(2)
    for center in range(lattice.vertex_count):
        neighbors, edges = periodic_local_neighborhood(lattice, center)
        assert len(set(neighbors)) == len(set(edges)) == 3
        assert all(
            int(lattice.vertex_colors[neighbor])
            != int(lattice.vertex_colors[center])
            for neighbor in neighbors
        )
        assert set(edges) == set(
            np.flatnonzero(np.any(lattice.edge_vertices == center, axis=1))
        )


def test_periodic_adapter_covers_all_source_rotations_for_both_colours() -> None:
    lattice = paper_periodic_honeycomb(2)
    centers = (
        lattice.vertex_id(0, 0, BLUE),
        lattice.vertex_id(-1, 3, GREEN),
    )
    for center in centers:
        neighbors, edge_indices = periodic_local_neighborhood(lattice, center)
        for rule in POSTFLUX_LOCAL_RULES:
            for rotation in range(3):
                canonical_physical = rotate_arm_mask(
                    rule.physical_mask, rotation
                )
                canonical_correction = rotate_arm_mask(
                    rule.correction_mask, rotation
                )
                reflected = int(lattice.vertex_colors[center]) == GREEN
                physical_mask = (
                    reflect_arm_mask(canonical_physical)
                    if reflected
                    else canonical_physical
                )
                correction_mask = (
                    reflect_arm_mask(canonical_correction)
                    if reflected
                    else canonical_correction
                )
                application = apply_periodic_postflux_local_rule(
                    lattice,
                    center,
                    _selection_from_mask(
                        lattice.edge_count, edge_indices, physical_mask
                    ),
                    _selection_from_mask(
                        lattice.edge_count, edge_indices, correction_mask
                    ),
                    rule.measured_after_error,
                )
                assert application.row == rule.row
                assert application.neighbor_vertices == neighbors
                assert application.edge_indices == edge_indices
                assert application.physical_mask == physical_mask
                assert application.correction_mask == correction_mask
                expected_arms = lookup_postflux_local_rule(
                    canonical_physical,
                    canonical_correction,
                    rule.measured_after_error,
                )[1]
                if reflected:
                    expected_arms = tuple(
                        LocalArm.BOTTOM_RIGHT
                        if arm == LocalArm.BOTTOM_LEFT
                        else LocalArm.BOTTOM_LEFT
                        if arm == LocalArm.BOTTOM_RIGHT
                        else LocalArm.TOP
                        for arm in expected_arms
                    )
                anchor = neighbors[int(expected_arms[0])]
                assert application.entanglement_pairs == tuple(
                    (anchor, neighbors[int(arm)]) for arm in expected_arms[1:]
                )


def test_periodic_adapter_drives_bounded_dsu_fixture() -> None:
    lattice = paper_periodic_honeycomb(2)
    center = lattice.vertex_id(0, 0, BLUE)
    neighbors, edge_indices = periodic_local_neighborhood(lattice, center)
    rule = POSTFLUX_LOCAL_RULES[5]
    application = apply_periodic_postflux_local_rule(
        lattice,
        center,
        _selection_from_mask(lattice.edge_count, edge_indices, rule.physical_mask),
        _selection_from_mask(
            lattice.edge_count, edge_indices, rule.correction_mask
        ),
        rule.measured_after_error,
    )
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[list(neighbors)] = (1, 0, 1)
    result = accumulate_postflux_constraints(
        lattice.vertex_count,
        neighbors,
        application.entanglement_pairs,
        charge,
    )
    assert application.row == 6
    assert result.components == (tuple(sorted(neighbors)),)
    assert result.charge_parities == (0,)
    assert result.allowed


def test_periodic_adapter_accumulates_overlapping_local_centers() -> None:
    lattice = paper_periodic_honeycomb(3)
    centers = (
        lattice.vertex_id(0, 0, BLUE),
        lattice.vertex_id(1, 0, BLUE),
    )
    physical = np.zeros(lattice.edge_count, dtype=bool)
    correction = np.zeros(lattice.edge_count, dtype=bool)
    _, first_edges = periodic_local_neighborhood(lattice, centers[0])
    _, second_edges = periodic_local_neighborhood(lattice, centers[1])
    first_mask = POSTFLUX_LOCAL_RULES[0].correction_mask
    second_mask = rotate_arm_mask(first_mask, 1)
    correction |= _selection_from_mask(
        lattice.edge_count, first_edges, first_mask
    )
    correction |= _selection_from_mask(
        lattice.edge_count, second_edges, second_mask
    )
    relations = collect_periodic_postflux_relations(
        lattice,
        centers,
        physical,
        correction,
        (False, False),
    )
    shared = lattice.vertex_id(0, 0, GREEN)
    assert len(relations.applications) == 2
    assert shared in relations.active_vertices
    assert len(relations.active_vertices) == 3
    assert len(relations.entanglement_pairs) == 2
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[list(relations.active_vertices)] = (1, 0, 1)
    result = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        charge,
    )
    assert result.components == (relations.active_vertices,)
    assert result.allowed


def test_periodic_adapter_fails_closed_on_edge_schema_or_unlisted_row() -> None:
    lattice = paper_periodic_honeycomb(2)
    center = lattice.vertex_id(0, 0, BLUE)
    empty = np.zeros(lattice.edge_count, dtype=bool)
    with np.testing.assert_raises_regex(ValueError, "one value per lattice edge"):
        apply_periodic_postflux_local_rule(
            lattice, center, empty[:-1], empty, False
        )
    with np.testing.assert_raises_regex(ValueError, "not one unique"):
        apply_periodic_postflux_local_rule(lattice, center, empty, empty, False)


def _union_colour_components(lattice, physical, correction):
    adjacency = [set() for _ in range(lattice.vertex_count)]
    for edge in np.flatnonzero(np.asarray(physical) | np.asarray(correction)):
        left, right = (int(value) for value in lattice.edge_vertices[edge])
        adjacency[left].add(right)
        adjacency[right].add(left)
    unseen = {vertex for vertex, neighbors in enumerate(adjacency) if neighbors}
    expected = []
    while unseen:
        stack = [min(unseen)]
        component = set()
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            unseen.discard(vertex)
            stack.extend(adjacency[vertex])
        for color in (BLUE, GREEN):
            projected = tuple(
                sorted(
                    vertex
                    for vertex in component
                    if int(lattice.vertex_colors[vertex]) == color
                )
            )
            if projected:
                expected.append(projected)
    return tuple(sorted(expected))


def test_production_union_builder_preserves_singleton_colour_components() -> None:
    lattice = paper_periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=bool)
    physical[0] = True
    relations = infer_periodic_postflux_relations(
        lattice, physical, physical.copy()
    )
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[list(relations.active_vertices)] = 0
    constraints = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        charge,
    )
    assert constraints.components == _union_colour_components(
        lattice, physical, physical
    )
    assert len(constraints.components) == 2
    assert relations.entanglement_pairs == ()
    assert constraints.allowed


def test_production_union_builder_gives_one_parity_component_per_colour() -> None:
    lattice = paper_periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=bool)
    correction = np.zeros(lattice.edge_count, dtype=bool)
    center = lattice.vertex_id(0, 0, BLUE)
    _, edges = periodic_local_neighborhood(lattice, center)
    physical[list(edges[:2])] = True
    correction[list(edges[1:])] = True
    relations = infer_periodic_postflux_relations(
        lattice, physical, correction
    )
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[list(relations.active_vertices)] = 0
    constraints = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        charge,
    )
    assert constraints.components == _union_colour_components(
        lattice, physical, correction
    )
    assert constraints.allowed


def test_production_union_builder_covers_bounded_actual_mwpm_outputs() -> None:
    lattice = paper_periodic_honeycomb(2)
    completed = {"syndrome_only": 0, "heralded": 0}
    for seed in range(32):
        physical = np.random.default_rng(seed).random(lattice.edge_count) < 0.1
        observation = observation_from_error_edges(
            lattice, physical, seed=10_000 + seed
        )
        if observation.status != "sampled":
            continue
        charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
        modes = {
            "syndrome_only": syndrome_only_weights(lattice),
            "heralded": published_herald_weights(lattice, charge),
        }
        for mode, weights in modes.items():
            recovery = decode_and_score_flux_recovery(
                lattice, physical, weights
            )
            if recovery.logical_error:
                continue
            relations = infer_periodic_postflux_relations(
                lattice, physical, recovery.correction
            )
            post_charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
            post_charge[list(relations.active_vertices)] = 0
            constraints = accumulate_postflux_constraints(
                lattice.vertex_count,
                relations.active_vertices,
                relations.entanglement_pairs,
                post_charge,
            )
            assert constraints.components == _union_colour_components(
                lattice, physical, recovery.correction
            )
            assert constraints.allowed
            completed[mode] += 1
    assert completed["syndrome_only"] > 0
    assert completed["heralded"] > 0
