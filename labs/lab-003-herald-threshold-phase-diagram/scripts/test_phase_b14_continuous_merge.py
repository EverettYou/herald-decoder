#!/usr/bin/env python3
"""Tests for the Phase B14 continuous evidence merge."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("merge_phase_b14_continuous_map.py")
SPEC = importlib.util.spec_from_file_location("phase_b14_continuous_merge", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB14ContinuousMergeTests(unittest.TestCase):
    def test_exactly_four_cells_are_replaced_without_labels(self) -> None:
        output = MODULE.merge(
            json.loads(MODULE.DEFAULT_BASE.read_text()),
            json.loads(MODULE.DEFAULT_ANALYSIS.read_text()),
            json.loads(MODULE.DEFAULT_AUDIT.read_text()),
        )
        self.assertEqual(len(output["cells"]), 231)
        self.assertEqual(len(output["provenance"]["updated_cells"]), 4)
        self.assertEqual(
            sum(row["evidence_source"] == "phase_b14_combined_distance_and_precision" for row in output["cells"]),
            4,
        )
        for row in output["cells"]:
            self.assertNotIn("classification", row)
            self.assertNotIn("phase", row)

    def test_updates_match_combined_branch_probabilities(self) -> None:
        analysis = json.loads(MODULE.DEFAULT_ANALYSIS.read_text())
        output = MODULE.merge(
            json.loads(MODULE.DEFAULT_BASE.read_text()), analysis, json.loads(MODULE.DEFAULT_AUDIT.read_text())
        )
        by_key = {(row["q"], row["p"]): row for row in output["cells"]}
        for row in analysis["analyses"]:
            combined = row["variants"]["combined"]
            merged = by_key[(row["q"], row["p"])]
            self.assertEqual(merged["posterior_probability_upward_trend"], combined["posterior_probability_upward_trend"])
            self.assertEqual(merged["posterior_log_odds_upward_vs_downward"], combined["posterior_log_odds_upward_vs_downward"])


if __name__ == "__main__":
    unittest.main()
