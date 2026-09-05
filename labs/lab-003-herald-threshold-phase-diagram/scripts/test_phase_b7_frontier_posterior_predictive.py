#!/usr/bin/env python3
"""Tests for the Phase B7 frontier posterior-predictive diagnostic."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_phase_b7_frontier_posterior_predictive.py")
SPEC = importlib.util.spec_from_file_location("phase_b7_frontier_design", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB7FrontierPredictiveTests(unittest.TestCase):
    def test_frontier_and_design_costs_are_exact(self) -> None:
        output = MODULE.analyze(MODULE.DEFAULT_MAP, outer_draws=8, inner_draws=64, seed=2)
        self.assertEqual({(row["q"], row["p"]) for row in output["frontier_candidates"]}, MODULE.EXPECTED)
        costs = {row["name"]: row["total_additional_decodes"] for row in output["designs"]}
        self.assertEqual(costs, {"raise_minimum_by_1000": 11000, "all_sizes_1000": 18000, "balance_to_3000": 14000})

    def test_source_windows_and_minimum_additions(self) -> None:
        phase_map = json.loads(MODULE.DEFAULT_MAP.read_text())
        three = MODULE.cell_by_key(phase_map, 0.65, 0.28)
        five = MODULE.cell_by_key(phase_map, 0.30, 0.20)
        self.assertEqual(three["sizes"], [7, 9, 11])
        self.assertEqual(MODULE.additions(three, "raise_minimum_by_1000").tolist(), [1000, 1000, 1000])
        self.assertEqual(MODULE.additions(five, "raise_minimum_by_1000").tolist(), [0, 1000, 1000, 1000, 0])


if __name__ == "__main__":
    unittest.main()
