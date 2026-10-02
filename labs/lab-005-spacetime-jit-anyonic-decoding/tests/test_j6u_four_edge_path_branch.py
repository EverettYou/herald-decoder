"""Acceptance and exact replay tests for the registered four-edge topology matrix."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6u_four_edge_path_branch import RESULT, run


class J6UTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()
        cls.cases = {(case["topology"], case["action"]): case
                     for case in cls.result["cases"]}

    def test_pins_and_eight_registered_branches(self):
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(self.result["status"], "passed_two_topology_exact_matrix")
        self.assertEqual(len(self.cases), 8)
        self.assertTrue(all(case["status"] == "exact_full_public_law"
                            for case in self.cases.values()))

    def test_path_and_branch_have_distinct_first_record_support(self):
        path = self.cases[("four_edge_nonbranching_path", "matched_all_four")]
        branch = self.cases[("four_edge_branched_tree", "matched_all_four")]
        self.assertEqual(path["first_random_sites_private"], [1, 2, 3])
        self.assertEqual(path["positive_first_record_count"], 8)
        self.assertEqual(branch["first_random_sites_private"], [1])
        self.assertEqual(branch["positive_first_record_count"], 2)

    def test_novel_joint_records_do_not_depend_on_first(self):
        for case in self.cases.values():
            new = case["new_only_projected_law_private"]
            novel = case["new_plus_changed_projected_law_private"]
            self.assertIn(new["first_dependence"],
                          {"identical_across_first_records", "no_sites_vacuous"})
            self.assertIn(novel["first_dependence"],
                          {"identical_across_first_records", "no_sites_vacuous"})
        matched_path = self.cases[("four_edge_nonbranching_path", "matched_all_four")]
        self.assertEqual(matched_path["new_sites_private"], [0, 4])
        self.assertEqual(matched_path["changed_sites_private"], [1, 2, 3])
        self.assertEqual(matched_path["new_plus_changed_projected_law_private"]["first_dependence"],
                         "identical_across_first_records")

    def test_full_dependence_is_repeated_operator_only(self):
        dependent = {key for key, case in self.cases.items()
                     if case["full_public_first_dependence"] == "dependent_on_first_record"}
        self.assertEqual(dependent, {
            ("four_edge_nonbranching_path", "correct_edge_0"),
            ("four_edge_nonbranching_path", "correct_edge_3"),
            ("four_edge_branched_tree", "correct_edge_3"),
        })
        self.assertTrue(all(self.cases[key]["repeat_sites_private"] for key in dependent))

    def test_exact_mass_and_public_boundary(self):
        for case in self.cases.values():
            totals = {}
            for row in case["public_law_rows"]:
                for field in ("first_public", "second_public"):
                    record = row[field]
                    self.assertEqual(set(record), {"flux", "charge", "vacuum"})
                    self.assertTrue(all(len(record[key]) == 24 for key in record))
                first = tuple(row["first_public"]["charge"])
                totals[first] = totals.get(first, Fraction()) + Fraction(
                    row["second_conditional_probability"])
            self.assertEqual(len(totals), case["positive_first_record_count"])
            self.assertTrue(all(total == 1 for total in totals.values()))

    def test_exact_replay_and_no_sampling(self):
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
