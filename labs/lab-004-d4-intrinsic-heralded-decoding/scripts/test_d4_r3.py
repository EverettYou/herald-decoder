from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import paper_periodic_honeycomb, periodic_honeycomb  # noqa: E402
from d4_r3 import (  # noqa: E402
    component_auxiliary_fusion_milp,
    decode_observation_record_r3,
    exhaustive_fusion_constrained_map,
    finite_support_fusion_constrained_milp,
    geometry_trivial_loop_catalog,
    structural_fusion_constrained_milp,
)
from d4_sampler import observation_from_error_edges  # noqa: E402


def _fixture():
    lattice = periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[[0, 3, 6]] = 1
    observation = observation_from_error_edges(lattice, physical, seed=11)
    assert observation.charge_outcomes is not None
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(observation.flux_vertices)] = 1
    return lattice, flux, np.asarray(observation.charge_outcomes, dtype=np.int64)


def _mask(error: np.ndarray) -> int:
    return sum(int(bit) << edge for edge, bit in enumerate(error))


def test_r3_exhaustive_fixture_preserves_map_homology_tie() -> None:
    lattice, flux, charge = _fixture()
    result = exhaustive_fusion_constrained_map(lattice, flux, charge, 0.1)
    assert result.enumerated_candidate_count == 4096
    assert result.compatible_candidate_count == 4
    assert {_mask(candidate.error) for candidate in result.maximizers} == {73, 82, 268}
    assert {candidate.error_weight for candidate in result.maximizers} == {3}


def test_r3_map_changes_with_declared_prior_without_becoming_sector_posterior() -> None:
    lattice, flux, charge = _fixture()
    result = exhaustive_fusion_constrained_map(lattice, flux, charge, 0.6)
    assert [_mask(candidate.error) for candidate in result.maximizers] == [279]
    assert result.maximizers[0].error_weight == 5


def test_r3_exhaustive_limit_and_prior_fail_closed() -> None:
    lattice, flux, charge = _fixture()
    with pytest.raises(ValueError, match="strictly"):
        exhaustive_fusion_constrained_map(lattice, flux, charge, 0.0)
    with pytest.raises(ValueError, match="bounded"):
        exhaustive_fusion_constrained_map(
            lattice, flux, charge, 0.1, maximum_edges=11
        )


@pytest.mark.parametrize("error_rate", (0.1, 0.6))
def test_r3_finite_milp_matches_complete_exhaustive_optimizer_set(
    error_rate: float,
) -> None:
    lattice, flux, charge = _fixture()
    exhaustive = exhaustive_fusion_constrained_map(
        lattice, flux, charge, error_rate
    )
    integer = finite_support_fusion_constrained_milp(
        lattice, flux, charge, error_rate
    )
    assert integer.compatible_candidate_count == exhaustive.compatible_candidate_count
    assert np.isclose(
        integer.minimum_negative_log2_joint,
        -exhaustive.maximum_log2_joint_probability,
    )
    assert {_mask(candidate.error) for candidate in integer.maximizers} == {
        _mask(candidate.error) for candidate in exhaustive.maximizers
    }
    assert _mask(integer.solver_selected_error) in {
        _mask(candidate.error) for candidate in exhaustive.maximizers
    }


def test_r3_finite_milp_enumerates_relative_homology_sectors() -> None:
    lattice, flux, charge = _fixture()
    integer = finite_support_fusion_constrained_milp(lattice, flux, charge, 0.1)
    sector_masks = {
        sector.relative_windings: {
            _mask(candidate.error) for candidate in sector.maximizers
        }
        for sector in integer.sector_optima
    }
    assert sector_masks[()] == {73}
    assert sector_masks[((1, 0),)] == {82}
    assert sector_masks[((0, 1),)] == {268}
    assert sector_masks[((1, -1),)] == {279}


@pytest.mark.parametrize("error_rate", (0.1, 0.6))
def test_r3_structural_edge_milp_matches_r3_0_and_r3_1(error_rate: float) -> None:
    lattice, flux, charge = _fixture()
    exhaustive = exhaustive_fusion_constrained_map(
        lattice, flux, charge, error_rate
    )
    structural = structural_fusion_constrained_milp(
        lattice, flux, charge, error_rate
    )
    assert structural.structurally_feasible_count == 4
    assert structural.fusion_no_good_count == 0
    assert np.isclose(
        structural.minimum_negative_log2_joint,
        -exhaustive.maximum_log2_joint_probability,
    )
    assert {_mask(candidate.error) for candidate in structural.maximizers} == {
        _mask(candidate.error) for candidate in exhaustive.maximizers
    }


