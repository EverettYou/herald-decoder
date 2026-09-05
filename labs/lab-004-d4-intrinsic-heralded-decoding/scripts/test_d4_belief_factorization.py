from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import (  # noqa: E402
    PublicD4Observation,
    build_fixed_cycle_factor_catalog,
    explicit_local_edge_flow_partition,
    explicit_local_spin_partition,
    f1_local_support_weight,
    f2_support_plus_parity_weight,
    fixed_cycle_factor_weight,
    local_edge_flow_factor_weight,
    local_spin_factor_weight,
)
from d4_honeycomb import (  # noqa: E402
    generate_loop_constraints,
    paper_periodic_honeycomb,
    periodic_honeycomb,
)
from d4_observation import evaluate_observation  # noqa: E402


def _public_observation(lattice, selected, charge_bits: dict[int, int] | None = None):
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[degrees == 2] = 0
    for vertex, value in (charge_bits or {}).items():
        charge[vertex] = value
    return PublicD4Observation(
        tuple(int(value) for value in degrees % 2),
        tuple(int(value) for value in charge),
    )


def _find_trivial_loop(lattice):
    for mask in range(1, 1 << lattice.edge_count):
        selected = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool
        )
        analysis = generate_loop_constraints(lattice, selected)
        if analysis.constraints:
            return selected, analysis
    raise AssertionError("paper L=2 fixture has no trivial-loop constraint")


def _find_winding_loop(lattice):
    for mask in range(1, 1 << lattice.edge_count):
        selected = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool
        )
        analysis = generate_loop_constraints(lattice, selected)
        if any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        ):
            return selected
    raise AssertionError("paper L=2 fixture has no winding loop")


def test_vacuum_and_open_path_match_exact_oracle() -> None:
    lattice = paper_periodic_honeycomb(2)
    vacuum = np.zeros(lattice.edge_count, dtype=bool)
    observation = _public_observation(lattice, vacuum)
    assert f1_local_support_weight(lattice, vacuum, observation).probability == 1.0
    assert f2_support_plus_parity_weight(lattice, vacuum, observation).probability == 1.0

    first = 0
    shared = int(lattice.edge_vertices[first, 1])
    second = next(
        int(edge)
        for edge in np.flatnonzero(np.any(lattice.edge_vertices == shared, axis=1))
        if int(edge) != first
    )
    path = np.zeros(lattice.edge_count, dtype=bool)
    path[[first, second]] = True
    observation = _public_observation(lattice, path)
    constraints = generate_loop_constraints(lattice, path).constraints
    exact = evaluate_observation(
        lattice.edge_vertices,
        path,
        np.asarray(observation.flux_syndrome, dtype=bool),
        np.asarray(observation.charge_outcomes, dtype=int),
        constraints,
    )
    assert exact.allowed and exact.probability == 0.5
    assert f1_local_support_weight(lattice, path, observation).probability == exact.probability
    assert f2_support_plus_parity_weight(lattice, path, observation).probability == exact.probability


def test_trivial_loop_requires_parity_multiplier_for_exact_weight() -> None:
    lattice = paper_periodic_honeycomb(2)
    selected, analysis = _find_trivial_loop(lattice)
    observation = _public_observation(lattice, selected)
    exact = evaluate_observation(
        lattice.edge_vertices,
        selected,
        np.asarray(observation.flux_syndrome, dtype=bool),
        np.asarray(observation.charge_outcomes, dtype=int),
        analysis.constraints,
    )
    f1 = f1_local_support_weight(lattice, selected, observation)
    f2 = f2_support_plus_parity_weight(lattice, selected, observation)
    assert exact.allowed
    assert f1.probability < exact.probability
    assert f2.probability == exact.probability
    assert len(f2.parity_factors) == len(analysis.constraints) == 2
    assert all(factor.value == 2.0 for factor in f2.parity_factors)


def test_parity_violation_is_seen_only_by_f2() -> None:
    lattice = paper_periodic_honeycomb(2)
    selected, analysis = _find_trivial_loop(lattice)
    flipped_vertex = analysis.constraints[0].vertices[0]
    observation = _public_observation(lattice, selected, {flipped_vertex: 1})
    exact = evaluate_observation(
        lattice.edge_vertices,
        selected,
        np.asarray(observation.flux_syndrome, dtype=bool),
        np.asarray(observation.charge_outcomes, dtype=int),
        analysis.constraints,
    )
    assert not exact.allowed
    assert f1_local_support_weight(lattice, selected, observation).probability > 0.0
    f2 = f2_support_plus_parity_weight(lattice, selected, observation)
    assert f2.status == "forbidden"
    assert f2.probability == 0.0


