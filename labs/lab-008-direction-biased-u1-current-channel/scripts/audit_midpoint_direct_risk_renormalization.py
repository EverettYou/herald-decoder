#!/usr/bin/env python3
"""Exact direct-risk reductions at the directed square midpoint."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

from check_midpoint_switching_pairing import (
    _path_available,
    _path_key,
    _simple_crossing_paths,
)
from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results" / "midpoint-direct-risk-renormalization-2026-09-20.json"


def exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def binary_entropy(a: int, b: int) -> float:
    total = a + b
    value = 0.0
    for count in (a, b):
        if count:
            probability = count / total
            value -= probability * math.log2(probability)
    return value


def enumerate_fibers(L: int):
    graph = square_graph(L)
    edge_count = len(graph.edges)
    assert edge_count <= 18
    incidence = charge_matrix(graph)
    fibers: dict[tuple[int, ...], list[list[int]]] = defaultdict(lambda: [[], []])
    rows = []
    for state in range(1 << edge_count):
        bits = ((state >> np.arange(edge_count)) & 1).astype(np.int8)
        charge = tuple(map(int, incidence @ bits))
        sector = sum(int(bits[edge]) for edge in graph.logical_edges) & 1
        fibers[charge][sector].append(state)
        rows.append((charge, sector))
    return graph, fibers, rows


def selector_second_moment(graph, fibers, ordered_paths) -> dict:
    edge_count = len(graph.edges)
    selected = {}
    for state in range(1 << edge_count):
        for path in ordered_paths:
            if _path_available(path, state):
                selected[state] = state ^ path["mask"]
                break

    majority_domain = 0
    second_moment = 0
    maximum_multiplicity = 0
    ambiguous_states = 0
    exact_minority = 0
    missing_selector_states = 0
    for sector_zero, sector_one in fibers.values():
        a, b = len(sector_zero), len(sector_one)
        exact_minority += min(a, b)
        if not a or not b:
            continue
        ambiguous_states += a + b
        majority = sector_zero if a >= b else sector_one
        missing_selector_states += sum(state not in selected for state in majority)
        multiplicity = Counter(selected[state] for state in majority if state in selected)
        majority_domain += len(majority)
        second_moment += sum(value * value for value in multiplicity.values())
        maximum_multiplicity = max(maximum_multiplicity, max(multiplicity.values()))

    assert missing_selector_states == 0
    bound = Fraction(majority_domain**2, (1 << edge_count) * second_moment)
    return {
        "ambiguous_states": ambiguous_states,
        "ambiguous_probability_exact": exact(Fraction(ambiguous_states, 1 << edge_count)),
        "majority_domain_states": majority_domain,
        "majority_domain_probability_exact": exact(Fraction(majority_domain, 1 << edge_count)),
        "preimage_multiplicity_second_moment": second_moment,
        "effective_size_biased_multiplicity_exact": exact(Fraction(second_moment, majority_domain)),
        "maximum_multiplicity": maximum_multiplicity,
        "Cauchy_direct_risk_lower_bound_exact": exact(bound),
        "Cauchy_direct_risk_lower_bound": float(bound),
        "exact_Bayes_risk_exact": exact(Fraction(exact_minority, 1 << edge_count)),
        "certificate_fraction_of_exact_risk": float(
            bound / Fraction(exact_minority, 1 << edge_count)
        ),
        "missing_selector_states": missing_selector_states,
    }


def reveal_profile(edge_count: int, rows) -> dict:
    dimension = len(rows[0][0])
    risks = []
    entropies = []
    for prefix_length in range(dimension + 1):
        counts: dict[tuple[int, ...], list[int]] = defaultdict(lambda: [0, 0])
        for charge, sector in rows:
            counts[charge[:prefix_length]][sector] += 1
        risk = Fraction(sum(min(a, b) for a, b in counts.values()), 1 << edge_count)
        entropy = sum(
            Fraction(a + b, 1 << edge_count) * binary_entropy(a, b)
            for a, b in counts.values()
        )
        risks.append(exact(risk))
        entropies.append(float(entropy))
    information_increments = [
        entropies[index] - entropies[index + 1]
        for index in range(len(entropies) - 1)
    ]
    return {
        "charge_prefix_lengths": list(range(dimension + 1)),
        "Bayes_risk_exact": risks,
        "conditional_logical_entropy_bits": entropies,
        "conditional_mutual_information_increment_bits": information_increments,
        "interpretation": "This fixed valid reveal order can concentrate all observed logical information in its final charge. Chain rule and martingale monotonicity alone therefore do not distribute a positive entropy floor across local reveals.",
    }


def exact_control(L: int) -> dict:
    graph, fibers, rows = enumerate_fibers(L)
    paths = sorted(_simple_crossing_paths(graph), key=lambda path: _path_key(path, graph))
    lower = selector_second_moment(graph, fibers, paths)
    upper = selector_second_moment(graph, fibers, list(reversed(paths)))
    return {
        "L": L,
        "edges": len(graph.edges),
        "measured_charge_dimension": len(rows[0][0]),
        "simple_rough_to_rough_paths": len(paths),
        "lower_extremal_selector": lower,
        "upper_extremal_selector": upper,
        "natural_charge_reveal": reveal_profile(len(graph.edges), rows),
    }


def main() -> None:
    controls = [exact_control(3), exact_control(4)]
    source_paths = [
        LAB / "scripts" / "audit_midpoint_direct_risk_renormalization.py",
        LAB / "scripts" / "check_midpoint_switching_pairing.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-direct-risk-renormalization-2026-09-20.json",
        LAB / "results" / "midpoint-switching-pairing-2026-09-20.json",
        LAB / "results" / "midpoint-charge-fiber-balance-theorem-2026-09-20.json",
    ]
    result = {
        "status": "complete_direct_reduction_missing_uniform_average_congestion",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "direct_average_congestion_lemma": {
            "setup": "On every ambiguous full-charge fiber, choose its majority sector and apply one deterministic residual-crossing selector to every majority state. Let A_L be the number of such domain states and m_y the number of selected preimages of target state y.",
            "inequality": "R_L >= A_L^2 / (2^E sum_y m_y^2) = (A_L/2^E)/kappa_L, where kappa_L=(sum_y m_y^2)/A_L.",
            "proof": "Within each fiber, Cauchy-Schwarz gives a_Q^2 <= s_Q sum_y m_y^2, where a_Q and s_Q are majority and minority counts. Sum over fibers and apply Cauchy-Schwarz once more.",
            "thermodynamic_sufficient_condition": "RSW supplies positive ambiguous mass and A_L is at least half that mass. A size-uniform upper bound on kappa_L for one full-record selector would therefore prove a positive physical Bayes-risk lower bound.",
            "boundary": "The finite exact values of kappa_L are controls only; no size-uniform bound is proved.",
        },
        "branch_matrix": {
            "full_record_renormalized_switching": {
                "outcome": "exact_direct_reduction_but_missing_uniform_second_moment_bound",
                "progress": "Worst-case selector congestion is replaced by the physical-domain second moment of preimage multiplicity. The exact certificate is positive and substantially below the true risk at L3/L4.",
                "missing_hypothesis": "A renormalization or arm-event theorem must bound kappa_L uniformly while retaining the entire external charge record. Ordinary RSW controls crossing existence but not selector-collision second moments after conditioning.",
            },
            "conditional_entropy_martingale": {
                "outcome": "chain_rule_is_exact_but_not_a_local_lower_bound",
                "progress": "For the frozen natural charge order, exact conditional risk and entropy are reported after every prefix.",
                "obstruction": "Conditional entropy decreases as charges are revealed, and the information increments can be concentrated in a late reveal. A lower bound for a partial record therefore does not lower-bound entropy after the full record; a new geometric upper bound on total information gain is required.",
            },
            "compatible_physical_obstruction": {
                "outcome": "finite_square_mechanism_exists_but_no_asymptotic_physical_family_is_constructed",
                "progress": "Canonical L4 already contains 96 physical K_(1,6) fibers of total mass 21/8192, showing that large local imbalance is compatible with the square channel.",
                "boundary": "Neither this finite family nor the abstract K_(1,M) model proves vanishing physical average risk. An asymptotic square-lattice family with controlled physical mass remains unconstructed.",
            },
        },
        "primary_source_applicability": [
            {
                "source": "O'Donnell, Saks, Schramm and Servedio, Every decision tree has an influential variable (2005)",
                "url": "https://arxiv.org/abs/cs/0508071",
                "supported": "OSSS bounds the variance of a product-space Boolean function by revealments times raw-coordinate influences.",
                "missing": "It does not lower-bound logical entropy remaining after the many-to-one full integer-charge observation, nor control the selector-collision second moment.",
            },
            {
                "source": "Schramm and Steif, Quantitative noise sensitivity and exceptional times for percolation (2010)",
                "url": "https://doi.org/10.4007/annals.2010.171.619",
                "supported": "low-revealment algorithms control Fourier levels of percolation crossing events.",
                "missing": "the full-charge posterior minority ratio and selector multiplicity are not crossing indicators or monotone events.",
            },
            {
                "source": "Aizenman, Duminil-Copin, Sidoravicius and Sly, Random currents and continuity of Ising model's spontaneous magnetization (2015)",
                "url": "https://doi.org/10.1007/s00220-015-2462-2",
                "supported": "the random-current switching lemma exactly exchanges source constraints under factorial current weights.",
                "missing": "this project has bounded directed binary currents, a fixed full divergence record and a logical-parity split, so the Ising source-switching identity does not provide the required map or averaged congestion bound.",
            },
        ],
        "decision": {
            "outcome": "promote_average_congestion_as_the_precise_direct_target",
            "established": "A positive midpoint Bayes-risk lower bound follows from RSW plus a size-uniform bound on the physical-domain selector multiplicity second moment kappa_L. This reduction avoids collision reweighting and worst-case congestion.",
            "not_established": "No reviewed theorem bounds kappa_L with the full charge record; the entropy chain rule alone and finite K_(1,6) fibers do not resolve the thermodynamic risk.",
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
