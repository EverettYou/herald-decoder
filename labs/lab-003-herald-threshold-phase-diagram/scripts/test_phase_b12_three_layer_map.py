#!/usr/bin/env python3
"""Tests for the Phase B12 presentation-only three-layer renderer."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_phase_b12_three_layer_map.py")
SPEC = importlib.util.spec_from_file_location("phase_b12_three_layer_map", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB12ThreeLayerMapTests(unittest.TestCase):
    def test_midpoint_edges_preserve_nonuniform_grid(self) -> None:
        observed = MODULE.midpoint_edges([0.08, 0.12, 0.16])
        for actual, expected in zip(observed, [0.06, 0.1, 0.14, 0.18]):
            self.assertAlmostEqual(actual, expected)

    def test_classification_is_exhaustive_and_preserves_absolute_anchors(self) -> None:
        manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())
        source = json.loads((MODULE.LAB_DIR / manifest["source_analysis"]["path"]).read_text())
        payload = MODULE.classify(source)
        self.assertEqual(sum(payload["display_counts"].values()), 231)
        self.assertEqual(payload["absolute_anchor_counts"], {"decodable": 25, "undecodable": 64})
        self.assertGreater(payload["display_counts"]["boundary"], 0)
        self.assertGreater(payload["display_counts"]["unclassified"], 0)

    def test_manifest_is_presentation_only_and_forbids_crossings(self) -> None:
        manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())
        MODULE.validate_manifest(manifest)
        self.assertEqual(manifest["new_decodes"], 0)
        self.assertIsNone(manifest["sample_selection"])
        self.assertFalse(manifest["display_semantics"]["crossing_markers"])
        self.assertFalse(manifest["display_semantics"]["continuous_interpolation"])


if __name__ == "__main__":
    unittest.main()
