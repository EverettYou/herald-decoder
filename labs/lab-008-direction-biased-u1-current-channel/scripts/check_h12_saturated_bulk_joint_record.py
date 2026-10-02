"""Deterministic geometry control for an all-size joint-record witness.

This generates no physical samples or new sizes. The proof is the saturation
and strip-charge sum identity in the owning Local Wiki.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from current_oracle import charge_matrix
from herald_decoder.lattice_model import square_graph


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
MANIFEST = LAB / "manifests/h12-saturated-bulk-joint-record-witness-2026-09-23.json"
RESULT = LAB / "results/h12-saturated-bulk-joint-record-witness-2026-09-23.json"


def check_size(size: int) -> dict:
    graph = square_graph(size)
    measured = graph.detector_vertices
    rows = graph.detector_row
    D = charge_matrix(graph)
    column = [v for v in measured if int(graph.vertices[v].x) == size - 3]
    strip = [v for v in measured if int(graph.vertices[v].x) == size - 2]
    assert len(column) == len(strip) == size

    required: dict[int, int] = {}
    for v in column:
        y = int(graph.vertices[v].y)
        sign = 1 if y % 2 == 0 else -1
        for e in graph.incident_edges[v]:
            value = sign * int(D[rows[v], e])
            assert value in (-1, 1)
            assert e not in required or required[e] == value
            required[e] = value
    assert len(required) == 3 * size - 1

    interface = [e for e in required if any(v in strip for v in graph.edges[e])]
    assert len(interface) == size
    assert set(interface).isdisjoint(graph.logical_edges)
    for e in interface:
        assert sum(v in column for v in graph.edges[e]) == 1
        assert sum(v in strip for v in graph.edges[e]) == 1

    cases = []
    for case in ("zero_cut", "one_cut"):
        currents = np.zeros(len(graph.edges), dtype=np.int8)
        for e, value in required.items():
            currents[e] = value
        if case == "one_cut":
            currents[min(graph.logical_edges)] = 1
        charges = D @ currents
        for v in column:
            y = int(graph.vertices[v].y)
            sign = 1 if y % 2 == 0 else -1
            assert int(charges[rows[v]]) == sign * len(graph.incident_edges[v])
        interface_sum = sum(int(currents[e]) for e in interface)
        strip_sum = sum(int(charges[rows[v]]) for v in strip)
        cut_sum = sum(int(currents[e]) for e in graph.logical_edges)
        assert interface_sum - strip_sum == cut_sum
        predicted_parity = (interface_sum - strip_sum) % 2
        actual_parity = sum(int(currents[e] != 0) for e in graph.logical_edges) % 2
        assert predicted_parity == actual_parity
        cases.append({
            "case": case,
            "strip_charge_sum": strip_sum,
            "pinned_interface_sum": interface_sum,
            "inferred_parity": predicted_parity,
            "actual_parity": actual_parity,
        })

    n_plus = sum(value == 1 for value in required.values())
    n_minus = len(required) - n_plus
    p = 0.3
    event_masses = {
        str(q): (p * q) ** n_plus * (p * (1 - q)) ** n_minus
        for q in (0.5, 0.9)
    }
    assert all(mass > 0 for mass in event_masses.values())
    assert np.isclose(event_masses["0.5"], (p / 2) ** (3 * size - 1))
    return {
        "L": size,
        "saturated_bulk_vertices": len(column),
        "fixed_edges": len(required),
        "pinned_interface_edges": len(interface),
        "fixed_plus_currents": n_plus,
        "fixed_minus_currents": n_minus,
        "event_probability_p_0_3": event_masses,
        "deterministic_cases": cases,
        "gate": "pass",
    }


def main() -> None:
    checks = [check_size(size) for size in (5, 7, 11)]
    result = {
        "id": "lab008-h12-saturated-bulk-joint-record-witness-2026-09-23",
        "status": "passed_all_size_proof_geometry_controls",
        "source_manifest": "../manifests/h12-saturated-bulk-joint-record-witness-2026-09-23.json",
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "lattice_source_sha256": hashlib.sha256((ROOT / "src/herald_decoder/lattice_model.py").read_bytes()).hexdigest(),
        "sampling": {"new_physical_samples": 0, "new_system_sizes": 0, "bootstrap_replicates": 0},
        "theorem": "For every L>=4, 0<p<1 and finite bias, the alternating saturated charges on the last bulk column have positive probability, pin all interface currents, and make the complete public strip charge sum determine cut-current parity exactly. Thus conditional full-record contrast is one on this rare bulk event. Its probability is at least [p min(q,1-q)]^(3L-1) for uniform finite q.",
        "checks": checks,
        "claim_boundary": "This is a pointwise conditional obstruction and exponentially small physical-average lower bound, not a size-uniform estimate of typical bulk records, a p=.30 phase, or a threshold.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "sizes": len(checks), "cases": sum(len(c["deterministic_cases"]) for c in checks)}))


if __name__ == "__main__":
    main()
