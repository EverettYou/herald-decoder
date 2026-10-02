#!/usr/bin/env python3
"""Test two-environment witness tails and bounded diamond-fan templates."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product

from audit_midpoint_selector_second_moment import (
    exact,
    path_orders,
    physical_majority_domains,
)
from audit_midpoint_shortest_selector_exchange import _selected_outputs
from check_midpoint_switching_pairing import _path_available, _simple_crossing_paths
from current_oracle import LAB, ROOT


RESULT = LAB / "results" / "midpoint-boundary-fan-tail-2026-09-21.json"


def _raw_first_exchange(path_left, path_right):
    def virtual(path):
        return ("LEFT",) + tuple(path["vertices"][1:-1]) + ("RIGHT",)

    left, right = virtual(path_left), virtual(path_right)
    prefix = 0
    while prefix < min(len(left), len(right)) and left[prefix] == right[prefix]:
        prefix += 1
    assert prefix > 0
    right_after = {vertex: index for index, vertex in enumerate(right[prefix:], prefix)}
    reconnect_left, reconnect_right, reconnection = min(
        (index, right_after[vertex], vertex)
        for index, vertex in enumerate(left[prefix:], prefix)
        if vertex in right_after
    )
    return left[prefix - 1], reconnection, reconnect_left, reconnect_right


def exact_tail_control(L: int) -> dict:
    graph, domains = physical_majority_domains(L)
    paths = path_orders(graph, _simple_crossing_paths(graph))[
        "shortest_then_lexicographic"
    ]
    outputs = _selected_outputs(graph, domains, paths)
    histogram = Counter(len(preimages) for preimages in outputs.values())
    maximum = max(histogram)
    tail = {}
    tail_sum = Fraction()
    for threshold in range(1, maximum + 1):
        count = sum(
            multiplicity * targets
            for multiplicity, targets in histogram.items()
            if multiplicity >= threshold
        )
        probability = Fraction(count, len(domains))
        tail[str(threshold)] = {
            "preimage_states": count,
            "probability_exact": exact(probability),
            "probability": float(probability),
        }
        tail_sum += probability
    second_moment = sum(multiplicity * multiplicity * targets for multiplicity, targets in histogram.items())
    kappa = Fraction(second_moment, len(domains))
    assert tail_sum == kappa

    ordered_alternates = 0
    signature_multiplicity = Counter()
    first_collision = None
    for target, preimages in outputs.items():
        for base_index, (_, _, base_path) in enumerate(preimages):
            signatures = []
            for alternate_index, (_, _, alternate_path) in enumerate(preimages):
                if base_index == alternate_index:
                    continue
                divergence, reconnection, _, _ = _raw_first_exchange(
                    base_path, alternate_path
                )
                signature = (
                    alternate_path["vertices"][0],
                    alternate_path["vertices"][-1],
                    divergence,
                    reconnection,
                )
                signatures.append(signature)
                ordered_alternates += 1
            counts = Counter(signatures)
            signature_multiplicity.update(counts.values())
            if counts and max(counts.values()) > 1 and first_collision is None:
                first_collision = {
                    "target": target,
                    "base_index": base_index,
                    "maximum_signature_multiplicity": max(counts.values()),
                }
    assert ordered_alternates == 2 * sum(
        targets * multiplicity * (multiplicity - 1) // 2
        for multiplicity, targets in histogram.items()
    )
    return {
        "L": L,
        "edges": len(graph.edges),
        "majority_domain_states": len(domains),
        "multiplicity_histogram": dict(sorted(histogram.items())),
        "tail_under_size_biased_majority_domain": tail,
        "tail_sum_exact": exact(tail_sum),
        "kappa_exact": exact(kappa),
        "tail_identity_replayed": tail_sum == kappa,
        "two_environment_witness": {
            "signature": "alternate rough endpoints + first virtual divergence + first virtual reconnection",
            "ordered_alternate_preimages": ordered_alternates,
            "signature_multiplicity_histogram": dict(sorted(signature_multiplicity.items())),
            "injective_on_exact_control": first_collision is None,
            "first_collision": first_collision,
            "boundary": "Finite injectivity does not bound the number or probability of signatures uniformly in L.",
        },
    }


def diamond_chain_paths(diamonds: int):
    paths = []
    for choices in product((0, 1), repeat=diamonds):
        mask = 0
        for index, branch in enumerate(choices):
            mask |= 1 << (4 * index + 2 * branch)
            mask |= 1 << (4 * index + 2 * branch + 1)
        paths.append({
            "choices": choices,
            "mask": mask,
            "required": 0,
            "edges": tuple(edge for edge in range(4 * diamonds) if mask >> edge & 1),
        })
    return paths


def diamond_chain_control(diamonds: int) -> dict:
    paths = diamond_chain_paths(diamonds)
    edge_count = 4 * diamonds
    histogram = Counter()
    for target in range(1 << edge_count):
        multiplicity = 0
        for path_index, path in enumerate(paths):
            preimage = target ^ path["mask"]
            selected = next(
                (
                    index
                    for index, candidate in enumerate(paths)
                    if _path_available(candidate, preimage)
                ),
                None,
            )
            multiplicity += int(selected == path_index)
        histogram[multiplicity] += 1
    domain_preimages = sum(multiplicity * targets for multiplicity, targets in histogram.items())
    second_moment = sum(
        multiplicity * multiplicity * targets
        for multiplicity, targets in histogram.items()
    )
    maximum = max(histogram)
    maximum_targets = histogram[maximum]
    return {
        "diamonds": diamonds,
        "edges": edge_count,
        "rough_to_rough_paths": len(paths),
        "target_multiplicity_histogram": dict(sorted(histogram.items())),
        "maximum_multiplicity": maximum,
        "maximum_multiplicity_targets": maximum_targets,
        "maximum_target_probability_under_uniform_target_exact": exact(
            Fraction(maximum_targets, 1 << edge_count)
        ),
        "maximum_event_first_moment_weight_exact": exact(
            Fraction(maximum * maximum_targets, 1 << edge_count)
        ),
        "domain_preimages": domain_preimages,
        "selector_kappa_exact": exact(Fraction(second_moment, domain_preimages)),
        "boundary": "This isolated diamond chain checks selector compatibility only. Embedding it in the full square requires suppressing outside earlier paths and restoring the physical majority-domain law.",
    }


def main() -> None:
    start = time.monotonic()
    exact_controls = [exact_tail_control(3), exact_tail_control(4)]
    template_controls = [diamond_chain_control(diamonds) for diamonds in range(1, 5)]
    assert exact_controls[0]["kappa_exact"] == "11/9"
    assert exact_controls[1]["kappa_exact"] == "3113/1605"
    assert all(
        control["two_environment_witness"]["injective_on_exact_control"]
        for control in exact_controls
    )
    assert [control["maximum_multiplicity"] for control in template_controls] == [1, 2, 4, 8]
    elapsed = time.monotonic() - start
    assert elapsed < 300
    source_paths = [
        LAB / "scripts" / "audit_midpoint_boundary_fan_tail.py",
        LAB / "scripts" / "audit_midpoint_shortest_selector_exchange.py",
        LAB / "scripts" / "audit_midpoint_selector_second_moment.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "manifests" / "midpoint-boundary-fan-tail-2026-09-20.json",
        LAB / "results" / "midpoint-shortest-selector-geodesic-exchange-2026-09-20.json",
    ]
    result = {
        "status": "complete_witness_injection_conditioning_gap_and_bounded_template",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": exact_controls,
        "diamond_chain_templates": template_controls,
        "branch_matrix": {
            "two_environment_witness_injection": {
                "outcome": "finite_injection_passes_but_uniform_signature_tail_is_open",
                "established": "For every ordered alternate preimage at L3/L4, alternate rough endpoints plus first virtual divergence/reconnection uniquely identify the alternate path relative to the base preimage.",
                "boundary": "The signature space grows with the boundary and bulk vertices. Exact injectivity alone gives no uniform count or probability tail.",
            },
            "disjoint_occurrence_probability": {
                "outcome": "BK_Reimer_product_measure_interface_fails_twice",
                "established": "BK/Reimer bounds disjoint occurrence witnessed in one configuration under a product measure; Reimer allows arbitrary events but retains those two interfaces.",
                "hypothesis_gap": "The alternate path is selected in a different preimage configuration, and kappa uses the majority-domain size-biased law. Lifting to two independent configurations still requires conditioning on their common selected target, which destroys the product law and induces collision weighting.",
            },
            "nested_fan_comb_template": {
                "outcome": "bounded_diamond_chain_is_selector_compatible_but_not_a_physical_square_obstruction",
                "established": "One through four square-embeddable diamonds have 2^n candidate paths and exact maximum selector multiplicity 2^(n-1) on 4n edges.",
                "boundary": "The isolated template omits all outside square paths and the physical majority-domain filter. Its finite uniform-target weights cannot be promoted into an all-size physical event or kappa divergence.",
            },
        },
        "primary_source_applicability": [
            {
                "source": "van den Berg and Kesten, Inequalities with applications to percolation and reliability (1985)",
                "url": "https://doi.org/10.2307/3213860",
                "supported": "BK bounds disjoint occurrence of increasing events in a finite product measure.",
                "missing": "the majority-domain size-biased law and witnesses selected in two different configurations",
            },
            {
                "source": "Reimer, Proof of the Van den Berg-Kesten Conjecture (2000)",
                "url": "https://doi.org/10.1017/S0963548399004113",
                "supported": "the disjoint-occurrence inequality extends to arbitrary events in a product probability space.",
                "missing": "Reimer still requires product measure and disjoint reasons inside one configuration",
            },
            {
                "source": "van den Berg and Jonasson, A BK inequality for randomly drawn subsets of fixed size (2012)",
                "url": "https://arxiv.org/abs/1105.3862",
                "supported": "a non-product BK extension holds for the special k-out-of-n law and increasing events.",
                "missing": "the full-charge fiber-majority selector law is not a k-out-of-n measure",
            },
        ],
        "precise_missing_lemma": "Under the physical majority-domain law, bound the probability that one selected target has at least r two-environment boundary-fan witnesses by a sequence g_r with sum_r g_r finite uniformly in L. Product-measure disjoint occurrence and finite witness injectivity do not supply this conditional tail.",
        "decision": {
            "outcome": "close_direct_BK_Reimer_shortcut_and_retain_conditional_tail_as_named_gap",
            "established": "The exact tail identity, finite witness injection and bounded selector-compatible diamond templates isolate both the combinatorial and probabilistic interfaces.",
            "not_established": "No uniform conditional fan tail, physical nested obstruction, uniform kappa bound, midpoint noncorrectability or square threshold is proved.",
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
