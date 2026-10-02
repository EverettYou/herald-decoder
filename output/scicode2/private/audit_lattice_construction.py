"""Independently check the exam's integer geometry against the current repository.

Run from the repository root:
  ./run_research_python.sh output/scicode2/private/audit_lattice_construction.py
This is a private author audit, not a candidate solution.
"""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
import hashlib
import json
from math import sqrt
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from herald_decoder.lattice_model import honeycomb_graph


def construction(L: int) -> dict:
    offsets = ((2, 0), (1, 1), (-1, 1), (-2, 0), (-1, -1), (1, -1))
    occurrences = defaultdict(list)
    vertices = set()
    for a in range(L):
        for b in range(L):
            corners = [(3*a + dx, 2*b + a % 2 + dy) for dx, dy in offsets]
            vertices.update(corners)
            for j in range(6):
                edge = tuple(sorted((corners[j], corners[(j+1) % 6])))
                occurrences[edge].append((a, b, j))
    left_removed, right_removed = set(), set()
    for edge, local_sides in occurrences.items():
        if len(local_sides) == 1:
            a, b, j = local_sides[0]
            if a == 0 and j in (2, 3):
                left_removed.add(edge)
            if a == L-1 and j in (0, 5):
                right_removed.add(edge)
    left = {v for edge in left_removed for v in edge}
    right = {v for edge in right_removed for v in edge}
    retained = set(occurrences) - left_removed - right_removed
    detectors = vertices - left - right
    logical = {edge for edge in retained if any(v in right for v in edge)}
    return dict(vertices=vertices, edges=retained, detectors=detectors,
                left=left, right=right, logical=logical,
                raw_edges=len(occurrences), removed=len(left_removed | right_removed))


def rank_f2(matrix: np.ndarray) -> int:
    a = matrix.copy().astype(np.uint8)
    rank = 0
    for col in range(a.shape[1]):
        pivots = np.flatnonzero(a[rank:, col])
        if not len(pivots):
            continue
        pivot = rank + int(pivots[0])
        a[[rank, pivot]] = a[[pivot, rank]]
        other = np.flatnonzero(a[:, col])
        other = other[other != rank]
        a[other] ^= a[rank]
        rank += 1
        if rank == a.shape[0]:
            break
    return rank


def check(L: int) -> dict:
    exam = construction(L)
    repo = honeycomb_graph(L)
    coords = []
    for v in repo.vertices:
        X, Y = round(2*v.x), round(2*v.y/sqrt(3))
        assert abs(v.x-X/2) < 1e-10
        assert abs(v.y-sqrt(3)*Y/2) < 1e-10
        coords.append((X, Y))
    repo_edges = [tuple(sorted((coords[a], coords[b]))) for a, b in repo.edges]
    assert len(set(coords)) == len(coords)
    assert len(set(repo_edges)) == len(repo_edges)
    checks = {
        "vertices": exam["vertices"] == set(coords),
        "edges": exam["edges"] == set(repo_edges),
        "detectors": exam["detectors"] == {coords[v] for v in repo.detector_vertices},
        "left_boundary": exam["left"] == {coords[i] for i,v in enumerate(repo.vertices) if v.boundary_side == "left"},
        "right_boundary": exam["right"] == {coords[i] for i,v in enumerate(repo.vertices) if v.boundary_side == "right"},
        "logical_cut": exam["logical"] == {repo_edges[e] for e in repo.logical_edges},
    }
    assert all(checks.values()), (L, checks)
    counts = dict(L=L, vertices=len(coords), edges=len(repo.edges),
                  detectors=len(repo.detector_vertices), logical_edges=len(repo.logical_edges))
    assert counts["vertices"] == 2*L*L+4*L
    assert counts["edges"] == 3*L*L-1
    assert counts["detectors"] == 2*L*L-2
    assert counts["logical_edges"] == L+1
    assert exam["raw_edges"] == 3*L*L+4*L-1
    assert exam["removed"] == 4*L
    assert len(exam["left"]) == len(exam["right"]) == 2*L+1
    assert not exam["left"] & exam["right"]

    # Relabel the repository arrays into the exam's canonical lexicographic order.
    edge_order = sorted(exam["edges"])
    detector_order = sorted(exam["detectors"])
    H = np.array([[int(v in edge) for edge in edge_order] for v in detector_order], dtype=np.uint8)
    repo_edge_index = {edge: i for i, edge in enumerate(repo_edges)}
    repo_detector_index = {coords[v]: i for i,v in enumerate(repo.detector_vertices)}
    row_perm = [repo_detector_index[v] for v in detector_order]
    col_perm = [repo_edge_index[e] for e in edge_order]
    repo_H = repo.check_matrix.toarray()[np.ix_(row_perm, col_perm)]
    assert np.array_equal(H, repo_H)
    assert set(H.sum(axis=0)) <= {1, 2}
    checks["check_matrix_after_relabeling"] = True
    # Equality of this row establishes equality of logical parity on every chain.
    ell = np.array([int(e in exam["logical"]) for e in edge_order], dtype=np.uint8)
    repo_ell = np.array([int(repo_edge_index[e] in repo.logical_edges) for e in edge_order], dtype=np.uint8)
    assert np.array_equal(ell, repo_ell)
    checks["logical_functional_all_chains"] = True

    # Explicit left-to-right relative chain: zero detector syndrome, odd logical parity.
    adjacency = defaultdict(list)
    for i, (a,b) in enumerate(edge_order):
        adjacency[a].append((b,i)); adjacency[b].append((a,i))
    queue = deque(sorted(exam["left"]))
    parent = {v: None for v in queue}
    target = None
    while queue:
        v = queue.popleft()
        if v in exam["right"]:
            target = v
            break
        for u,e in adjacency[v]:
            if u not in parent:
                parent[u] = (v,e)
                queue.append(u)
    assert target is not None
    chain = np.zeros(len(edge_order), dtype=np.uint8)
    while parent[target] is not None:
        target,e = parent[target]
        chain[e] = 1
    assert not np.any((H @ chain) % 2)
    assert int((ell @ chain) % 2) == 1
    assert int(chain.sum()) == 2*L-1
    counts["shortest_rough_to_rough_chain"] = int(chain.sum())
    checks["nontrivial_logical_chain"] = True

    if L <= 4:
        counts["rank_H"] = rank_f2(H)
        counts["rank_H_with_logical_row"] = rank_f2(np.vstack((H,ell)))
        assert counts["rank_H"] == len(detector_order)
        assert counts["rank_H_with_logical_row"] == len(detector_order)+1
        checks["two_logical_sectors_per_syndrome"] = True
    return dict(**counts, checks=checks)


def main() -> None:
    sizes = list(range(2, 21))
    results = [check(L) for L in sizes]
    tex = ROOT / "output/scicode2/herald_decoding_problem.tex"
    model = ROOT / "src/herald_decoder/lattice_model.py"
    output = Path(__file__).with_name("lattice_construction_audit.json")
    payload = {
        "status": "passed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sizes": sizes,
        "source_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "exam_sha256": hashlib.sha256(tex.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Exact integer construction against repository geometry, boundaries, H and logical functional; finite checks do not alone prove general formulas.",
        "results": results,
    }
    output.write_text(json.dumps(payload, indent=2)+"\n")
    print(json.dumps({"status":"passed", "sizes":sizes, "requested_sizes":results[:3], "output":str(output)}, indent=2))


if __name__ == "__main__":
    main()
