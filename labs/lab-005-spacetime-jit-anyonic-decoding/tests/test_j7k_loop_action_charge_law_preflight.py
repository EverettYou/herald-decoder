"""Exact acceptance/replay checks for loop-action charge-law preflight."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7k_loop_action_charge_law_preflight import CONTRACT, RESULT, run


class J7KTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_registered_preflight(self):
        result, budget = self.result, self.contract["budget"]
        self.assertEqual(result["status"], "loop_action_exact_preflight_closed")
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertEqual(result["topology_edge_bijection_count"], 36)
        self.assertTrue(result["loop_nonbranching_closed"])
        self.assertTrue(result["loop_homologically_trivial"])
        self.assertEqual(result["loop_winding_vectors"], [])
        self.assertEqual(result["loop_colour_parity_constraints"], 2)
        self.assertTrue(result["public_action_boundary_equal"])
        self.assertTrue(result["token_interface_can_whitelist_declared_actions"])
        self.assertEqual(result["frozen_jit_policy_emits_toggled_action"],
                         "not_established")
        self.assertEqual(result["first_public_mass"], "1/4")
        self.assertEqual([row["variable_second_sites_private"] for row
                          in result["action_rows"]], [[0], [0, 17, 20, 21, 22]])
        self.assertEqual([row["complete_second_law_site_cap_pass"] for row
                          in result["action_rows"]], [True, False])
        self.assertFalse(result["complete_second_law_site_cap_pass"])
        self.assertLessEqual(result["usage"]["ordered_moment_terms"],
                             budget["max_ordered_moment_terms"])
        self.assertLessEqual(result["cpu_seconds"], budget["max_cpu_seconds"])
        self.assertEqual(set(result["counters"].values()), {0})

    def test_exact_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
