#!/usr/bin/env python3
"""Tests for the B18 p<->1-p symmetry-constrained guide."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("analyze_phase_b18_symmetry_constrained_guide.py")
SPEC = importlib.util.spec_from_file_location("phase_b18", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.b17 = json.loads(MODULE.DEFAULT_B17.read_text())
        cls.payload = MODULE.analyze(MODULE.DEFAULT_EVIDENCE, MODULE.DEFAULT_B17, MODULE.DEFAULT_MANIFEST)

    def test_endpoint_symmetry_slope_is_exactly_zero(self) -> None:
        self.assertEqual(self.payload["diagnostics"]["analytic_endpoint_dq_dp"], 0.0)
        p = self.payload["guide"]["p_control"]
        q = self.payload["guide"]["q_control"]
        self.assertLess(p[-2], p[-1])
        self.assertEqual(q[-2], q[-1])

    def test_parametric_guide_is_single_valued_and_has_no_reversal(self) -> None:
        p = np.asarray(self.payload["display"]["guide_p"])
        q = np.asarray(self.payload["display"]["guide_q"])
        self.assertTrue(np.all(np.diff(p) >= -1e-12))
        self.assertTrue(np.all(np.diff(q) >= -1e-12))
        self.assertFalse(self.payload["diagnostics"]["low_q_reversal_present"])

    def test_b17_directional_region_is_unchanged(self) -> None:
        self.assertEqual(self.payload["transition_region"], self.b17["transition_region"])
        self.assertEqual(len(self.payload["transition_region"]["raw_brackets"]), 19)

    def test_full_axis_does_not_fabricate_evidence_cells(self) -> None:
        self.assertEqual(self.payload["display"]["axis_p"], [0.0, 0.5])
        self.assertEqual(self.payload["display"]["measured_p_cell_support"], [0.06, 0.5])
        self.assertEqual(self.payload["diagnostics"]["evidence_cell_count"], 231)
        self.assertEqual(self.payload["diagnostics"]["added_evidence_cell_count"], 0)

    def test_no_new_decoder_compute(self) -> None:
        self.assertEqual(self.payload["new_decoder_runs"], 0)
        self.assertEqual(self.payload["new_decodes"], 0)


if __name__ == "__main__":
    unittest.main()
