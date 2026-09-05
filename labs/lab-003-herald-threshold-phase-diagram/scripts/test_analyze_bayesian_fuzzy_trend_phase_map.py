import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_bayesian_fuzzy_trend_phase_map.py")
SPEC = importlib.util.spec_from_file_location("fuzzy_phase_map", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class BayesianFuzzyTrendPhaseMapTests(unittest.TestCase):
    def test_gray_with_resolved_curvature_routes_to_distance(self):
        trend = {"classification": "unresolved", "sensitivity": {"posterior_probability_midpoint_above_endpoint_chord": 0.97, "posterior_probability_midpoint_below_endpoint_chord": 0.03}}
        self.assertEqual(module.gray_measurement_route(trend), "add_L5_L13_distance_leverage")

    def test_gray_without_resolved_curvature_routes_to_shots(self):
        trend = {"classification": "unresolved", "sensitivity": {"posterior_probability_midpoint_above_endpoint_chord": 0.70, "posterior_probability_midpoint_below_endpoint_chord": 0.30}}
        self.assertEqual(module.gray_measurement_route(trend), "more_shots_existing_L7_L9_L11_first")

    def test_resolved_cell_has_no_gray_route(self):
        trend = {"classification": "decodable", "sensitivity": {"posterior_probability_midpoint_above_endpoint_chord": 0.99, "posterior_probability_midpoint_below_endpoint_chord": 0.01}}
        self.assertIsNone(module.gray_measurement_route(trend))


if __name__ == "__main__":
    unittest.main()
