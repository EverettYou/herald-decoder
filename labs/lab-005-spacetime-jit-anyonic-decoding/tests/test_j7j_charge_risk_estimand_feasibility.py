"""Acceptance/replay checks for the two-branch estimand prerequisite."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7j_charge_risk_estimand_feasibility import CONTRACT, RESULT, run


class J7JTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_both_branches(self):
        result = self.result
        self.assertEqual(result["status"],
                         "same_flux_geometry_candidate_risk_not_identified")
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertTrue(result["loop_public_flux_zero"])
        self.assertEqual(result["baseline_public_action"], [0])
        self.assertEqual(result["loop_toggled_public_action"], [1, 30, 32, 34, 35])
        self.assertEqual(len(result["geometry_cells"]),
                         self.contract["budget"]["max_geometry_cells"])
        for i in (0, 2):
            left, right = result["geometry_cells"][i:i + 2]
            self.assertEqual(left["future_physical_red_edges_private"],
                             right["future_physical_red_edges_private"])
            self.assertEqual(left["final_public_flux"], right["final_public_flux"])
            self.assertNotEqual(left["final_red_edges_private"],
                                right["final_red_edges_private"])
        self.assertFalse(result["risk_branch"]["expected_logical_risk_identified"])
        self.assertEqual(len(result["risk_branch"]["missing_inputs"]), 3)
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertLessEqual(result["cpu_seconds"],
                             self.contract["budget"]["max_cpu_seconds"])

    def test_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
