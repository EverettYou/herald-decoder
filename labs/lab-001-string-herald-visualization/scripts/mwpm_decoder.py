#!/usr/bin/env python3
"""Lab 001 Stage-2 decoder using PyMatching MWPM."""

from __future__ import annotations

import numpy as np
import pymatching
from scipy.sparse import csc_matrix


def mwpm_decode(body: dict) -> dict:
    """Decode the Lab 001 graphlike check matrix with PyMatching.

    Every retained data edge is one column. Detector vertices select the check
    rows; a singleton column is accepted only when its other endpoint is an
    explicitly declared rough-boundary vertex.
    """
    vertex_count = body.get("vertex_count")
    raw_edges, raw_syndromes = body.get("edges"), body.get("syndromes")
    raw_detectors = body.get("detector_vertices")
    raw_boundaries = body.get("boundary_vertices", [])
    if isinstance(vertex_count, bool) or not isinstance(vertex_count, int) or not 1 <= vertex_count <= 1000:
        raise ValueError("vertex_count must be an integer in [1, 1000]")
    if not isinstance(raw_edges, list) or len(raw_edges) > 5000:
        raise ValueError("edges must be a list with at most 5000 entries")
    if not isinstance(raw_syndromes, list) or len(raw_syndromes) > 1000:
        raise ValueError("syndromes must be a list with at most 1000 entries")

    if raw_detectors is None:
        detectors = list(range(vertex_count))
    else:
        if not isinstance(raw_detectors, list) or len(raw_detectors) > vertex_count:
            raise ValueError("detector_vertices must be a list of lattice vertex ids")
        if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < vertex_count for v in raw_detectors):
            raise ValueError("detector vertex is out of range")
        detectors = sorted(set(raw_detectors))
        if len(detectors) != len(raw_detectors):
            raise ValueError("duplicate detector vertex")

    if not isinstance(raw_boundaries, list) or len(raw_boundaries) > vertex_count:
        raise ValueError("boundary_vertices must be a list of lattice vertex ids")
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < vertex_count for v in raw_boundaries):
        raise ValueError("boundary vertex is out of range")
    boundaries = sorted(set(raw_boundaries))
    if len(boundaries) != len(raw_boundaries):
        raise ValueError("duplicate boundary vertex")
    if set(detectors) & set(boundaries):
        raise ValueError("detector_vertices and boundary_vertices must be disjoint")

    detector_row = {vertex: row for row, vertex in enumerate(detectors)}
    boundary_set = set(boundaries)
    edge_keys = set()
    matrix_rows, matrix_columns = [], []
    boundary_edge_indices = []
    for index, edge in enumerate(raw_edges):
        if not isinstance(edge, list) or len(edge) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in edge):
            raise ValueError("each edge must contain two integer vertex ids")
        a, b = edge
        if a == b or not 0 <= a < vertex_count or not 0 <= b < vertex_count:
            raise ValueError("edge vertex is out of range")
        key = tuple(sorted((a, b)))
        if key in edge_keys:
            raise ValueError("duplicate graph edge")
        edge_keys.add(key)
        incident_rows = [detector_row[vertex] for vertex in (a, b) if vertex in detector_row]
        non_detector_vertices = [vertex for vertex in (a, b) if vertex not in detector_row]
        if len(incident_rows) == 1 and any(vertex not in boundary_set for vertex in non_detector_vertices):
            raise ValueError("a singleton check-matrix column must terminate on an explicit boundary vertex")
        if not incident_rows:
            raise ValueError("an edge with no incident detector is not a physical data edge")
        matrix_rows.extend(incident_rows)
        matrix_columns.extend([index] * len(incident_rows))
        if len(incident_rows) == 1:
            boundary_edge_indices.append(index)

    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < vertex_count for v in raw_syndromes):
        raise ValueError("syndrome vertex is out of range")
    syndromes = sorted(set(raw_syndromes))
    if len(syndromes) != len(raw_syndromes):
        raise ValueError("duplicate syndrome vertex")
    if any(vertex not in detector_row for vertex in syndromes):
        raise ValueError("every syndrome vertex must be a detector vertex")
    if len(syndromes) % 2 and not boundary_edge_indices:
        return {
            "status": "odd_syndrome_count",
            "matching": [],
            "correction_edge_indices": [],
            "total_weight": 0,
            "unmatched_syndromes": syndromes,
            "boundary_edge_indices": [],
        }

    check_matrix = csc_matrix(
        (np.ones(len(matrix_rows), dtype=np.uint8), (matrix_rows, matrix_columns)),
        shape=(len(detectors), len(raw_edges)),
        dtype=np.uint8,
    )
    matching_decoder = pymatching.Matching.from_check_matrix(
        check_matrix,
        weights=np.ones(len(raw_edges), dtype=float),
        use_virtual_boundary_node=True,
    )
    syndrome_vector = np.zeros(len(detectors), dtype=np.uint8)
    syndrome_vector[[detector_row[vertex] for vertex in syndromes]] = 1
    try:
        prediction, solution_weight = matching_decoder.decode(syndrome_vector, return_weight=True)
        matched_rows = matching_decoder.decode_to_matched_dets_array(syndrome_vector)
    except ValueError:
        return {
            "status": "disconnected_syndromes",
            "matching": [],
            "correction_edge_indices": [],
            "total_weight": 0,
            "unmatched_syndromes": syndromes,
            "boundary_edge_indices": boundary_edge_indices,
        }

    correction = np.flatnonzero(prediction).astype(int).tolist()
    matched_vertices = [
        [detectors[int(a)], None if int(b) == -1 else detectors[int(b)]]
        for a, b in matched_rows
    ]
    return {
        "status": "ok",
        "matching": matched_vertices,
        "correction_edge_indices": correction,
        "total_weight": float(solution_weight),
        "unmatched_syndromes": [],
        "boundary_edge_indices": boundary_edge_indices,
    }
