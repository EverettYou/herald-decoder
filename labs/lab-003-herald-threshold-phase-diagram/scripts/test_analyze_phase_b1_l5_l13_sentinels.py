import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_phase_b1_l5_l13_sentinels.py")
SPEC = importlib.util.spec_from_file_location("phase_b1_analyze", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB1AnalyzerTests(unittest.TestCase):
    def test_exchangeable_counts_are_direction_symmetric(self):
        posterior = module.posterior_order_qmc(np.full(5, 50), np.full(5, 100), base2_power=12)
        self.assertAlmostEqual(posterior["posterior_probability_decreasing"], posterior["posterior_probability_increasing"], delta=0.001)
        self.assertAlmostEqual(posterior["posterior_log_odds_increasing_vs_decreasing"], 0.0, delta=0.08)
        self.assertGreater(posterior["posterior_probability_other_order"], 0.97)
        self.assertGreater(posterior["qmc_ordering_entropy_bits"], 6.8)

    def test_clear_decrease_is_decodable(self):
        posterior = module.posterior_order_qmc(np.array([800, 600, 400, 200, 50]), np.full(5, 1000), base2_power=11)
        self.assertGreater(posterior["posterior_probability_decreasing"], 0.999)
        self.assertEqual(module.classify(posterior), "decodable")
        self.assertIsNone(posterior["posterior_log_odds_increasing_vs_decreasing"])
        self.assertEqual(posterior["posterior_log_odds_censoring"]["relation"], "less_than")
        self.assertEqual(posterior["qmc_top_orderings"][0]["indices_low_to_high"], [4, 3, 2, 1, 0])

    def test_clear_increase_is_undecodable(self):
        posterior = module.posterior_order_qmc(np.array([50, 200, 400, 600, 800]), np.full(5, 1000), base2_power=11)
        self.assertGreater(posterior["posterior_probability_increasing"], 0.999)
        self.assertEqual(module.classify(posterior), "undecodable")
        self.assertIsNone(posterior["posterior_log_odds_increasing_vs_decreasing"])
        self.assertEqual(posterior["posterior_log_odds_censoring"]["relation"], "greater_than")
        self.assertEqual(posterior["qmc_top_orderings"][0]["indices_low_to_high"], [0, 1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
