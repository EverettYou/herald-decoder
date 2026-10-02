"""Audit the strip-only parity-erasure product bound without new samples."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from current_oracle import exact_enumeration
from herald_decoder.lattice_model import square_graph


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
RESULT = LAB / "results/h12-strip-only-parity-erasure-2026-09-23.json"
P = Fraction(3, 10)
Q_VALUES = (Fraction(1, 2), Fraction(9, 10), Fraction(1, 1))
TOL = 1e-12


def row_kernel(p: Fraction, q: Fraction):
    weights = {-1: p * (1 - q), 0: 1 - p, 1: p * q}
    signed = {r: sum(weights[x] * weights[c] * (1 if c == 0 else -1)
                     for x in weights for c in weights if x - c == r)
              for r in range(-2, 3)}
    a, b, c = weights[0], weights[1], weights[-1]
    closed = {
        -2: -b * c,
        -1: a * (c - b),
        0: a * a - b * b - c * c,
        1: a * (b - c),
        2: -b * c,
    }
    assert signed == closed
    delta = sum(abs(value) for value in signed.values())
    assert delta <= 1 - 2 * min(a * a, b * b + c * c) < 1
    return signed, delta


def main() -> None:
    geometry = []
    for size in (3, 5, 7, 11):
        graph = square_graph(size)
        strip = {v for v in graph.detector_vertices if graph.vertices[v].x == size - 2}
        cut = set(graph.logical_edges)
        interface = set()
        vertical = set()
        for v in strip:
            incident = graph.incident_edges[v]
            left = [e for e in incident if graph.vertices[graph.edges[e][0]].x == size - 3
                    or graph.vertices[graph.edges[e][1]].x == size - 3]
            right = [e for e in incident if e in cut]
            internal = [e for e in incident if e not in left and e not in right]
            assert len(left) == len(right) == 1
            assert all(set(graph.edges[e]) <= strip for e in internal)
            interface.update(left)
            vertical.update(internal)
        assert len(interface) == len(cut) == size
        assert len(vertical) == size - 1
        assert not (interface & cut or interface & vertical or cut & vertical)
        geometry.append({"L": size, "interface_edges": len(interface), "cut_edges": len(cut), "vertical_strip_edges": len(vertical), "gate": "pass"})

    graph = square_graph(3)
    cells = []
    for q in Q_VALUES:
        signed, delta = row_kernel(P, q)
        table = exact_enumeration(graph, float(P), float(q))
        exact_contrast = sum(abs(float(value[0][0]) - float(value[0][1])) for value in table.values())
        bound = delta ** 3
        violation = max(0.0, exact_contrast - float(bound))
        assert violation < TOL
        cells.append({
            "p": float(P), "q": float(q),
            "signed_row_kernel": {str(r): str(value) for r, value in signed.items()},
            "delta_exact": str(delta), "delta": float(delta),
            "strip_only_L3_contrast": exact_contrast,
            "oracle_bound_delta_cubed": float(bound),
            "violation": violation,
        })
    result = {
        "id": "lab008-h12-strip-only-parity-erasure-2026-09-23",
        "status": "passed_exact_partial_record_bound",
        "source_manifest": "../manifests/h12-strip-only-parity-erasure-2026-09-23.json",
        "source_sha256": hashlib.sha256((ROOT / "src/herald_decoder/lattice_model.py").read_bytes()).hexdigest(),
        "oracle_sha256": hashlib.sha256((LAB / "scripts/current_oracle.py").read_bytes()).hexdigest(),
        "sampling": {"new_physical_samples": 0, "new_system_sizes": 0, "bootstrap_replicates": 0},
        "theorem": "For strip charges S and vertical strip currents V, Y=S-D_V V consists of L independent row differences X_y-C_y. Revealing V can only increase absolute logical contrast. Therefore A(S)<=A(S,V)=delta(p,q)^L, where delta=|a^2-b^2-c^2|+2a|b-c|+2bc<1 for a=1-p,b=pq,c=p(1-q), 0<p<1 and 0<=q<=1.",
        "geometry_checks": geometry,
        "exact_controls": cells,
        "maximum_exact_control_violation": max(cell["violation"] for cell in cells),
        "claim_boundary": "The bound applies only when bulk charges are hidden. It does not bound full physical-record contrast A(Q_bulk,Q_strip), which can exploit bulk-strip correlations; no p=.30 phase is inferred.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "cells": len(cells), "maximum_violation": result["maximum_exact_control_violation"]}))


if __name__ == "__main__":
    main()
