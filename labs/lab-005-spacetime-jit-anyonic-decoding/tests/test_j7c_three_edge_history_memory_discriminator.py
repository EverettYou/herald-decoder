"""Exact three-edge matched-final-support history-memory acceptance gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j7c_three_edge_history_memory_discriminator import RESULT, run


class J7CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_two_complete_branch_laws(self):
        result = self.result
        self.assertEqual(result["status"], "exact_three_edge_history_discriminator_complete")
        self.assertTrue(all(result["pinned_input_checks"].values()))
        self.assertEqual(set(result["counters"].values()), {0})
        self.assertLess(result["cpu_seconds"], 60)
        matrix = result["matrix"]
        self.assertEqual(matrix["status"], "passed_complete_two_branch_history_discriminator")
        self.assertEqual(matrix["exact_total_variation_by_first_charge"],
                         {"00": "0", "10": "0", "01": "0", "11": "0"})
        self.assertTrue(all(matrix["binding_controls"].values()))
        self.assertLessEqual(matrix["usage"]["ordered_moment_terms"], 262144)
        self.assertLessEqual(matrix["usage"]["positive_next_rows"], 128)
        self.assertEqual(matrix["branch_a"]["positive_prior_prefixes"], 8)
        self.assertEqual(matrix["branch_b"]["positive_prior_prefixes"], 16)
        self.assertEqual(matrix["branch_a"]["next_flux"], matrix["branch_b"]["next_flux"])
        for branch_name in ("branch_a", "branch_b"):
            branch = matrix[branch_name]
            self.assertEqual(sum((Fraction(row["prefix_mass"]) for row in branch["rows"]),
                                 Fraction()), 1)
            for row in branch["rows"]:
                self.assertEqual(sum((Fraction(nxt["conditional_probability"])
                                      for nxt in row["next_rows"]), Fraction()), 1)
                for nxt in row["next_rows"]:
                    record = nxt["next_first_public"]
                    self.assertEqual(set(record), {"flux", "charge", "vacuum"})
                    self.assertEqual({len(bits) for bits in record.values()}, {24})
                    self.assertEqual(nxt["public_completion"]["next_first_public"], record)
        for row in matrix["branch_a"]["rows"]:
            self.assertEqual(len(row["next_rows"]), 2)
            self.assertEqual({nxt["conditional_probability"] for nxt in row["next_rows"]},
                             {"1/2"})
            self.assertEqual({nxt["next_first_public"]["charge"][0]
                              for nxt in row["next_rows"]}, {row["second_public"]["charge"][0]})
        for row in matrix["branch_b"]["rows"]:
            self.assertEqual(len(row["next_rows"]), 1)
            self.assertEqual(row["next_rows"][0]["next_first_public"], row["second_public"])

    def test_replay_and_frozen_caller(self):
        self.assertEqual(self.result["frozen_caller_gate"],
                         "unchanged_not_integrated_stateful_future_first_callback")
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
