from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_charge import (  # noqa: E402
    build_charge_lattice,
    charge_chain_boundary,
    charge_check_matrix,
    classify_closed_charge_chain,
    decode_public_postflux_charges,
    effective_error_from_relations,
    public_postflux_charge_record,
    recover_postflux_charges,
    score_public_postflux_charge_action,
)
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_matching import published_herald_weights, syndrome_only_weights  # noqa: E402
from d4_pipeline import sample_postflux_charge_outcomes  # noqa: E402
from d4_postflux import (  # noqa: E402
    POSTFLUX_LOCAL_RULES,
    collect_periodic_postflux_relations,
    infer_periodic_postflux_relations,
    periodic_local_neighborhood,
    reflect_arm_mask,
)
from d4_recovery import decode_and_score_flux_recovery  # noqa: E402
from d4_sampler import observation_from_error_edges  # noqa: E402


def _selection_from_mask(edge_count, edge_indices, mask):
    selected = np.zeros(edge_count, dtype=bool)
    for arm, edge in enumerate(edge_indices):
        selected[edge] = bool(mask & (1 << arm))
    return selected


def test_charge_lattices_have_source_counts_degree_and_incidence() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    for color in (BLUE, GREEN):
        lattice = build_charge_lattice(honeycomb, color)
        assert lattice.vertex_count == 3 * honeycomb.size**2
        assert lattice.edge_count == 9 * honeycomb.size**2
        assert len({tuple(edge) for edge in lattice.edge_global_vertices}) == (
            lattice.edge_count
        )
        check = charge_check_matrix(lattice)
        assert np.all(np.sum(check, axis=0) == 2)
        assert np.all(np.sum(check, axis=1) == 6)


