"""Frozen exact J6Y two-branch acceptance and replay gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6y_conditional_site_nonrepeat_matrix import RESULT, run


class J6YTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_pins_and_zero_sampling(self):
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(set(self.result["counters"].values()), {0})
        self.assertLess(self.result["cpu_seconds"], 60)

    def test_path_conditional_selection_and_third_laws(self):
        path = self.result["three_edge_path"]
        self.assertEqual(path["positive_first_records"], 4)
        self.assertEqual(path["first_random_sites_private"], [1, 2])
        for row in path["cases"]:
            self.assertEqual(row["second_site_private"], 0)
            self.assertEqual(set(row["second_conditional_law"].values()), {"1/2"})
            self.assertEqual({case["third_site_private"] for case in row["third_action_cases"]},
                             {1, 3})
            for case in row["third_action_cases"]:
                self.assertTrue(case["third_operator_nonrepeated"])
                for third in case["rows"]:
                    self.assertEqual(set(third["third_conditional_law"].values()), {"1/2"})

    def test_loop_nonrepeated_site_is_deterministic_and_replay(self):
        loop = self.result["loop"]
        self.assertEqual(loop["positive_first_records"], 16)
        self.assertEqual(sum((Fraction(row["first_mass"]) for row in loop["cases"]), Fraction(0)), 1)
        for row in loop["cases"]:
            self.assertEqual(row["second_site_private"], 2)
            self.assertTrue(row["second_operator_nonrepeated"])
            self.assertEqual(row["second_conditional_law"], {"1": "1", "-1": "0"})
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)


if __name__ == "__main__":
    unittest.main()
