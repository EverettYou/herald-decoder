from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_exact import (  # noqa: E402
    enumerate_affine_chains,
    exact_unit_t_join_minimum,
    exhaustive_chain_minimum,
)
from d4_charge import build_charge_lattice, decode_charge_syndrome  # noqa: E402
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_matching import (  # noqa: E402
    d4_check_matrix,
    decode_flux_syndrome,
    published_herald_weights,
    syndrome_only_weights,
)


def test_paper_l2_affine_space_is_complete_and_syndrome_faithful() -> None:
    lattice = paper_periodic_honeycomb(2)
    check = d4_check_matrix(lattice)
    syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
    chains = enumerate_affine_chains(check, syndrome)
    assert chains.shape == (8192, lattice.edge_count)
    assert len({bytes(chain) for chain in chains}) == len(chains)
    assert not np.any((check @ chains.T) % 2)


def test_exhaustive_oracle_matches_both_public_flux_objectives() -> None:
    lattice = paper_periodic_honeycomb(2)
    check = d4_check_matrix(lattice)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[[0, 4, 7]] = 1
    syndrome = np.asarray((check @ physical) % 2, dtype=np.uint8)
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[np.flatnonzero(syndrome)[:2]] = 1
    for weights in (
        syndrome_only_weights(lattice),
        published_herald_weights(lattice, charge),
    ):
        exact = exhaustive_chain_minimum(check, syndrome, weights)
        decoded = decode_flux_syndrome(lattice, syndrome, weights)
        assert np.isclose(decoded.objective_weight, exact.minimum_weight)
        assert any(np.array_equal(decoded.correction, row) for row in exact.minimizers)


def test_t_join_oracle_matches_full_affine_enumeration_for_every_even_syndrome() -> None:
    edges = np.asarray(
        ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)),
        dtype=np.int64,
    )
    check = np.zeros((5, len(edges)), dtype=np.uint8)
    for edge, (left, right) in enumerate(edges):
        check[left, edge] = 1
        check[right, edge] = 1
    for bits in range(1 << 5):
        syndrome = np.asarray([(bits >> vertex) & 1 for vertex in range(5)], dtype=np.uint8)
        if int(syndrome.sum()) % 2:
            continue
        exact_affine = exhaustive_chain_minimum(check, syndrome, np.ones(len(edges)))
        exact_t_join = exact_unit_t_join_minimum(5, edges, syndrome)
        assert exact_t_join.minimum_weight == exact_affine.minimum_weight
        assert {bytes(row) for row in exact_t_join.minimizers} == {
            bytes(row) for row in exact_affine.minimizers
        }


def test_t_join_oracle_matches_paper_charge_decoder_objective() -> None:
    honeycomb = paper_periodic_honeycomb(2)
    for color in (BLUE, GREEN):
        lattice = build_charge_lattice(honeycomb, color)
        for pair in ((0, 1), (0, 5), (3, 8)):
            syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
            syndrome[list(pair)] = 1
            exact = exact_unit_t_join_minimum(
                lattice.vertex_count, lattice.edge_vertices, syndrome
            )
            correction, weight = decode_charge_syndrome(lattice, syndrome)
            assert weight == exact.minimum_weight
            assert any(np.array_equal(correction, row) for row in exact.minimizers)
