import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_slope_flow_phase_map.py")
SPEC = importlib.util.spec_from_file_location("slope_flow", SCRIPT)
slope_flow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(slope_flow)


class SlopeFlowTests(unittest.TestCase):
    def test_logit_slope_signs(self):
        sizes = np.log(np.asarray([7, 9, 11], dtype=float))
        totals = np.full((3, 3), 10000.0)
        successes = np.asarray(
            [
                [1800, 900, 450],
                [450, 900, 1800],
                [900, 900, 900],
            ],
            dtype=float,
        )
        beta = slope_flow.fit_logit_slopes(successes, totals, sizes)
        self.assertLess(beta[0], 0)
        self.assertGreater(beta[1], 0)
        self.assertAlmostEqual(beta[2], 0.0, places=10)

    def test_requires_two_distances(self):
        with self.assertRaises(ValueError):
            slope_flow.fit_logit_slopes(
                np.asarray([[1.0]]),
                np.asarray([[10.0]]),
                np.log(np.asarray([7.0])),
            )


if __name__ == "__main__":
    unittest.main()
