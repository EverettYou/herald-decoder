"""Acceptance checks for the registered red-X action/future algebra audit."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7h_action_future_identifiability_audit import CONTRACT, RESULT, run


class J7HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_exact_identifiability_matrix(self):
        result = self.result
        self.assertEqual(result["status"],
                         "additive_red_x_action_future_identifiability_boundary_passed")
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertEqual(result["counts"], {
            "primary_cells": 4, "exhaustive_control_cells": 32,
            "distinct_action_same_future_pair_checks": 112})
        self.assertEqual([row["final_red_edges_private"]
                          for row in result["primary_matrix"]],
                         [[0, 3, 4], [3], [3], [0, 3, 4]])
        self.assertEqual({result[key] for key in
                         ("stochastic_histories", "schedule_arm_evaluations",
                          "bootstrap_replicates")}, {0})
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
