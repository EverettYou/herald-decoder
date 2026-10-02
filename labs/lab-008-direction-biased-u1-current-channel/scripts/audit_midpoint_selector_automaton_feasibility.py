#!/usr/bin/env python3
"""Exact selector-availability automaton feasibility matrix on width-three strips."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

from audit_midpoint_boundary_fan_strip_transfer import width_three_strip
from audit_midpoint_selector_second_moment import exact
from check_midpoint_switching_pairing import (
    _path_available,
    _path_key,
    _simple_crossing_paths,
)
from current_oracle import LAB, ROOT, charge_matrix


RESULT = LAB / "results" / "midpoint-selector-automaton-feasibility-2026-09-21.json"
STATE_CAP = 2_000_000


def exact_selector_table(width: int) -> tuple[dict, list[int]]:
    """Return exact strip statistics and the majority-domain selector map."""
    graph = width_three_strip(width)
    edge_count = len(graph.edges)
    incidence = charge_matrix(graph)
    paths = sorted(
        _simple_crossing_paths(graph),
        key=lambda path: (len(path["edges"]), _path_key(path, graph)),
    )
    fibers = defaultdict(lambda: [0, 0])
    records = []
    for state in range(1 << edge_count):
        bits = ((state >> np.arange(edge_count)) & 1).astype(np.int8)
        charge = tuple(map(int, incidence @ bits))
        sector = sum(int(bits[edge]) for edge in graph.logical_edges) & 1
        fibers[charge][sector] += 1
        records.append((charge, sector))

    selector_outputs = [-1] * (1 << edge_count)
    selected_path_histogram = Counter()
    target_counts = defaultdict(int)
    domain_size = 0
    bayes_numerator = 0
    ambiguous_states = 0
    for sector_zero, sector_one in fibers.values():
        if sector_zero and sector_one:
            bayes_numerator += min(sector_zero, sector_one)
            ambiguous_states += sector_zero + sector_one
    for state, (charge, sector) in enumerate(records):
        sector_zero, sector_one = fibers[charge]
        if not sector_zero or not sector_one:
            continue
        majority_sector = 0 if sector_zero >= sector_one else 1
        if sector != majority_sector:
            continue
        domain_size += 1
        for path_index, path in enumerate(paths):
            if _path_available(path, state):
                target = state ^ path["mask"]
                selector_outputs[state] = target
                target_counts[target] += 1
                selected_path_histogram[path_index] += 1
                break
        else:
            raise AssertionError("majority-domain state lacks an available crossing")

    multiplicity_histogram = Counter(target_counts.values())
    second_moment = sum(multiplicity * multiplicity for multiplicity in target_counts.values())
    ordered_alternate_pairs = sum(
        multiplicity * (multiplicity - 1) for multiplicity in target_counts.values()
    )
    assert second_moment == domain_size + ordered_alternate_pairs
    return {
        "width_columns": width,
        "edges": edge_count,
        "configurations": 1 << edge_count,
        "simple_paths": len(paths),
        "charge_fibers": len(fibers),
        "ambiguous_states": ambiguous_states,
        "physical_majority_domain_states": domain_size,
        "exact_Bayes_numerator": bayes_numerator,
        "selected_targets": len(target_counts),
        "target_multiplicity_histogram": dict(sorted(multiplicity_histogram.items())),
        "selector_second_moment": second_moment,
        "ordered_alternate_pairs": ordered_alternate_pairs,
        "paired_identity_replayed": True,
        "kappa_exact": exact(Fraction(second_moment, domain_size)),
        "maximum_multiplicity": max(multiplicity_histogram),
        "direct_risk_lower_bound_exact": exact(
            Fraction(domain_size * domain_size, (1 << edge_count) * second_moment)
        ),
        "selected_path_indices_used": len(selected_path_histogram),
    }, selector_outputs


def reduce_selector_mtbdd(outputs: list[int], edge_count: int) -> dict:
    """Reduce the exact selector/majority truth table as an ordered MTBDD."""
    terminal_labels = sorted(set(outputs))
    terminal_to_id = {label: index for index, label in enumerate(terminal_labels)}
    id_to_terminal = {index: label for label, index in terminal_to_id.items()}
    identifiers = [terminal_to_id[label] for label in outputs]
    nodes: dict[int, tuple[int, int, int]] = {}
    level_profile = []
    eliminated_equal_children = 0
    next_id = len(terminal_labels)
    for level in range(edge_count):
        canonical = {}
        next_identifiers = []
        for offset in range(0, len(identifiers), 2):
            low, high = identifiers[offset], identifiers[offset + 1]
            if low == high:
                node_id = low
                eliminated_equal_children += 1
            else:
                key = (level, low, high)
                node_id = canonical.get(key)
                if node_id is None:
                    node_id = next_id
                    next_id += 1
                    canonical[key] = node_id
                    nodes[node_id] = key
            next_identifiers.append(node_id)
        level_profile.append({
            "edge_variable": level,
            "unreduced_width": len(next_identifiers),
            "new_reduced_nodes": len(canonical),
            "unique_references": len(set(next_identifiers)),
        })
        identifiers = next_identifiers
    assert len(identifiers) == 1
    root = identifiers[0]

    def evaluate(state: int) -> int:
        node_id = root
        while node_id in nodes:
            level, low, high = nodes[node_id]
            node_id = high if (state >> level) & 1 else low
        return id_to_terminal[node_id]

    replay_mismatches = sum(evaluate(state) != label for state, label in enumerate(outputs))
    total_states = len(terminal_labels) + len(nodes)
    return {
        "variable_order": "edge indices 0..E-1, with edge 0 eliminated first",
        "reduction_key": "(edge variable, reduced low-child id, reduced high-child id)",
        "retained_semantics": {
            "charge_prefix": "encoded extensionally by the remaining subfunction; no charge-distinct continuation is merged",
            "frontier_data": "encoded extensionally by the remaining subfunction",
            "selected_target_relation": "terminal is the exact output edge mask, or -1 outside the physical majority domain",
            "earlier_path_availability": "encoded by the shortest-selector terminal map for every suffix assignment",
        },
        "terminals": len(terminal_labels),
        "internal_nodes": len(nodes),
        "total_states": total_states,
        "registered_state_cap": STATE_CAP,
        "within_registered_cap": total_states <= STATE_CAP,
        "full_unreduced_binary_tree_nodes": (1 << (edge_count + 1)) - 1,
        "eliminated_equal_child_nodes": eliminated_equal_children,
        "level_profile": level_profile,
        "truth_table_replay_mismatches": replay_mismatches,
        "anti_merge_gate_passed": replay_mismatches == 0,
    }


def main() -> None:
    start = time.monotonic()
    widths = []
    for width in (3, 4, 5):
        control, outputs = exact_selector_table(width)
        bdd = reduce_selector_mtbdd(outputs, control["edges"])
        assert bdd["anti_merge_gate_passed"]
        assert bdd["within_registered_cap"]
        control["reduced_selector_mtbdd"] = bdd
        control["target_pair_accumulator"] = {
            "key": "exact selected target edge mask",
            "states": control["selected_targets"],
            "within_registered_cap": control["selected_targets"] <= STATE_CAP,
            "ordered_pair_count": control["ordered_alternate_pairs"],
            "second_moment_from_pair_identity": control["physical_majority_domain_states"] + control["ordered_alternate_pairs"],
            "anti_merge_gate": "only identical complete target masks share an accumulator state",
        }
        widths.append(control)

    expected = {
        3: (126, 154, "11/9", 2),
        4: (3926, 7968, "3984/1963", 5),
        5: (108978, 336814, "168407/54489", 12),
    }
    for control in widths:
        assert (
            control["physical_majority_domain_states"],
            control["selector_second_moment"],
            control["kappa_exact"],
            control["maximum_multiplicity"],
        ) == expected[control["width_columns"]]
    elapsed = time.monotonic() - start
    assert elapsed < 300
    source_paths = [
        LAB / "scripts" / "audit_midpoint_selector_automaton_feasibility.py",
        LAB / "scripts" / "audit_midpoint_boundary_fan_strip_transfer.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-selector-automaton-feasibility-2026-09-21.json",
        LAB / "results" / "midpoint-boundary-fan-strip-transfer-2026-09-21.json",
    ]
    result = {
        "status": "complete_exact_W5_selector_moment_with_bounded_reduced_automaton",
        "physical_parameters": {"geometry": "width-three square strip", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "width_controls": widths,
        "branch_matrix": {
            "reduced_decision_diagram": {
                "outcome": "passes_W3_W4_replay_and_W5_cap_gate",
                "established": "The exact multi-terminal reduced decision diagram preserves majority membership and the complete shortest-selector target map with zero truth-table replay mismatches.",
                "boundary": "This is an extensional finite-width compilation, not a width-independent frontier recurrence.",
            },
            "target_pair_accumulator": {
                "outcome": "passes_W3_W4_replay_and_computes_W5_second_moment",
                "established": "Grouping only identical complete target masks gives the exact ordered collision-pair count and replays S=A+ordered_alternate_pairs at all three widths.",
                "boundary": "The accumulator enumerates all 2^18 W5 configurations and therefore does not establish scalable transfer complexity.",
            },
            "analytic_embedded_subfamily": {
                "outcome": "not_reached_because_both_exact_branches_passed",
                "established": "No substitute one-sided family bound was needed for the registered W5 feasibility question.",
                "boundary": "An analytic all-width family remains necessary for any divergence or boundedness claim.",
            },
        },
        "decision": {
            "outcome": "W5_selector_moment_is_exactly_feasible_but_no_rate_is_identified",
            "established": "At W=5, A=108978, selector second moment S=336814, kappa=168407/54489, and maximum multiplicity 12. The reduced exact selector map has 179446 total states, below the two-million cap, and a zero-mismatch replay.",
            "not_established": "Three finite widths do not establish exponential, polynomial or bounded kappa behavior, a nonzero limiting Bayes risk, midpoint noncorrectability or a two-dimensional threshold.",
            "threshold_claim": "No threshold claim is promoted.",
        },
        "next_interface": "Replace the extensional truth-table compilation by a symbolic width-recursive selector-availability automaton or prove an analytic all-width embedded-family bound before making any rate claim.",
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
