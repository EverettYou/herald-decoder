#!/usr/bin/env python3
"""Tests for the Phase B14 two-branch acquisition design."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("design_phase_b14_branch_matrix.py")
SPEC = importlib.util.spec_from_file_location("phase_b14_design", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB14BranchMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.selection, self.manifest = MODULE.build()

    def test_selection_is_two_sign_contrast_pairs_in_two_q_strata(self) -> None:
        keys = {
            (cell["q"], cell["p"])
            for pair in self.selection["selected_pairs"]
            for cell in pair["cells"]
        }
        self.assertEqual(keys, {(0.2, 0.16), (0.2, 0.2), (0.7, 0.28), (0.7, 0.32)})
        self.assertEqual(len(self.selection["selected_pairs"]), 2)
        for pair in self.selection["selected_pairs"]:
            left, right = pair["cells"]
            self.assertLess(
                left["posterior_log_odds_upward_vs_downward"]
                * right["posterior_log_odds_upward_vs_downward"],
                0.0,
            )

    def test_matrix_covers_both_branches_at_every_cell(self) -> None:
        jobs = self.selection["jobs"]
        self.assertEqual(len(jobs), 8)
        for key in {(row["q"], row["p"]) for row in jobs}:
            branches = {row["branch"] for row in jobs if (row["q"], row["p"]) == key}
            self.assertEqual(branches, {"distance_leverage_L5_L13", "same_window_precision_L7_L9_L11"})
        self.assertEqual(self.selection["expected_new_decodes"], 10000)

    def test_design_has_no_interpretive_or_adaptive_branch(self) -> None:
        self.assertIsNone(self.selection["phase_interpretation"])
        self.assertIsNone(self.selection["boundary_inference"])
        self.assertFalse(self.selection["new_data_launched"])
        self.assertFalse(self.manifest["analysis_contract"]["cell_or_phase_classification"])
        self.assertFalse(self.manifest["analysis_contract"]["boundary_inference"])
        self.assertIn("no adaptive", self.manifest["stop_rule"])


if __name__ == "__main__":
    unittest.main()
