import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_phase_b2_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("phase_b2_analyze", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB2AnalyzerTests(unittest.TestCase):
    def test_distance_pooling_adds_new_sizes_without_duplication(self):
        pooled = module.pool_counts("distance_leverage", {7: (3, 1000), 9: (2, 1000), 11: (1, 1000)}, {5: (8, 1000), 13: (1, 1000)})
        self.assertEqual(sorted(pooled), [5, 7, 9, 11, 13])
        self.assertEqual(pooled[7], (3, 1000))

    def test_shot_pooling_adds_independent_counts(self):
        pooled = module.pool_counts("shot_limited_upward_frontier", {7: (400, 1000), 9: (450, 1000), 11: (480, 1000)}, {7: (390, 1000), 9: (460, 1000), 11: (500, 1000)})
        self.assertEqual(pooled, {7: (790, 2000), 9: (910, 2000), 11: (980, 2000)})

    def test_pooling_fails_closed_on_wrong_sizes(self):
        with self.assertRaises(ValueError):
            module.pool_counts("distance_leverage", {7: (1, 10)}, {5: (1, 10), 13: (1, 10)})


if __name__ == "__main__":
    unittest.main()
