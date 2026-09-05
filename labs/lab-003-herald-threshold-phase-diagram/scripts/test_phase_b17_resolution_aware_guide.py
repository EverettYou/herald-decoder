#!/usr/bin/env python3
"""Tests for the B17 resolution-aware guide and transition region."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("analyze_phase_b17_resolution_aware_guide.py")
SPEC = importlib.util.spec_from_file_location("phase_b17", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(MODULE.DEFAULT_EVIDENCE.read_text())
        cls.brackets = json.loads(MODULE.DEFAULT_BRACKETS.read_text())
        cls.manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())
        cls.payload = MODULE.analyze(MODULE.DEFAULT_EVIDENCE, MODULE.DEFAULT_BRACKETS, MODULE.DEFAULT_B16, MODULE.DEFAULT_MANIFEST)

    def test_endpoints_are_derived_from_current_evidence(self) -> None:
        start_p, end_q = MODULE.derive_guide_endpoints(self.evidence)
        self.assertGreater(start_p, 0.17)
        self.assertLess(start_p, 0.19)
        self.assertGreater(end_q, 0.84)
        self.assertLess(end_q, 0.87)

    def test_guide_is_monotone_and_has_no_low_q_reversal(self) -> None:
        q = np.asarray(self.payload["display"]["guide_q"])
        p = np.asarray(self.payload["display"]["guide_p"])
        self.assertTrue(np.all(np.diff(p) >= -1e-12))
        self.assertFalse(np.any(np.diff(p[q <= 0.4 + 1e-12]) < -1e-12))
        self.assertTrue(self.payload["diagnostics"]["guide_monotone_nondecreasing_p"])
        self.assertFalse(self.payload["diagnostics"]["low_q_reversal_present"])

    def test_region_contains_all_measured_and_censored_brackets(self) -> None:
        region = self.payload["transition_region"]
        self.assertEqual(len(region["raw_brackets"]), 19)
        self.assertEqual(self.payload["diagnostics"]["measured_bracket_count"], 16)
        self.assertEqual(self.payload["diagnostics"]["right_censor_bracket_count"], 3)
        self.assertTrue(self.payload["diagnostics"]["all_raw_brackets_contained"])
        self.assertTrue(np.all(np.diff(region["lower"]) >= -1e-12))
        self.assertTrue(np.all(np.diff(region["upper"]) >= -1e-12))

    def test_region_is_materially_wider_than_b16_refit_envelope(self) -> None:
        self.assertGreater(self.payload["diagnostics"]["width_ratio_b17_to_b16"], 10.0)
        self.assertFalse(self.payload["guide"]["inferential_interval"])
        self.assertFalse(self.payload["transition_region"]["joint_coverage_claim"])

    def test_no_new_decoder_compute(self) -> None:
        self.assertEqual(self.payload["new_decoder_runs"], 0)
        self.assertEqual(self.payload["new_decodes"], 0)


if __name__ == "__main__":
    unittest.main()
