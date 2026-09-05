#!/usr/bin/env python3
"""Tests for the Phase B8 frontier posterior-predictive diagnostic."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_phase_b8_frontier_posterior_predictive.py")
SPEC = importlib.util.spec_from_file_location("phase_b8_frontier_design", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB8FrontierPredictiveTests(unittest.TestCase):
    def test_frontier_and_design_costs_are_exact(self) -> None:
        output = MODULE.analyze(MODULE.DEFAULT_MAP, outer_draws=8, inner_draws=64, seed=2)
        self.assertEqual(
            {(row["q"], row["p"]) for row in output["frontier_candidates"]},
            MODULE.EXPECTED,
        )
        costs = {row["name"]: row["total_additional_decodes"] for row in output["designs"]}
        self.assertEqual(
            costs,
            {
                "measured_endpoints_1000": 8000,
                "all_measured_sizes_1000": 18000,
                "balance_measured_to_4000": 21000,
            },
        )

    def test_designs_cover_all_cells_without_unmeasured_extrapolation(self) -> None:
        phase_map = json.loads(MODULE.DEFAULT_MAP.read_text())
        five = MODULE.cell_by_key(phase_map, 0.30, 0.20)
        three = MODULE.cell_by_key(phase_map, 0.65, 0.28)
        self.assertEqual(five["sizes"], [5, 7, 9, 11, 13])
        self.assertEqual(three["sizes"], [7, 9, 11])
        self.assertEqual(MODULE.additions(five, "measured_endpoints_1000").tolist(), [1000, 0, 0, 0, 1000])
        self.assertEqual(MODULE.additions(three, "measured_endpoints_1000").tolist(), [1000, 0, 1000])


if __name__ == "__main__":
    unittest.main()
