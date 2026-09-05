import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("analyze_phase4_cohort_heterogeneity.py")
SPEC = importlib.util.spec_from_file_location("heterogeneity", SCRIPT)
heterogeneity = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(heterogeneity)


def payload(seeds, l11_errors, l13_errors):
    rows = []
    for size, errors in ((11, l11_errors), (13, l13_errors)):
        for seed, logical_errors in zip(seeds, errors):
            rows.append(
                {
                    "L": size,
                    "p": 0.4,
                    "seed": seed,
                    "shots": 100,
                    "logical_errors": logical_errors,
                }
            )
    return {
        "q": 0.95,
        "seeds": seeds,
        "shots_per_seed": 100,
        "per_seed": rows,
        "source_hashes": {"decoder": "same"},
        "runtime": {"python": "same"},
    }


class CohortHeterogeneityTests(unittest.TestCase):
    def test_resolves_positive_size_trend_shift(self):
        old = payload([1, 2, 3, 4], [20, 20, 20, 20], [20, 20, 20, 20])
        new = payload([5, 6, 7, 8], [40, 40, 40, 40], [20, 20, 20, 20])
        result = heterogeneity.analyze_cohort_pair(
            old, new, common_p=(0.4,), replicates=500, seed=9
        )
        self.assertEqual(result["classification"], "resolved_between_cohort_heterogeneity")
        self.assertEqual(result["cells"][0]["classification"], "confirmation_more_decodable")
        self.assertTrue(np.allclose(result["cells"][0]["difference_interval90"], [0.2, 0.2]))

    def test_rejects_overlapping_seed_streams(self):
        old = payload([1, 2], [20, 20], [20, 20])
        new = payload([2, 3], [20, 20], [20, 20])
        with self.assertRaises(heterogeneity.ValidationError):
            heterogeneity.analyze_cohort_pair(
                old, new, common_p=(0.4,), replicates=100, seed=9
            )


if __name__ == "__main__":
    unittest.main()
