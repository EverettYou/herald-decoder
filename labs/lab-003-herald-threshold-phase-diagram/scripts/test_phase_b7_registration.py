#!/usr/bin/env python3
"""Registration tests for Phase B7."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("select_and_register_phase_b7_endpoints.py")
SPEC = importlib.util.spec_from_file_location("phase_b7_registration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PhaseB7RegistrationTests(unittest.TestCase):
    def test_endpoint_design_covers_all_four_cells_with_fixed_budget(self) -> None:
        selection = MODULE.build_selection(MODULE.DEFAULT_MAP, MODULE.DEFAULT_ANALYSIS, MODULE.DEFAULT_DESIGN)
        self.assertEqual({(row["q"], row["p"]) for row in selection["jobs"]}, MODULE.EXPECTED)
        self.assertTrue(all(row["sizes"] == [5, 13] for row in selection["jobs"]))
        self.assertTrue(all(row["expected_decodes"] == 2000 for row in selection["jobs"]))
        self.assertEqual(selection["expected_new_decodes"], 8000)

    def test_new_seed_stream_has_no_prior_summary_overlap(self) -> None:
        audit = MODULE.seed_overlap_audit()
        self.assertEqual(audit["planned_seeds"], MODULE.NEW_SEEDS)
        self.assertEqual(audit["overlaps"], [])


if __name__ == "__main__":
    unittest.main()
