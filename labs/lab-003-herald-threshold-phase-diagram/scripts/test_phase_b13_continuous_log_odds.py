#!/usr/bin/env python3
"""Tests for the Phase B13 continuous trend-evidence renderer."""

from __future__ import annotations

import importlib.util
import json
import math
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_phase_b13_continuous_log_odds.py")
SPEC = importlib.util.spec_from_file_location("phase_b13_continuous_log_odds", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB13ContinuousLogOddsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text())

    def test_manifest_is_evidence_only(self) -> None:
        MODULE.validate_manifest(self.manifest)
        self.assertEqual(self.manifest["new_decodes"], 0)
        self.assertIsNone(self.manifest["sample_selection"])
        semantics = self.manifest["display_semantics"]
        self.assertFalse(semantics["cell_classification"])
        self.assertFalse(semantics["boundary_inference"])
        self.assertEqual(semantics["axes"], {"x": "edge error p", "y": "herald probability q"})

    def test_merge_is_exhaustive_and_updates_exactly_four_cells(self) -> None:
        payload = MODULE.merge_evidence(self.manifest)
        self.assertEqual(len(payload["cells"]), 231)
        self.assertEqual(payload["provenance"]["base_cell_count"], 227)
        self.assertEqual(payload["provenance"]["updated_cell_count"], 4)
        counts = {}
        for row in payload["cells"]:
            counts[row["evidence_source"]] = counts.get(row["evidence_source"], 0) + 1
        self.assertEqual(counts, {"phase_b9_base_grid": 227, "phase_b10_measured_endpoint_update": 4})

    def test_probabilities_log_odds_and_censoring_are_preserved(self) -> None:
        payload = MODULE.merge_evidence(self.manifest)
        for row in payload["cells"]:
            self.assertAlmostEqual(
                row["posterior_probability_upward_trend"] + row["posterior_probability_downward_trend"],
                1.0,
            )
            relation = row["posterior_log_odds_censoring"]["relation"]
            raw = row["posterior_log_odds_upward_vs_downward"]
            if relation == "equal":
                expected = math.log(
                    row["posterior_probability_upward_trend"]
                    / row["posterior_probability_downward_trend"]
                )
                self.assertAlmostEqual(raw, expected)
            else:
                self.assertIsNone(raw)
                self.assertIn(relation, {"less_than", "greater_than"})

    def test_only_display_values_are_clipped_and_no_classification_is_emitted(self) -> None:
        payload = MODULE.merge_evidence(self.manifest)
        limit = payload["display"]["symmetric_limit"]
        self.assertGreater(payload["display"]["clipped_cell_count"], 0)
        for row in payload["cells"]:
            self.assertLessEqual(abs(row["display_log_odds"]), limit)
            self.assertNotIn("classification", row)
            self.assertNotIn("phase", row)


if __name__ == "__main__":
    unittest.main()
