#!/usr/bin/env python3
"""Exhaustive small-square check of the straight-separator parity identity.

This is a deterministic topology check, not physical sampling.  It enumerates
all q=1 binary currents on L=3,4 and verifies that the measured charge record
and the complete interface-divergence vector determine logical parity.
"""
from __future__ import annotations

from itertools import product
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from herald_decoder.lattice_model import square_graph


def divergence(graph, edge_indices, current, vertex):
    value = 0
    for edge in edge_indices:
        tail, head = graph.edges[edge]
        if tail == vertex:
            value -= int(current[edge])
        if head == vertex:
            value += int(current[edge])
    return value


def audit(size):
    graph = square_graph(size)
    separator_x = (size - 1) // 2
    separator = tuple(
        vertex
        for vertex in graph.detector_vertices
        if int(graph.vertices[vertex].x) == separator_x
    )
    left_edges = tuple(
        edge
        for edge, (tail, head) in enumerate(graph.edges)
        if graph.vertices[tail].x <= separator_x
        and graph.vertices[head].x <= separator_x
    )
    all_edges = tuple(range(len(graph.edges)))
    fibers = {}
    parity_failures = 0

    for bits in product((0, 1), repeat=len(graph.edges)):
        current = np.asarray(bits, dtype=np.uint8)
        charge = tuple(
            divergence(graph, all_edges, current, vertex)
            for vertex in graph.detector_vertices
        )
        interface_flux = tuple(
            divergence(graph, left_edges, current, vertex)
            for vertex in separator
        )
        logical = graph.logical_parity(current)
        right_charge = sum(
            charge[row]
            for row, vertex in enumerate(graph.detector_vertices)
            if graph.vertices[vertex].x >= separator_x
        )
        reconstructed = (right_charge + sum(interface_flux)) & 1
        parity_failures += logical != reconstructed
        fibers.setdefault(charge, (set(), set()))[logical].add(interface_flux)

    ambiguous = sum(bool(sector_0 and sector_1) for sector_0, sector_1 in fibers.values())
    overlaps = sum(bool(sector_0 & sector_1) for sector_0, sector_1 in fibers.values())
    return {
        "L": size,
        "edges": len(graph.edges),
        "separator_x": separator_x,
        "separator_vertices": len(separator),
        "binary_currents": 2 ** len(graph.edges),
        "charge_records": len(fibers),
        "ambiguous_charge_records": ambiguous,
        "parity_identity_failures": parity_failures,
        "cross_sector_interface_support_overlaps": overlaps,
    }


if __name__ == "__main__":
    payload = {
        "check": "straight_separator_interface_flux_determines_logical_parity",
        "sampling": False,
        "rows": [audit(3), audit(4)],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
