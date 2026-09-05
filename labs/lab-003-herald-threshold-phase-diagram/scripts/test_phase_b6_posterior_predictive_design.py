#!/usr/bin/env python3
"""Tests for the Phase B6 posterior-predictive design diagnostic."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_phase_b6_posterior_predictive_design.py")
SPEC = importlib.util.spec_from_file_location("phase_b6_design", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PosteriorPredictiveDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cell = {
            "q": 0.3,
            "p": 0.2,
            "sizes": [5, 7, 9, 11, 13],
            "logical_errors": [190, 195, 200, 205, 210],
            "shots": [1000, 1000, 1000, 1000, 1000],
            "posterior_probability_upward_trend": 0.8,
        }

    def test_design_costs_and_balance(self) -> None:
        np.testing.assert_array_equal(
            MODULE.planned_additions(self.cell, "endpoints_1000"),
            [1000, 0, 0, 0, 1000],
        )
        np.testing.assert_array_equal(
            MODULE.planned_additions(self.cell, "all_sizes_1000"),
            [1000, 1000, 1000, 1000, 1000],
        )
        unequal = dict(self.cell, shots=[1000, 3000, 3000, 3000, 1000])
        np.testing.assert_array_equal(
            MODULE.planned_additions(unequal, "balance_to_3000"),
            [2000, 0, 0, 0, 2000],
        )

    def test_simulation_is_reproducible_and_probabilities_normalize(self) -> None:
        additions = MODULE.planned_additions(self.cell, "endpoints_1000")
        first = MODULE.simulate_cell(
            self.cell, additions, outer_draws=32, inner_draws=256, seed=123
        )
        second = MODULE.simulate_cell(
            self.cell, additions, outer_draws=32, inner_draws=256, seed=123
        )
        self.assertEqual(first, second)
        total = (
            first["posterior_predictive_probability_resolved_upward"]
            + first["posterior_predictive_probability_resolved_downward"]
            + first["posterior_predictive_probability_unresolved"]
        )
        self.assertAlmostEqual(total, 1.0)
        self.assertGreaterEqual(
            first["posterior_predictive_probability_false_direction_resolution"], 0.0
        )
        self.assertLessEqual(
            first["posterior_predictive_probability_false_direction_resolution"], 1.0
        )


if __name__ == "__main__":
    unittest.main()
