from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import BLUE, GREEN, periodic_honeycomb  # noqa: E402
from d4_matching import (  # noqa: E402
    classify_closed_chain,
    classify_physical_correction_union,
    compose_edge_chains,
    edge_chain_boundary,
    syndrome_only_weights,
)
from d4_recovery import decode_and_score_flux_recovery  # noqa: E402


def _cycle_mask(lattice, vertices: list[int]) -> np.ndarray:
    selected = np.zeros(lattice.edge_count, dtype=np.uint8)
    for left, right in zip(vertices, vertices[1:] + vertices[:1]):
        selected[lattice.edge_between(left, right)] = 1
    return selected


def _vertical_winding(lattice) -> np.ndarray:
    vertices: list[int] = []
    for y in range(lattice.size):
        vertices.extend(
            [
                lattice.vertex_id(0, y, BLUE),
                lattice.vertex_id(0, y, GREEN),
            ]
        )
    return _cycle_mask(lattice, vertices)


def _local_hexagon(lattice) -> np.ndarray:
    return _cycle_mask(
        lattice,
        [
            lattice.vertex_id(0, 0, BLUE),
            lattice.vertex_id(0, 0, GREEN),
            lattice.vertex_id(1, 0, BLUE),
            lattice.vertex_id(1, -1, GREEN),
            lattice.vertex_id(1, -1, BLUE),
            lattice.vertex_id(0, -1, GREEN),
        ],
    )


def test_pauli_composition_cancels_double_acted_edges() -> None:
    lattice = periodic_honeycomb(3)
    chain = _local_hexagon(lattice)
    assert not np.any(compose_edge_chains(lattice, chain, chain))


def test_closed_chain_classifier_separates_local_and_winding_cycles() -> None:
    lattice = periodic_honeycomb(3)
    local = classify_closed_chain(lattice, _local_hexagon(lattice))
    winding = classify_closed_chain(lattice, _vertical_winding(lattice))
    assert all(component.homologically_trivial for component in local.components)
    assert any(not component.homologically_trivial for component in winding.components)


def test_closed_chain_classifier_rejects_nonzero_boundary() -> None:
    lattice = periodic_honeycomb(3)
    open_edge = np.zeros(lattice.edge_count, dtype=np.uint8)
    open_edge[0] = 1
    with np.testing.assert_raises_regex(ValueError, "closed"):
        classify_closed_chain(lattice, open_edge)


def test_exhaustive_l2_xor_recovery_identity_and_winding_fixture() -> None:
    lattice = periodic_honeycomb(2)
    winding = _vertical_winding(lattice)
    assert not np.any(edge_chain_boundary(lattice, winding))
    for bits in range(1 << lattice.edge_count):
        physical = np.fromiter(
            ((bits >> edge) & 1 for edge in range(lattice.edge_count)),
            dtype=np.uint8,
            count=lattice.edge_count,
        )
        correction = compose_edge_chains(lattice, physical, winding)
        assert np.array_equal(
            edge_chain_boundary(lattice, physical),
            edge_chain_boundary(lattice, correction),
        )
        residual = compose_edge_chains(lattice, physical, correction)
        assert np.array_equal(residual, winding)
        analysis = classify_closed_chain(lattice, residual)
        assert any(
            not component.homologically_trivial
            for component in analysis.components
        )


def test_decode_and_score_flux_recovery_reports_closed_residual() -> None:
    lattice = periodic_honeycomb(3)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[0] = 1
    result = decode_and_score_flux_recovery(
        lattice,
        physical,
        syndrome_only_weights(lattice),
    )
    assert not np.any(edge_chain_boundary(lattice, result.residual))
    assert result.logical_error == any(
        not component.homologically_trivial
        for component in result.union_analysis.components
    )


def test_union_not_xor_controls_postflux_logical_decision() -> None:
    lattice = periodic_honeycomb(3)
    winding = _vertical_winding(lattice)
    assert not np.any(compose_edge_chains(lattice, winding, winding))
    union_analysis = classify_physical_correction_union(
        lattice, winding, winding
    )
    assert any(
        not component.homologically_trivial
        for component in union_analysis.components
    )

    weights = np.ones(lattice.edge_count, dtype=np.float64)
    weights[winding.astype(bool)] = -10.0
    result = decode_and_score_flux_recovery(lattice, winding, weights)
    assert np.array_equal(result.correction, winding)
    assert not np.any(result.residual)
    assert result.logical_error
