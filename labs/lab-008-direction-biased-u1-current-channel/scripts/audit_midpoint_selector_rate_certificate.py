#!/usr/bin/env python3
"""Bounded all-width selector-rate certificate matrix."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict

import numpy as np

from audit_midpoint_boundary_fan_strip_transfer import count_simple_paths, width_three_strip
from audit_midpoint_selector_automaton_feasibility import exact_selector_table
from check_midpoint_switching_pairing import (
    _path_available,
    _path_key,
    _simple_crossing_paths,
)
from current_oracle import LAB, ROOT, charge_matrix


RESULT = LAB / "results" / "midpoint-selector-rate-certificate-2026-09-21.json"
STATE_CAP = 2_000_000


def _compact_bits(state: int, edges: list[int]) -> int:
    return sum(((state >> edge) & 1) << index for index, edge in enumerate(edges))


def charge_frontier_counterexample() -> dict:
    """Find a same-local-key, same-suffix pair with different selected paths."""
    width = 4
    graph = width_three_strip(width)
    edge_count = len(graph.edges)
    incidence = charge_matrix(graph)
    detector_vertices = [index for index, vertex in enumerate(graph.vertices) if vertex.detector]
    first_column_rows = [
        row for row, vertex in enumerate(detector_vertices)
        if int(graph.vertices[vertex].x) == 1
    ]

    def x(vertex: int) -> int:
        return int(graph.vertices[vertex].x)

    prefix_edges = []
    frontier_edges = []
    for edge, (left, right) in enumerate(graph.edges):
        columns = {x(left), x(right)}
        if columns == {0, 1} or x(left) == x(right) == 1 or columns == {1, 2}:
            prefix_edges.append(edge)
        if columns == {1, 2}:
            frontier_edges.append(edge)
    suffix_edges = [edge for edge in range(edge_count) if edge not in prefix_edges]
    _, outputs = exact_selector_table(width)
    paths = sorted(
        _simple_crossing_paths(graph),
        key=lambda path: (len(path["edges"]), _path_key(path, graph)),
    )
    groups = defaultdict(list)
    for state, target in enumerate(outputs):
        if target < 0:
            continue
        bits = ((state >> np.arange(edge_count)) & 1).astype(np.int8)
        charge = tuple(map(int, incidence @ bits))
        selected_path = next(
            index for index, path in enumerate(paths) if _path_available(path, state)
        )
        key = (
            tuple(charge[row] for row in first_column_rows),
            _compact_bits(state, frontier_edges),
            _compact_bits(state, suffix_edges),
        )
        groups[key].append({
            "prefix_assignment": _compact_bits(state, prefix_edges),
            "full_state": state,
            "selected_path_index": selected_path,
            "selected_target": target,
            "full_charge": charge,
        })
    for key, rows in groups.items():
        for left_index, left in enumerate(rows):
            for right in rows[left_index + 1 :]:
                if (
                    left["full_charge"] == right["full_charge"]
                    and left["selected_path_index"] != right["selected_path_index"]
                ):
                    return {
                        "width_columns": width,
                        "candidate_key": "processed-column charge, three frontier bits and identical unprocessed suffix",
                        "key_value": {
                            "processed_charge": list(key[0]),
                            "frontier_bits": key[1],
                            "suffix_bits": key[2],
                        },
                        "prefix_edges": prefix_edges,
                        "frontier_edges": frontier_edges,
                        "suffix_edges": suffix_edges,
                        "left": left,
                        "right": right,
                        "same_full_charge": True,
                        "different_selected_paths": True,
                        "different_selected_targets": left["selected_target"] != right["selected_target"],
                        "conclusion": "charge/frontier plus a common suffix is not a congruence for the shortest-selector map",
                    }
    raise AssertionError("expected charge/frontier selector counterexample was not found")


def zero_background_family() -> list[dict]:
    """Audit the natural family consisting of path-only inputs mapping to zero."""
    rows = []
    for width in (3, 4, 5):
        control, outputs = exact_selector_table(width)
        selected_to_zero = sum(target == 0 for target in outputs)
        rows.append({
            "width_columns": width,
            "simple_path_configurations": control["simple_paths"],
            "physical_majority_states_mapping_to_zero": selected_to_zero,
            "physical_probability_numerator_at_p_half": selected_to_zero,
            "physical_probability_denominator_at_p_half": control["configurations"],
            "passes_positive_physical_weight_gate": selected_to_zero > 0,
        })
    return rows


def path_count_tail_audit() -> list[dict]:
    rows = []
    for width in range(3, 13):
        path_count = count_simple_paths(width)
        monotone_family = 3 ** (width - 1)
        assert path_count >= monotone_family
        rows.append({
            "width_columns": width,
            "simple_paths": path_count,
            "explicit_x_monotone_paths": monotone_family,
            "pointwise_selector_tail_cutoff": f"Pr(M_W >= r)=0 for r>{path_count}",
        })
    return rows


def main() -> None:
    start = time.monotonic()
    counterexample = charge_frontier_counterexample()
    family = zero_background_family()
    tail = path_count_tail_audit()
    assert [row["physical_majority_states_mapping_to_zero"] for row in family] == [0, 0, 0]
    assert counterexample["same_full_charge"]
    assert counterexample["different_selected_paths"]
    assert (1 << 23) > STATE_CAP
    elapsed = time.monotonic() - start
    assert elapsed < 300
    source_paths = [
        LAB / "scripts" / "audit_midpoint_selector_rate_certificate.py",
        LAB / "scripts" / "audit_midpoint_selector_automaton_feasibility.py",
        LAB / "scripts" / "audit_midpoint_boundary_fan_strip_transfer.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "manifests" / "midpoint-selector-rate-certificate-2026-09-21.json",
        LAB / "results" / "midpoint-selector-automaton-feasibility-2026-09-21.json",
    ]
    result = {
        "status": "complete_no_all_width_rate_certificate_three_precise_obstructions",
        "physical_parameters": {"geometry": "width-three square strip", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "symbolic_recurrence_audit": {
            "local_state_counterexample": counterexample,
            "W6_extensional_truth_table": {
                "edges": 23,
                "configurations": 1 << 23,
                "registered_state_cap": STATE_CAP,
                "evaluated": False,
                "reason": "the extensional input table alone exceeds the registered state cap before reduction",
            },
        },
        "embedded_family_audit": family,
        "uniform_tail_audit": {
            "pointwise_fact": "M_W(y) is at most the number P_W of simple rough-to-rough paths",
            "path_counts": tail,
            "all_width_lower_family": "There are exactly 3^(W-1) x-monotone paths: choose the incoming left row and the outgoing row independently at each of W-2 interior columns.",
            "uniform_summability_result": "The pointwise cutoff is not uniformly summable because P_W is unbounded (indeed P_W >= 3^(W-1)); its width supremum is one at every finite tail index.",
        },
        "branch_matrix": {
            "symbolic_width_recursion": {
                "outcome": "candidate_charge_frontier_quotient_rejected_at_W4",
                "established": "States 79 and 106 have the same full charge, processed-column charge, frontier bits and common suffix, but select path indices 0 and 2 and produce different targets.",
                "obstruction": "A valid quotient must retain an exact earlier-path availability language; the extensional W6 input table has 8388608 states and was not built.",
            },
            "physical_probability_embedded_family": {
                "outcome": "natural_zero_background_fan_has_zero_physical_majority_weight",
                "established": "Although there are 9, 29 and 95 path-only configurations at W=3,4,5, none is in the physical majority domain and selected to the zero target.",
                "obstruction": "Path multiplicity without a positive physical majority-domain numerator cannot lower-bound kappa.",
            },
            "uniform_fan_tail_upper_bound": {
                "outcome": "path_count_cutoff_is_valid_but_not_uniformly_summable",
                "established": "M_W is pointwise bounded by the simple-path count, and the exact counts are recorded through W=12.",
                "obstruction": "The cutoff grows at least as 3^(W-1), so it gives no width-uniform summable envelope for Pr(M_W>=r).",
            },
        },
        "decision": {
            "outcome": "no_all_width_selector_rate_certificate_within_registered_matrix",
            "established": "Each of the three preregistered routes stops at a distinct exact interface: noncongruent local state, zero physical weight for the natural embedded family, and a nonsummable deterministic tail cutoff.",
            "not_established": "No upper or lower asymptotic rate for kappa, uniform kappa bound, nonzero limiting Bayes risk, midpoint noncorrectability or two-dimensional threshold is established.",
            "threshold_claim": "No threshold claim is promoted.",
        },
        "precise_missing_lemma": "Either construct a finite-state congruence for the two-environment shortest-selector language that composes with full-charge majority, or construct a positive-majority-probability nested fan family; otherwise prove a genuinely width-uniform summable multiplicity tail.",
        "elapsed_seconds": elapsed,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        },
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
