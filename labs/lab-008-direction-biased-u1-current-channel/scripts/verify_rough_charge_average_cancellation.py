#!/usr/bin/env python3
"""Existing-L3 exact replay of physical versus boundary-only parity averages."""
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
    L = graph.size
    E = len(graph.edges)
    d = np.zeros((len(graph.vertices), E), dtype=np.int8)
    for e, (tail, head) in enumerate(graph.edges):
        d[tail, e] = -1
        d[head, e] = 1
    psi = np.asarray([int(v.x + v.y) for v in graph.vertices], dtype=np.int16)
    interior = graph.detector_vertices
    rough = graph.boundary_vertices
    den = p + (1 - p) * cosh(h)
    p_eff = p / den
    c = den / cosh(h)
    wh = {0: 1 - p, 1: p * exp(h) / (2 * cosh(h)), -1: p * exp(-h) / (2 * cosh(h))}
    w0 = {0: 1 - p_eff, 1: p_eff / 2, -1: p_eff / 2}
    z = defaultdict(float)
    f = defaultdict(float)
    direct_global_signed = 0.0
    parity_failures = 0
    for values in product((0, 1, -1), repeat=E):
        j = np.asarray(values, dtype=np.int8)
        q_all = d @ j
        q = tuple(int(q_all[v]) for v in interior)
        a = graph.logical_parity((j != 0).astype(np.uint8))
        right_charge = sum(int(q_all[v]) for v in rough if graph.vertices[v].boundary_side == "right")
        parity_failures += (a != right_charge % 2)
        m = sum(int(psi[v] * q_all[v]) for v in interior)
        b = sum(int(psi[v] * q_all[v]) for v in rough)
        ph = float(np.prod([wh[x] for x in values]))
        p0 = float(np.prod([w0[x] for x in values]))
        z[q, a] += ph
        f[q, a] += p0 * exp(h * b)
        direct_global_signed += (1 - 2 * a) * ph
    records = {q for q, _ in z}
    max_reconstruction_error = max(
        abs(z[q, a] - c**E * exp(h * sum(psi[v] * q[i] for i, v in enumerate(interior))) * f[q, a])
        for q in records for a in (0, 1)
    )
    boundary_signed = sum(f[q, 0] - f[q, 1] for q in records)
    boundary_total = sum(f[q, 0] + f[q, 1] for q in records)
    right_ratio = 1.0
    for y in range(L):
        a_y = 1 - p_eff
        b_y = p_eff * cosh(h * (L - 1 + y))
        right_ratio *= (a_y - b_y) / (a_y + b_y)
    physical_signed = sum(z[q, 0] - z[q, 1] for q in records)
    physical_absolute = sum(abs(z[q, 0] - z[q, 1]) for q in records)
    return {
        "L": L, "edges": E, "states": 3**E, "p": p, "h": h,
        "p_eff": p_eff, "records": len(records),
        "boundary_only_signed_ratio": boundary_signed / boundary_total,
        "boundary_only_product_formula": right_ratio,
        "physical_signed_contrast": physical_signed,
        "physical_signed_product_formula": (1 - 2 * p)**L,
        "physical_absolute_contrast": physical_absolute,
        "bayes_risk": (1 - physical_absolute) / 2,
        "formula_errors": {
            "reconstruction": max_reconstruction_error,
            "boundary_only_product": abs(boundary_signed / boundary_total - right_ratio),
            "physical_parity_product": abs(physical_signed - (1 - 2 * p)**L),
            "direct_global_parity": abs(direct_global_signed - physical_signed),
        },
        "right_charge_parity_failures": parity_failures,
    }


if __name__ == "__main__":
    rows = [audit(0.30, h) for h in (0.10, 0.50)]
    assert all(max(r["formula_errors"].values()) < 1e-12 for r in rows)
    assert all(r["right_charge_parity_failures"] == 0 for r in rows)
    assert all(r["physical_absolute_contrast"] >= abs(r["physical_signed_contrast"]) for r in rows)
    print(json.dumps({
        "id": "lab008-rough-charge-physical-average-cancellation-2026-09-22",
        "status": "verified_existing_l3_controls", "new_sizes": 0,
        "new_physical_samples": 0, "rows": rows,
    }, indent=2, sort_keys=True))
