from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import (  # noqa: E402
    BLUE,
    GREEN,
    LogicalSectorPolicy,
    WindingParityRule,
    generate_loop_constraints,
    periodic_honeycomb,
)
from d4_sampler import observation_from_error_edges, sample_observation  # noqa: E402


def _local_hexagon(lattice) -> np.ndarray:
    vertices = [
        lattice.vertex_id(0, 0, BLUE),
        lattice.vertex_id(0, 0, GREEN),
        lattice.vertex_id(1, 0, BLUE),
        lattice.vertex_id(1, -1, GREEN),
        lattice.vertex_id(1, -1, BLUE),
        lattice.vertex_id(0, -1, GREEN),
    ]
    selected = np.zeros(lattice.edge_count, dtype=bool)
    for left, right in zip(vertices, vertices[1:] + vertices[:1]):
        selected[lattice.edge_between(left, right)] = True
    return selected


def _winding_loop(lattice) -> np.ndarray:
    selected = np.zeros(lattice.edge_count, dtype=bool)
    for y in range(lattice.size):
        for left, right in (
            (lattice.vertex_id(0, y, BLUE), lattice.vertex_id(0, y, GREEN)),
            (lattice.vertex_id(0, y, BLUE), lattice.vertex_id(0, y - 1, GREEN)),
        ):
            selected[lattice.edge_between(left, right)] = True
    return selected


def test_fixed_error_sampling_is_reproducible_and_satisfies_constraints() -> None:
    lattice = periodic_honeycomb(3)
    selected = _local_hexagon(lattice)
    first = observation_from_error_edges(lattice, selected, seed=1201)
    second = observation_from_error_edges(lattice, selected, seed=1201)
    assert first == second
    assert first.status == "sampled"
    assert first.schema_version == 3
    assert not first.logical_error
    assert first.log2_conditional_probability == -4
    analysis = generate_loop_constraints(lattice, selected)
    assert first.charge_outcomes is not None
    charge = np.asarray(first.charge_outcomes)
    for constraint in analysis.constraints:
        assert sum(charge[list(constraint.vertices)]) % 2 == constraint.required_parity


def test_sampler_reaches_every_allowed_local_hexagon_outcome() -> None:
    lattice = periodic_honeycomb(3)
    selected = _local_hexagon(lattice)
    outcomes = {
        observation_from_error_edges(lattice, selected, seed=seed).charge_outcomes
        for seed in range(512)
    }
    assert len(outcomes) == 16


def test_winding_observation_is_sector_agnostic_logical_failure() -> None:
    lattice = periodic_honeycomb(3)
    record = observation_from_error_edges(lattice, _winding_loop(lattice), seed=9)
    assert record.status == "logical_failure"
    assert record.logical_error
    assert not record.logical_sector_required
    assert record.logical_sector_label is None
    assert record.charge_outcomes is None
    assert record.log2_conditional_probability is None
    assert record.winding_components


def test_p_zero_versioned_record_is_empty_and_normalized() -> None:
    record = sample_observation(3, 0.0, seed=17)
    assert record.status == "sampled"
    assert record.error_rate == 0.0
    assert record.error_edges == ()
    assert record.flux_vertices == ()
    assert record.log2_conditional_probability == 0
    assert set(record.charge_outcomes or ()) == {0}
    assert not record.logical_error
    assert record.to_dict()["schema_version"] == 3


def test_error_and_charge_streams_are_reproducible() -> None:
    first = sample_observation(3, 0.2, seed=481)
    second = sample_observation(3, 0.2, seed=481)
    third = sample_observation(3, 0.2, seed=482)
    assert first == second
    assert first.error_edges != third.error_edges


def test_all_winding_colour_parity_branches_are_sampled() -> None:
    lattice = periodic_honeycomb(3)
    selected = _winding_loop(lattice)
    direction = (0, 1)
    color_vertices = {
        color: np.flatnonzero(
            (np.bincount(
                lattice.edge_vertices[selected].ravel(),
                minlength=lattice.vertex_count,
            ) == 2)
            & (lattice.vertex_colors == color)
        )
        for color in (BLUE, GREEN)
    }

    for blue_parity in (0, 1, None):
        for green_parity in (0, 1, None):
            label = f"matrix-b{blue_parity}-g{green_parity}"
            policy = LogicalSectorPolicy(
                label,
                (
                    WindingParityRule(direction, BLUE, blue_parity),
                    WindingParityRule(direction, GREEN, green_parity),
                ),
            )
            observed = {BLUE: set(), GREEN: set()}
            for seed in range(128):
                record = observation_from_error_edges(
                    lattice, selected, seed=seed, logical_sector=policy
                )
                assert record.status == "sampled"
                assert record.logical_error
                assert not record.logical_sector_required
                assert record.logical_sector_label == label
                assert record.winding_components
                assert record.charge_outcomes is not None
                constraint_count = int(blue_parity is not None) + int(
                    green_parity is not None
                )
                assert record.log2_conditional_probability == constraint_count - 6
                assert len(record.constraint_labels) == constraint_count
                charge = np.asarray(record.charge_outcomes)
                for color, required in (
                    (BLUE, blue_parity),
                    (GREEN, green_parity),
                ):
                    parity = int(sum(charge[color_vertices[color]]) % 2)
                    observed[color].add(parity)
                    if required is not None:
                        assert parity == required
            if blue_parity is None:
                assert observed[BLUE] == {0, 1}
            if green_parity is None:
                assert observed[GREEN] == {0, 1}


def test_winding_policy_requires_both_colour_rules() -> None:
    lattice = periodic_honeycomb(3)
    policy = LogicalSectorPolicy(
        "incomplete",
        (WindingParityRule((0, 2), BLUE, 0),),
    )
    with np.testing.assert_raises_regex(ValueError, "lacks rule"):
        observation_from_error_edges(
            lattice, _winding_loop(lattice), seed=4, logical_sector=policy
        )
