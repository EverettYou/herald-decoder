#!/usr/bin/env python3
"""Exact rational L3 replay of the fixed-p zero-field response identities."""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from herald_decoder.lattice_model import square_graph


def charge_matrix(graph):
    rows = {vertex: row for row, vertex in enumerate(graph.detector_vertices)}
    matrix = np.zeros((len(rows), len(graph.edges)), dtype=np.int8)
    for edge, (tail, head) in enumerate(graph.edges):
        if tail in rows:
            matrix[rows[tail], edge] -= 1
        if head in rows:
            matrix[rows[head], edge] += 1
    return matrix


def exact_control(p: Fraction) -> dict:
    graph = square_graph(3)
    edge_count = len(graph.edges)
    D = charge_matrix(graph)
    table = defaultdict(lambda: [[Fraction(0), Fraction(0), Fraction(0)] for _ in range(2)])
    total = [Fraction(0), Fraction(0), Fraction(0)]

    for values in product((0, 1, -1), repeat=edge_count):
        current = np.asarray(values, dtype=np.int8)
        activity = int(np.count_nonzero(current))
        signed_sum = int(current.sum())
        weight = (1 - p) ** (edge_count - activity) * (p / 2) ** activity
        charge = tuple(int(value) for value in D @ current)
        sector = graph.logical_parity((current != 0).astype(np.uint8))
        moments = table[charge][sector]
        derivatives = (weight, weight * signed_sum, weight * (signed_sum**2 - activity))
        for order, value in enumerate(derivatives):
            moments[order] += value
            total[order] += value

    risk = Fraction(0)
    tied = 0
    cusp_twice = Fraction(0)
    nontied_linear = Fraction(0)
    reflection_failures = 0
    maximum_gap_slope = Fraction(0)
    for charge, sectors in table.items():
        z0, z1 = sectors[0][0], sectors[1][0]
        risk += min(z0, z1)
        d0 = z0 - z1
        d1 = sectors[0][1] - sectors[1][1]
        if z0 and z1:
            slope = abs(sectors[0][1] / z0 - sectors[1][1] / z1)
            maximum_gap_slope = max(maximum_gap_slope, slope)
        if d0 == 0:
            tied += 1
            cusp_twice += abs(d1)
        else:
            nontied_linear += (1 if d0 > 0 else -1) * d1
        reflected = table.get(tuple(-value for value in charge))
        if reflected is None:
            reflection_failures += 1
        else:
            for sector in (0, 1):
                reflection_failures += reflected[sector][0] != sectors[sector][0]
                reflection_failures += reflected[sector][1] != -sectors[sector][1]
                reflection_failures += reflected[sector][2] != sectors[sector][2]

    return {
        "L": 3,
        "p": str(p),
        "states": 3**edge_count,
        "charge_records": len(table),
        "tied_records": tied,
        "bayes_risk_exact": str(risk),
        "right_cusp_magnitude_exact": str(cusp_twice / 2),
        "maximum_absolute_record_gap_slope_exact": str(maximum_gap_slope),
        "normalization_exact": str(total[0]),
        "total_first_derivative_exact": str(total[1]),
        "total_second_derivative_exact": str(total[2]),
        "nontied_linear_cancellation_exact": str(nontied_linear),
        "reflection_failures": reflection_failures,
    }


if __name__ == "__main__":
    rows = [exact_control(Fraction(3, 10)), exact_control(Fraction(1, 2))]
    assert all(row["normalization_exact"] == "1" for row in rows)
    assert all(row["total_first_derivative_exact"] == "0" for row in rows)
    assert all(row["total_second_derivative_exact"] == "0" for row in rows)
    assert all(row["nontied_linear_cancellation_exact"] == "0" for row in rows)
    assert all(row["reflection_failures"] == 0 for row in rows)
    print(json.dumps({
        "id": "lab008-zero-field-infinitesimal-response-2026-09-22",
        "status": "verified",
        "new_sizes": 0,
        "rows": rows,
    }, indent=2, sort_keys=True))
