#!/usr/bin/env python3
"""Exhaustive residual-directed sector transport on canonical q=1 squares."""
from __future__ import annotations

from collections import Counter, defaultdict
import heapq
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from herald_decoder.lattice_model import square_graph


def bits_of(state, edges):
    return np.fromiter(((state >> edge) & 1 for edge in range(edges)), dtype=np.int8, count=edges)


def charge_matrix(graph):
    rows = {vertex: row for row, vertex in enumerate(graph.detector_vertices)}
    matrix = np.zeros((len(rows), len(graph.edges)), dtype=np.int8)
    for edge, (tail, head) in enumerate(graph.edges):
        if tail in rows:
            matrix[rows[tail], edge] -= 1
        if head in rows:
            matrix[rows[head], edge] += 1
    return matrix


def best_directional_path(graph, state, sources, targets):
    adjacency = [[] for _ in graph.vertices]
    for edge, (tail, head) in enumerate(graph.edges):
        if (state >> edge) & 1:
            tail, head = head, tail
        adjacency[tail].append((edge, head))
    for row in adjacency:
        row.sort()

    target_set = set(targets)
    heap = []
    best = {}
    for source in sorted(sources):
        key = (0, (), (source,))
        heapq.heappush(heap, (*key, source))
        if source not in best or key < best[source]:
            best[source] = key
    while heap:
        length, edges, vertices, vertex = heapq.heappop(heap)
        if best.get(vertex) != (length, edges, vertices):
            continue
        if vertex in target_set:
            return edges, vertices
        for edge, head in adjacency[vertex]:
            candidate = (length + 1, edges + (edge,), vertices + (head,))
            if head not in best or candidate < best[head]:
                best[head] = candidate
                heapq.heappush(heap, (*candidate, head))
    return None


def selected_path(graph, state, left, right):
    candidates = []
    for direction, (sources, targets) in enumerate(((left, right), (right, left))):
        path = best_directional_path(graph, state, sources, targets)
        if path is not None:
            edges, vertices = path
            candidates.append(((len(edges), direction, edges, vertices), edges, direction))
    if not candidates:
        return None
    _, edges, direction = min(candidates, key=lambda item: item[0])
    return edges, direction


def audit(size):
    graph = square_graph(size)
    edge_count = len(graph.edges)
    total = 1 << edge_count
    D = charge_matrix(graph)
    logical_mask = sum(1 << edge for edge in graph.logical_edges)
    left = tuple(v for v in graph.boundary_vertices if graph.vertices[v].boundary_side == "left")
    right = tuple(v for v in graph.boundary_vertices if graph.vertices[v].boundary_side == "right")

    sector_masks = defaultdict(int)
    charges = [None] * total
    for state in range(total):
        charge = tuple(int(value) for value in D @ bits_of(state, edge_count))
        sector = (state & logical_mask).bit_count() & 1
        charges[state] = charge
        sector_masks[charge] |= 1 << sector

    mapping = {}
    preimages = Counter()
    path_lengths = Counter()
    activity_changes = Counter()
    directions = Counter()
    domain_mismatch = binary_failures = charge_failures = logical_failures = 0

    for state in range(total):
        path = selected_path(graph, state, left, right)
        ambiguous = sector_masks[charges[state]] == 3
        domain_mismatch += (path is not None) != ambiguous
        if path is None:
            continue
        edges, direction = path
        path_mask = sum(1 << edge for edge in edges)
        image = state ^ path_mask
        binary_failures += image < 0 or image >= total
        charge_failures += charges[image] != charges[state]
        logical_failures += (((image & logical_mask).bit_count() -
                              (state & logical_mask).bit_count()) & 1) != 1
        mapping[state] = image
        preimages[image] += 1
        path_lengths[len(edges)] += 1
        delta_n = image.bit_count() - state.bit_count()
        activity_changes[delta_n] += 1
        directions["left_to_right" if direction == 0 else "right_to_left"] += 1

    involutive = sum(mapping.get(image) == state for state, image in mapping.items())
    multiplicities = Counter(preimages.values())
    max_abs_delta = max(abs(delta) for delta in activity_changes)
    distortions = {}
    for p in (0.3, 0.5):
        base = p / (1 - p)
        distortions[str(p)] = max(max(base**delta, base**(-delta)) for delta in activity_changes)
    zero_path = selected_path(graph, 0, left, right)

    return {
        "L": size,
        "edges": edge_count,
        "states": total,
        "charge_records": len(sector_masks),
        "ambiguous_charge_records": sum(mask == 3 for mask in sector_masks.values()),
        "transport_domain_states": len(mapping),
        "domain_mismatch_failures": domain_mismatch,
        "binary_feasibility_failures": binary_failures,
        "charge_preservation_failures": charge_failures,
        "logical_flip_failures": logical_failures,
        "direction_counts": dict(sorted(directions.items())),
        "path_length_histogram": {str(k): v for k, v in sorted(path_lengths.items())},
        "activity_change_histogram": {str(k): v for k, v in sorted(activity_changes.items())},
        "maximum_absolute_activity_change": max_abs_delta,
        "maximum_inverse_multiplicity": max(preimages.values()),
        "inverse_multiplicity_histogram": {str(k): v for k, v in sorted(multiplicities.items())},
        "involution_fraction": involutive / len(mapping),
        "maximum_reciprocal_weight_distortion": distortions,
        "all_zero_selected_path_length": len(zero_path[0]),
        "all_zero_activity_change": len(zero_path[0]),
    }


if __name__ == "__main__":
    print(json.dumps({
        "id": "lab008-residual-directed-sector-transport-2026-09-22",
        "status": "complete",
        "sampling": False,
        "rows": [audit(3), audit(4)],
    }, indent=2, sort_keys=True))