def test_branched_component_has_no_extra_parity_factor() -> None:
    lattice = paper_periodic_honeycomb(2)
    center = 0
    selected = np.zeros(lattice.edge_count, dtype=bool)
    selected[np.flatnonzero(np.any(lattice.edge_vertices == center, axis=1))] = True
    observation = _public_observation(lattice, selected)
    f1 = f1_local_support_weight(lattice, selected, observation)
    f2 = f2_support_plus_parity_weight(lattice, selected, observation)
    assert f1.status == f2.status == "allowed"
    assert f1.probability == f2.probability == 1.0
    assert f2.parity_factors == ()


def test_winding_candidate_is_terminal_not_a_bp_likelihood() -> None:
    lattice = paper_periodic_honeycomb(2)
    selected = _find_winding_loop(lattice)
    observation = _public_observation(lattice, selected)
    for evaluator in (f1_local_support_weight, f2_support_plus_parity_weight):
        result = evaluator(lattice, selected, observation)
        assert result.status == "terminal_winding"
        assert result.probability == 0.0


def test_local_support_rejects_wrong_flux_and_measurement_support() -> None:
    lattice = paper_periodic_honeycomb(2)
    selected = np.zeros(lattice.edge_count, dtype=bool)
    observation = _public_observation(lattice, selected)
    wrong_flux = list(observation.flux_syndrome)
    wrong_flux[0] = 1
    result = f1_local_support_weight(
        lattice,
        selected,
        PublicD4Observation(tuple(wrong_flux), observation.charge_outcomes),
    )
    assert result.status == "forbidden"
    assert result.probability == 0.0

    wrong_charge = list(observation.charge_outcomes)
    wrong_charge[0] = 0
    result = f2_support_plus_parity_weight(
        lattice,
        selected,
        PublicD4Observation(observation.flux_syndrome, tuple(wrong_charge)),
    )
    assert result.status == "forbidden"
    assert result.probability == 0.0


def test_public_schema_rejects_truth_and_diagnostic_ledger_is_not_public() -> None:
    lattice = paper_periodic_honeycomb(2)
    selected = np.zeros(lattice.edge_count, dtype=bool)
    observation = _public_observation(lattice, selected)
    with pytest.raises(ValueError, match="forbidden hidden fields"):
        PublicD4Observation.from_mapping(
            {**observation.to_dict(), "physical_error": [0] * lattice.edge_count}
        )
    result = f2_support_plus_parity_weight(lattice, selected, observation)
    assert set(observation.to_dict()) == {"flux_syndrome", "charge_outcomes"}
    serialized = result.diagnostic_dict()
    assert serialized["decoder_visible"] is False
    assert "error_edges" not in serialized
    assert "physical_error" not in serialized
    assert "components" not in serialized
    assert "logical_sector" not in serialized


