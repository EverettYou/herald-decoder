"""Registered exact same-future total-action matrix acceptance checks."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7i_same_future_total_action_law import CONTRACT, RESULT, run


class J7ITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_registered_matrix_and_public_laws(self):
        result, budget = self.result, self.contract["budget"]
        self.assertEqual(result["status"], "exact_same_future_total_action_law_closed")
        self.assertEqual(result["first_mass"], "1/4")
        self.assertEqual(len(result["cells"]), 4)
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertTrue(all(result["binding_controls"].values()))
        self.assertTrue(result["j7g_diagonal_replay"])
        self.assertEqual([row["exact_full_public_total_variation"] for row
                          in result["same_future_action_comparisons"]], ["1", "1"])
        self.assertTrue(all(row["distinct_final_public_flux"] for row
                            in result["same_future_action_comparisons"]))
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertLessEqual(result["cpu_seconds"], budget["max_cpu_seconds"])
        for key, cap in (("ordered_moment_terms", "max_ordered_moment_terms"),
                         ("second_rows", "max_positive_second_rows"),
                         ("next_rows", "max_positive_next_rows")):
            self.assertLessEqual(result["usage"][key], budget[cap])
        for cell in result["cells"]:
            self.assertEqual(sum((Fraction(row["prefix_mass"])
                                  for row in cell["rows"]), Fraction()), Fraction(1, 4))
            for row in cell["rows"]:
                self.assertEqual(sum((Fraction(nxt["conditional_probability"])
                                      for nxt in row["next_rows"]), Fraction()), Fraction(1))
                for nxt in row["next_rows"]:
                    public = nxt["next_first_public"]
                    self.assertEqual(set(public), {"flux", "charge", "vacuum"})
                    self.assertEqual({len(bits) for bits in public.values()}, {24})
                    self.assertEqual(public["flux"], cell["final_public_flux"])
                    self.assertEqual(nxt["public_completion"]["next_first_public"], public)

    def test_exact_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
