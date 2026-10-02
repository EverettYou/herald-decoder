#!/usr/bin/env python3
"""Classify selector collisions controlling the direct midpoint risk bound."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

from check_midpoint_switching_pairing import (
    _path_available,
    _path_key,
    _simple_crossing_paths,
)
from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results" / "midpoint-selector-second-moment-renormalization-2026-09-20.json"


def exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def physical_majority_domains(L: int):
    graph = square_graph(L)
    edge_count = len(graph.edges)
    assert edge_count <= 18
    incidence = charge_matrix(graph)
    fibers: dict[tuple[int, ...], list[list[int]]] = defaultdict(lambda: [[], []])
    for state in range(1 << edge_count):
        bits = ((state >> np.arange(edge_count)) & 1).astype(np.int8)
        charge = tuple(map(int, incidence @ bits))
        sector = sum(int(bits[edge]) for edge in graph.logical_edges) & 1
        fibers[charge][sector].append(state)
    domains = []
    for sector_zero, sector_one in fibers.values():
        if not sector_zero or not sector_one:
            continue
        domains.extend(sector_zero if len(sector_zero) >= len(sector_one) else sector_one)
    return graph, domains


def path_orders(graph, paths):
    lexicographic = sorted(paths, key=lambda path: _path_key(path, graph))
    return {
        "lexicographic_lower": lexicographic,
        "lexicographic_upper": list(reversed(lexicographic)),
        "shortest_then_lexicographic": sorted(
            paths, key=lambda path: (len(path["edges"]), _path_key(path, graph))
        ),
        "longest_then_lexicographic": sorted(
            paths, key=lambda path: (-len(path["edges"]), _path_key(path, graph))
        ),
    }


def symmetric_difference_geometry(graph, mask: int) -> tuple[int, int, int]:
    used_edges = [edge for edge in range(len(graph.edges)) if mask >> edge & 1]
    adjacency = defaultdict(list)
    degrees = Counter()
    for edge in used_edges:
        u, v = graph.edges[edge]
        adjacency[u].append(v)
        adjacency[v].append(u)
        degrees[u] += 1
        degrees[v] += 1
    seen = set()
    components = 0
    for vertex in adjacency:
        if vertex in seen:
            continue
        components += 1
        stack = [vertex]
        seen.add(vertex)
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    odd_rough = sum(
        degrees[vertex] % 2
        for vertex in degrees
        if graph.vertices[vertex].boundary_side is not None
    )
    odd_interior = sum(
        degrees[vertex] % 2
        for vertex in degrees
        if graph.vertices[vertex].boundary_side is None
    )
    return len(used_edges), components, odd_rough + 100 * odd_interior


def audit_order(graph, domains, ordered_paths) -> dict:
    outputs = defaultdict(list)
    missing = 0
    for state in domains:
        selected = None
        for path in ordered_paths:
            if _path_available(path, state):
                selected = path
                break
        if selected is None:
            missing += 1
            continue
        outputs[state ^ selected["mask"]].append((state, selected))
    assert missing == 0

    domain_size = len(domains)
    multiplicity_second_moment = sum(len(preimages) ** 2 for preimages in outputs.values())
    off_diagonal_pairs = 0
    edge_count_distribution = Counter()
    component_distribution = Counter()
    rough_endpoint_distribution = Counter()
    joint_geometry = Counter()
    same_path_off_diagonal = 0
    for target, preimages in outputs.items():
        multiplicity = len(preimages)
        off_diagonal_pairs += multiplicity * (multiplicity - 1) // 2
        for left in range(multiplicity):
            state_left, path_left = preimages[left]
            for right in range(left + 1, multiplicity):
                state_right, path_right = preimages[right]
                same_path_off_diagonal += int(path_left["mask"] == path_right["mask"])
                difference = path_left["mask"] ^ path_right["mask"]
                assert difference == state_left ^ state_right
                edges, components, packed_odds = symmetric_difference_geometry(graph, difference)
                odd_interior, odd_rough = divmod(packed_odds, 100)
                assert odd_interior == 0
                edge_count_distribution[edges] += 1
                component_distribution[components] += 1
                rough_endpoint_distribution[odd_rough] += 1
                joint_geometry[f"edges={edges};components={components};odd_rough={odd_rough}"] += 1

    assert same_path_off_diagonal == 0
    assert multiplicity_second_moment == domain_size + 2 * off_diagonal_pairs
    kappa = Fraction(multiplicity_second_moment, domain_size)
    risk_bound = Fraction(domain_size**2, (1 << len(graph.edges)) * multiplicity_second_moment)
    return {
        "domain_states": domain_size,
        "distinct_targets": len(outputs),
        "maximum_multiplicity": max(len(preimages) for preimages in outputs.values()),
        "preimage_multiplicity_second_moment": multiplicity_second_moment,
        "paired_identity": {
            "diagonal_ordered_pairs": domain_size,
            "off_diagonal_unordered_collision_pairs": off_diagonal_pairs,
            "identity": "sum_y m_y^2 = A_L + 2 N_offdiag",
            "replayed": multiplicity_second_moment == domain_size + 2 * off_diagonal_pairs,
        },
        "kappa_exact": exact(kappa),
        "kappa": float(kappa),
        "direct_risk_lower_bound_exact": exact(risk_bound),
        "direct_risk_lower_bound": float(risk_bound),
        "collision_geometry": {
            "symmetric_difference_edge_count": dict(sorted(edge_count_distribution.items())),
            "connected_components": dict(sorted(component_distribution.items())),
            "odd_rough_boundary_endpoints": dict(sorted(rough_endpoint_distribution.items())),
            "joint_class_count": dict(sorted(joint_geometry.items())),
            "same_path_off_diagonal_pairs": same_path_off_diagonal,
            "interior_odd_degree_failures": 0,
        },
    }


def exact_control(L: int) -> dict:
    graph, domains = physical_majority_domains(L)
    paths = _simple_crossing_paths(graph)
    orders = {
        name: audit_order(graph, domains, ordered)
        for name, ordered in path_orders(graph, paths).items()
    }
    kappas = {name: Fraction(value["kappa_exact"]) for name, value in orders.items()}
    best = min(kappas, key=kappas.get)
    average = sum(kappas.values(), Fraction()) / len(kappas)
    return {
        "L": L,
        "edges": len(graph.edges),
        "simple_rough_to_rough_paths": len(paths),
        "common_physical_majority_domain_states": len(domains),
        "order_matrix": orders,
        "finite_family_summary": {
            "orders": list(orders),
            "best_order": best,
            "best_kappa_exact": exact(kappas[best]),
            "family_average_kappa_exact": exact(average),
            "deterministic_averaging_consequence": "At least one registered order has kappa no larger than the finite-family average; this does not imply an all-size bound.",
        },
    }


def main() -> None:
    controls = [exact_control(3), exact_control(4)]
    source_paths = [
        LAB / "scripts" / "audit_midpoint_selector_second_moment.py",
        LAB / "scripts" / "audit_midpoint_direct_risk_renormalization.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-selector-second-moment-renormalization-2026-09-20.json",
        LAB / "results" / "midpoint-direct-risk-renormalization-2026-09-20.json",
    ]
    result = {
        "status": "complete_collision_identity_missing_summable_arm_bound",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "branch_matrix": {
            "paired_collision_geometry": {
                "outcome": "exact_identity_and_geometry_classification",
                "established": "The preimage second moment exactly equals the diagonal domain mass plus twice the number of unordered distinct majority-state pairs mapped to one target. Every off-diagonal pair is generated by the symmetric difference of two distinct selected rough-to-rough paths and has even interior degree.",
                "boundary": "The observed boundary-endpoint and component classes are finite exact controls; their L3/L4 frequencies are not arm exponents or a size trend.",
            },
            "finite_path_order_matrix": {
                "outcome": "bounded_order_choice_changes_constants_not_the_missing_theorem",
                "established": "Four deterministic orders use the identical physical majority domains. Their exact kappa values identify the best registered finite control before any order is preferred.",
                "boundary": "Finite averaging guarantees one order no worse than the family mean but supplies no uniform-in-L selector construction.",
            },
            "arm_event_theorem_audit": {
                "outcome": "standard_arm_results_do_not_bound_full_record_selector_collisions",
                "established": "Kesten-type RSW/quasi-multiplicativity controls prescribed open/closed arms across annuli. Exact polychromatic arm exponents are established for triangular-site percolation, not generally for square-bond percolation.",
                "hypothesis_gap": "Selector collisions are conditioned on the complete integer charge record and compare two state-dependent lowest/shortest/longest crossings. Their path symmetric difference can have zero, two, or four rough endpoints and multiple components; it is not a single prescribed monotone or alternating-arm event. A domination from each collision class to a summable physical arm event remains unproved.",
            },
            "compatible_divergence": {
                "outcome": "no_positive_mass_square_divergence_family_constructed",
                "established": "Finite controls contain multiplicities up to 16 and multiple collision topologies.",
                "boundary": "Neither finite multiplicity nor the abstract star model constructs a square-lattice event on which kappa_L diverges with positive physical mass.",
            },
        },
        "primary_source_applicability": [
            {
                "source": "Kesten, Scaling relations for 2D-percolation (1987)",
                "url": "https://doi.org/10.1007/BF01205674",
                "supported": "RSW-based arm estimates and quasi-multiplicative comparison methods for planar percolation events.",
                "missing": "a full-charge-conditioned domination of selector-collision pairs by one standard arm event with a summable bound.",
            },
            {
                "source": "Smirnov and Werner, Critical exponents for two-dimensional percolation (2001)",
                "url": "https://doi.org/10.4310/MRL.2001.v8.n6.a4",
                "supported": "exact critical arm exponents for site percolation on the triangular lattice.",
                "missing": "the exact-exponent result is not a square-bond theorem and the selector-collision classes are not identified with its alternating-arm events.",
            },
            {
                "source": "Schramm and Steif, Quantitative noise sensitivity and exceptional times for percolation (2010)",
                "url": "https://doi.org/10.4007/annals.2010.171.619",
                "supported": "algorithmic revealment controls Fourier levels of crossing indicators.",
                "missing": "a revealment/Fourier inequality for the full-charge-conditioned selector multiplicity second moment.",
            },
        ],
        "precise_missing_lemma": "Construct one full-record charge-preserving selector for which the expected preimage multiplicity seen from a uniformly chosen physical majority state, kappa_L, is bounded independently of L; equivalently, dominate every off-diagonal selector-collision class by a family of summable physical events without discarding the charge conditioning.",
        "decision": {
            "outcome": "close_standard_arm_shortcut_and_retain_kappa_as_open_target",
            "established": "The exact collision identity and bounded order matrix isolate what must be controlled. Existing planar arm and revealment theorems do not directly apply to the full-record, state-dependent collision classes.",
            "not_established": "No uniform kappa_L bound, divergence mechanism on positive physical mass, midpoint noncorrectability, or square decoding threshold is proved.",
            "threshold_claim": "No square midpoint noncorrectability or decoding-threshold claim is promoted.",
        },
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        },
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
