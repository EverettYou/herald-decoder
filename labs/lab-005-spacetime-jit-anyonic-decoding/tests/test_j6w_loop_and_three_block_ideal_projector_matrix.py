"""Replay and exact-mass gates for the registered local projector matrix."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6w_loop_and_three_block_ideal_projector_matrix import RESULT, run


class J6WTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_pins_loop_cap_and_local_normalization(self):
        result = self.result
        self.assertTrue(all(result["pinned_input_checks"].values()))
        self.assertEqual(len(result["loop"]["all_random_first_sites_private"]), 6)
        self.assertEqual(len(result["loop"]["cases"]), 2)
        for case in result["loop"]["cases"]:
            self.assertEqual(case["full_public_law_status"], "censored_first_random_site_cap")
            by_first = {}
            for row in case["rows"]:
                key = tuple(row["first_local_charge"])
                by_first[key] = by_first.get(key, Fraction()) + Fraction(
                    row["second_conditional_probability"])
            self.assertEqual(len(by_first), 4)
            self.assertTrue(all(mass == 1 for mass in by_first.values()))

    def test_third_block_repeat_and_changed_action(self):
        by_action = {case["action"]: case for case in self.result["three_block"]["cases"]}
        self.assertEqual(set(by_action), {"repeat_no_second_action", "complete_with_edge_4"})
        for action, case in by_action.items():
            self.assertEqual(case["positive_first_second_count"], 4)
            by_prefix = {}
            for row in case["rows"]:
                key = (row["first_local_charge"], row["second_local_charge"])
                by_prefix[key] = by_prefix.get(key, Fraction()) + Fraction(
                    row["third_conditional_probability"])
                if Fraction(row["third_conditional_probability"]) > 0:
                    self.assertEqual(row["third_local_charge"],
                                     [row["second_local_charge"]] * len(case["third_local_sites_private"]))
            self.assertEqual(set(by_prefix.values()), {1})
            self.assertEqual(len(by_prefix), 4)

    def test_replay_and_zero_sampling(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)
        self.assertEqual(set(self.result["counters"].values()), {0})


if __name__ == "__main__":
    unittest.main()