def test_fixed_cycle_factors_separate_paper_l2_ambiguous_candidates() -> None:
    lattice = paper_periodic_honeycomb(2)
    catalog = build_fixed_cycle_factor_catalog(lattice)
    assert len(catalog) == 1068
    flux = (
        0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
        0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    )
    measured = (
        True, True, False, False, False, False, False, False, False, False,
        True, False, False, False, False, True, True, True, True, True, True,
        False, True, False,
    )
    charge = tuple(0 if value else -1 for value in measured)
    observation = PublicD4Observation(flux, charge)
    no_loop = np.asarray([(49098751766 >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool)
    with_loop = np.asarray([(32942290069 >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool)
    no_loop_result = fixed_cycle_factor_weight(lattice, no_loop, observation, catalog)
    loop_result = fixed_cycle_factor_weight(lattice, with_loop, observation, catalog)
    assert no_loop_result.status == loop_result.status == "allowed"
    assert no_loop_result.active_cycle_count == 0
    assert loop_result.active_cycle_count == 1
    assert loop_result.probability == 4.0 * no_loop_result.probability

    analysis = generate_loop_constraints(lattice, with_loop)
    violated = list(charge)
    violated[analysis.constraints[0].vertices[0]] = 1
    forbidden = fixed_cycle_factor_weight(
        lattice, with_loop, PublicD4Observation(flux, tuple(violated)), catalog
    )
    assert forbidden.status == "forbidden"
    assert forbidden.probability == 0.0


def test_local_spin_sum_reproduces_open_branch_and_loop_multipliers() -> None:
    lattice = periodic_honeycomb(2)
    vacuum = np.zeros(lattice.edge_count, dtype=bool)
    open_path = np.zeros(lattice.edge_count, dtype=bool)
    first = 0
    shared = int(lattice.edge_vertices[first, 1])
    second = next(
        int(edge)
        for edge in np.flatnonzero(np.any(lattice.edge_vertices == shared, axis=1))
        if int(edge) != first
    )
    open_path[[first, second]] = True
    branch = np.zeros(lattice.edge_count, dtype=bool)
    branch[np.flatnonzero(np.any(lattice.edge_vertices == 0, axis=1))] = True
    loop, analysis = _find_trivial_loop(lattice)

    for selected in (vacuum, open_path, branch):
        observation = _public_observation(lattice, selected)
        explicit = tuple(
            explicit_local_spin_partition(lattice, selected, observation, colour)
            for colour in (0, 1)
        )
        result = local_spin_factor_weight(lattice, selected, observation)
        assert explicit == result.colour_partitions == (1, 1)
        assert result.closed_component_count == 0
        edge_explicit = tuple(
            explicit_local_edge_flow_partition(lattice, selected, observation, colour)
            for colour in (0, 1)
        )
        edge_result = local_edge_flow_factor_weight(lattice, selected, observation)
        assert edge_explicit == pytest.approx(edge_result.colour_partitions, abs=1e-14)
        assert edge_result.colour_partitions == (1.0, 1.0)

    observation = _public_observation(lattice, loop)
    explicit = tuple(
        explicit_local_spin_partition(lattice, loop, observation, colour)
        for colour in (0, 1)
    )
    result = local_spin_factor_weight(lattice, loop, observation)
    assert explicit == result.colour_partitions == (2, 2)
    assert result.closed_component_count == 1
    edge_explicit = tuple(
        explicit_local_edge_flow_partition(lattice, loop, observation, colour)
        for colour in (0, 1)
    )
    edge_result = local_edge_flow_factor_weight(lattice, loop, observation)
    assert edge_explicit == pytest.approx(edge_result.colour_partitions, abs=1e-14)
    assert edge_result.colour_partitions == (2.0, 2.0)

    flipped_vertex = analysis.constraints[0].vertices[0]
    violated = _public_observation(lattice, loop, {flipped_vertex: 1})
    explicit = tuple(
        explicit_local_spin_partition(lattice, loop, violated, colour)
        for colour in (0, 1)
    )
    result = local_spin_factor_weight(lattice, loop, violated)
    assert explicit == result.colour_partitions
    assert 0 in explicit
    assert result.status == "forbidden"
    edge_explicit = tuple(
        explicit_local_edge_flow_partition(lattice, loop, violated, colour)
        for colour in (0, 1)
    )
    edge_result = local_edge_flow_factor_weight(lattice, loop, violated)
    assert edge_explicit == pytest.approx(edge_result.colour_partitions, abs=1e-14)
    assert 0.0 in edge_explicit
    assert edge_result.status == "forbidden"


def test_local_spin_factor_separates_paper_l2_ambiguous_candidates() -> None:
    lattice = paper_periodic_honeycomb(2)
    flux = (
        0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
        0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    )
    measured = (
        True, True, False, False, False, False, False, False, False, False,
        True, False, False, False, False, True, True, True, True, True, True,
        False, True, False,
    )
    observation = PublicD4Observation(
        flux, tuple(0 if value else -1 for value in measured)
    )
    no_loop = np.asarray(
        [(49098751766 >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool
    )
    with_loop = np.asarray(
        [(32942290069 >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool
    )
    no_loop_result = local_spin_factor_weight(lattice, no_loop, observation)
    loop_result = local_spin_factor_weight(lattice, with_loop, observation)
    assert no_loop_result.colour_partitions == (1, 1)
    assert loop_result.colour_partitions == (2, 2)
    assert loop_result.probability == 4.0 * no_loop_result.probability
    no_loop_flow = local_edge_flow_factor_weight(lattice, no_loop, observation)
    loop_flow = local_edge_flow_factor_weight(lattice, with_loop, observation)
    assert no_loop_flow.colour_partitions == (1.0, 1.0)
    assert loop_flow.colour_partitions == (2.0, 2.0)
    assert loop_flow.probability == 4.0 * no_loop_flow.probability
