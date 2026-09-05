#!/usr/bin/env python3
"""Tests for both public Phase B15 comparison branches."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("analyze_phase_b15_boundary_comparison.py")
SPEC = importlib.util.spec_from_file_location("phase_b15_compare", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB15ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = MODULE.prepare(
            json.loads(MODULE.DEFAULT_EVIDENCE.read_text()),
            json.loads(MODULE.DEFAULT_BRACKETS.read_text()),
            0.04,
        )

    def test_transition_contract_has_sixteen_rows_and_current_counts(self) -> None:
        self.assertEqual(len(self.data["q"]), 16)
        self.assertGreaterEqual(len(self.data["observations"]), 60)
        for row in self.data["observations"]:
            self.assertEqual(len(row["sizes"]), len(row["logical_errors"]))
            self.assertEqual(len(row["sizes"]), len(row["shots"]))

    def test_spline_branch_is_single_valued_and_bracket_constrained(self) -> None:
        fit = MODULE.fit_spline(self.data)
        curve = MODULE.spline_curve(self.data, fit["q_fit"], fit["z"], self.data["q"])
        self.assertTrue(np.all(curve >= self.data["lower"] - 1e-12))
        self.assertTrue(np.all(curve <= self.data["upper"] + 1e-12))

    def test_neural_branch_is_width_three_single_valued_and_constrained(self) -> None:
        fit = MODULE.fit_neural(self.data, starts=2, steps=80, seed=919000)
        self.assertEqual(fit["model"].hidden_weight.numel(), 3)
        curve = MODULE.neural_curve(fit["model"], self.data, self.data["q"])
        self.assertTrue(np.all(curve >= self.data["lower"] - 1e-12))
        self.assertTrue(np.all(curve <= self.data["upper"] + 1e-12))


if __name__ == "__main__":
    unittest.main()
