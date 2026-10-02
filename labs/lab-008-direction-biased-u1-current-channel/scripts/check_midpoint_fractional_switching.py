"""Exact L3/L4 matching audit for midpoint single-path switching.

The vertices are binary directed-current configurations at p=1/2, q=1.
Within each measured charge record, opposite logical sectors are joined when
one residual-directed simple rough-to-rough path flip maps one current to the
other.  The script computes an exact maximum integral matching, replays every
matched edge, and supplies a matching-size vertex-cover dual certificate.

For a bipartite graph with unit vertex capacities the fractional matching
polytope is integral.  Consequently the integral matching is also an optimal
symmetric fractional-flow certificate; fractional weights cannot exceed it.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import json
import time

import numpy as np
from scipy.sparse import bmat, coo_matrix
from scipy.sparse.csgraph import connected_components, maximum_bipartite_matching

from check_midpoint_switching_pairing import _simple_crossing_paths
from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results/midpoint-fractional-switching-2026-09-20.json"
PREDECESSOR = LAB / "results/midpoint-switching-pairing-2026-09-20.json"


def _state_data(graph):
    edge_count = len(graph.edges)
    state_count = 1 << edge_count
    states = np.arange(state_count, dtype=np.uint32)
    parity = np.zeros(state_count, dtype=np.uint8)
    for edge in graph.logical_edges:
        parity ^= ((states >> edge) & 1).astype(np.uint8)

    bits = ((states[:, None] >> np.arange(edge_count)) & 1).astype(np.int8)
    charges = bits @ charge_matrix(graph).T
    charge_values, charge_index = np.unique(charges, axis=0, return_inverse=True)
    return states, parity, charge_values, charge_index


def _switching_adjacency(graph, states, parity, paths):
    even_states = np.flatnonzero(parity == 0)
    odd_states = np.flatnonzero(parity == 1)
    even_index = np.full(len(states), -1, dtype=np.int32)
    odd_index = np.full(len(states), -1, dtype=np.int32)
    even_index[even_states] = np.arange(len(even_states), dtype=np.int32)
    odd_index[odd_states] = np.arange(len(odd_states), dtype=np.int32)

    rows = []
    columns = []
    for path in paths:
        restricted = states & path["mask"]
        available = (restricted == path["required"]) | (
            restricted == (path["mask"] ^ path["required"])
        )
        sources = states[available]
        images = sources ^ path["mask"]
        keep = parity[sources] == 0
        rows.append(even_index[sources[keep]])
        columns.append(odd_index[images[keep]])

    rows = np.concatenate(rows)
    columns = np.concatenate(columns)
    adjacency = coo_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(even_states), len(odd_states)),
    ).tocsr()
    adjacency.sum_duplicates()
    adjacency.data[:] = 1
    return adjacency, even_states, odd_states


def _size_audit(size, selector_pairs):
    graph = square_graph(size)
    states, parity, charge_values, charge_index = _state_data(graph)
    paths = _simple_crossing_paths(graph)
    adjacency, even_states, odd_states = _switching_adjacency(
        graph, states, parity, paths
    )

    edges = adjacency.tocoo()
    edge_even_states = even_states[edges.row]
    edge_odd_states = odd_states[edges.col]
    edge_charge_failures = int(
        np.count_nonzero(
            charge_index[edge_even_states] != charge_index[edge_odd_states]
        )
    )
    edge_parity_failures = int(
        np.count_nonzero(parity[edge_even_states] == parity[edge_odd_states])
    )
    assert edge_charge_failures == 0
    assert edge_parity_failures == 0

    record_count = len(charge_values)
    sector_zero_counts = np.bincount(
        charge_index[parity == 0], minlength=record_count
    )
    sector_one_counts = np.bincount(
        charge_index[parity == 1], minlength=record_count
    )
    record_minority = np.minimum(sector_zero_counts, sector_one_counts)
    bayes_numerator = int(record_minority.sum())

    matching = maximum_bipartite_matching(adjacency, perm_type="column")
    matched_rows = np.flatnonzero(matching >= 0)
    matched_columns = matching[matched_rows]
    assert len(matching) == len(even_states)
    assert len(np.unique(matched_columns)) == len(matched_columns)
    assert np.all(adjacency[matched_rows, matched_columns].A1 == 1)
    matched_even_states = even_states[matched_rows]
    matched_odd_states = odd_states[matched_columns]
    assert np.all(
        charge_index[matched_even_states] == charge_index[matched_odd_states]
    )
    matching_size = len(matched_rows)
    matched_by_record = np.bincount(
        charge_index[matched_even_states], minlength=record_count
    )
    record_saturation_failures = int(
        np.count_nonzero(matched_by_record != record_minority)
    )

    # An explicit minimum vertex-cover upper bound: for each charge record,
    # select every vertex in its smaller sector (sector zero on ties).  Every
    # switching edge stays within one record and therefore touches this cover.
    cover_sector = np.where(sector_zero_counts <= sector_one_counts, 0, 1)
    edge_covered = (cover_sector[charge_index[edge_even_states]] == 0) | (
        cover_sector[charge_index[edge_odd_states]] == 1
    )
    vertex_cover_failures = int(np.count_nonzero(~edge_covered))
    vertex_cover_size = int(record_minority.sum())

    # Connected-component accounting diagnoses whether disconnected switching
    # classes cause an additional Hall deficit inside a charge record.
    zero = coo_matrix((len(even_states), len(even_states)), dtype=np.int8)
    full_graph = bmat(
        [[zero, adjacency], [adjacency.T, zero]], format="csr", dtype=np.int8
    )
    component_count, component = connected_components(full_graph, directed=False)
    node_states = np.concatenate([even_states, odd_states])
    component_sizes = np.bincount(component, minlength=component_count)
    component_zero = np.bincount(
        component, weights=(parity[node_states] == 0), minlength=component_count
    ).astype(np.int64)
    component_one = np.bincount(
        component, weights=(parity[node_states] == 1), minlength=component_count
    ).astype(np.int64)
    active_components = np.flatnonzero(component_sizes > 1)
    component_minority_sum = int(
        np.minimum(component_zero[active_components], component_one[active_components]).sum()
    )

    even_degree = np.diff(adjacency.indptr)
    odd_degree = np.asarray(adjacency.sum(axis=0)).ravel().astype(np.int64)
    degree = np.concatenate([even_degree, odd_degree])
    active_degree = degree[degree > 0]
    degree_histogram = {
        str(int(value)): int(count)
        for value, count in sorted(Counter(active_degree.tolist()).items())
    }

    assert matching_size == bayes_numerator
    assert vertex_cover_size == matching_size
    assert vertex_cover_failures == 0
    assert record_saturation_failures == 0
    assert component_minority_sum == matching_size

    state_count = len(states)
    ambiguous_records = int(
        np.count_nonzero((sector_zero_counts > 0) & (sector_one_counts > 0))
    )
    return {
        "L": size,
        "edges": len(graph.edges),
        "current_states": state_count,
        "charge_records": record_count,
        "ambiguous_charge_records": ambiguous_records,
        "simple_rough_to_rough_paths": len(paths),
        "unique_switching_edges": int(adjacency.nnz),
        "switching_edge_charge_failures": edge_charge_failures,
        "switching_edge_parity_failures": edge_parity_failures,
        "maximum_integral_matching_pairs": matching_size,
        "bayes_numerator_sum_min_sector_counts": bayes_numerator,
        "record_saturation_failures": record_saturation_failures,
        "finite_Bayes_LER_exact": str(Fraction(bayes_numerator, state_count)),
        "selector_stable_pairs": selector_pairs,
        "additional_pairs_over_selector": matching_size - selector_pairs,
        "matching_fraction_of_bayes_numerator_exact": str(
            Fraction(matching_size, bayes_numerator)
        ),
        "fractional_certificate": {
            "construction": "put symmetric weight one on each integral matching edge and zero elsewhere",
            "total_weight": matching_size,
            "maximum_vertex_load": 1,
            "bipartite_integrality": True,
            "fractional_optimum_equals_integral_optimum": True,
        },
        "dual_vertex_cover": {
            "construction": "within every charge record select all vertices of its smaller sector; choose sector zero on ties",
            "size": vertex_cover_size,
            "uncovered_switching_edges": vertex_cover_failures,
            "equals_matching_size": vertex_cover_size == matching_size,
        },
        "component_audit": {
            "all_components_including_isolates": int(component_count),
            "active_components": len(active_components),
            "isolated_states": int(np.count_nonzero(component_sizes == 1)),
            "balanced_active_components": int(
                np.count_nonzero(
                    component_zero[active_components] == component_one[active_components]
                )
            ),
            "unbalanced_active_components": int(
                np.count_nonzero(
                    component_zero[active_components] != component_one[active_components]
                )
            ),
            "largest_active_component": int(component_sizes[active_components].max()),
            "maximum_active_component_sector_imbalance": int(
                np.max(
                    np.abs(
                        component_zero[active_components]
                        - component_one[active_components]
                    )
                )
            ),
            "sum_component_minority_sizes": component_minority_sum,
            "component_decomposition_gap_to_bayes_numerator": (
                bayes_numerator - component_minority_sum
            ),
        },
        "path_degree_audit": {
            "active_states": int(len(active_degree)),
            "minimum_active_degree": int(active_degree.min()),
            "maximum_active_degree": int(active_degree.max()),
            "mean_active_degree_exact": str(
                Fraction(int(active_degree.sum()), len(active_degree))
            ),
            "degree_histogram": degree_histogram,
            "interpretation": "positive degree is crossing existence; degree counts alone do not imply Hall expansion",
        },
    }


def analyze():
    start = time.monotonic()
    predecessor = json.loads(PREDECESSOR.read_text())
    stable_pairs = {
        row["L"]: row["lower_extremal_selector"][
            "certified_disjoint_cross_sector_pairs"
        ]
        for row in predecessor["size_audits"]
    }
    sizes = [_size_audit(size, stable_pairs[size]) for size in (3, 4)]
    assert sizes[0]["maximum_integral_matching_pairs"] == 112
    assert sizes[1]["maximum_integral_matching_pairs"] == 94792
    assert sizes[0]["unique_switching_edges"] == 352
    assert sizes[1]["unique_switching_edges"] == 580608
    elapsed = time.monotonic() - start
    assert elapsed < 300

    source_files = [
        LAB / "scripts/check_midpoint_fractional_switching.py",
        LAB / "scripts/check_midpoint_switching_pairing.py",
        LAB / "scripts/current_oracle.py",
        LAB / "manifests/midpoint-fractional-switching-2026-09-20.json",
        PREDECESSOR,
    ]
    return {
        "status": "complete_finite_saturation_missing_uniform_theorem",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "graph_definition": "within each full measured charge record, join opposite-sector binary currents iff one residual-directed simple rough-to-rough path flip maps them",
        "optimization_definition": "unit-capacity bipartite maximum matching; symmetric fractional edge flow has the same optimum by bipartite matching-polytope integrality",
        "size_audits": sizes,
        "controller_audit": {
            "path_count": "exact vertex degree; useful finite diagnostic but no degree-only lower bound supplies all-subset Hall expansion",
            "crossing_existence": "equivalent to positive switching degree and therefore insufficient by itself to bound paired mass",
            "crossing_cluster_or_arm_event": "a possible analytic route only if it yields size-uniform neighborhood capacity or a positive-density family of pairable components",
            "required_asymptotic_statement": "a size-uniform lower bound on maximum matching density, or an explicit all-size injection/mass transport with bounded congestion",
        },
        "decision": {
            "outcome": "exact_L3_L4_saturation_but_missing_asymptotic_capacity_theorem",
            "established": "For every L3/L4 charge record, maximum single-path matching saturates the smaller logical sector. The matching equals the Bayes numerator and an explicit same-size vertex cover, so the integral and fractional optima are exact.",
            "selector_comparison": "Removing the deterministic selector recovers 26 additional pairs at L3 and 38086 at L4 over the selector-stable construction.",
            "finite_only": "The exact matching densities are 7/16 at L3 and 11849/32768 at L4. Two sizes and finite saturation do not bound the thermodynamic limit.",
            "not_established": "No all-size Hall theorem, bounded-congestion mass transport, or size-uniform positive matching-density event has been proved.",
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
