#!/usr/bin/env python3
"""Zero-sampling audit of collision-to-physical charge-law conversion."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from fractions import Fraction

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results" / "midpoint-charge-collision-comparison-2026-09-20.json"


def exact(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def exact_control(L: int) -> dict:
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
    totals = {charge: sum(counts) for charge, counts in fibers.items()}
    collision = Fraction(sum(value * value for value in totals.values()), denominator**2)
    overlap = Fraction(2 * sum(a * b for a, b in fibers.values()), denominator**2)
    maximum = max(totals.values())

    line_tests = 0
    line_violations: list[dict] = []
    dimension = len(next(iter(totals)))
    for charge, middle in totals.items():
        for axis in range(dimension):
            lower = list(charge)
            upper = list(charge)
            lower[axis] -= 1
            upper[axis] += 1
            lower_t, upper_t = tuple(lower), tuple(upper)
            if lower_t not in totals or upper_t not in totals:
                continue
            line_tests += 1
            if middle * middle < totals[lower_t] * totals[upper_t]:
                line_violations.append(
                    {
                        "charge": list(charge),
                        "axis": axis,
                        "counts": [totals[lower_t], middle, totals[upper_t]],
                    }
                )

    return {
        "L": L,
        "edges": E,
        "measured_charge_dimension": dimension,
        "charge_records": len(fibers),
        "same_charge_collision_probability_exact": exact(collision),
        "opposite_sector_same_charge_overlap_exact": exact(overlap),
        "collision_conditioned_opposite_sector_probability_exact": exact(overlap / collision),
        "maximum_record_count": maximum,
        "maximum_record_probability_exact": exact(Fraction(maximum, denominator)),
        "collision_to_maximum_record_probability_exact": exact(
            collision / Fraction(maximum, denominator)
        ),
        "Gaussian_density_benchmark_2_to_minus_d_over_2": 2 ** (-dimension / 2),
        "coordinate_line_log_concavity": {
            "tested_neighbor_triples": line_tests,
            "violations": len(line_violations),
            "first_violation": line_violations[:1],
        },
        "logical_cut_length": len(graph.logical_edges),
        "bitwise_complement_sector_action": (
            "swaps_logical_sector" if len(graph.logical_edges) % 2 else "preserves_logical_sector"
        ),
    }


def main() -> None:
    controls = [exact_control(3), exact_control(4)]
    assert controls[0]["coordinate_line_log_concavity"]["violations"] == 0
    assert controls[1]["coordinate_line_log_concavity"]["violations"] == 0

    source_paths = [
        LAB / "scripts" / "audit_midpoint_charge_collision_comparison.py",
        LAB / "scripts" / "current_oracle.py",
        LAB / "manifests" / "midpoint-charge-collision-comparison-2026-09-20.json",
        LAB / "results" / "midpoint-averaged-charge-balance-2026-09-20.json",
        LAB / "results" / "midpoint-charge-fiber-balance-theorem-2026-09-20.json",
    ]
    result = {
        "status": "complete_existing_theorems_do_not_give_dimension_free_conversion",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exact_controls": controls,
        "branch_matrix": {
            "local_limit_or_anti_concentration": {
                "outcome": "existing_results_do_not_supply_the_required_growing_dimension_atom_comparison",
                "established": [
                    "Classical lattice local-limit theorems control sums in fixed dimension or under hypotheses not verified uniformly for this growing divergence vector.",
                    "The reviewed decomposable-vector CLT controls convex-set probabilities, not individual lattice atoms or collision probability in a dimension that grows with L.",
                    "The reviewed graph-orientation asymptotic requires average degree at least n^(1/3+epsilon) plus strong mixing and therefore excludes the bounded-degree square family.",
                ],
                "structural_warning": "For a d-dimensional Gaussian density, integral(f^2)/max(f)=2^(-d/2). Since the measured-charge dimension grows with L, even ideal Gaussian regularity predicts exponential dimension loss rather than a positive constant lower bound on C_L/p_max,L.",
            },
            "collision_weighted_sector_balance": {
                "outcome": "no_structural_lower_bound_on_Psi_L",
                "established": "Exact Psi_L controls are positive at L3/L4 but are not a trend. Bitwise complement swaps sector for the odd L3 logical cut and preserves it for the even L4 cut, while also changing the charge record in general.",
                "compatible_countermodel": "Two equal-mass records with sector counts (1,M) and (M,1), exchanged by a complement-style involution, both satisfy normalized matching but have Psi=2M/(M+1)^2 -> 0.",
            },
            "compatible_obstruction": {
                "outcome": "coordinate_log_concavity_does_not_make_the_conversion_dimension_free",
                "established": "Every coordinate-neighbor triple of the exact total-charge counts is log-concave at L3/L4.",
                "obstruction": "Product log-concave and Gaussian laws still have C/p_max decaying as c^d. Total-count log-concavity also says nothing about how the two logical sectors split inside a charge fiber.",
            },
        },
        "finite_control_interpretation": {
            "observed": "C_L/p_max,L is 29/56 at L3 and 653081/4423680 at L4; Psi_L is 57/116 and 313452/653081.",
            "boundary": "These two exact sizes validate identities and theorem hypotheses only; they are not used as a fitted trend.",
        },
        "primary_source_applicability": [
            {
                "source": "Mitalauskas and Statulevicius, Local limit theorem and asymptotic expansion for sums of independent lattice random variables (1966)",
                "url": "https://doi.org/10.15388/LMJ.1966.19754",
                "supported": "classical local-limit control for independent lattice sums",
                "missing": "a dimension-uniform atom estimate for the dependent growing-dimensional divergence record",
            },
            {
                "source": "Fang, A multivariate CLT for bounded decomposable random vectors with the best known rate (2014)",
                "url": "https://arxiv.org/abs/1408.0508",
                "supported": "normal approximation for bounded decomposable random vectors over convex sets",
                "missing": "lattice-atom and collision estimates with controlled growing dimension and covariance conditioning",
            },
            {
                "source": "Isaev, Iyer and McKay, Asymptotic enumeration of orientations of a graph as a function of the out-degree sequence (2020)",
                "url": "https://doi.org/10.37236/8929",
                "supported": "asymptotic orientation counts under dense-degree and mixing hypotheses",
                "missing": "the average-degree hypothesis fails for the bounded-degree square lattice",
            },
        ],
        "precise_remaining_target": {
            "direct_form": "Control E_{Q~p}[r_Q] directly under the physical charge law, without collision reweighting.",
            "why_not_more_collision_work": "A high-dimensional local limit would naturally lose a factor comparable to 2^(-d/2), while NMP, complement symmetry and finite coordinate log-concavity do not control the sector split.",
            "candidate_routes": [
                "a renormalized charge-preserving logical switch whose congestion is averaged directly under the physical law",
                "a multiscale martingale or conditional-entropy decomposition that retains the full boundary charge record",
                "a compatible physical obstruction family if neither direct route is possible",
            ],
        },
        "decision": {
            "outcome": "close_collision_conversion_route_at_registered_scope",
            "established": "No reviewed theorem or tested structural property yields the required dimension-free collision-to-physical comparison or a positive lower bound on collision-weighted sector balance.",
            "not_established": "The failure of this proof route does not show that physical midpoint Bayes risk vanishes or that midpoint is correctable.",
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
