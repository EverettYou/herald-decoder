#!/usr/bin/env python3
"""Unit checks for the lab-001 local herald decoder."""

from __future__ import annotations

import unittest

from local_decoder import (
    decode_local,
    lattice_edges,
    logical_boundary_edges,
    logical_parity,
    predecode_payload,
    predict_correction,
    predict_correction_by_rule,
    residual_state,
)


class LocalDecoderTest(unittest.TestCase):
    def test_square_rough_plaquettes_omit_the_open_outer_edge(self) -> None:
        edges = set(lattice_edges(3))
        self.assertNotIn(((0, 0), (0, 1)), edges)
        self.assertNotIn(((2, 0), (2, 1)), edges)
        self.assertIn(((1, 0), (1, 1)), edges)

    def test_predicts_herald_herald_bond(self) -> None:
        self.assertIn(((1, 0), (2, 0)), predict_correction(4, set(), {(1, 0), (2, 0)}))

    def test_connects_distance_two_heralds_along_shortest_path(self) -> None:
        predicted = predict_correction(5, set(), {(1, 0), (3, 0)})
        self.assertEqual(predicted, {((1, 0), (2, 0)), ((2, 0), (3, 0))})

    def test_distance_two_tie_break_is_deterministic(self) -> None:
        predicted = predict_correction(4, set(), {(1, 0), (2, 1)})
        self.assertEqual(predicted, {((1, 0), (1, 1)), ((1, 1), (2, 1))})

    def test_connects_two_syndromes_through_one_herald(self) -> None:
        center = (2, 2)
        correction, consumed = decode_local(5, {(1, 2), (3, 2)}, {center})
        self.assertEqual(correction, {((1, 2), center), (center, (3, 2))})
        self.assertEqual(consumed, {center})

    def test_rule_three_requires_exactly_two_neighboring_syndromes(self) -> None:
        center = (2, 2)
        predicted = predict_correction(5, {(1, 2), (3, 2), (2, 1)}, {center})
        self.assertEqual(predicted, set())

    def test_rule_breakdown_keeps_the_three_stages_separate(self) -> None:
        rules = predict_correction_by_rule(5, {(2, 2), (3, 1)}, {(1, 0), (2, 0), (3, 2)})
        self.assertEqual(
            list(rules),
            ["herald_distance_1", "syndrome_herald_syndrome", "herald_distance_2"],
        )
        self.assertEqual(rules["herald_distance_1"], {((1, 0), (2, 0))})
        self.assertEqual(rules["syndrome_herald_syndrome"], {((2, 2), (3, 2)), ((3, 1), (3, 2))})

    def test_distance_one_pairing_consumes_heralds_before_distance_two(self) -> None:
        correction, consumed = decode_local(6, set(), {(1, 0), (2, 0), (4, 0)})
        self.assertEqual(correction, {((1, 0), (2, 0))})
        self.assertEqual(consumed, {(1, 0), (2, 0)})

    def test_three_consecutive_heralds_update_in_parallel(self) -> None:
        correction, consumed = decode_local(5, set(), {(1, 0), (2, 0), (3, 0)})
        self.assertEqual(correction, {((1, 0), (2, 0)), ((2, 0), (3, 0))})
        self.assertEqual(consumed, {(1, 0), (2, 0), (3, 0)})

    def test_distance_two_parallel_update_allows_shared_herald(self) -> None:
        heralds = {(1, 0), (3, 0), (1, 2)}
        correction, consumed = decode_local(5, set(), heralds)
        self.assertEqual(
            correction,
            {
                ((1, 0), (2, 0)),
                ((2, 0), (3, 0)),
                ((1, 0), (1, 1)),
                ((1, 1), (1, 2)),
            },
        )
        self.assertEqual(consumed, heralds)

    def test_syndrome_herald_syndrome_consumes_center_before_distance_two(self) -> None:
        heralds = {(1, 1), (3, 1)}
        correction, consumed = decode_local(5, {(1, 0), (1, 2)}, heralds)
        self.assertEqual(correction, {((1, 0), (1, 1)), ((1, 1), (1, 2))})
        self.assertEqual(consumed, {(1, 1)})

    def test_artifact_payload_delegates_order_and_consumption_to_python(self) -> None:
        result = predecode_payload(
            {
                "vertex_count": 5,
                "edges": [[0, 1], [1, 2], [2, 3], [3, 4]],
                "detector_vertices": [0, 1, 2, 3, 4],
                "syndromes": [0, 2],
                "heralds": [1, 3],
            }
        )
        self.assertEqual(result["algorithm_source"], "scripts/local_decoder.py")
        self.assertEqual(
            result["rule_order"],
            ["herald_distance_1", "syndrome_herald_syndrome", "herald_distance_2"],
        )
        self.assertEqual(result["rules"]["syndrome_herald_syndrome"], [0, 1])
        self.assertEqual(result["rules"]["herald_distance_2"], [])
        self.assertEqual(result["correction_edge_indices"], [0, 1])
        self.assertEqual(result["consumed_herald_vertices"], [1])
        self.assertEqual(result["remaining_herald_vertices"], [3])

    def test_artifact_payload_rejects_non_detector_messages(self) -> None:
        with self.assertRaisesRegex(ValueError, "herald vertex"):
            predecode_payload(
                {
                    "vertex_count": 2,
                    "edges": [[0, 1]],
                    "detector_vertices": [0],
                    "syndromes": [],
                    "heralds": [1],
                }
            )

    def test_does_not_predict_other_local_pairs(self) -> None:
        predicted = predict_correction(6, {(1, 0)}, {(1, 0), (4, 0)})
        self.assertNotIn(((1, 0), (2, 0)), predicted)
        self.assertEqual(predicted, set())

    def test_matched_correction_removes_error_and_syndrome(self) -> None:
        edge = ((0, 0), (1, 0))
        residual, syndromes, heralds = residual_state(3, {edge}, {edge}, {(0, 0)})
        self.assertEqual(residual, set())
        self.assertEqual(syndromes, set())
        self.assertEqual(heralds, set())

    def test_false_correction_creates_residual_syndrome(self) -> None:
        edge = ((0, 0), (1, 0))
        residual, syndromes, _ = residual_state(3, set(), {edge}, set())
        self.assertEqual(residual, {edge})
        self.assertEqual(syndromes, {(0, 0), (1, 0)})

    def test_herald_remains_only_with_two_residual_bonds(self) -> None:
        center = (1, 1)
        two_bonds = {((0, 1), center), (center, (2, 1))}
        _, _, heralds = residual_state(3, two_bonds, set(), {center})
        self.assertEqual(heralds, {center})
        _, _, heralds = residual_state(3, {((0, 1), center)}, set(), {center})
        self.assertEqual(heralds, set())

    def test_square_logical_check_crosses_right_open_plaquette_edges(self) -> None:
        self.assertEqual(
            logical_boundary_edges(3),
            {
                ((1, 0), (2, 0)),
                ((1, 1), (2, 1)),
                ((1, 2), (2, 2)),
            },
        )

    def test_logical_error_is_the_open_plaquette_line_parity(self) -> None:
        boundary = logical_boundary_edges(4)
        first, second = sorted(boundary)[:2]
        self.assertEqual(logical_parity({first}, 4), 1)
        self.assertEqual(logical_parity({first, second}, 4), 0)


if __name__ == "__main__":
    unittest.main()
