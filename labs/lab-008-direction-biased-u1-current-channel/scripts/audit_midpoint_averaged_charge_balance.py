#!/usr/bin/env python3
"""Exact two-copy and block-route audit for midpoint averaged balance."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results" / "midpoint-averaged-charge-balance-2026-09-20.json"


def exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def count_fibers(L: int) -> dict:
    graph = square_graph(L)
    E = len(graph.edges)
    assert E <= 18
    D = charge_matrix(graph)
    fibers: dict[tuple[int, ...], list[int]] = defaultdict(lambda: [0, 0])
    for state in range(1 << E):
        bits = ((state >> np.arange(E)) & 1).astype(np.int8)
        charge = tuple(map(int, D @ bits))
        sector = sum(int(bits[e]) for e in graph.logical_edges) & 1
        fibers[charge][sector] += 1

    denominator = 1 << E
    risk = Fraction(sum(min(a, b) for a, b in fibers.values()), denominator)
    collision = Fraction(sum((a + b) ** 2 for a, b in fibers.values()), denominator**2)
    opposite_overlap = Fraction(2 * sum(a * b for a, b in fibers.values()), denominator**2)
    maximum_record_probability = Fraction(max(a + b for a, b in fibers.values()), denominator)
    magnetization_second_moment = sum(
        Fraction((a - b) ** 2, denominator * (a + b)) for a, b in fibers.values()
    )
    posterior_variance = (1 - magnetization_second_moment) / 4
    assert posterior_variance <= risk <= 2 * posterior_variance
    assert risk >= opposite_overlap / (2 * maximum_record_probability)

    thresholds = [Fraction(1, 2), Fraction(1, 3), Fraction(1, 4), Fraction(1, 8), Fraction(1, 16)]
    balance_mass = {}
    for eta in thresholds:
        mass = sum(
            Fraction(a + b, denominator)
            for a, b in fibers.values()
            if min(a, b) and Fraction(min(a, b), a + b) >= eta
        )
        balance_mass[exact(eta)] = exact(mass)

    return {
        "L": L,
        "edges": E,
        "charge_records": len(fibers),
        "exact_Bayes_risk": exact(risk),
        "magnetization_second_moment": float(magnetization_second_moment),
        "posterior_variance_exact": exact(posterior_variance),
        "posterior_variance_risk_bounds_exact": [exact(posterior_variance), exact(2 * posterior_variance)],
        "same_charge_collision_probability_exact": exact(collision),
        "opposite_sector_same_charge_overlap_exact": exact(opposite_overlap),
        "collision_conditioned_opposite_sector_probability_exact": exact(opposite_overlap / collision),
        "maximum_record_probability_exact": exact(maximum_record_probability),
        "collision_to_maximum_record_probability_exact": exact(collision / maximum_record_probability),
        "overlap_lower_bound_on_risk_exact": exact(opposite_overlap / (2 * maximum_record_probability)),
        "physical_mass_with_minority_ratio_at_least": balance_mass,
    }


def abstract_countermodels() -> dict:
    return {
        "unnormalized_overlap_can_vanish_at_maximal_risk": {
            "construction": "N equiprobable charge records, each with balanced logical posterior",
            "Bayes_risk": "1/2",
            "same_charge_collision_probability": "1/N",
            "opposite_sector_same_charge_overlap": "1/(2N) -> 0",
            "collision_conditioned_opposite_probability": "1/2",
        },
        "normalized_overlap_can_stay_positive_while_risk_vanishes": {
            "construction": "one balanced record of mass epsilon=1/n and n^3 deterministic records sharing mass 1-epsilon",
            "Bayes_risk": "1/(2n) -> 0",
            "opposite_sector_same_charge_overlap": "1/(2n^2)",
            "same_charge_collision_probability": "1/n^2 + (1-1/n)^2/n^3",
            "collision_conditioned_opposite_probability_limit": "1/2",
        },
    }


def main() -> None:
    controls = [count_fibers(3), count_fibers(4)]
    source_paths = [
        LAB / "scripts" / "audit_midpoint_averaged_charge_balance.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-averaged-charge-balance-2026-09-20.json",
        LAB / "results" / "midpoint-charge-fiber-balance-theorem-2026-09-20.json",
        LAB / "results" / "midpoint-minority-mass-lower-bound-2026-09-20.json",
        LAB / "results" / "midpoint-switching-pairing-2026-09-20.json",
    ]
    result = {
        "status": "complete_overlap_and_block_routes_missing_global_average_lemma",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "exact_identities": {
            "physical_risk": "R_L=sum_Q p_Q r_Q",
            "magnetization": "m_Q=(N0-N1)/(N0+N1), so (1-E[m_Q^2])/4=E[r_Q(1-r_Q)] and (1-E[m_Q^2])/4 <= R_L <= (1-E[m_Q^2])/2",
            "two_copy_overlap": "O_L=Pr(Q1=Q2,H1!=H2)=sum_Q p_Q^2 2r_Q(1-r_Q)",
            "collision_normalization": "C_L=Pr(Q1=Q2)=sum_Q p_Q^2 and Psi_L=O_L/C_L uses the collision-size-biased charge law, not the physical charge law p_Q",
            "sufficient_conversion": "O_L <= 2 p_max,L R_L, hence R_L >= O_L/(2 p_max,L) = (Psi_L/2)(C_L/p_max,L)",
        },
        "branch_matrix": {
            "two_copy_overlap": {
                "outcome": "exact_observable_but_collision_bias_blocks_asymptotic_conversion",
                "established": "The overlap, collision normalization, magnetization moment and Bayes risk are exactly related and exhaustively verified on L3/L4.",
                "obstruction": "Neither unnormalized O_L nor normalized Psi_L alone lower-bounds the physical p_Q-weighted risk; explicit abstract probability models separate them.",
                "missing_input": "A positive lower bound on both Psi_L and C_L/p_max,L, or another comparison between collision-size-biased and physical charge laws.",
            },
            "multiscale_block": {
                "outcome": "local_gluing_does_not_supply_logical_charge_balance",
                "established": "A sector-changing charge-preserving move must contain an opposite-rough-side residual path; the exact L4 standalone plaquette audit has zero logical-parity flips.",
                "obstruction": "RSW/FKG can glue increasing crossing events, but fixed-charge posterior balance and bounded switching congestion are neither increasing events nor consequences of crossing existence.",
                "missing_input": "A positive-probability global event measurable under the physical current law on which the full-charge fiber admits size-uniform bounded congestion or minority ratio.",
            },
            "direct_average_profile": {
                "outcome": "finite_controls_only",
                "established": "Exact physical masses above fixed minority-ratio cutoffs are reported for L3/L4.",
                "boundary": "Two sizes are controls, not a trend or an asymptotic lower bound.",
            },
        },
        "countermodels": abstract_countermodels(),
        "primary_source_applicability": [
            {
                "source": "Lessa et al., Strong-to-Weak Spontaneous Symmetry Breaking in Mixed Quantum States (2024)",
                "url": "https://arxiv.org/abs/2405.03639",
                "supported": "nonlinear fidelity/Renyi observables can diagnose information hidden from one-copy averages",
                "missing": "the general two-copy motivation does not identify the collision-size-biased charge law with this project's physical p_Q-weighted decoding risk",
            },
            {
                "source": "Duminil-Copin, Introduction to Bernoulli percolation, Sections 2 and 4 (2018)",
                "url": "https://www.ihes.fr/~duminil/publi/2017percolation.pdf",
                "supported": "Harris-FKG and RSW control increasing connectivity and crossing events in Bernoulli percolation",
                "missing": "charge-conditioned logical posterior balance is not an increasing percolation event, so these results do not provide the required fiber comparison",
            },
        ],
        "precise_missing_lemma": {
            "direct_form": "There exist eta,delta>0 independent of L such that physical probability at least delta lies on full-charge fibers with minority ratio at least eta.",
            "two_copy_sufficient_form": "There exist c1,c2>0 independent of L such that Psi_L>=c1 and C_L/p_max,L>=c2.",
            "block_sufficient_form": "There is a positive-probability multiscale event on which a charge-preserving logical switch has uniformly bounded congestion after conditioning on the full global charge record.",
        },
        "decision": {
            "outcome": "explicit_missing_collision_to_physical_charge_comparison",
            "established": "The two-copy observable is exact but uses the wrong charge weighting by itself; local block gluing preserves connectivity information but does not supply logical charge-fiber balance.",
            "not_established": "No positive size-uniform physical average balance, midpoint noncorrectability, or square decoding threshold is proved.",
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
