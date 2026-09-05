#!/usr/bin/env python3
"""Tests for the Phase B11 three-layer preregistered analysis."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_phase_b11_three_layer.py")
SPEC = importlib.util.spec_from_file_location("phase_b11_three_layer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def cell(errors, shots=1000):
    return {"logical_errors": list(errors), "shots": [shots] * len(errors), "sizes": [7, 9, 11][:len(errors)]}


class PhaseB11ThreeLayerTests(unittest.TestCase):
    def test_anchor_probabilities_separate_floor_saturation_and_transition(self) -> None:
        floor = cell([0, 1, 0])
        saturation = cell([500, 510, 490])
        transition = cell([220, 240, 260])
        self.assertGreater(MODULE.joint_anchor_probability(floor, "floor", 0.02, (0.5, 0.5)), 0.99)
        self.assertGreater(MODULE.joint_anchor_probability(saturation, "saturation", 0.075, (0.5, 0.5)), 0.99)
        self.assertLess(MODULE.joint_anchor_probability(transition, "saturation", 0.075, (0.5, 0.5)), 1e-6)

    def test_rule_selection_is_fail_closed_and_deterministic(self) -> None:
        cells = {(0.0, 0.0): cell([0, 0, 1]), (0.0, 0.1): cell([200, 220, 240])}
        selected, diagnostics = MODULE.choose_rule(
            cells, kind="floor", tolerances=[0.01, 0.02], gates=[0.8, 0.9, 0.95],
            validation_keys=[(0.0, 0.0)], exclusion_keys=[(0.0, 0.1)], prior=(0.5, 0.5))
        self.assertEqual(selected["gate"], 0.95)
        self.assertEqual(selected["tolerance"], 0.01)
        self.assertTrue(any(row["qualifies"] for row in diagnostics))

    def test_manifest_is_no_new_data_and_no_render(self) -> None:
        import json
        manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())
        # B11 is a frozen historical analysis.  Later additive methodology
        # sections (including B17) must not rewrite its registered hashes.
        self.assertEqual(manifest["status"], "analyzed")
        self.assertEqual(manifest["new_decodes"], 0)
        self.assertIsNone(manifest["render_output"])


if __name__ == "__main__":
    unittest.main()