def test_r3_structural_fusion_cut_fails_closed_on_violated_loop_parity() -> None:
    lattice = periodic_honeycomb(2)
    loop = np.asarray([(238 >> edge) & 1 for edge in range(12)], dtype=np.uint8)
    observation = observation_from_error_edges(lattice, loop, seed=11)
    assert observation.charge_outcomes is not None
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(observation.flux_vertices)] = 1
    charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    allowed = structural_fusion_constrained_milp(lattice, flux, charge, 0.1)
    assert allowed.structurally_feasible_count == 1
    charge[0] ^= 1
    with pytest.raises(ValueError, match="no supported"):
        structural_fusion_constrained_milp(lattice, flux, charge, 0.1)


@pytest.mark.parametrize("error_rate", (0.1, 0.6))
def test_r3_component_auxiliary_milp_matches_all_map_and_sector_fixtures(
    error_rate: float,
) -> None:
    lattice, flux, charge = _fixture()
    exhaustive = exhaustive_fusion_constrained_map(
        lattice, flux, charge, error_rate
    )
    component = component_auxiliary_fusion_milp(
        lattice, flux, charge, error_rate
    )
    assert component.loop_auxiliary_count == 4
    assert component.winding_no_good_count == 0
    assert np.isclose(
        component.minimum_negative_log2_joint,
        -exhaustive.maximum_log2_joint_probability,
    )
    assert {_mask(candidate.error) for candidate in component.maximizers} == {
        _mask(candidate.error) for candidate in exhaustive.maximizers
    }
    assert {
        sector.relative_windings for sector in component.sector_optima
    } == {(), ((1, 0),), ((0, 1),), ((1, -1),)}


def test_r3_component_auxiliary_counts_loop_likelihood_exactly() -> None:
    lattice = periodic_honeycomb(2)
    loop = np.asarray([(238 >> edge) & 1 for edge in range(12)], dtype=np.uint8)
    observation = observation_from_error_edges(lattice, loop, seed=11)
    assert observation.charge_outcomes is not None
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(observation.flux_vertices)] = 1
    charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    exhaustive = exhaustive_fusion_constrained_map(lattice, flux, charge, 0.1)
    component = component_auxiliary_fusion_milp(lattice, flux, charge, 0.1)
    assert observation.log2_conditional_probability == -4
    assert np.isclose(
        component.minimum_negative_log2_joint,
        -exhaustive.maximum_log2_joint_probability,
    )
    assert [_mask(candidate.error) for candidate in component.maximizers] == [238]


def test_r3_geometry_loop_generator_matches_bounded_exhaustive_catalog() -> None:
    lattice = periodic_honeycomb(2)
    geometry_masks = {
        _mask(chain) for chain, _, _ in geometry_trivial_loop_catalog(lattice)
    }
    assert geometry_masks == {238, 1589, 2947, 3416}


def test_r3_geometry_loop_generator_finds_paper_l2_hexagons_without_edge_scan() -> None:
    catalog = geometry_trivial_loop_catalog(
        paper_periodic_honeycomb(2), maximum_cycle_length=6, cycle_limit=10_000
    )
    assert len(catalog) == 12
    assert {int(chain.sum()) for chain, _, _ in catalog} == {6}


def test_r3_record_interface_routes_nonwinding_observation_to_solver() -> None:
    lattice = periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[[0, 3, 6]] = 1
    observation = observation_from_error_edges(lattice, physical, seed=11)
    decision = decode_observation_record_r3(lattice, observation, 0.1)
    assert decision.status == "recovered_nonwinding"
    assert not decision.logical_error
    assert decision.recovery is not None


def test_r3_record_interface_exhausts_terminal_primitive_winding_fixtures() -> None:
    lattice = periodic_honeycomb(2)
    terminal_count = 0
    for mask in range(1 << lattice.edge_count):
        physical = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        observation = observation_from_error_edges(lattice, physical, seed=11)
        if observation.status != "logical_failure":
            continue
        decision = decode_observation_record_r3(lattice, observation, 0.1)
        assert decision.status == "terminal_winding_logical_failure"
        assert decision.logical_error
        assert decision.recovery is None
        terminal_count += 1
    assert terminal_count == 123
