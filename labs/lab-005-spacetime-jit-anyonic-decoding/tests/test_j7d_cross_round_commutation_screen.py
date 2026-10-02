"""Acceptance gates for the bounded cross-round structural screen."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6m_periodic_operator_ground_orbit import parity, qphase
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j7d_cross_round_commutation_screen import (
    CONTRACT, INPUTS, RESULT, cross_vacuum_anticommutes, run,
)


class J7DTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.result = run()

    def test_complete_registered_structural_matrix(self):
        result, budget = self.result, self.contract["budget"]
        self.assertEqual(result["status"], "finite_structural_opening_found")
        self.assertTrue(all(result["pinned_input_checks_before"].values()))
        self.assertTrue(all(result["pinned_input_checks_after"].values()))
        self.assertEqual(set(result["fixture_counts"]), {
            "two_edge_path", "three_edge_chain", "four_edge_path",
            "four_edge_branch", "six_edge_loop"})
        self.assertEqual(result["counts"]["histories"], 628)
        self.assertEqual(sum(item["histories"] for item in result["fixture_counts"].values()),
                         result["counts"]["histories"])
        self.assertEqual(sum(item["matched_pairs"] for item in result["fixture_counts"].values()),
                         result["counts"]["matched_pairs"])
        self.assertEqual(sum(item["structurally_open_matched_pairs"]
                             for item in result["fixture_counts"].values()),
                         result["counts"]["structurally_open_matched_pairs"])
        self.assertGreater(result["counts"]["same_sector_pairs"], 0)
        self.assertGreater(result["counts"]["cross_round_pairs"], 0)
        self.assertLessEqual(result["counts"]["histories"], budget["max_histories"])
        self.assertLessEqual(result["counts"]["matched_pairs"], budget["max_matched_pairs"])
        self.assertLessEqual(result["counts"]["cross_round_pairs"],
                             budget["max_pair_operator_checks"])
        self.assertLessEqual(result["cpu_seconds"], budget["max_cpu_seconds"])
        self.assertEqual(result["j7c_history_coverage"], {
            "branch_a": True, "branch_b": True,
            "prior_exact_total_variation_all_four_first": "0"})
        self.assertEqual((result["stochastic_histories"], result["schedule_arm_evaluations"],
                          result["bootstrap_replicates"]), (0, 0, 0))
        self.assertEqual(result["ranked_open_pairs_first_32"][0]["fixture"],
                         "two_edge_path")

    def test_replay_and_inference_boundary(self):
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)
        self.assertIn("does not prove nonzero Born-law TV", current["inference_boundary"])

    def test_witness_commutator_matches_direct_operator_action(self):
        embedding = json.loads(INPUTS["j6l_result"].read_text())
        state = json.loads(INPUTS["j6m_result"].read_text())
        sites = {int(star["center"].split(":")[1]): star
                 for star in embedding["star_supports"]
                 if star["center_color"] in ("blue", "green")}
        red = {qubit["lab004_red_edge_id"]: qubit
               for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
        residual, _ = red_boundary(red, [4])
        final, _ = red_boundary(red, [0, 4])
        left = conjugated_star(sites[0], residual)
        right = conjugated_star(sites[1], final)
        self.assertTrue(cross_vacuum_anticommutes(left, right))
        pair = next(row for row in state["pair_rows"]
                    if {row["left"], row["right"]} ==
                    {sites[0]["center"], sites[1]["center"]})
        base_mask = int(pair["commutator_z_mask_hex"], 16)

        def phase(op, star, basis):
            sign, zmask, flip = op
            ring = [tuple(pair) for pair in star["six_cz_pairs"]]
            return (int(sign == -1) ^ qphase(ring, basis) ^
                    parity(zmask & (basis ^ flip)))

        for basis in [0, *[1 << bit for bit in range(108)]]:
            left_then_right = (phase(right, sites[1], basis) ^
                               phase(left, sites[0], basis ^ right[2]))
            right_then_left = (phase(left, sites[0], basis) ^
                               phase(right, sites[1], basis ^ left[2]))
            self.assertEqual(left_then_right ^ right_then_left,
                             1 ^ parity(base_mask & basis))


if __name__ == "__main__":
    unittest.main()
