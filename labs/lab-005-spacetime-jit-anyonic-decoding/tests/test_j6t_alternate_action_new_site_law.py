"""J6T exact action-subset, public-boundary and negative-witness gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6t_alternate_action_new_site_law import RESULT, run


class J6TTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()
        cls.cases = {tuple(case["public_action_red_edge_ids"]): case
                     for case in cls.result["cases"]}

    def test_registered_matrix_and_pins(self):
        self.assertEqual(set(self.cases), {(3,), (4,), (0, 3), (4, 3)})
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(self.result["first_random_sites_private"], [1, 2])
        self.assertEqual(self.result["positive_first_record_count"], 4)
        self.assertEqual(self.result["status"], "passed_four_alternate_action_exact_matrix")

    def test_no_new_or_changed_site_first_dependence(self):
        for case in self.cases.values():
            self.assertEqual(case["new_only_projected_law_private"]["first_dependence"],
                             "identical_across_first_records")
            self.assertEqual(case["new_plus_changed_projected_law_private"]["first_dependence"],
                             "identical_across_first_records")
        self.assertEqual(self.cases[(3,)]["full_public_first_dependence"],
                         "dependent_on_first_record")
        self.assertIn(1, self.cases[(3,)]["repeat_sites_private"])
        self.assertEqual(self.cases[(3,)]["new_sites_private"], [3])

    def test_joint_new_site_support_not_just_marginals(self):
        both = self.cases[(0, 3)]["new_only_projected_law_private"]
        self.assertEqual(both["sites_private"], [0, 3])
        for distribution in both["distributions_by_first"]:
            support = distribution["second_charge_support"]
            self.assertEqual({tuple(row["bits"]) for row in support},
                             {(0, 0), (0, 1), (1, 0), (1, 1)})
            self.assertEqual({row["probability"] for row in support}, {"1/4"})

    def test_exact_normalization_and_public_arrays(self):
        for case in self.cases.values():
            totals = {}
            for row in case["public_law_rows"]:
                for field in ("first_public", "second_public"):
                    record = row[field]
                    self.assertEqual(set(record), {"flux", "charge", "vacuum"})
                    self.assertTrue(all(len(record[name]) == 24 for name in record))
                first = tuple(row["first_public"]["charge"])
                totals[first] = totals.get(first, Fraction()) + Fraction(
                    row["second_conditional_probability"])
            self.assertEqual(len(totals), 4)
            self.assertTrue(all(total == 1 for total in totals.values()))

    def test_replay_and_zero_sampling(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)
        self.assertEqual(self.result["stochastic_histories"], 0)
        self.assertEqual(self.result["schedule_arm_evaluations"], 0)
        self.assertEqual(self.result["bootstrap_replicates"], 0)


if __name__ == "__main__":
    unittest.main()
