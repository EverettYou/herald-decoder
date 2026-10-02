#!/usr/bin/env python3
"""Audit geodesic-exchange and collision-fan routes for the shortest selector."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

from audit_midpoint_selector_second_moment import (
    exact,
    path_orders,
    physical_majority_domains,
    symmetric_difference_geometry,
)
from check_midpoint_switching_pairing import _path_available, _simple_crossing_paths
from current_oracle import LAB, ROOT, charge_matrix


RESULT = LAB / "results" / "midpoint-shortest-selector-geodesic-exchange-2026-09-20.json"


def _fraction(value: int, total: int) -> dict:
    ratio = Fraction(value, total)
    return {"count": value, "exact": exact(ratio), "value": float(ratio)}


def _first_virtual_exchange(path_left, path_right) -> dict:
    """Return the first divergence/reconnection after collapsing each rough side."""

    def virtual(path):
        return ("LEFT",) + tuple(path["vertices"][1:-1]) + ("RIGHT",)

    left = virtual(path_left)
    right = virtual(path_right)
    prefix = 0
    while prefix < min(len(left), len(right)) and left[prefix] == right[prefix]:
        prefix += 1
    assert prefix > 0 and prefix < max(len(left), len(right))
    divergence = left[prefix - 1]
    right_after = {vertex: index for index, vertex in enumerate(right[prefix:], prefix)}
    candidates = [
        (index, right_after[vertex], vertex)
        for index, vertex in enumerate(left[prefix:], prefix)
        if vertex in right_after
    ]
    assert candidates
    reconnect_left, reconnect_right, reconnection = min(candidates)
    return {
        "divergence": str(divergence),
        "reconnection": str(reconnection),
        "left_branch_edges": reconnect_left - (prefix - 1),
        "right_branch_edges": reconnect_right - (prefix - 1),
    }


def _selected_outputs(graph, domains, ordered_paths):
    outputs = defaultdict(list)
    for state in domains:
        for rank, path in enumerate(ordered_paths):
            if _path_available(path, state):
                outputs[state ^ path["mask"]].append((state, rank, path))
                break
        else:  # pragma: no cover - exact controls assert this is impossible
            raise AssertionError("majority-domain state lacks a residual crossing")
    return outputs


def exact_control(L: int) -> dict:
    graph, domains = physical_majority_domains(L)
    incidence = charge_matrix(graph)
    paths = path_orders(graph, _simple_crossing_paths(graph))[
        "shortest_then_lexicographic"
    ]
    outputs = _selected_outputs(graph, domains, paths)
    multiplicity_histogram = Counter(len(preimages) for preimages in outputs.values())
    second_moment = sum(
        multiplicity * multiplicity * targets
        for multiplicity, targets in multiplicity_histogram.items()
    )
    kappa = Fraction(second_moment, len(domains))

    checks = Counter()
    endpoint_classes = Counter()
    length_difference = Counter()
    exchange_components = Counter()
    first_exchange_shapes = Counter()
    collision_pairs = 0
    closed_same_endpoint_pairs = 0
    equal_length_pairs = 0

    for target, preimages in outputs.items():
        target_bits = np.array(
            [(target >> edge) & 1 for edge in range(len(graph.edges))], dtype=np.int8
        )
        for state, rank, path in preimages:
            state_bits = np.array(
                [(state >> edge) & 1 for edge in range(len(graph.edges))], dtype=np.int8
            )
            checks["preimages"] += 1
            checks["selector_replay"] += int(
                next(
                    index
                    for index, candidate in enumerate(paths)
                    if _path_available(candidate, state)
                )
                == rank
            )
            checks["target_replay"] += int((state ^ path["mask"]) == target)
            checks["charge_preservation"] += int(
                np.array_equal(incidence @ state_bits, incidence @ target_bits)
            )
            checks["logical_parity_flip"] += int(
                sum(
                    int(state_bits[edge] != target_bits[edge])
                    for edge in graph.logical_edges
                )
                % 2
                == 1
            )
        for left in range(len(preimages)):
            for right in range(left + 1, len(preimages)):
                collision_pairs += 1
                path_left = preimages[left][2]
                path_right = preimages[right][2]
                same_left = path_left["vertices"][0] == path_right["vertices"][0]
                same_right = path_left["vertices"][-1] == path_right["vertices"][-1]
                endpoint_classes[
                    f"same_left={same_left};same_right={same_right}"
                ] += 1
                difference = abs(len(path_left["edges"]) - len(path_right["edges"]))
                length_difference[difference] += 1
                equal_length_pairs += int(difference == 0)
                _, components, packed_odds = symmetric_difference_geometry(
                    graph, path_left["mask"] ^ path_right["mask"]
                )
                odd_interior, odd_rough = divmod(packed_odds, 100)
                assert odd_interior == 0
                exchange_components[components] += 1
                closed_same_endpoint_pairs += int(same_left and same_right)
                witness = _first_virtual_exchange(path_left, path_right)
                first_exchange_shapes[
                    f"left={witness['left_branch_edges']};right={witness['right_branch_edges']}"
                ] += 1
                checks["virtual_divergence_reconnection"] += 1
                if same_left and same_right:
                    assert odd_rough == 0 and components == 1
                elif same_left or same_right:
                    assert odd_rough == 2 and components == 1
                else:
                    assert odd_rough == 4 and components == 2

    expected_pairs = sum(
        targets * multiplicity * (multiplicity - 1) // 2
        for multiplicity, targets in multiplicity_histogram.items()
    )
    assert collision_pairs == expected_pairs
    assert second_moment == len(domains) + 2 * collision_pairs
    assert all(checks[name] == checks["preimages"] for name in (
        "selector_replay", "target_replay", "charge_preservation", "logical_parity_flip"
    ))
    assert checks["virtual_divergence_reconnection"] == collision_pairs

    high_target_count = sum(
        targets for multiplicity, targets in multiplicity_histogram.items() if multiplicity >= 4
    )
    high_preimage_mass = sum(
        multiplicity * targets
        for multiplicity, targets in multiplicity_histogram.items()
        if multiplicity >= 4
    )
    high_second_moment = sum(
        multiplicity * multiplicity * targets
        for multiplicity, targets in multiplicity_histogram.items()
        if multiplicity >= 4
    )
    maximum = max(multiplicity_histogram)
    maximum_targets = [
        preimages for preimages in outputs.values() if len(preimages) == maximum
    ]
    max_core_edges = Counter()
    max_endpoint_pairs = Counter()
    max_path_length_ranges = Counter()
    for preimages in maximum_targets:
        common_mask = (1 << len(graph.edges)) - 1
        endpoint_pairs = set()
        lengths = []
        for _, _, path in preimages:
            common_mask &= path["mask"]
            endpoint_pairs.add((path["vertices"][0], path["vertices"][-1]))
            lengths.append(len(path["edges"]))
        max_core_edges[common_mask.bit_count()] += 1
        max_endpoint_pairs[len(endpoint_pairs)] += 1
        max_path_length_ranges[max(lengths) - min(lengths)] += 1

    return {
        "L": L,
        "edges": len(graph.edges),
        "simple_paths": len(paths),
        "majority_domain_states": len(domains),
        "distinct_targets": len(outputs),
        "multiplicity_histogram": dict(sorted(multiplicity_histogram.items())),
        "second_moment": second_moment,
        "kappa_exact": exact(kappa),
        "collision_pairs": collision_pairs,
        "integrity_checks": dict(checks),
        "exchange_matrix": {
            "endpoint_relation": dict(sorted(endpoint_classes.items())),
            "absolute_path_length_difference": dict(sorted(length_difference.items())),
            "symmetric_difference_components": dict(sorted(exchange_components.items())),
            "first_virtual_exchange_branch_lengths": dict(sorted(first_exchange_shapes.items())),
            "same_physical_endpoints_closed_cycle_pairs": _fraction(
                closed_same_endpoint_pairs, collision_pairs
            ),
            "equal_path_length_pairs": _fraction(equal_length_pairs, collision_pairs),
            "all_pairs_have_virtual_boundary_divergence_reconnection": True,
        },
        "collision_fan_control": {
            "targets_with_multiplicity_at_least_4": high_target_count,
            "preimage_mass_at_multiplicity_at_least_4": _fraction(
                high_preimage_mass, len(domains)
            ),
            "second_moment_from_multiplicity_at_least_4": _fraction(
                high_second_moment, second_moment
            ),
            "maximum_multiplicity": maximum,
            "maximum_multiplicity_targets": len(maximum_targets),
            "maximum_target_common_core_edge_count": dict(sorted(max_core_edges.items())),
            "maximum_target_distinct_rough_endpoint_pairs": dict(
                sorted(max_endpoint_pairs.items())
            ),
            "maximum_target_path_length_range": dict(sorted(max_path_length_ranges.items())),
        },
    }


def main() -> None:
    start = time.monotonic()
    controls = [exact_control(3), exact_control(4)]
    assert controls[0]["kappa_exact"] == "11/9"
    assert controls[1]["kappa_exact"] == "3113/1605"
    elapsed = time.monotonic() - start
    assert elapsed < 300
    source_paths = [
        LAB / "scripts" / "audit_midpoint_shortest_selector_exchange.py",
        LAB / "scripts" / "audit_midpoint_selector_second_moment.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-shortest-selector-geodesic-exchange-2026-09-20.json",
        LAB / "results" / "midpoint-selector-second-moment-renormalization-2026-09-20.json",
    ]
    result = {
        "status": "complete_two_environment_geodesic_exchange_gap",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "weakest_sufficient_counting_lemma": {
            "identity": "For X uniform on the physical majority domain, T(X) is the selected target and M=m_T(X), kappa_L=E[M]=sum_{r>=1} Pr(M>=r).",
            "sufficient_condition": "A size-uniform summable tail Pr(M>=r)<=g_r with sum_r g_r<infinity proves sup_L kappa_L<infinity and hence a positive midpoint Bayes-risk lower bound once RSW supplies positive majority-domain mass.",
            "exchange_requirements": [
                "encode every alternate preimage by a divergence/reconnection witness in the same full-record selector environment",
                "bound witness multiplicity, including choices of both rough endpoints and path length",
                "dominate the physical probability of realized witnesses by a uniformly summable family",
            ],
        },
        "branch_matrix": {
            "divergence_reconnection_encoding": {
                "outcome": "virtual_boundary_encoding_exists_but_closed_geodesic_exchange_is_not_exhaustive",
                "established": "After collapsing each rough side, every exact collision pair has a first divergence and reconnection and passes charge, logical-parity, target and selector replay checks.",
                "obstruction": "The usual same-endpoint closed exchange covers none of the L3 collisions and only 4,170 of 64,844 L4 collisions. Most pairs change one or both rough endpoints, and many have unequal lengths.",
            },
            "local_exchange_involution": {
                "outcome": "standard_same_environment_geodesic_swap_hypothesis_fails",
                "established": "Same-endpoint pairs form one closed symmetric-difference component, while one-endpoint and two-endpoint changes form open boundary fans with one and two components respectively.",
                "hypothesis_gap": "The two paths are shortest-selected in two different preimage states, not geodesics in one common edge environment. Standard equal-length geodesic subpath exchange therefore supplies neither selector preservation nor a bound on alternate endpoint choices.",
            },
            "positive_mass_collision_ladder": {
                "outcome": "finite_collision_fans_found_but_no_scale_stable_ladder",
                "established": "At L4, multiplicity-at-least-four targets contain 7,528 of 138,030 majority preimages and contribute 33,900 of 267,718 to the second moment. Eight targets have multiplicity eight and mix rough endpoint pairs and path lengths around a common core.",
                "boundary": "These are finite collision fans, not a nested cylinder event with a size-uniform positive physical probability. No compatible all-size ladder or divergence of kappa_L is established.",
            },
        },
        "precise_missing_lemma": "Control open boundary-fan exchanges across two selector environments: prove a uniform summable tail for the number of shortest-selected alternate paths, including variable rough endpoints and unequal path lengths, or construct a nested square event on which that number grows while its physical majority-domain probability does not erase the growth.",
        "decision": {
            "outcome": "close_naive_geodesic_exchange_and_retain_boundary_fan_tail_as_open_target",
            "established": "The registered exact exchange matrix replays both kappa controls and identifies the dominant collision mechanism as an open boundary fan rather than a same-endpoint geodesic loop.",
            "not_established": "No uniform kappa_L bound, positive-mass collision ladder, midpoint noncorrectability, or square decoding threshold is proved.",
            "threshold_claim": "No threshold claim is promoted.",
        },
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
