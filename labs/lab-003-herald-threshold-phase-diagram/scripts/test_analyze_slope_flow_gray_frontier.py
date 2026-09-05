import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_slope_flow_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("gray_frontier_analysis", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)


class GrayFrontierAnalysisTests(unittest.TestCase):
    def test_preliminary_classification(self):
        self.assertEqual(analysis.preliminary_classification(np.asarray([-0.4, -0.1]), 0.98, 0.02), "decodable")
        self.assertEqual(analysis.preliminary_classification(np.asarray([0.1, 0.4]), 0.02, 0.98), "undecodable")
        self.assertEqual(analysis.preliminary_classification(np.asarray([-0.1, 0.2]), 0.70, 0.30), "unresolved")

    def test_gates_block_unstable_or_pair_disagreement(self):
        self.assertEqual(analysis.gated_classification("decodable", loo_stable=True, pair_agrees=None), "decodable")
        self.assertEqual(analysis.gated_classification("undecodable", loo_stable=False, pair_agrees=True), "unresolved")
        self.assertEqual(analysis.gated_classification("decodable", loo_stable=True, pair_agrees=False), "unresolved")


if __name__ == "__main__":
    unittest.main()
