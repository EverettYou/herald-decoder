import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("summarize_slope_flow_stability.py")
SPEC = importlib.util.spec_from_file_location("slope_stability", SCRIPT)
slope_stability = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(slope_stability)


def cell(p, classification, stable, probability=0.8):
    return {
        "p": p,
        "beta": -0.1 if probability >= 0.5 else 0.1,
        "beta_interval90": [-0.2, 0.2],
        "probability_decodable": probability,
        "probability_undecodable": 1 - probability,
        "classification": classification,
        "leave_one_distance_out_sign_stable": stable,
    }


class SlopeFlowStabilityTests(unittest.TestCase):
    def test_partitions_gray_cells_by_distance_stability(self):
        payload = {
            "q_values": [0.0, 1.0],
            "p_values": [0.1, 0.2, 0.3],
            "analyses": [
                {"q": 0.0, "cells": [cell(0.1, "decodable", True), cell(0.2, "unresolved", True, 0.94), cell(0.3, "undecodable", True, 0.1)]},
                {"q": 1.0, "cells": [cell(0.1, "decodable", False), cell(0.2, "unresolved", False), cell(0.3, "undecodable", False, 0.1)]},
            ],
        }
        result = slope_stability.summarize(payload)
        self.assertEqual(result["unresolved_evidence_need"], {"seed_limited": 1, "distance_limited": 1})
        self.assertEqual(result["unresolved_frontier"]["between_both_resolved_phases"], 2)
        self.assertEqual(result["stable_observed_boundary_edges"], 0)
        self.assertEqual(result["targets"][0]["evidence_need"], "additional independent seed trajectories")

    def test_rejects_incomplete_grid(self):
        payload = {"q_values": [0.0], "p_values": [0.1, 0.2], "analyses": [{"q": 0.0, "cells": [cell(0.1, "unresolved", True)]}]}
        with self.assertRaises(ValueError):
            slope_stability.summarize(payload)


if __name__ == "__main__":
    unittest.main()
