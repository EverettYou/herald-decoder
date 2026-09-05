#!/usr/bin/env python3
"""Unit checks for the Lab 001 PyMatching decoder."""

from __future__ import annotations

import unittest

from mwpm_decoder import mwpm_decode


class MwpmDecodeTest(unittest.TestCase):
    @staticmethod
    def square_open_boundary_payload(size: int, syndromes: list[int]) -> dict:
        edges = []
        for y in range(size):
            for x in range(size):
                vertex = y * size + x
                if x + 1 < size:
                    edges.append([vertex, vertex + 1])
                if y + 1 < size and 0 < x < size - 1:
                    edges.append([vertex, vertex + size])
        return {
            "vertex_count": size * size,
            "edges": edges,
            "detector_vertices": [y * size + x for y in range(size) for x in range(1, size - 1)],
            "boundary_vertices": [y * size + x for y in range(size) for x in (0, size - 1)],
            "syndromes": syndromes,
        }

    def test_line_graph_uses_minimum_weight_pairs(self) -> None:
        result = mwpm_decode({"vertex_count": 4, "edges": [[0, 1], [1, 2], [2, 3]], "syndromes": [0, 1, 2, 3]})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["matching"], [[0, 1], [2, 3]])
        self.assertEqual(result["correction_edge_indices"], [0, 2])
        self.assertEqual(result["total_weight"], 2)

    def test_single_pair_returns_shortest_correction_path(self) -> None:
        result = mwpm_decode({"vertex_count": 3, "edges": [[0, 1], [1, 2]], "syndromes": [0, 2]})
        self.assertEqual(result["correction_edge_indices"], [0, 1])

    def test_odd_syndrome_count_is_reported_without_fake_matching(self) -> None:
        result = mwpm_decode({"vertex_count": 3, "edges": [[0, 1], [1, 2]], "syndromes": [0, 1, 2]})
        self.assertEqual(result["status"], "odd_syndrome_count")
        self.assertEqual(result["correction_edge_indices"], [])

    def test_singleton_check_matrix_column_is_a_virtual_boundary_edge(self) -> None:
        result = mwpm_decode({
            "vertex_count": 4,
            "edges": [[0, 1], [1, 2], [2, 3]],
            "detector_vertices": [1, 2],
            "boundary_vertices": [0, 3],
            "syndromes": [1],
        })
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["correction_edge_indices"], [0])
        self.assertEqual(result["matching"], [[1, None]])
        self.assertEqual(result["boundary_edge_indices"], [0, 2])

    def test_open_rough_edge_is_rejected_instead_of_becoming_a_zero_column(self) -> None:
        with self.assertRaisesRegex(ValueError, "no incident detector"):
            mwpm_decode({
                "vertex_count": 3,
                "edges": [[0, 1], [1, 2], [0, 2]],
                "detector_vertices": [1],
                "boundary_vertices": [0, 2],
                "syndromes": [1],
            })

    def test_missing_detector_is_not_silently_treated_as_a_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit boundary vertex"):
            mwpm_decode({
                "vertex_count": 3,
                "edges": [[0, 1], [1, 2]],
                "detector_vertices": [1],
                "boundary_vertices": [0],
                "syndromes": [1],
            })

    def test_two_rough_boundaries_give_valid_singleton_columns(self) -> None:
        result = mwpm_decode({
            "vertex_count": 3,
            "edges": [[0, 1], [1, 2]],
            "detector_vertices": [1],
            "boundary_vertices": [0, 2],
            "syndromes": [1],
        })
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["correction_edge_indices"]), 1)
        self.assertEqual(result["boundary_edge_indices"], [0, 1])
        self.assertEqual(result["matching"], [[1, None]])

    def test_square_boundary_check_matches_to_a_physical_rough_edge(self) -> None:
        size = 5
        syndrome = 2 * size + 1
        payload = self.square_open_boundary_payload(size, [syndrome])
        result = mwpm_decode(payload)
        correction_edges = [payload["edges"][index] for index in result["correction_edge_indices"]]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["matching"], [[syndrome, None]])
        self.assertEqual(correction_edges, [[2 * size, syndrome]])
        self.assertEqual(len(result["boundary_edge_indices"]), 2 * size)


if __name__ == "__main__":
    unittest.main()
