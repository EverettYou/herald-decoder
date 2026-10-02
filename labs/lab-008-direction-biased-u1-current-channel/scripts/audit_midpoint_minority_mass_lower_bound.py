#!/usr/bin/env python3
"""Audit zero-sampling routes from midpoint crossings to nonzero Bayes risk."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "midpoint-minority-mass-lower-bound-2026-09-20.json"


def load(name: str) -> dict:
    return json.loads((LAB / "results" / name).read_text())


def exact(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    switching = load("midpoint-switching-pairing-2026-09-20.json")
    matching = load("midpoint-fractional-switching-2026-09-20.json")
    orientation = load("midpoint-all-size-matching-theorem-2026-09-20.json")
    switching_by_L = {row["L"]: row for row in switching["size_audits"]}
    matching_by_L = {row["L"]: row for row in matching["size_audits"]}
    orientation_by_L = {row["L"]: row for row in orientation["canonical_size_audits"]}

    audits = []
    for L in (3, 4):
        sw = switching_by_L[L]
        mt = matching_by_L[L]
        ori = orientation_by_L[L]
        states = mt["current_states"]
        ambiguity = Fraction(sw["lower_extremal_selector"]["eligible_crossing_states"], states)
        congestion = sw["lower_extremal_selector"]["all_eligible_map_maximum_multiplicity"]
        congestion_bound = ambiguity / (congestion + 1)
        stable_bound = Fraction(sw["lower_extremal_selector"]["finite_Bayes_LER_pairing_lower_bound_exact"])
        risk = Fraction(mt["finite_Bayes_LER_exact"])
        distance = L - 1
        one_straight_channel = Fraction(1, 2 ** (distance - 1))
        straight_union = 1 - (1 - one_straight_channel) ** L
        audits.append(
            {
                "L": L,
                "edges": mt["edges"],
                "ambiguity_probability_exact": exact(ambiguity),
                "exact_Bayes_risk": exact(risk),
                "selector_maximum_congestion": congestion,
                "bounded_congestion_certificate_exact": exact(congestion_bound),
                "stable_involution_certificate_exact": exact(stable_bound),
                "normalized_matching_property": ori["normalized_transport"][
                    "normalized_matching_property_all_charge_records"
                ],
                "straight_channel_gadget": {
                    "rough_to_rough_distance": distance,
                    "one_fixed_channel_coherent_either_direction_probability_exact": exact(
                        one_straight_channel
                    ),
                    "L_edge_disjoint_straight_channels_union_probability_exact": exact(straight_union),
                },
            }
        )

    source_paths = [
        LAB / "scripts" / "audit_midpoint_minority_mass_lower_bound.py",
        LAB / "manifests" / "midpoint-minority-mass-lower-bound-2026-09-20.json",
        LAB / "results" / "midpoint-switching-pairing-2026-09-20.json",
        LAB / "results" / "midpoint-fractional-switching-2026-09-20.json",
        LAB / "results" / "midpoint-all-size-matching-theorem-2026-09-20.json",
    ]
    out = {
        "status": "complete_rsw_and_nmp_information_obstruction",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "finite_controls": audits,
        "branch_matrix": {
            "fixed_or_local_gadget": {
                "outcome": "rejected_as_uniform_lower_bound",
                "proof": "Any parity-switching path spans at least d=L-1 edges. A fixed path is coherently directed in either direction with probability 2^(1-d). For K(L) prechosen paths, the union bound is K(L)2^(1-d); every polynomial-size family therefore vanishes. The L edge-disjoint straight-channel construction is retained as the smallest exact control.",
                "boundary": "This rejects fixed or polynomially many prechosen spanning gadgets, not adaptive critical crossing constructions."
            },
            "crossing_or_arm_event": {
                "outcome": "ordinary_RSW_is_insufficient",
                "proof": "RSW lower-bounds the probability A_L that both sectors are supported. It contains no information about the charge-fiber ratio min(N0,N1)/(N0+N1). Reimer's disjoint-occurrence inequality is an upper bound on product-space events and likewise does not lower-bound that posterior ratio.",
                "needed_extra_observable": "A size-uniform lower bound on conditional sector balance, or a switching map on all crossing states with uniformly bounded charge-fiber congestion."
            },
            "bounded_congestion": {
                "outcome": "sufficient_lemma_identified_but_not_uniformly_proved",
                "lemma": "If a charge-preserving sector-switching map is defined on every ambiguous state and every image has at most C preimages, then n0<=C n1 and n1<=C n0 in every charge fiber, hence R_L>=Pr(A_L)/(C+1).",
                "finite_result": "The extremal selector gives C=3 on L3 and C=16 on L4. Its resulting exact certificates are positive but supply no size-uniform C; stable-involution mass likewise has no RSW lower bound."
            }
        },
        "information_theoretic_countermodel": {
            "graph_family": "complete bipartite K_{1,M}",
            "normalized_matching_property": True,
            "ambiguity_probability": "1",
            "minority_fraction": "1/(M+1)",
            "limit": "0 as M tends to infinity",
            "conclusion": "Even RSW-level nonvanishing support plus all-size NMP cannot imply nonzero normalized minority mass without a sector-balance or congestion theorem.",
            "scope": "This is a logical countermodel to the proposed inference, not a claim that K_{1,M} is realized by the square current channel."
        },
        "primary_source_applicability": [
            {
                "source": "Seymour and Welsh, Percolation probabilities on the square lattice (1978)",
                "url": "https://doi.org/10.1016/S0167-5060(08)70509-0",
                "supported": "critical planar box-crossing probabilities stay nondegenerate",
                "missing": "no charge-fiber posterior sector-count comparison"
            },
            {
                "source": "Reimer, Proof of the Van den Berg-Kesten Conjecture (2000)",
                "url": "https://doi.org/10.1017/S0963548399004113",
                "supported": "disjoint occurrence is upper-bounded by the product of event probabilities",
                "missing": "the inequality has the wrong direction and no posterior-fiber multiplicity control"
            },
            {
                "source": "Balachandran and Kush, The Normalized Matching Property in Random and Pseudorandom Bipartite Graphs (2021)",
                "url": "https://doi.org/10.37236/9148",
                "supported": "NMP is a scaled Hall condition",
                "missing": "NMP permits K_{1,M}, whose normalized minority mass vanishes"
            }
        ],
        "decision": {
            "outcome": "rigorous_information_obstruction",
            "established": "Ordinary crossing probability and even all-size NMP do not logically imply a positive Bayes-risk density. A uniformly bounded-congestion sector-switching map would suffice, and the exact L3/L4 selector certificates instantiate the lemma with C=3 and C=16.",
            "not_established": "No physical size-uniform congestion, conditional sector-balance, or minority-mass lower bound is proved.",
            "threshold_claim": "No square midpoint noncorrectability or decoding-threshold claim is promoted."
        },
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in source_paths},
    }
    RESULT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
