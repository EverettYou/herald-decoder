"""Exact nonzero-future-fault and frozen-caller J7B gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7b_future_fault_next_first_and_caller_gate import RESULT, run


class J7BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_complete_future_fault_law(self):
        result = self.result
        self.assertEqual(result["status"], "exact_future_fault_matrix_completed")
        self.assertTrue(all(result["pinned_input_checks"].values()))
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertLess(result["cpu_seconds"], 60)
        physical = result["future_fault_fixed_path"]
        self.assertEqual(physical["positive_prefix_count"], 10)
        self.assertLessEqual(physical["usage"]["ordered_moment_terms"], 262144)
        self.assertLessEqual(physical["usage"]["positive_next_rows"], 128)
        self.assertEqual(physical["same_final_support_counterfactual_tv_by_first_charge"],
                         {"0": "0", "1": "0"})
        self.assertTrue(all(physical["binding_controls"].values()))
        self.assertEqual({a: sum(row["action"] == a for row in physical["rows"])
                          for a in ("defer", "partial", "matched")},
                         {"defer": 2, "partial": 4, "matched": 4})
        self.assertEqual({a: sum(len(row["next_rows"]) for row in physical["rows"]
                                 if row["action"] == a)
                          for a in ("defer", "partial", "matched")},
                         {"defer": 4, "partial": 8, "matched": 4})
        for row in physical["rows"]:
            self.assertEqual(sum((Fraction(next_row["conditional_probability"])
                                  for next_row in row["next_rows"]), Fraction()), 1)
            self.assertEqual({len(bits) for next_row in row["next_rows"]
                              for bits in next_row["next_first_public"].values()}, {24})
            self.assertEqual({next_row["conditional_probability"]
                              for next_row in row["next_rows"]},
                             {"1"} if row["action"] == "matched" else {"1/2"})
            for next_row in row["next_rows"]:
                self.assertEqual(next_row["public_completion"]["next_first_public"],
                                 next_row["next_first_public"])
                self.assertEqual(set(next_row["public_completion"]),
                                 {"trial_id", "first_prefix_digest", "action_digest",
                                  "second_prefix_digest", "future_key_digest",
                                  "next_first_public", "completion_digest"})
        self.assertEqual({row["next_variable_sites_private"][0]
                          for row in physical["rows"] if row["action"] == "defer"}, {0})
        self.assertEqual({row["next_variable_sites_private"][0]
                          for row in physical["rows"] if row["action"] == "partial"}, {1})
        self.assertTrue(all(not row["next_variable_sites_private"] for row in physical["rows"]
                            if row["action"] == "matched"))

    def test_caller_gap_and_replay(self):
        caller = self.result["frozen_caller_gate"]
        self.assertEqual(caller["status"], "not_integrated_stateful_future_first_callback")
        self.assertTrue(caller["first_observation_built_before_schedule_action"])
        self.assertTrue(caller["phenomenological_second_provider_invoked"])
        self.assertFalse(caller["action_bound_postselected_state_field"])
        self.assertFalse(caller["future_fault_state_callback_invoked"])
        self.assertFalse(caller["frozen_caller_modified"])
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
