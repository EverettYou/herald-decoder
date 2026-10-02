"""Audit candidate all-size theorems for midpoint path-switching matching.

The exact L3/L4 switching graphs saturate each charge record's smaller logical
sector.  This script tests the stronger normalized matching property, verifies
the embedding into planar alpha-orientations after contracting the rough
boundary, and records why published orientation-lattice results do not apply
to the restricted logical-sector switching graph.  It also searches every
single- and double-edge deletion of canonical L4 for a small Hall obstruction.
No L5 enumeration, sampling, decoder run, or threshold extrapolation occurs.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import time

import numpy as np
from scipy.sparse import bmat, coo_matrix
from scipy.sparse.csgraph import (
    connected_components,
    maximum_bipartite_matching,
    maximum_flow,
)

from herald_decoder.lattice_model import LatticeGraph
from check_midpoint_fractional_switching import (
    _state_data,
    _switching_adjacency,
)
from check_midpoint_switching_pairing import _simple_crossing_paths
from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results/midpoint-all-size-matching-theorem-2026-09-20.json"
FRACTIONAL_RESULT = LAB / "results/midpoint-fractional-switching-2026-09-20.json"
SWITCHING_RESULT = LAB / "results/midpoint-switching-pairing-2026-09-20.json"


def _orientation_embedding_audit(graph, states, charges):
    edge_count = len(graph.edges)
    bits = ((states[:, None] >> np.arange(edge_count)) & 1).astype(np.int8)
    outdegree = np.zeros((len(states), len(graph.vertices)), dtype=np.int8)
    stored_tail_count = np.zeros(len(graph.vertices), dtype=np.int8)
    degree = np.zeros(len(graph.vertices), dtype=np.int8)
    for edge, (tail, head) in enumerate(graph.edges):
        outdegree[:, tail] += bits[:, edge]
        outdegree[:, head] += 1 - bits[:, edge]
        stored_tail_count[tail] += 1
        degree[tail] += 1
        degree[head] += 1

    interior = np.asarray(graph.detector_vertices, dtype=np.int64)
    boundary = np.asarray(graph.boundary_vertices, dtype=np.int64)
    predicted_interior = (
        degree[interior][None, :]
        - stored_tail_count[interior][None, :]
        - charges
    )
    interior_formula_failures = int(
        np.count_nonzero(outdegree[:, interior] != predicted_interior)
    )
    contracted_root_outdegree = outdegree[:, boundary].sum(axis=1)
    predicted_root_outdegree = edge_count - predicted_interior.sum(axis=1)
    root_formula_failures = int(
        np.count_nonzero(contracted_root_outdegree != predicted_root_outdegree)
    )
    return {
        "interpretation": "bit one orients an edge as stored and bit zero reverses it; after all rough vertices are contracted to the outer root, fixed measured charge fixes every vertex outdegree",
        "interior_outdegree_formula": "outdeg(v)=degree(v)-stored_tail_count(v)-Q(v)",
        "interior_formula_failures": interior_formula_failures,
        "contracted_root_formula_failures": root_formula_failures,
        "alpha_orientation_embedding": (
            interior_formula_failures == 0 and root_formula_failures == 0
        ),
    }


def _root_cycle_audit(graph, paths):
    direction_failures = 0
    endpoint_failures = 0
    for path in paths:
        endpoint_failures += int(
            graph.vertices[path["vertices"][0]].boundary_side != "left"
            or graph.vertices[path["vertices"][-1]].boundary_side != "right"
        )
        for pattern in (path["required"], path["mask"] ^ path["required"]):
            directions = []
            for tail, head, edge in zip(
                path["vertices"], path["vertices"][1:], path["edges"]
            ):
                stored = graph.edges[edge]
                bit = (pattern >> edge) & 1
                oriented = stored if bit else (stored[1], stored[0])
                directions.append(1 if oriented == (tail, head) else -1)
            direction_failures += int(len(set(directions)) != 1)
    return {
        "paths": len(paths),
        "endpoint_failures": endpoint_failures,
        "directed_cycle_after_root_contraction_failures": direction_failures,
        "interpretation": "each registered path flip is a directed alpha-orientation cycle reversal through the contracted outer root",
    }


def _component_fragmentation(parity, charge_index, adjacency, even_states, odd_states):
    zero = coo_matrix((len(even_states), len(even_states)), dtype=np.int8)
    graph = bmat([[zero, adjacency], [adjacency.T, zero]], format="csr")
    component_count, component = connected_components(graph, directed=False)
    node_states = np.concatenate([even_states, odd_states])
    representative = np.full(component_count, len(parity), dtype=np.int64)
    np.minimum.at(representative, component, node_states)
    component_charge = charge_index[representative]
    record_count = int(charge_index.max()) + 1
    components_per_record = np.bincount(component_charge, minlength=record_count)
    sector_zero = np.bincount(charge_index[parity == 0], minlength=record_count)
    sector_one = np.bincount(charge_index[parity == 1], minlength=record_count)
    ambiguous = (sector_zero > 0) & (sector_one > 0)
    return {
        "switching_components": int(component_count),
        "records_split_into_multiple_switching_components": int(
            np.count_nonzero(components_per_record > 1)
        ),
        "ambiguous_records_split_into_multiple_switching_components": int(
            np.count_nonzero((components_per_record > 1) & ambiguous)
        ),
        "maximum_components_in_one_record": int(components_per_record.max()),
        "maximum_components_in_one_ambiguous_record": int(
            components_per_record[ambiguous].max()
        ),
    }


def _normalized_transport_audit(parity, charge_index, adjacency, even_states, odd_states):
    record_count = int(charge_index.max()) + 1
    sector_zero = np.bincount(charge_index[parity == 0], minlength=record_count).astype(
        np.int64
    )
    sector_one = np.bincount(charge_index[parity == 1], minlength=record_count).astype(
        np.int64
    )
    edge = adjacency.tocoo()
    left_count = len(even_states)
    right_count = len(odd_states)
    source = left_count + right_count
    sink = source + 1

    source_mask = sector_one[charge_index[even_states]] > 0
    sink_mask = sector_zero[charge_index[odd_states]] > 0
    edge_record = charge_index[even_states[edge.row]]
    rows = [
        np.full(np.count_nonzero(source_mask), source, dtype=np.int64),
        edge.row.astype(np.int64),
        left_count + np.flatnonzero(sink_mask),
    ]
    columns = [
        np.flatnonzero(source_mask),
        left_count + edge.col.astype(np.int64),
        np.full(np.count_nonzero(sink_mask), sink, dtype=np.int64),
    ]
    capacities = [
        sector_one[charge_index[even_states[source_mask]]],
        sector_zero[edge_record] * sector_one[edge_record],
        sector_zero[charge_index[odd_states[sink_mask]]],
    ]
    capacity = coo_matrix(
        (np.concatenate(capacities), (np.concatenate(rows), np.concatenate(columns))),
        shape=(sink + 1, sink + 1),
        dtype=np.int64,
    ).tocsr()
    target = int(np.sum(sector_zero * sector_one))
    flow = maximum_flow(capacity, source, sink)
    achieved = int(flow.flow_value)
    return {
        "transport_target": target,
        "transport_achieved": achieved,
        "deficit": target - achieved,
        "normalized_matching_property_all_charge_records": achieved == target,
        "certificate_interpretation": "for a record with sector sizes n0,n1, integral transport gives every sector-zero vertex supply n1 and every sector-one vertex demand n0; division by n0*n1 gives uniform normalized marginals",
    }


def _canonical_size_audit(size, plaquette_states):
    graph = square_graph(size)
    states, parity, charge_values, charge_index = _state_data(graph)
    bits = ((states[:, None] >> np.arange(len(graph.edges))) & 1).astype(np.int8)
    charges = bits @ charge_matrix(graph).T
    paths = _simple_crossing_paths(graph)
    adjacency, even_states, odd_states = _switching_adjacency(
        graph, states, parity, paths
    )
    orientation = _orientation_embedding_audit(graph, states, charges)
    root_cycles = _root_cycle_audit(graph, paths)
    components = _component_fragmentation(
        parity, charge_index, adjacency, even_states, odd_states
    )
    transport = _normalized_transport_audit(
        parity, charge_index, adjacency, even_states, odd_states
    )
    assert orientation["alpha_orientation_embedding"]
    assert root_cycles["endpoint_failures"] == 0
    assert root_cycles["directed_cycle_after_root_contraction_failures"] == 0
    assert transport["normalized_matching_property_all_charge_records"]
    return {
        "L": size,
        "edges": len(graph.edges),
        "current_states": len(states),
        "charge_records": len(charge_values),
        "orientation_embedding": orientation,
        "root_cycle_switches": root_cycles,
        "restricted_graph_fragmentation": components,
        "normalized_transport": transport,
        "internal_directed_plaquette_states": plaquette_states,
        "lattice_cover_alignment": (
            "false: internal directed-cycle reversals are valid alpha-orientation "
            "moves but preserve logical parity and are absent from the left-right "
            "root-cycle switching graph"
        ),
    }


def _edge_deleted_graph(graph, removed):
    kept = [(index, edge) for index, edge in enumerate(graph.edges) if index not in removed]
    logical = frozenset(
        new_index
        for new_index, (old_index, _) in enumerate(kept)
        if old_index in graph.logical_edges
    )
    return LatticeGraph(
        name=f"{graph.name}-edge-deleted",
        size=graph.size,
        vertices=graph.vertices,
        edges=tuple(edge for _, edge in kept),
        logical_edges=logical,
        logical_line=graph.logical_line,
    )


def _matching_gap(graph):
    states, parity, charge_values, charge_index = _state_data(graph)
    paths = _simple_crossing_paths(graph)
    if not paths:
        return None
    adjacency, _, _ = _switching_adjacency(graph, states, parity, paths)
    matching_size = int(
        np.count_nonzero(maximum_bipartite_matching(adjacency, perm_type="column") >= 0)
    )
    sector_zero = np.bincount(
        charge_index[parity == 0], minlength=len(charge_values)
    )
    sector_one = np.bincount(
        charge_index[parity == 1], minlength=len(charge_values)
    )
    bayes_numerator = int(np.minimum(sector_zero, sector_one).sum())
    return {
        "paths": len(paths),
        "switching_edges": int(adjacency.nnz),
        "maximum_matching": matching_size,
        "bayes_numerator": bayes_numerator,
        "gap": bayes_numerator - matching_size,
    }


def _deletion_counterexample_matrix():
    graph = square_graph(4)
    tested = {"single": 0, "double": 0}
    disconnected = {"single": 0, "double": 0}
    first_gap = None
    minimum_matching_fraction = Fraction(1, 1)
    for order, label in ((1, "single"), (2, "double")):
        for removed in itertools.combinations(range(len(graph.edges)), order):
            audit = _matching_gap(_edge_deleted_graph(graph, frozenset(removed)))
            if audit is None:
                disconnected[label] += 1
                continue
            tested[label] += 1
            if audit["bayes_numerator"]:
                minimum_matching_fraction = min(
                    minimum_matching_fraction,
                    Fraction(audit["maximum_matching"], audit["bayes_numerator"]),
                )
            if audit["gap"] and first_gap is None:
                first_gap = {
                    "removed_edge_indices": list(removed),
                    "removed_edges": [list(graph.edges[index]) for index in removed],
                    **audit,
                }
    return {
        "base_graph": "canonical square L4",
        "single_edge_deletions_tested": tested["single"],
        "double_edge_deletions_tested": tested["double"],
        "deletions_without_left_right_path": disconnected,
        "first_Hall_gap": first_gap,
        "minimum_matching_fraction_of_bayes_numerator_exact": str(
            minimum_matching_fraction
        ),
        "interpretation": "no counterexample occurs in this bounded perturbation matrix; this is robustness evidence, not an all-size proof",
    }


def analyze():
    start = time.monotonic()
    switching = json.loads(SWITCHING_RESULT.read_text())
    plaquette_states = {
        row["L"]: row["local_plaquette"]["states_with_directed_plaquette"]
        for row in switching["size_audits"]
    }
    sizes = [
        _canonical_size_audit(size, plaquette_states[size]) for size in (3, 4)
    ]
    deletion_matrix = _deletion_counterexample_matrix()
    assert sizes[0]["normalized_transport"]["transport_target"] == 456
    assert sizes[1]["normalized_transport"]["transport_target"] == 1_253_808
    assert sizes[1]["restricted_graph_fragmentation"][
        "ambiguous_records_split_into_multiple_switching_components"
    ] == 578
    assert deletion_matrix["single_edge_deletions_tested"] == 18
    assert deletion_matrix["double_edge_deletions_tested"] == 153
    assert deletion_matrix["first_Hall_gap"] is None
    elapsed = time.monotonic() - start
    assert elapsed < 300

    source_files = [
        LAB / "scripts/audit_midpoint_all_size_matching_theorem.py",
        LAB / "scripts/check_midpoint_fractional_switching.py",
        LAB / "scripts/check_midpoint_switching_pairing.py",
        LAB / "scripts/current_oracle.py",
        LAB / "manifests/midpoint-all-size-matching-theorem-2026-09-20.json",
        FRACTIONAL_RESULT,
        SWITCHING_RESULT,
    ]
    return {
        "status": "complete_missing_restricted_orientation_NMP_theorem",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "canonical_size_audits": sizes,
        "counterexample_matrix": deletion_matrix,
        "primary_source_applicability": [
            {
                "source": "Felsner, Lattice Structures from Planar Graphs (2004), Theorem 1",
                "url": "https://doi.org/10.37236/1768",
                "supported": "plane alpha-orientations with prescribed outdegrees form a distributive lattice under directed-cycle reversals",
                "missing_for_this_problem": "the theorem uses the full alpha-orientation cycle-flip structure, not only root cycles whose pre-contraction endpoints lie on opposite rough arcs, and it does not assert normalized matching between this logical-parity split",
            },
            {
                "source": "Propp, Lattice structure for orientations of graphs",
                "url": "https://arxiv.org/abs/math/0209005",
                "supported": "orientations with fixed indegrees in a plane embedding admit a distributive-lattice structure under local moves",
                "missing_for_this_problem": "internal local moves preserve the logical sector and are excluded from the public switching graph; distributivity alone does not supply the required restricted Hall inequalities",
            },
            {
                "source": "Balachandran and Kush, The Normalized Matching Property in Random and Pseudorandom Bipartite Graphs",
                "url": "https://arxiv.org/abs/1908.02628",
                "supported": "NMP is a scaled Hall condition, with results for independent random or Thomason-pseudorandom bipartite graphs",
                "missing_for_this_problem": "the charge-conditioned switching graph is deterministic and highly dependent; no required pseudorandom edge-discrepancy hypothesis has been proved",
            },
            {
                "source": "Khuller, Naor and Klein, The Lattice Structure of Flow in Planar Graphs",
                "url": "https://doi.org/10.1137/0406038",
                "supported": "bounded integral planar circulations admit a distributive lattice via dual potentials and facial augmentation",
                "missing_for_this_problem": "the result does not give normalized matching for a logical-parity subgraph restricted to opposite-rough-boundary path augmentations",
            },
        ],
        "precise_missing_lemma": {
            "structural": "For every canonical square size and fixed interior charge, the bipartite graph of binary alpha-orientations joined only by directed root-cycle reversals connecting opposite rough arcs has the normalized matching property between logical sectors.",
            "probabilistic": "The normalized total minority mass 2^{-E} sum_Q min(N0(Q),N1(Q)) has a positive size-uniform lower bound (or positive liminf).",
            "separation": "the structural lemma identifies/saturates finite capacity; only the probabilistic lemma implies midpoint noncorrectability",
        },
        "decision": {
            "outcome": "explicit_missing_theorem_boundary_after_primary_source_and_exact_matrix_audit",
            "established": "Fixed charge embeds exactly into planar alpha-orientations, and every L3/L4 charge-record switching graph satisfies normalized matching. All 18 single-edge and 153 double-edge deletions of canonical L4 with a crossing retain minority-sector matching saturation.",
            "theorem_mismatch": "Published orientation/flow lattice theorems include internal cycle or face moves that our logical switching graph excludes; L4 has 578 ambiguous charge records split across multiple restricted components and 86528 states with an internal plaquette move.",
            "not_established": "No reviewed theorem proves normalized matching for the restricted opposite-rough-arc root-cycle graph, and no canonical all-size proof or counterexample is obtained.",
            "threshold_claim": "No square midpoint noncorrectability or decoding-threshold claim is promoted.",
        },
        "elapsed_seconds": elapsed,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        },
    }


def main():
    result = analyze()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
