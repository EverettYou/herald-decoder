from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_observation import ParityConstraint, evaluate_observation  # noqa: E402


def test_two_edge_path_has_one_fair_intermediate_measurement() -> None:
    edges = np.array([[0, 1], [1, 2]])
    error = np.array([1, 1], dtype=bool)
    flux = np.array([1, 0, 1], dtype=bool)
    probabilities = []
    for outcome in (0, 1):
        charge = np.array([-1, outcome, -1])
        result = evaluate_observation(edges, error, flux, charge)
        assert result.allowed
        assert result.internal_vertices == (1,)
        probabilities.append(result.probability)
    assert probabilities == [0.5, 0.5]
    assert sum(probabilities) == 1.0


def test_closed_triangle_even_constraint_normalizes_allowed_outcomes() -> None:
    edges = np.array([[0, 1], [1, 2], [2, 0]])
    error = np.ones(3, dtype=bool)
    flux = np.zeros(3, dtype=bool)
    constraint = ParityConstraint((0, 1, 2), required_parity=0, label="loop")
    total = 0.0
    allowed_count = 0
    for bits in itertools.product((0, 1), repeat=3):
        result = evaluate_observation(
            edges, error, flux, np.asarray(bits), (constraint,)
        )
        total += result.probability
        allowed_count += int(result.allowed)
    assert allowed_count == 4
    assert total == 1.0


def test_constraint_violation_has_zero_likelihood() -> None:
    edges = np.array([[0, 1], [1, 2], [2, 0]])
    result = evaluate_observation(
        edges,
        np.ones(3, dtype=bool),
        np.zeros(3, dtype=bool),
        np.array([1, 0, 0]),
        (ParityConstraint((0, 1, 2), 0, "even loop"),),
    )
    assert not result.allowed
    assert result.probability == 0.0
    assert "even loop" in (result.reason or "")


def test_flux_must_equal_error_boundary() -> None:
    edges = np.array([[0, 1], [1, 2]])
    result = evaluate_observation(
        edges,
        np.ones(2, dtype=bool),
        np.zeros(3, dtype=bool),
        np.array([-1, 0, -1]),
    )
    assert not result.allowed
    assert result.reason == "flux syndrome is not boundary(E)"


def test_measurements_are_forbidden_off_internal_support() -> None:
    edges = np.array([[0, 1], [1, 2]])
    result = evaluate_observation(
        edges,
        np.ones(2, dtype=bool),
        np.array([1, 0, 1], dtype=bool),
        np.array([0, 0, -1]),
    )
    assert not result.allowed
    assert "degree-two" in (result.reason or "")


def test_constraint_may_not_reference_unmeasured_vertex() -> None:
    edges = np.array([[0, 1], [1, 2]])
    with pytest.raises(ValueError, match="unmeasured"):
        evaluate_observation(
            edges,
            np.ones(2, dtype=bool),
            np.array([1, 0, 1], dtype=bool),
            np.array([-1, 0, -1]),
            (ParityConstraint((0, 1), 0),),
        )
