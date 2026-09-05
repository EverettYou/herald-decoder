#!/usr/bin/env python3
"""Tests for the strongly smoothed B16 boundary guide."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("analyze_phase_b16_strong_smooth_boundary.py")
SPEC = importlib.util.spec_from_file_location("phase_b16", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(MODULE.DEFAULT_EVIDENCE.read_text())
        cls.brackets = json.loads(MODULE.DEFAULT_BRACKETS.read_text())
        cls.manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())
        cls.data = MODULE.prepare(cls.evidence, cls.brackets, 0.04, 0.36)

    def test_bezier_has_only_four_macro_scale_controls(self) -> None:
        control = np.asarray([0.18, 0.20, 0.31, 0.50])
        q = np.r_[np.arange(0.0, 0.82, 0.05), 0.82]
        curve = MODULE.bezier_curve(control, q, 0.82)
        self.assertEqual(len(control), 4)
        self.assertEqual(len(curve), 18)
        self.assertAlmostEqual(curve[0], control[0])
        self.assertAlmostEqual(curve[-1], 0.5)

    def test_fit_uses_physical_intercepts_and_closes_both_domain_edges(self) -> None:
        fit = MODULE.fit_curve(self.data, self.manifest)
        control = fit["control_p"]
        q = np.r_[np.arange(0.0, 0.82, 0.05), 0.82]
        curve = MODULE.bezier_curve(control, q, 0.82)
        self.assertAlmostEqual(control[0], 0.18)
        self.assertAlmostEqual(q[0], 0.0)
        self.assertAlmostEqual(q[-1], 0.82)
        self.assertAlmostEqual(curve[-1], 0.5)

    def test_high_q_evidence_is_not_dropped(self) -> None:
        regions = {row["region"] for row in self.data["observations"]}
        self.assertEqual(regions, {"audited_lower_transition", "high_q_right_edge_closure"})
        self.assertTrue(any(row["q"] > 0.75 for row in self.data["observations"]))


if __name__ == "__main__":
    unittest.main()