def test_effective_error_pairs_even_charges_along_relation_forest() -> None:
    honeycomb = paper_periodic_honeycomb(3)
    center = honeycomb.vertex_id(0, 0, BLUE)
    neighbors, edges = periodic_local_neighborhood(honeycomb, center)
    row6 = POSTFLUX_LOCAL_RULES[5]
    relations = collect_periodic_postflux_relations(
        honeycomb,
        (center,),
        _selection_from_mask(honeycomb.edge_count, edges, row6.physical_mask),
        _selection_from_mask(honeycomb.edge_count, edges, row6.correction_mask),
        (True,),
    )
    charge = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    charge[list(neighbors)] = (1, 0, 1)
    lattice = build_charge_lattice(honeycomb, GREEN)
    effective = effective_error_from_relations(
        lattice, relations.entanglement_pairs, charge
    )
    boundary = charge_chain_boundary(lattice, effective)
    expected = np.zeros(lattice.vertex_count, dtype=np.uint8)
    expected[[neighbor // 2 for neighbor in neighbors]] = (1, 0, 1)
    assert np.array_equal(boundary, expected)
    assert np.sum(effective) <= len(relations.entanglement_pairs)


def test_effective_error_rejects_odd_component_parity() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    center = honeycomb.vertex_id(0, 0, BLUE)
    neighbors, edges = periodic_local_neighborhood(honeycomb, center)
    row6 = POSTFLUX_LOCAL_RULES[5]
    relations = collect_periodic_postflux_relations(
        honeycomb,
        (center,),
        _selection_from_mask(honeycomb.edge_count, edges, row6.physical_mask),
        _selection_from_mask(honeycomb.edge_count, edges, row6.correction_mask),
        (True,),
    )
    charge = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    charge[list(neighbors)] = (1, 0, 0)
    with np.testing.assert_raises_regex(ValueError, "odd measured charge parity"):
        effective_error_from_relations(
            build_charge_lattice(honeycomb, GREEN),
            relations.entanglement_pairs,
            charge,
        )


def test_charge_homology_detects_closed_winding_and_rejects_open_chain() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    lattice = build_charge_lattice(honeycomb, BLUE)
    full = np.ones(lattice.edge_count, dtype=np.uint8)
    assert not np.any(charge_chain_boundary(lattice, full))
    assert classify_closed_charge_chain(lattice, full).logical_error
    single = np.zeros(lattice.edge_count, dtype=np.uint8)
    single[0] = 1
    with np.testing.assert_raises_regex(ValueError, "must be closed"):
        classify_closed_charge_chain(lattice, single)


def test_second_stage_recovers_both_colours_end_to_end() -> None:
    honeycomb = paper_periodic_honeycomb(3)
    centers = (
        honeycomb.vertex_id(0, 0, BLUE),
        honeycomb.vertex_id(2, 2, GREEN),
    )
    physical = np.zeros(honeycomb.edge_count, dtype=bool)
    correction = np.zeros(honeycomb.edge_count, dtype=bool)
    row6 = POSTFLUX_LOCAL_RULES[5]
    neighbor_sets = []
    for center in centers:
        neighbors, edges = periodic_local_neighborhood(honeycomb, center)
        neighbor_sets.append(neighbors)
        physical_mask = row6.physical_mask
        correction_mask = row6.correction_mask
        if int(honeycomb.vertex_colors[center]) == GREEN:
            physical_mask = reflect_arm_mask(physical_mask)
            correction_mask = reflect_arm_mask(correction_mask)
        physical |= _selection_from_mask(
            honeycomb.edge_count, edges, physical_mask
        )
        correction |= _selection_from_mask(
            honeycomb.edge_count, edges, correction_mask
        )
    relations = collect_periodic_postflux_relations(
        honeycomb, centers, physical, correction, (True, True)
    )
    charge = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    for neighbors in neighbor_sets:
        charge[list(neighbors)] = (1, 0, 1)
    result = recover_postflux_charges(
        honeycomb,
        relations,
        charge,
        flux_components_homologically_trivial=True,
    )
    assert not result.logical_error
    for color_result in (result.blue, result.green):
        assert np.sum(color_result.syndrome) == 2
        assert not np.any(
            charge_chain_boundary(
                build_charge_lattice(honeycomb, color_result.color),
                color_result.residual,
            )
        )


def test_second_stage_requires_trivial_flux_union() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    empty_relations = collect_periodic_postflux_relations(
        honeycomb,
        (),
        np.zeros(honeycomb.edge_count, dtype=bool),
        np.zeros(honeycomb.edge_count, dtype=bool),
        (),
    )
    charge = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    with np.testing.assert_raises_regex(ValueError, "homologically trivial"):
        recover_postflux_charges(
            honeycomb,
            empty_relations,
            charge,
            flux_components_homologically_trivial=False,
        )


def test_second_stage_accepts_even_singleton_colour_constraints() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    physical = np.zeros(honeycomb.edge_count, dtype=bool)
    physical[0] = True
    relations = infer_periodic_postflux_relations(
        honeycomb, physical, physical.copy()
    )
    assert len(relations.active_vertices) == 2
    assert relations.entanglement_pairs == ()
    charge = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    charge[list(relations.active_vertices)] = 0
    result = recover_postflux_charges(
        honeycomb,
        relations,
        charge,
        flux_components_homologically_trivial=True,
    )
    assert not result.logical_error
    assert not np.any(result.blue.effective_error)
    assert not np.any(result.green.effective_error)


def test_public_charge_action_uses_full_binary_record_only() -> None:
    honeycomb = paper_periodic_honeycomb(3)
    physical = np.zeros(honeycomb.edge_count, dtype=bool)
    physical[0] = True
    relations = infer_periodic_postflux_relations(
        honeycomb, physical, physical.copy()
    )
    internal = np.full(honeycomb.vertex_count, -1, dtype=np.int64)
    internal[list(relations.active_vertices)] = 0
    public = public_postflux_charge_record(internal)
    assert set(public.tolist()) <= {0, 1}
    action = decode_public_postflux_charges(honeycomb, public)
    result = score_public_postflux_charge_action(
        honeycomb,
        relations,
        public,
        action,
        flux_components_homologically_trivial=True,
    )
    assert not result.logical_error


def test_private_scorer_rejects_record_bound_to_wrong_action_support() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    physical = np.zeros(honeycomb.edge_count, dtype=np.uint8)
    physical[[2, 5, 8, 12, 17, 24, 30, 34]] = 1
    first = observation_from_error_edges(honeycomb, physical, seed=103)
    first_charge = np.asarray(first.charge_outcomes, dtype=np.int64)
    o0_flux = decode_and_score_flux_recovery(
        honeycomb, physical, syndrome_only_weights(honeycomb)
    )
    o2_flux = decode_and_score_flux_recovery(
        honeycomb,
        physical,
        published_herald_weights(honeycomb, first_charge),
    )
    o0_relations = infer_periodic_postflux_relations(
        honeycomb, physical, o0_flux.correction
    )
    o2_relations = infer_periodic_postflux_relations(
        honeycomb, physical, o2_flux.correction
    )
    internal = sample_postflux_charge_outcomes(
        honeycomb.vertex_count, o0_relations, seed=12345
    )
    public = public_postflux_charge_record(internal)
    action = decode_public_postflux_charges(honeycomb, public)
    with np.testing.assert_raises_regex(ValueError, "outside private support"):
        score_public_postflux_charge_action(
            honeycomb,
            o2_relations,
            public,
            action,
            flux_components_homologically_trivial=True,
        )
