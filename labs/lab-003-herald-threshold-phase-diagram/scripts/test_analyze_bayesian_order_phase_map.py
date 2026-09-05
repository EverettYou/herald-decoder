#!/usr/bin/env python3
"""Tests for Bayesian order-constrained finite-size LER inference."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


def load_module():
    path = Path(__file__).with_name("analyze_bayesian_order_phase_map.py")
    spec = importlib.util.spec_from_file_location("bayesian_order_map", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


analysis = load_module()


class BayesianOrderTests(unittest.TestCase):
    def test_equal_counts_are_symmetric(self):
        result = analysis.posterior_order_probabilities(
            np.array([50, 50, 50]), np.array([100, 100, 100])
        )
        self.assertAlmostEqual(
            result["posterior_probability_decreasing"],
            result["posterior_probability_increasing"],
            places=10,
        )
        self.assertAlmostEqual(result["posterior_log_odds_increasing_vs_decreasing"], 0.0, places=10)
        self.assertAlmostEqual(
            result["posterior_probability_decreasing"]
            + result["posterior_probability_increasing"]
            + result["posterior_probability_other_order"],
            1.0,
            places=10,
        )

    def test_clear_decrease_has_high_posterior_probability(self):
        result = analysis.posterior_order_probabilities(
            np.array([400, 200, 50]), np.array([1000, 1000, 1000])
        )
        self.assertGreater(result["posterior_probability_decreasing"], 0.999)
        self.assertEqual(analysis.classify(result), "decodable")

    def test_clear_increase_has_high_posterior_probability(self):
        result = analysis.posterior_order_probabilities(
            np.array([50, 200, 400]), np.array([1000, 1000, 1000])
        )
        self.assertGreater(result["posterior_probability_increasing"], 0.999)
        self.assertEqual(analysis.classify(result), "undecodable")

    def test_nonmonotone_counts_remain_unresolved(self):
        result = analysis.posterior_order_probabilities(
            np.array([100, 400, 200]), np.array([1000, 1000, 1000])
        )
        self.assertGreater(result["posterior_probability_other_order"], 0.999)
        self.assertEqual(analysis.classify(result), "unresolved")


if __name__ == "__main__":
    unittest.main()
