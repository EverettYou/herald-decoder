#!/usr/bin/env python3
"""Exact parity-aligned interface matrix for canonical q=1 squares."""
from __future__ import annotations

from collections import defaultdict
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from herald_decoder.lattice_model import square_graph


def divergence(graph, edges, current, vertex):
    value = 0
    for edge in edges:
        tail, head = graph.edges[edge]
        if tail == vertex:
            value -= int(current[edge])
        if head == vertex:
            value += int(current[edge])
    return value


def state_table(size):
    graph = square_graph(size)
    k = (size - 1) // 2
    separator = tuple(v for v in graph.detector_vertices if int(graph.vertices[v].x) == k)
    left_edges = tuple(
        edge for edge, (tail, head) in enumerate(graph.edges)
        if graph.vertices[tail].x <= k and graph.vertices[head].x <= k
    )
    all_edges = tuple(range(len(graph.edges)))
    table = defaultdict(lambda: (defaultdict(lambda: defaultdict(int)),
                                 defaultdict(lambda: defaultdict(int))))
    fixed_path = tuple(
        edge for edge, (tail, head) in enumerate(graph.edges)
        if graph.vertices[tail].y == 0 and graph.vertices[head].y == 0
        and abs(graph.vertices[tail].x - graph.vertices[head].x) == 1
    )
    fixed_path_charge_preserved = 0
    fixed_path_sector_flips = 0
    total = 0

    for bits in product((0, 1), repeat=len(graph.edges)):
        current = np.asarray(bits, dtype=np.uint8)
        charge = tuple(divergence(graph, all_edges, current, v) for v in graph.detector_vertices)
        flux = tuple(divergence(graph, left_edges, current, v) for v in separator)
        sector = graph.logical_parity(current)
        activity = int(current.sum())
        table[charge][sector][flux][activity] += 1

        toggled = current.copy()
        toggled[list(fixed_path)] ^= 1
        charge_t = tuple(divergence(graph, all_edges, toggled, v) for v in graph.detector_vertices)
        fixed_path_charge_preserved += charge_t == charge
        fixed_path_sector_flips += graph.logical_parity(toggled) != sector
        total += 1
    return graph, k, separator, table, {
        "path_row": 0,
        "states": total,
        "binary_feasibility_fraction": 1.0,
        "logical_flip_fraction": fixed_path_sector_flips / total,
        "charge_preservation_fraction": fixed_path_charge_preserved / total,
    }


def weight_histogram(histogram, edges, p):
    return sum(count * p**activity * (1-p)**(edges-activity)
               for activity, count in histogram.items())


def analyze(size, p):
    graph, k, separator, table, path_audit = state_table(size)
    rows = []
    for anchor_index, anchor_vertex in enumerate(separator):
        risk = 0.0
        revealed_risk = 0.0
        weighted_tv = 0.0
        ambiguous = 0
        overlap = 0
        nonunit_tv = 0
        parity_failures = 0
        reproduction_error = 0.0

        for charge, sectors in table.items():
            aligned = [defaultdict(float), defaultdict(float)]
            original = [0.0, 0.0]
            known = sum(
                charge[row] for row, vertex in enumerate(graph.detector_vertices)
                if graph.vertices[vertex].x >= k
            )
            for sector in (0, 1):
                for flux, activity_histogram in sectors[sector].items():
                    shifted = list(flux)
                    shifted[anchor_index] -= sector
                    shifted = tuple(shifted)
                    parity_failures += ((sum(shifted) - known) & 1) != 0
                    value = weight_histogram(activity_histogram, len(graph.edges), p)
                    aligned[sector][shifted] += value
                    original[sector] += value
            reproduction_error = max(
                reproduction_error,
                abs(sum(aligned[0].values()) - original[0]),
                abs(sum(aligned[1].values()) - original[1]),
            )
            if min(original) == 0:
                continue
            ambiguous += 1
            keys = set(aligned[0]) | set(aligned[1])
            overlap += bool(set(aligned[0]) & set(aligned[1]))
            tv = 0.5 * sum(abs(aligned[0].get(u, 0.0) / original[0]
                               - aligned[1].get(u, 0.0) / original[1]) for u in keys)
            nonunit_tv += tv < 1 - 1e-12
            risk += min(original)
            revealed_risk += sum(min(aligned[0].get(u, 0.0), aligned[1].get(u, 0.0)) for u in keys)
            weighted_tv += min(original) * tv

        rows.append({
            "L": size,
            "p": p,
            "separator_x": k,
            "anchor_row": int(graph.vertices[anchor_vertex].y),
            "ambiguous_charge_records": ambiguous,
            "aligned_support_overlap_records": overlap,
            "aligned_support_overlap_fraction": overlap / ambiguous,
            "aligned_nonunit_tv_records": nonunit_tv,
            "risk": risk,
            "aligned_revealed_risk": revealed_risk,
            "aligned_revealed_risk_fraction": revealed_risk / risk,
            "aligned_cancellation": risk - revealed_risk,
            "risk_weighted_aligned_tv": weighted_tv,
            "risk_weighted_aligned_tv_fraction": weighted_tv / risk,
            "parity_normalization_failures": parity_failures,
            "maximum_sector_weight_reproduction_error": reproduction_error,
        })
    return rows, path_audit


if __name__ == "__main__":
    rows = []
    audits = {}
    for size in (3, 4):
        for p in (0.3, 0.5):
            result, audit = analyze(size, p)
            rows.extend(result)
            audits[str(size)] = audit
    output = {
        "id": "lab008-parity-aligned-interface-matrix-2026-09-22",
        "status": "complete",
        "sampling": False,
        "rows": rows,
        "fixed_geometric_path_transport": audits,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
