#!/usr/bin/env python3
"""Exact width-three strip controls and transfer-state feasibility audit."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

from audit_midpoint_selector_second_moment import exact
from check_midpoint_switching_pairing import (
    _path_available,
    _path_key,
    _simple_crossing_paths,
)
from current_oracle import LAB, ROOT, charge_matrix
from herald_decoder.lattice_model import LatticeGraph, Vertex


RESULT = LAB / "results" / "midpoint-boundary-fan-strip-transfer-2026-09-21.json"
TRANSFER_CAP = 2_000_000


def width_three_strip(width: int) -> LatticeGraph:
    if width < 3:
        raise ValueError("strip width must be at least three columns")
    height = 3
    vertices = tuple(
        Vertex(
            float(x),
            float(y),
            detector=0 < x < width - 1,
            boundary_side="left" if x == 0 else "right" if x == width - 1 else None,
        )
        for y in range(height)
        for x in range(width)
    )
    edges = []
    for y in range(height):
        for x in range(width):
            vertex = y * width + x
            if x + 1 < width:
                edges.append((vertex, vertex + 1))
            if y + 1 < height and 0 < x < width - 1:
                edges.append((vertex, vertex + width))
    logical_edges = frozenset(
        edge
        for edge, (left, right) in enumerate(edges)
        if {left % width, right % width} == {width - 2, width - 1}
    )
    return LatticeGraph(
        name=f"square-strip-{width}x3",
        size=width,
        vertices=vertices,
        edges=tuple(edges),
        logical_edges=logical_edges,
        logical_line=(),
    )


def direct_control(width: int) -> dict:
    graph = width_three_strip(width)
    edge_count = len(graph.edges)
    assert edge_count <= 16
    incidence = charge_matrix(graph)
    fibers = defaultdict(lambda: [[], []])
    for state in range(1 << edge_count):
        bits = ((state >> np.arange(edge_count)) & 1).astype(np.int8)
        charge = tuple(map(int, incidence @ bits))
        sector = sum(int(bits[edge]) for edge in graph.logical_edges) & 1
        fibers[charge][sector].append(state)
    domains = []
    bayes_numerator = 0
    ambiguous_states = 0
    for sector_zero, sector_one in fibers.values():
        if not sector_zero or not sector_one:
            continue
        bayes_numerator += min(len(sector_zero), len(sector_one))
        ambiguous_states += len(sector_zero) + len(sector_one)
        domains.extend(
            sector_zero if len(sector_zero) >= len(sector_one) else sector_one
        )
    paths = sorted(
        _simple_crossing_paths(graph),
        key=lambda path: (len(path["edges"]), _path_key(path, graph)),
    )
    outputs = defaultdict(int)
    for state in domains:
        for path in paths:
            if _path_available(path, state):
                outputs[state ^ path["mask"]] += 1
                break
        else:
            raise AssertionError("majority-domain state lacks a crossing")
    histogram = Counter(outputs.values())
    second_moment = sum(multiplicity * multiplicity for multiplicity in outputs.values())
    kappa = Fraction(second_moment, len(domains))
    risk_bound = Fraction(len(domains) ** 2, (1 << edge_count) * second_moment)
    return {
        "width_columns": width,
        "height_rows": 3,
        "edges": edge_count,
        "measured_charge_dimension": 3 * (width - 2),
        "simple_rough_to_rough_paths": len(paths),
        "charge_fibers": len(fibers),
        "ambiguous_states": ambiguous_states,
        "physical_majority_domain_states": len(domains),
        "exact_Bayes_numerator": bayes_numerator,
        "target_multiplicity_histogram": dict(sorted(histogram.items())),
        "selector_second_moment": second_moment,
        "kappa_exact": exact(kappa),
        "maximum_multiplicity": max(histogram),
        "direct_risk_lower_bound_exact": exact(risk_bound),
    }


def charge_transfer(max_interior_columns: int = 12) -> dict:
    states = {((), left): 1 for left in range(8)}
    completed = []
    cap_hit = None
    for interior_columns in range(1, max_interior_columns + 1):
        next_states = defaultdict(int)
        stopped = False
        for (charge_prefix, left), count in states.items():
            left_bits = [(left >> row) & 1 for row in range(3)]
            for vertical in range(4):
                vertical_bits = [(vertical >> row) & 1 for row in range(2)]
                for right in range(8):
                    right_bits = [(right >> row) & 1 for row in range(3)]
                    charge = (
                        left_bits[0] - right_bits[0] - vertical_bits[0],
                        left_bits[1] - right_bits[1] + vertical_bits[0] - vertical_bits[1],
                        left_bits[2] - right_bits[2] + vertical_bits[1],
                    )
                    next_states[(charge_prefix + charge, right)] += count
                    if len(next_states) > TRANSFER_CAP:
                        stopped = True
                        break
                if stopped:
                    break
            if stopped:
                break
        width = interior_columns + 2
        if stopped:
            cap_hit = {
                "width_columns": width,
                "interior_columns": interior_columns,
                "states_observed_before_fail_closed": len(next_states),
                "registered_state_cap": TRANSFER_CAP,
            }
            break
        states = next_states
        fibers = defaultdict(lambda: [0, 0])
        for (charge, right), count in states.items():
            fibers[charge][right.bit_count() & 1] += count
        ambiguous = [(a, b) for a, b in fibers.values() if a and b]
        completed.append({
            "width_columns": width,
            "interior_columns": interior_columns,
            "edges": 5 * width - 7,
            "frontier_charge_prefix_states": len(states),
            "charge_fibers": len(fibers),
            "ambiguous_charge_fibers": len(ambiguous),
            "physical_majority_domain_states": sum(max(a, b) for a, b in ambiguous),
            "exact_Bayes_numerator": sum(min(a, b) for a, b in fibers.values()),
            "ambiguous_states": sum(a + b for a, b in ambiguous),
            "total_configurations": sum(states.values()),
        })
    return {"completed_widths": completed, "cap_hit": cap_hit}


def count_simple_paths(width: int) -> int:
    graph = width_three_strip(width)
    left = {i for i, vertex in enumerate(graph.vertices) if vertex.boundary_side == "left"}
    right = {i for i, vertex in enumerate(graph.vertices) if vertex.boundary_side == "right"}
    adjacency = [[] for _ in graph.vertices]
    for u, v in graph.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    count = 0
    for start in left:
        stack = [(start, frozenset((start,)))]
        while stack:
            vertex, visited = stack.pop()
            for neighbor in adjacency[vertex]:
                if neighbor in visited or neighbor in left:
                    continue
                if neighbor in right:
                    count += 1
                elif graph.vertices[neighbor].boundary_side is None:
                    stack.append((neighbor, visited | {neighbor}))
    return count


def selector_transfer_profile(max_width: int = 12) -> list[dict]:
    profile = []
    for width in range(3, max_width + 1):
        paths = count_simple_paths(width)
        pair_channels = paths * paths
        profile.append({
            "width_columns": width,
            "edges": 5 * width - 7,
            "simple_paths": paths,
            "ordered_path_pair_channels": pair_channels,
            "pair_channels_exceed_registered_cap": pair_channels > TRANSFER_CAP,
        })
    return profile


def main() -> None:
    start = time.monotonic()
    direct = [direct_control(3), direct_control(4)]
    transfer = charge_transfer()
    profile = selector_transfer_profile()
    assert direct[0]["kappa_exact"] == "11/9"
    assert direct[1]["kappa_exact"] == "3984/1963"
    for control in direct:
        replay = next(
            row for row in transfer["completed_widths"]
            if row["width_columns"] == control["width_columns"]
        )
        assert replay["charge_fibers"] == control["charge_fibers"]
        assert replay["physical_majority_domain_states"] == control["physical_majority_domain_states"]
        assert replay["exact_Bayes_numerator"] == control["exact_Bayes_numerator"]
    assert transfer["completed_widths"][-1]["width_columns"] == 5
    assert transfer["cap_hit"]["width_columns"] == 6
    elapsed = time.monotonic() - start
    assert elapsed < 300
    source_paths = [
        LAB / "scripts" / "audit_midpoint_boundary_fan_strip_transfer.py",
        LAB / "scripts" / "audit_midpoint_boundary_fan_tail.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-boundary-fan-strip-transfer-2026-09-21.json",
        LAB / "results" / "midpoint-boundary-fan-tail-2026-09-21.json",
    ]
    result = {
        "status": "complete_embedded_controls_and_selector_transfer_state_obstruction",
        "physical_parameters": {"geometry": "width-three square strip", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "embedded_model": {
            "vertices": "three rows and W columns",
            "rough_boundaries": "all x=0 and x=W-1 vertices are unmeasured left/right rough boundaries",
            "measured_charges": "integer divergence at every vertex in the W-2 interior columns",
            "edges": "all horizontal nearest-neighbor edges plus vertical edges only in interior columns",
            "logical_cut": "the three horizontal edges entering the right rough boundary",
            "selector": "shortest path first, then the frozen lexicographic y/edge order",
        },
        "direct_controls": direct,
        "charge_majority_transfer": transfer,
        "selector_transfer_profile": profile,
        "branch_matrix": {
            "embedded_fan": {
                "outcome": "fan_multiplicity_survives_first_full_square_strip_embedding",
                "established": "The W=4, height-three strip includes all square-strip paths, full interior charge and the physical majority filter. It has A=3926, second moment 7968, kappa=3984/1963 and maximum multiplicity five.",
                "boundary": "W=3 and W=4 are exact controls, not a growth rate or all-width obstruction.",
            },
            "charge_majority_transfer": {
                "outcome": "exact_denominator_reaches_W5_then_registered_state_cap_blocks_W6",
                "established": "The column transfer replays all W3/W4 fibers and reaches W5 with 144464 prefix/frontier states, 80182 charge fibers, majority-domain denominator 108978 and Bayes numerator 55496.",
                "obstruction": "The W6 transition was stopped as soon as it created 2000001 states, above the registered 2000000-state cap.",
            },
            "selector_second_moment_transfer": {
                "outcome": "full_charge_transfer_does_not_carry_the_nonlocal_selector_moment",
                "established": "The exact second moment decomposes into ordered selected-path-pair channels. Simple-path counts and channel counts are profiled through W12.",
                "obstruction": "Charge-prefix/frontier states merge configurations with different earlier-path availability. Retaining the ordered selector predicates with the charge-majority trie is an unresolved automaton; the uncompressed path-pair channel count exceeds two million at W8. No W5 selector second moment was evaluated.",
            },
        },
        "decision": {
            "outcome": "embedded_fan_survives_finitely_but_registered_transfer_stops_at_selector_automaton_interface",
            "established": "Outside square-strip paths and the physical majority filter do not destroy finite multiplicity at W4; the exact charge denominator is transferable one width farther.",
            "not_established": "No fixed-width kappa rate, physical divergence obstruction, uniform kappa bound, midpoint noncorrectability or two-dimensional threshold is proved.",
            "threshold_claim": "No threshold claim is promoted.",
        },
        "precise_missing_interface": "Construct a reduced decision diagram or equivalent frontier automaton that carries, for every target, all earlier-path availability predicates needed by the shortest selector together with the full-charge majority-sector trie; validate it on W3/W4 before evaluating W5.",
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
