"""Registered J6S exact-law and public-boundary acceptance checks."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6s_repeat_transfer_four_site import RESULT, run


class J6STests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()
        cls.cases = {case["action"]: case for case in cls.result["cases"]}

    def test_registered_inputs_and_no_sampling(self):
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(self.result["stochastic_histories"], 0)
        self.assertEqual(self.result["schedule_arm_evaluations"], 0)
        self.assertEqual(self.result["bootstrap_replicates"], 0)
        self.assertEqual(self.result["status"], "passed_exact_repeat_control_and_four_site_completion")

    def test_saved_exact_replay_excluding_elapsed_cpu(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)

    def test_repeat_is_not_new_site_transfer(self):
        one = self.cases["partial_one"]
        self.assertIn(2, one["unchanged_operator_repeat_sites_private"])
        self.assertNotIn(2, one["newly_eligible_sites_private"])
        self.assertEqual(one["newly_eligible_sites_private"], [0])
        self.assertTrue(all(row == {"0": "1/2"}
                            for row in one["new_site_conditional_plus_probabilities_private"]))
        self.assertEqual(one["first_dependence_full_public_law"], "dependent_on_first_record")

    def test_two_edge_first_independence(self):
        two = self.cases["partial_two"]
        self.assertIn(1, two["changed_operator_sites_private"])
        self.assertEqual(two["first_dependence_full_public_law"], "identical_across_first_records")

    def test_matched_four_site_completion_and_correlations(self):
        matched = self.cases["matched"]
        self.assertEqual(matched["second_random_sites_by_first_private"], [[0, 1, 2, 3]] * 4)
        self.assertEqual(len(matched["public_law_rows"]), 16)
        self.assertEqual(matched["first_dependence_full_public_law"], "identical_across_first_records")
        patterns = {tuple(row["second_public"]["charge"][:4])
                    for row in matched["public_law_rows"]}
        self.assertEqual(patterns, {(0, 0, 0, 0), (1, 0, 1, 0),
                                    (0, 1, 0, 1), (1, 1, 1, 1)})

    def test_public_records_and_exact_conditional_mass(self):
        for case in self.cases.values():
            by_first = {}
            for row in case["public_law_rows"]:
                for name in ("first_public", "second_public"):
                    record = row[name]
                    self.assertEqual(set(record), {"flux", "charge", "vacuum"})
                    self.assertTrue(all(len(record[key]) == 24 for key in record))
                key = tuple(row["first_public"]["charge"])
                by_first.setdefault(key, Fraction())
                by_first[key] += Fraction(row["second_conditional_probability"])
            self.assertEqual(len(by_first), 4)
            self.assertTrue(all(total == 1 for total in by_first.values()))


if __name__ == "__main__":
    unittest.main()
