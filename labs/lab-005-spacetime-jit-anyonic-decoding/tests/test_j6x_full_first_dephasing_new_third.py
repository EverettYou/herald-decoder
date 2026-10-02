"""Frozen acceptance and replay checks for the two J6X diagnostic branches."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6x_full_first_dephasing_new_third import RESULT, run


class J6XTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_pins_and_independent_censor(self):
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(self.result["three_edge_new_third"]["status"],
                         "censored_second_structure")
        self.assertEqual(self.result["three_edge_new_third"]["second_random_sites_private"], [2])
        self.assertEqual(self.result["loop_full_first_dephasing"]["status"],
                         "exact_full_first_one_site_second_law")

    def test_full_first_loop_and_repeat_boundary(self):
        loop = self.result["loop_full_first_dephasing"]
        self.assertEqual(len(loop["first_random_sites_private"]), 6)
        self.assertEqual(loop["positive_full_first_records"], 16)
        self.assertTrue(loop["second_operator_repeats_first_site"])
        by_first = {}
        for row in loop["rows"]:
            key = tuple(row["full_first_variable_bits_private"])
            by_first[key] = by_first.get(key, Fraction()) + Fraction(
                row["second_conditional_probability"])
            if Fraction(row["second_conditional_probability"]) > 0:
                self.assertEqual(row["second_local_bit_private"], key[2])
        self.assertEqual(len(by_first), 16)
        self.assertEqual(set(by_first.values()), {1})
        self.assertEqual({row["difference_full_minus_selected"]
                          for row in loop["coarse_contrast"]}, {"0"})

    def test_replay_and_zero_sampling(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)
        self.assertEqual(set(current["counters"].values()), {0})


if __name__ == "__main__":
    unittest.main()
