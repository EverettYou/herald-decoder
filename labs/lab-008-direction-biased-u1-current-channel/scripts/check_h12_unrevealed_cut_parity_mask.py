"""Audit the all-size unrevealed-cut parity masking bound on retained exact L3 data."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
import hashlib
import json
from pathlib import Path

from current_oracle import exact_enumeration
from herald_decoder.lattice_model import square_graph


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
RESULT = LAB / "results/h12-unrevealed-cut-parity-mask-2026-09-23.json"
P = 0.3
TOL = 1e-12


def subsets(items):
    for count in range(len(items) + 1):
        yield from combinations(items, count)


def main() -> None:
    geometry = []
    for size in (3, 5, 7, 11):
        graph = square_graph(size)
        strip = {v for v in graph.detector_vertices if graph.vertices[v].x == size - 2}
        bulk = set(graph.detector_vertices) - strip
        cut = set(graph.logical_edges)
        assert len(strip) == len(cut) == size
        cut_by_strip = {}
        for edge in cut:
            endpoints = set(graph.edges[edge])
            assert len(endpoints & strip) == 1
            assert len(endpoints & bulk) == 0
            assert len(endpoints & set(graph.boundary_vertices)) == 1
            vertex = next(iter(endpoints & strip))
            assert vertex not in cut_by_strip
            cut_by_strip[vertex] = edge
        assert set(cut_by_strip) == strip
        geometry.append({"L": size, "cut_edges": len(cut), "unique_strip_endpoints": len(cut_by_strip), "gate": "pass"})

    graph = square_graph(3)
    checks = []
    maximum_violation = 0.0
    for q in (0.5, 0.9, 1.0):
        table = exact_enumeration(graph, P, q)
        for subset in subsets(range(3)):
            grouped = defaultdict(lambda: [0.0, 0.0])
            for charge, value in table.items():
                key = tuple(charge[i] for i in subset)
                grouped[key][0] += float(value[0][0])
                grouped[key][1] += float(value[0][1])
            contrast = sum(abs(a - b) for a, b in grouped.values())
            bound = abs(1 - 2 * P) ** (3 - len(subset))
            violation = max(0.0, contrast - bound)
            maximum_violation = max(maximum_violation, violation)
            assert violation < TOL
            checks.append({"q": q, "observed_strip_rows": list(subset), "unobserved_cut_rows": 3 - len(subset), "contrast": contrast, "upper_bound": bound, "violation": violation})
    assert len(checks) == 24
    result = {
        "id": "lab008-h12-unrevealed-cut-parity-mask-2026-09-23",
        "status": "passed_exact_partial_record_controls",
        "source_manifest": "../manifests/h12-unrevealed-cut-parity-mask-2026-09-23.json",
        "source_sha256": hashlib.sha256((ROOT / "src/herald_decoder/lattice_model.py").read_bytes()).hexdigest(),
        "oracle_sha256": hashlib.sha256((LAB / "scripts/current_oracle.py").read_bytes()).hexdigest(),
        "sampling": {"new_physical_samples": 0, "new_system_sizes": 0, "bootstrap_replicates": 0},
        "theorem": "For O=(Q_B,Q_T), H parity of all cut activities, and r=L-|T| cut rows with no observed adjacent strip charge, E[(-1)^H|O]=(1-2p)^r E[(-1)^(sum observed cut activities)|O]. Consequently A(O)<=|1-2p|^r and R(H|O)>=(1-|1-2p|^r)/2, for every L and independent-edge bias pattern at fixed activity p.",
        "maximum_exact_control_violation": maximum_violation,
        "geometry_checks": geometry,
        "exact_controls": checks,
        "claim_boundary": "Partial-record obstruction only. At T equal to all strip rows the bound is trivial; it cannot decide full-record H12 or the p=.30 phase.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "exact_cells": len(checks), "maximum_violation": maximum_violation}))


if __name__ == "__main__":
    main()
