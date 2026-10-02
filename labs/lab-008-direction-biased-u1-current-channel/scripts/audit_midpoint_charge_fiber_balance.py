#!/usr/bin/env python3
"""Exact charge-fiber balance controls at the directed square midpoint."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results" / "midpoint-charge-fiber-balance-theorem-2026-09-20.json"


def exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def binary_entropy(r: float) -> float:
    if r <= 0.0 or r >= 1.0:
        return 0.0
    return -r * math.log2(r) - (1.0 - r) * math.log2(1.0 - r)


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

    ambiguous = [(Q, a, b) for Q, (a, b) in fibers.items() if a and b]
    max_ratio = max(Fraction(max(a, b), min(a, b)) for _, a, b in ambiguous)
    witnesses = [
        (Q, a, b)
        for Q, a, b in ambiguous
        if Fraction(max(a, b), min(a, b)) == max_ratio
    ]
    bayes_numerator = sum(min(a, b) for _, a, b in ambiguous)
    entropy = sum(
        Fraction(a + b, 1 << E) * binary_entropy(a / (a + b))
        for _, a, b in ambiguous
    )
    risk = Fraction(bayes_numerator, 1 << E)
    optimal_congestion = math.ceil(max_ratio)
    witness_Q, witness_a, witness_b = sorted(witnesses)[0]
    witness_mass = Fraction(sum(a + b for _, a, b in witnesses), 1 << E)
    return {
        "L": L,
        "edges": E,
        "current_states": 1 << E,
        "charge_records": len(fibers),
        "ambiguous_charge_records": len(ambiguous),
        "exact_Bayes_risk": exact(risk),
        "conditional_logical_entropy_bits": float(entropy),
        "entropy_square_certificate": float(entropy * entropy / 4),
        "maximum_charge_fiber_sector_ratio_exact": exact(max_ratio),
        "records_attaining_maximum_ratio": len(witnesses),
        "physical_mass_of_maximum_ratio_records_exact": exact(witness_mass),
        "optimal_deterministic_switching_congestion": optimal_congestion,
        "optimality_reason": "pigeonhole lower bound plus the exact record-wise NMP capacity certificate",
        "first_maximum_ratio_witness": {
            "Q": list(witness_Q),
            "sector_counts": [witness_a, witness_b],
            "switching_graph": (
                f"K_{{1,{max(witness_a, witness_b)}}}"
                if min(witness_a, witness_b) == 1
                else "not a star"
            ),
        },
    }


def main() -> None:
    controls = [count_fibers(3), count_fibers(4)]
    selector = json.loads(
        (LAB / "results" / "midpoint-switching-pairing-2026-09-20.json").read_text()
    )
    selector_C = {
        row["L"]: row["lower_extremal_selector"]["all_eligible_map_maximum_multiplicity"]
        for row in selector["size_audits"]
    }
    for row in controls:
        row["extremal_selector_congestion"] = selector_C[row["L"]]

    source_paths = [
        LAB / "scripts" / "audit_midpoint_charge_fiber_balance.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-charge-fiber-balance-theorem-2026-09-20.json",
        LAB / "results" / "midpoint-switching-pairing-2026-09-20.json",
        LAB / "results" / "midpoint-all-size-matching-theorem-2026-09-20.json",
    ]
    result = {
        "status": "complete_finite_balance_controls_missing_averaged_theorem",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "branch_matrix": {
            "switching_congestion": {
                "outcome": "finite_optimum_exact_no_uniform_theorem",
                "theorem": "For a charge fiber with sector sizes n0,n1 whose switching graph has NMP in both directions, the minimum deterministic image congestion is ceil(max(n0/n1,n1/n0)).",
                "proof": "Pigeonhole gives the lower bound. Scaled Hall/NMP gives a capacitated matching from the larger sector with that ceiling capacity, while the smaller sector injects into the larger.",
                "control": "The best possible global congestion is 2 on L3 and 6 on L4, improving the extremal selector's 3 and 16 but providing no all-size bound."
            },
            "conditional_entropy": {
                "outcome": "exact_equivalent_target_no_closure_theorem",
                "identity": "H(logical sector | Q)=E_Q h2(r_Q), where r_Q is conditional Bayes risk.",
                "bounds": "For 0<=r<=1/2, 2r<=h2(r)<=2 sqrt(r). Therefore 2 R_L <= H(H|Q) <= 2 sqrt(R_L), and H(H|Q)>=eta implies R_L>=eta^2/4.",
                "control": "Exact finite conditional entropies are reported, but no reviewed fixed-divergence binary-flow theorem lower-bounds them uniformly in size."
            },
            "canonical_imbalance": {
                "outcome": "finite_physical_star_found_no_unbounded_family",
                "control": "Canonical L4 contains 96 maximum-imbalance records of sector ratio 6; each minority-one witness has physical switching graph K_{1,6}. Their total physical mass is 21/8192.",
                "boundary": "This rejects exact or near-unity every-record balance at finite size, but neither two sizes nor a finite K_{1,6} witness proves unbounded all-size imbalance. No analytic canonical family was established."
            }
        },
        "primary_source_applicability": [
            {
                "source": "Mészáros and Morales, Flow polytopes and the Kostant partition function (2012)",
                "url": "https://doi.org/10.46298/dmtcs.3096",
                "supported": "integer-flow counts can be represented by Kostant partition functions and flow polytopes",
                "missing": "the results concern unrestricted nonnegative integral flows and do not compare bounded binary logical-parity sectors under rough-boundary charge conditioning"
            },
            {
                "source": "Kapoor, Mészáros and Setiabrata, Counting integer points of flow polytopes (2019)",
                "url": "https://arxiv.org/abs/1906.05592",
                "supported": "Ehrhart and Kostant formulas count lattice points of integral flow polytopes",
                "missing": "no size-uniform lower bound on the parity split or conditional logical entropy of the canonical binary square fibers"
            },
            {
                "source": "Felsner, Lattice Structures from Planar Graphs (2004)",
                "url": "https://doi.org/10.37236/1768",
                "supported": "fixed-outdegree planar orientations form a distributive lattice under full cycle reversals",
                "missing": "lattice order does not bound charge-fiber sector ratios or average minority mass"
            }
        ],
        "precise_missing_lemma": {
            "averaged_balance": "There exist eta,delta>0 independent of L such that physical probability at least delta lies on charge fibers with min(N0,N1)/(N0+N1)>=eta.",
            "entropy_equivalent": "Equivalently sufficient is a positive size-uniform lower bound on H(logical sector | measured integer charge).",
            "congestion_sufficient": "A uniformly bounded-congestion switching map on a positive-probability crossing event implies the averaged-balance lemma."
        },
        "decision": {
            "outcome": "explicit_missing_averaged_charge_fiber_lemma",
            "established": "Optimal finite switching congestion is exactly 2 on L3 and 6 on L4; canonical L4 realizes physical K_{1,6} star fibers; conditional logical entropy is an exact equivalent asymptotic target with an elementary risk certificate.",
            "not_established": "No size-uniform physical congestion, conditional-entropy lower bound, or analytic family with unbounded sector imbalance is proved.",
            "threshold_claim": "No square midpoint noncorrectability or decoding-threshold claim is promoted."
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
