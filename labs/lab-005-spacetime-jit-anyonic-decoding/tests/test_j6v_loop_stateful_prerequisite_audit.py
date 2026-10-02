"""Acceptance and replay checks for the two registered prerequisite branches."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6v_loop_stateful_prerequisite_audit import RESULT, run


class J6VTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_pins_cycle_and_nonpromotion(self):
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        loop = self.result["simple_loop_geometry"]
        self.assertEqual(loop["minimum_cycle_length"], 6)
        self.assertEqual(len(set(loop["canonical_red_edge_ids_private"])), 6)
        self.assertEqual(loop["all_red_edges_deleted_once"], 36)
        self.assertTrue(loop["all_witness_vertex_degrees_two"])

    def test_stateful_interface_absent_and_counters_zero(self):
        interface = self.result["stateful_multiround_interface"]
        self.assertFalse(interface["action_feedback_kernel_present"])
        self.assertFalse(interface["three_block_projector_signature_present"])
        self.assertFalse(interface["builder_accepts_prior_action"])
        self.assertEqual(set(self.result["counters"].values()), {0})

    def test_exact_replay(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(current, saved)


if __name__ == "__main__":
    unittest.main()
