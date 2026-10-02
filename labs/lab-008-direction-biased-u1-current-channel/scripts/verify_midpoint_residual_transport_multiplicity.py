#!/usr/bin/env python3
"""Replay the analytic row-preimage counterfamily on the existing L3/L4 controls."""
from __future__ import annotations

import json

from run_residual_directed_sector_transport import (
    bits_of,
    charge_matrix,
    selected_path,
    square_graph,
)


def verify(size: int) -> dict:
    graph = square_graph(size)
    left = tuple(v for v in graph.boundary_vertices if graph.vertices[v].boundary_side == "left")
    right = tuple(v for v in graph.boundary_vertices if graph.vertices[v].boundary_side == "right")
    horizontal = {
        edge for edge, (a, b) in enumerate(graph.edges)
        if graph.vertices[a].y == graph.vertices[b].y
    }
    target = sum(1 << edge for edge in horizontal)
    charge = charge_matrix(graph)
    target_charge = tuple(int(value) for value in charge @ bits_of(target, len(graph.edges)))
    construction_failures = selector_failures = image_failures = 0
    charge_failures = logical_failures = 0
    preimages = []

    for row in range(size):
        path = tuple(
            edge for edge, (a, b) in enumerate(graph.edges)
            if graph.vertices[a].y == row and graph.vertices[b].y == row
        )
        construction_failures += len(path) != size - 1
        path_mask = sum(1 << edge for edge in path)
        preimage = target ^ path_mask
        chosen = selected_path(graph, preimage, left, right)
        selector_failures += chosen is None or chosen[0] != path or chosen[1] != 0
        image = preimage ^ sum(1 << edge for edge in chosen[0]) if chosen else None
        image_failures += image != target
        if image is not None:
            image_charge = tuple(int(value) for value in charge @ bits_of(image, len(graph.edges)))
            preimage_charge = tuple(int(value) for value in charge @ bits_of(preimage, len(graph.edges)))
            charge_failures += preimage_charge != target_charge or image_charge != target_charge
            logical_failures += (
                ((preimage & sum(1 << edge for edge in graph.logical_edges)).bit_count()
                 ^ (image & sum(1 << edge for edge in graph.logical_edges)).bit_count()) & 1
            ) != 1
        preimages.append(preimage)

    return {
        "L": size,
        "target": target,
        "candidate_preimages": len(preimages),
        "distinct_preimages": len(set(preimages)),
        "inverse_multiplicity_lower_bound": size,
        "construction_failures": construction_failures,
        "selector_failures": selector_failures,
        "common_image_failures": image_failures,
        "charge_failures": charge_failures,
        "logical_flip_failures": logical_failures,
    }


if __name__ == "__main__":
    rows = [verify(3), verify(4)]
    assert all(
        row[key] == 0
        for row in rows
        for key in (
            "construction_failures",
            "selector_failures",
            "common_image_failures",
            "charge_failures",
            "logical_flip_failures",
        )
    )
    print(json.dumps({
        "id": "lab008-midpoint-residual-transport-multiplicity-2026-09-22",
        "status": "verified",
        "new_sizes": 0,
        "rows": rows,
    }, indent=2, sort_keys=True))
