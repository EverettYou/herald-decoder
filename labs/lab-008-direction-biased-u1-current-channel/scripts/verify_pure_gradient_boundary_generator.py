#!/usr/bin/env python3
"""Exact existing-L3 replay of the pure-gradient rough-charge identity."""
from __future__ import annotations

from collections import defaultdict
from itertools import product
import json
from math import cosh, exp
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from herald_decoder.lattice_model import square_graph


def audit(p: float, h: float) -> dict:
    graph = square_graph(3)
    edge_count = len(graph.edges)
    d = np.zeros((len(graph.vertices), edge_count), dtype=np.int8)
    for e, (tail, head) in enumerate(graph.edges):
        d[tail, e] = -1
        d[head, e] = 1
    psi = np.asarray([round(v.x + v.y) for v in graph.vertices], dtype=np.int16)
    measured = graph.detector_vertices
    boundary = graph.boundary_vertices
    assert all(psi[head] - psi[tail] == 1 for tail, head in graph.edges)
    den = p + (1 - p) * cosh(h)
    p_eff = p / den
    c = den / cosh(h)
    field_w = {0: 1 - p, 1: p * exp(h) / (2 * cosh(h)), -1: p * exp(-h) / (2 * cosh(h))}
    zero_eff_w = {0: 1 - p_eff, 1: p_eff / 2, -1: p_eff / 2}
    direct = defaultdict(float)
    boundary_generator = defaultdict(float)
    max_state_error = 0.0
    max_gradient_error = 0
    for values in product((0, 1, -1), repeat=edge_count):
        current = np.asarray(values, dtype=np.int8)
        charges = d @ current
        q = tuple(int(charges[v]) for v in measured)
        sector = graph.logical_parity((current != 0).astype(np.uint8))
        m = int(np.dot(psi[list(measured)], charges[list(measured)]))
        b = int(np.dot(psi[list(boundary)], charges[list(boundary)]))
        j = int(np.sum(current))
        max_gradient_error = max(max_gradient_error, abs(j - m - b))
        direct_weight = float(np.prod([field_w[v] for v in values]))
        zero_eff_weight = float(np.prod([zero_eff_w[v] for v in values]))
        reparam_weight = c**edge_count * exp(h * (m + b)) * zero_eff_weight
        max_state_error = max(max_state_error, abs(direct_weight - reparam_weight))
        direct[q, sector] += direct_weight
        boundary_generator[q, sector] += zero_eff_weight * exp(h * b)
    max_sector_error = max(
        abs(value - c**edge_count * exp(h * sum(psi[v] * q[i] for i, v in enumerate(measured))) * boundary_generator[q, a])
        for (q, a), value in direct.items()
    )
    return {
        "L": 3, "edges": edge_count, "states": 3**edge_count,
        "p": p, "h": h, "p_eff": p_eff, "normalization_c": c,
        "charge_sector_cells": len(direct),
        "max_gradient_identity_error": max_gradient_error,
        "max_state_weight_error": max_state_error,
        "max_charge_sector_error": max_sector_error,
    }


if __name__ == "__main__":
    rows = [audit(0.30, h) for h in (0.10, 0.50)]
    assert all(r["max_gradient_identity_error"] == 0 for r in rows)
    assert all(max(r["max_state_weight_error"], r["max_charge_sector_error"]) < 1e-12 for r in rows)
    print(json.dumps({
        "id": "lab008-pure-gradient-rough-boundary-generator-2026-09-22",
        "status": "verified_exact_l3_control",
        "new_sizes": 0, "new_physical_samples": 0,
        "rows": rows,
    }, indent=2, sort_keys=True))
