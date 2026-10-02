"""Frozen exact no-new-fault state-handoff acceptance gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7a_postselected_next_first_limiting_fixtures import RESULT, run


class J7ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_two_branch_exact_limits(self):
        result = self.result
        self.assertEqual(result["status"], "passed_two_exact_no_fault_state_handoff_limits")
        self.assertTrue(all(result["pinned_input_checks"].values()))
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertLess(result["cpu_seconds"], 60)
        path = result["two_edge_path"]
        self.assertEqual(path["positive_case_count"], 10)
        self.assertEqual({a: sum(row["action"] == a for row in path["rows"])
                          for a in ("defer", "partial", "matched")},
                         {"defer": 2, "partial": 4, "matched": 4})
        self.assertEqual(len(path["binding_controls"]), 7)
        self.assertTrue(all(path["binding_controls"].values()))
        for row in path["rows"]:
            self.assertEqual(row["next_first_conditional_probability"], "1")
            expected = row["first_public"] if row["action"] == "defer" else row["second_public"]
            self.assertEqual(row["public_completion"]["next_first_public"], expected)
            self.assertEqual(set(row["public_completion"]["next_first_public"]),
                             {"flux", "charge", "vacuum"})
        for action in ("defer", "partial", "matched"):
            mass = sum((Fraction(row["first_probability"]) *
                        (Fraction(1) if row["second_conditional_probability"] is None
                         else Fraction(row["second_conditional_probability"]))
                       for row in path["rows"] if row["action"] == action), Fraction())
            self.assertEqual(mass, 1)
        loop = result["six_edge_loop"]
        self.assertEqual(loop["positive_prefixes"], 16)
        self.assertEqual(len(loop["rows"]), 16)
        for row in loop["rows"]:
            self.assertEqual(row["next_first_public"], row["second_public"])
            self.assertEqual(row["next_first_conditional_probability"], "1")
            self.assertEqual(row["varying_site_three_block_checked"], 17)

    def test_exact_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
