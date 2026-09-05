import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_phase_b1_bayesian_fuzzy_trend.py")
SPEC = importlib.util.spec_from_file_location("phase_b1_fuzzy", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB1FuzzyTrendTests(unittest.TestCase):
    def test_exchangeable_counts_are_unresolved(self):
        result = module.posterior_fuzzy_linear_trend(
            np.full(5, 50), np.full(5, 100), np.array([5, 7, 9, 11, 13]), base2_power=11
        )
        self.assertAlmostEqual(result["posterior_probability_upward_trend"], 0.5, delta=0.01)
        self.assertEqual(result["classification"], "unresolved")

    def test_noisy_overall_upward_trend(self):
        result = module.posterior_fuzzy_linear_trend(
            np.array([300, 410, 390, 520, 490]), np.full(5, 1000), np.array([5, 7, 9, 11, 13]), base2_power=11
        )
        self.assertGreater(result["posterior_probability_upward_trend"], 0.999)
        self.assertEqual(result["classification"], "undecodable")

    def test_noisy_overall_downward_trend(self):
        result = module.posterior_fuzzy_linear_trend(
            np.array([700, 590, 610, 480, 510]), np.full(5, 1000), np.array([5, 7, 9, 11, 13]), base2_power=11
        )
        self.assertGreater(result["posterior_probability_downward_trend"], 0.999)
        self.assertEqual(result["classification"], "decodable")


if __name__ == "__main__":
    unittest.main()
