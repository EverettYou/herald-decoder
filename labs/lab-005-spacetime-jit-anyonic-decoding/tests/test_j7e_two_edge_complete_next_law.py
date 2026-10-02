"""Acceptance checks for the registered two-edge exact public-law matrix."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7e_two_edge_complete_next_law import CONTRACT, RESULT, run


class J7ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_complete_two_branch_exact_law(self):
        result = self.result
        matrix = result["matrix"]
        budget = self.contract["budget"]
        self.assertEqual(result["status"],
                         "exact_two_edge_complete_public_discriminator_closed")
        self.assertEqual(matrix["status"], "passed_two_branch_complete_public_law")
        self.assertTrue(all(result["pinned_input_checks"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertTrue(all(matrix["binding_controls"].values()))
        self.assertEqual(matrix["exact_total_variation_by_first_charge"],
                         {"0": "0", "1": "0"})
        self.assertLessEqual(result["cpu_seconds"], budget["max_cpu_seconds"])
        self.assertLessEqual(matrix["usage"]["ordered_moment_terms"],
                             budget["max_ordered_moment_terms"])
        self.assertLessEqual(matrix["usage"]["second_rows"],
                             budget["max_positive_second_rows"])
        self.assertLessEqual(matrix["usage"]["next_rows"],
                             budget["max_positive_next_rows"])
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertEqual(result["frozen_caller_gate"],
                         "unchanged_not_integrated_stateful_future_first_callback")
        for label, second_site in (("branch_a", 0), ("branch_b", 2)):
            branch = matrix[label]
            self.assertEqual(branch["positive_prefixes"], 4)
            self.assertEqual(sum((Fraction(row["prefix_mass"])
                                  for row in branch["rows"]), Fraction()), Fraction(1))
            for row in branch["rows"]:
                self.assertEqual(row["second_variable_sites_private"], [second_site])
                self.assertEqual(row["next_variable_sites_private"], [1])
                self.assertEqual(len(row["next_rows"]), 2)
                self.assertEqual({nxt["conditional_probability"] for nxt in row["next_rows"]},
                                 {"1/2"})
                for nxt in row["next_rows"]:
                    public = nxt["next_first_public"]
                    self.assertEqual(set(public), {"flux", "charge", "vacuum"})
                    self.assertEqual({len(bits) for bits in public.values()}, {24})
                    self.assertEqual(nxt["public_completion"]["next_first_public"], public)

    def test_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
