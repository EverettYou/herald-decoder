from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import paper_periodic_honeycomb, periodic_honeycomb  # noqa: E402
from d4_matching import (  # noqa: E402
    d4_check_matrix,
    decode_flux_syndrome,
    published_herald_weights,
    syndrome_only_weights,
)


def _enumerated_edge_subsets(edge_count: int) -> np.ndarray:
    masks = np.arange(1 << edge_count, dtype=np.uint64)[:, None]
    shifts = np.arange(edge_count, dtype=np.uint64)[None, :]
    return ((masks >> shifts) & 1).astype(np.uint8)


def _all_even_syndromes(vertex_count: int) -> list[np.ndarray]:
    syndromes = []
    for mask in range(1 << (vertex_count - 1)):
        bits = [(mask >> index) & 1 for index in range(vertex_count - 1)]
        bits.append(sum(bits) % 2)
        syndromes.append(np.asarray(bits, dtype=np.uint8))
    return syndromes


def test_periodic_matching_graph_is_exact_incidence_matrix() -> None:
    lattice = periodic_honeycomb(3)
    check = d4_check_matrix(lattice)
    assert check.shape == (lattice.vertex_count, lattice.edge_count)
    assert np.all(np.sum(check, axis=0) == 2)
    assert np.all(np.sum(check, axis=1) == 3)
    for edge, vertices in enumerate(lattice.edge_vertices):
        assert tuple(np.flatnonzero(check[:, edge])) == tuple(sorted(vertices))


def test_published_weights_count_zero_one_or_two_adjacent_charges() -> None:
    lattice = periodic_honeycomb(2)
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    left, right = (int(value) for value in lattice.edge_vertices[0])
    charge[left] = 1
    one_charge = published_herald_weights(lattice, charge)
    forcing_scale = 3 * lattice.edge_count
    assert forcing_scale == 36
    assert one_charge[0] == 1 - forcing_scale
    assert set(one_charge) == {1.0, -35.0}

    charge[right] = 1
    two_charges = published_herald_weights(lattice, charge)
    assert two_charges[0] == 1 - 2 * forcing_scale
    assert set(two_charges) == {1.0, -35.0, -71.0}
    assert np.all(syndrome_only_weights(lattice) == 1.0)


def test_paper_supercell_recovers_published_forcing_scale() -> None:
    lattice = paper_periodic_honeycomb(2)
    assert lattice.edge_count == 36
    forcing_scale = 3 * lattice.edge_count
    assert forcing_scale == 27 * lattice.size * lattice.size == 108
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[int(lattice.edge_vertices[0, 0])] = 1
    weights = published_herald_weights(lattice, charge)
    assert weights[0] == 1 - forcing_scale


def test_pymatching_negative_weights_equal_global_binary_minimum() -> None:
    lattice = periodic_honeycomb(2)
    check = d4_check_matrix(lattice)
    candidates = _enumerated_edge_subsets(lattice.edge_count)
    candidate_syndromes = (candidates @ check.T) % 2

    charge_cases = []
    empty = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge_cases.append(empty)
    one = empty.copy()
    one[int(lattice.edge_vertices[0, 0])] = 1
    charge_cases.append(one)
    two = one.copy()
    two[int(lattice.edge_vertices[0, 1])] = 1
    charge_cases.append(two)

    for charge in charge_cases:
        weights = published_herald_weights(lattice, charge)
        candidate_weights = candidates @ weights
        for syndrome in _all_even_syndromes(lattice.vertex_count):
            compatible = np.all(candidate_syndromes == syndrome, axis=1)
            exact_minimum = float(np.min(candidate_weights[compatible]))
            result = decode_flux_syndrome(lattice, syndrome, weights)
            assert np.isclose(result.objective_weight, exact_minimum)
            assert np.isclose(result.correction @ weights, exact_minimum)


def test_negative_closed_cycle_is_included_for_zero_syndrome() -> None:
    lattice = periodic_honeycomb(2)
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[int(lattice.edge_vertices[0, 0])] = 1
    weights = published_herald_weights(lattice, charge)
    result = decode_flux_syndrome(
        lattice,
        np.zeros(lattice.vertex_count, dtype=np.uint8),
        weights,
    )
    assert np.any(result.correction)
    assert result.objective_weight < 0


def test_unit_weight_ties_are_deterministic_across_rebuilds() -> None:
    lattice = periodic_honeycomb(2)
    weights = syndrome_only_weights(lattice)
    for syndrome in _all_even_syndromes(lattice.vertex_count):
        corrections = [
            decode_flux_syndrome(lattice, syndrome, weights).correction
            for _ in range(4)
        ]
        assert all(np.array_equal(corrections[0], other) for other in corrections[1:])


def test_matching_inputs_fail_closed() -> None:
    lattice = periodic_honeycomb(2)
    charge = np.zeros(lattice.vertex_count, dtype=np.int64)
    charge[0] = 2
    with np.testing.assert_raises_regex(ValueError, "charge outcomes"):
        published_herald_weights(lattice, charge)
    odd = np.zeros(lattice.vertex_count, dtype=np.uint8)
    odd[0] = 1
    with np.testing.assert_raises_regex(ValueError, "even parity"):
        decode_flux_syndrome(lattice, odd, syndrome_only_weights(lattice))
