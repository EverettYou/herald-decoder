"""Acceptance checks for the registered three-edge complete-public contrast."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7g_three_edge_matched_complete_next_law import CONTRACT, RESULT, run


class J7GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_complete_public_laws_and_exact_contrast(self):
        result = self.result
        matrix = result["matrix"]
        budget = self.contract["budget"]
        self.assertEqual(result["status"],
                         "exact_three_edge_one_first_complete_public_contrast_closed")
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertEqual(matrix["status"], "passed_two_branch_complete_public_law")
        self.assertEqual(matrix["first_mass"], "1/4")
        self.assertEqual(matrix["exact_total_variation"], "1/2")
        self.assertEqual(matrix["next_site_one_charge_probability"],
                         {"A": "1/2", "B": "0"})
        self.assertTrue(all(matrix["binding_controls"].values()))
        self.assertLessEqual(matrix["usage"]["ordered_moment_terms"],
                             budget["max_ordered_moment_terms"])
        self.assertLessEqual(matrix["usage"]["second_rows"],
                             budget["max_positive_second_rows"])
        self.assertLessEqual(matrix["usage"]["next_rows"],
                             budget["max_positive_next_rows"])
        self.assertLessEqual(result["cpu_seconds"], budget["max_cpu_seconds"])
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertEqual((matrix["branch_a"]["positive_prefixes"],
                          matrix["branch_b"]["positive_prefixes"]), (2, 1))
        for label in ("branch_a", "branch_b"):
            branch = matrix[label]
            self.assertEqual(sum((Fraction(row["prefix_mass"])
                                  for row in branch["rows"]), Fraction()), Fraction(1, 4))
            for row in branch["rows"]:
                self.assertEqual(sum((Fraction(n["conditional_probability"])
                                      for n in row["next_rows"]), Fraction()), Fraction(1))
                for next_row in row["next_rows"]:
                    public = next_row["next_first_public"]
                    self.assertEqual(set(public), {"flux", "charge", "vacuum"})
                    self.assertEqual({len(bits) for bits in public.values()}, {24})
                    self.assertEqual(next_row["public_completion"]["next_first_public"],
                                     public)

    def test_deterministic_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
