from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pymatching

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_charge_multigraph import (  # noqa: E402
    build_branch_charge_lattice,
    branch_chain_sector,
    build_expanded_branch_matching,
    decode_expanded_branch_syndrome,
    build_charge_branch_catalog,
    infer_branch_postflux_relations,
    validate_endpoint_projection,
)
from d4_charge import charge_chain_boundary, charge_check_matrix, classify_closed_charge_chain  # noqa: E402
from d4_honeycomb import BLUE, GREEN, periodic_honeycomb  # noqa: E402


def test_primitive_catalog_retains_both_physical_branches() -> None:
    lattice = periodic_honeycomb(2)
    for color in (BLUE, GREEN):
        branches = build_charge_branch_catalog(lattice, color)
        assert len(branches) == 12
        assert [branch.branch_id for branch in branches] == list(range(12))
        multiplicities = Counter(branch.endpoints for branch in branches)
        assert len(multiplicities) == 6
        assert set(multiplicities.values()) == {2}
        for endpoints in multiplicities:
            parallel = [branch for branch in branches if branch.endpoints == endpoints]
            assert len({branch.opposite_center for branch in parallel}) == 2
            assert len({branch.displacement for branch in parallel}) == 2


def test_simple_two_step_union_has_unique_branch_and_exact_projection() -> None:
    lattice = periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    correction = np.zeros_like(physical)
    physical[[0, 1]] = 1
    enriched = infer_branch_postflux_relations(lattice, physical, correction)
    assert len(enriched.relations) == 1
    relation = enriched.relations[0]
    assert relation.honeycomb_edges == (0, 1)
    agrees, endpoint = validate_endpoint_projection(
        lattice, physical, correction, enriched
    )
    assert agrees
    assert enriched.entanglement_pairs == endpoint.entanglement_pairs


def test_empty_union_has_no_branch_relations() -> None:
    lattice = periodic_honeycomb(2)
    empty = np.zeros(lattice.edge_count, dtype=np.uint8)
    enriched = infer_branch_postflux_relations(lattice, empty, empty)
    assert enriched.active_vertices == ()
    assert enriched.relations == ()
    agrees, _ = validate_endpoint_projection(lattice, empty, empty, enriched)
    assert agrees


def test_parallel_branch_pair_closes_and_winds() -> None:
    lattice = periodic_honeycomb(2)
    for color in (BLUE, GREEN):
        charge_lattice = build_branch_charge_lattice(lattice, color)
        branches = build_charge_branch_catalog(lattice, color)
        endpoints = branches[0].endpoints
        parallel = [branch for branch in branches if branch.endpoints == endpoints]
        chain = np.zeros(charge_lattice.edge_count, dtype=np.uint8)
        chain[[branch.branch_id for branch in parallel]] = 1
        assert not np.any(charge_chain_boundary(charge_lattice, chain))
        analysis = classify_closed_charge_chain(charge_lattice, chain)
        assert analysis.logical_error
        assert branch_chain_sector(lattice, color, chain) != (0, 0)


def test_pymatching_check_matrix_collapses_parallel_branch_identities() -> None:
    lattice = periodic_honeycomb(2)
    charge_lattice = build_branch_charge_lattice(lattice, BLUE)
    matching = pymatching.Matching.from_check_matrix(
        charge_check_matrix(charge_lattice),
        weights=np.ones(charge_lattice.edge_count),
    )
    assert charge_lattice.edge_count == 12
    assert matching.num_edges == 6
    assert all(len(attributes["fault_ids"]) == 1 for _, _, attributes in matching.edges())


def test_private_auxiliary_matching_retains_and_selects_each_branch() -> None:
    honeycomb = periodic_honeycomb(2)
    lattice = build_branch_charge_lattice(honeycomb, BLUE)
    branches = build_charge_branch_catalog(honeycomb, BLUE)
    for target in (0, 1):
        weights = np.full(lattice.edge_count, 16.0)
        weights[target] = 0.125
        matching = build_expanded_branch_matching(honeycomb, BLUE, weights)
        assert matching.num_nodes == 16
        assert matching.num_edges == 24
        assert matching.num_fault_ids == 12
        syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
        for endpoint in branches[target].endpoints:
            syndrome[lattice.local_vertex(endpoint)] ^= 1
        correction, objective = decode_expanded_branch_syndrome(
            honeycomb, BLUE, syndrome, weights
        )
        assert correction[target] == 1
        assert np.count_nonzero(correction) == 1
        assert abs(objective - 0.125) < 1e-6
