from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_single_phase2_shard.py")
SPEC = importlib.util.spec_from_file_location("analyze_single_phase2_shard", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)


class SeedClusterBootstrapTests(unittest.TestCase):
    def test_uniform_size_advantage_has_no_directed_crossing(self) -> None:
        rows = []
        for size, errors in ((9, 2), (11, 0)):
            for seed in range(5):
                for p in (0.36, 0.37, 0.38):
                    rows.append({
                        "L": size,
                        "p": p,
                        "seed": seed,
                        "shots": 10,
                        "logical_errors": errors,
                    })
        result = analysis.bootstrap_adjacent_pair(
            rows,
            smaller=9,
            larger=11,
            replicates=200,
            seed=7,
        )
        self.assertEqual(result["larger_size_lower_at_every_p_fraction"], 1.0)
        self.assertEqual(result["one_or_more_directed_crossings_fraction"], 0.0)
        self.assertIsNone(result["directed_crossing_estimate_interval95"])


if __name__ == "__main__":
    unittest.main()
