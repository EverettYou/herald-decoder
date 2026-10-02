#!/usr/bin/env python3
"""Existing-L3 replay of exact zero-field change-of-measure bounds."""
from __future__ import annotations

from collections import defaultdict
from itertools import product
import json
from math import cosh, exp, log, sqrt, tanh
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


def audit(p: float, h: float) -> dict:
    graph = square_graph(3)
    edges = len(graph.edges)
    D = charge_matrix(graph)
    w0 = {0: 1 - p, 1: p / 2, -1: p / 2}
    wh = {0: 1 - p, 1: p * exp(h) / (2 * cosh(h)), -1: p * exp(-h) / (2 * cosh(h))}
    joint0 = defaultdict(lambda: [0.0, 0.0])
    jointh = defaultdict(lambda: [0.0, 0.0])
    current_tv_l1 = kl_0h = kl_h0 = 0.0
    affinity = 0.0

    for values in product((0, 1, -1), repeat=edges):
        current = np.asarray(values, dtype=np.int8)
        prob0 = float(np.prod([w0[value] for value in values]))
        probh = float(np.prod([wh[value] for value in values]))
        current_tv_l1 += abs(prob0 - probh)
        kl_0h += prob0 * log(prob0 / probh)
        kl_h0 += probh * log(probh / prob0)
        affinity += sqrt(prob0 * probh)
        charge = tuple(int(value) for value in D @ current)
        sector = graph.logical_parity((current != 0).astype(np.uint8))
        joint0[charge][sector] += prob0
        jointh[charge][sector] += probh

    records = set(joint0) | set(jointh)
    risk0 = sum(min(joint0[q]) for q in records)
    riskh = sum(min(jointh[q]) for q in records)
    output_tv = 0.5 * sum(
        abs(joint0[q][sector] - jointh[q][sector])
        for q in records for sector in (0, 1)
    )
    current_tv = current_tv_l1 / 2
    kappa = min(log(cosh(h)), h * tanh(h) - log(cosh(h)))
    pinsker = min(1.0, sqrt(edges * p * kappa / 2))
    single_affinity = 1 - p + p * cosh(h / 2) / sqrt(cosh(h))

    return {
        "L": 3,
        "edges": edges,
        "p": p,
        "h": h,
        "states": 3**edges,
        "risk_zero": risk0,
        "risk_field": riskh,
        "risk_change_absolute": abs(riskh - risk0),
        "output_total_variation": output_tv,
        "current_total_variation": current_tv,
        "pinsker_bound": pinsker,
        "kl_zero_to_field": kl_0h,
        "kl_field_to_zero": kl_h0,
        "hellinger_affinity": affinity,
        "formula_errors": {
            "kl_zero_to_field": abs(kl_0h - edges * p * log(cosh(h))),
            "kl_field_to_zero": abs(kl_h0 - edges * p * (h * tanh(h) - log(cosh(h)))),
            "affinity": abs(affinity - single_affinity**edges),
        },
        "gate_risk_le_output_tv": abs(riskh - risk0) <= output_tv + 1e-14,
        "gate_output_le_current_tv": output_tv <= current_tv + 1e-14,
        "gate_current_le_pinsker": current_tv <= pinsker + 1e-14,
    }


if __name__ == "__main__":
    rows = [audit(0.30, h) for h in (0.10, 0.50)]
    assert all(max(row["formula_errors"].values()) < 1e-12 for row in rows)
    assert all(row["gate_risk_le_output_tv"] for row in rows)
    assert all(row["gate_output_le_current_tv"] for row in rows)
    assert all(row["gate_current_le_pinsker"] for row in rows)
    print(json.dumps({
        "id": "lab008-zero-field-field-window-bound-2026-09-22",
        "status": "verified",
        "new_sizes": 0,
        "rows": rows,
    }, indent=2, sort_keys=True))
