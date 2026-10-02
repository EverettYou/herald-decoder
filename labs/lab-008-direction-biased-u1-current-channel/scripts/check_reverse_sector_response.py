"""Exact fixed-p reverse-sector response and uniform LER error certificate.

The approximation is a normalized joint law, not an approximate posterior
averaged under the physical record law.  For epsilon=1-q it retains the
zero-reverse configurations and every single-reverse insertion before the
record-sector minimum is taken.
"""

from collections import Counter
from fractions import Fraction
from itertools import product
import hashlib
import json
import time

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


def f(value: str) -> Fraction:
    return Fraction(value)


def enumerate_l3():
    graph = square_graph(3)
    edge_count = len(graph.edges)
    incidence = charge_matrix(graph)
    groups: dict[tuple[int, ...], list[Counter]] = {}
    states = []
    for raw in product((0, 1, -1), repeat=edge_count):
        current = np.asarray(raw, dtype=np.int8)
        record = tuple(int(x) for x in incidence @ current)
        sector = int(current[list(graph.logical_edges)].sum()) % 2
        plus = int((current == 1).sum())
        minus = int((current == -1).sum())
        groups.setdefault(record, [Counter(), Counter()])[sector][plus, minus] += 1
        states.append((current, record, sector, plus, minus))
    return graph, incidence, groups, states


def sector_coefficients(groups, edge_count: int, p: Fraction):
    idle = 1 - p
    intercept = {}
    derivative = {}
    for record, sectors in groups.items():
        a = [Fraction(0), Fraction(0)]
        b = [Fraction(0), Fraction(0)]
        for sector, counts in enumerate(sectors):
            for (plus, minus), multiplicity in counts.items():
                occupied = plus + minus
                base = idle ** (edge_count - occupied) * p ** occupied
                if minus == 0:
                    a[sector] += multiplicity * base
                    b[sector] -= multiplicity * occupied * base
                elif minus == 1:
                    b[sector] += multiplicity * base
        intercept[record] = tuple(a)
        derivative[record] = tuple(b)
    assert sum(sum(x) for x in intercept.values()) == 1
    assert sum(sum(x) for x in derivative.values()) == 0
    return intercept, derivative


def verify_insertion_operator(
    states, incidence, edge_count: int, p: Fraction, derivative
) -> None:
    """Independently reconstruct dP/depsilon at zero by edge insertions."""
    idle = 1 - p
    inserted: dict[tuple[int, ...], list[Fraction]] = {}
    for current, record, sector, plus, minus in states:
        if minus:
            continue
        weight = idle ** (edge_count - plus) * p ** plus
        row = inserted.setdefault(record, [Fraction(0), Fraction(0)])
        row[sector] -= plus * weight
        for edge in np.flatnonzero(current == 1):
            changed = current.copy()
            changed[edge] = -1
            changed_record = tuple(int(x) for x in incidence @ changed)
            inserted.setdefault(changed_record, [Fraction(0), Fraction(0)])[sector] += weight
    all_records = set(derivative) | set(inserted)
    for record in all_records:
        assert tuple(inserted.get(record, (Fraction(0), Fraction(0)))) == derivative.get(
            record, (Fraction(0), Fraction(0))
        )


def risk(masses) -> Fraction:
    return sum(min(pair) for pair in masses.values())


def response_summary(intercept, derivative):
    strict = Fraction(0)
    positive_ties = Fraction(0)
    new_records = Fraction(0)
    strict_count = positive_tie_count = new_record_count = 0
    new_two_sector_count = 0
    for record, base in intercept.items():
        slope = derivative[record]
        if base[0] < base[1]:
            strict += slope[0]
            strict_count += 1
        elif base[1] < base[0]:
            strict += slope[1]
            strict_count += 1
        elif base[0] > 0:
            positive_ties += min(slope)
            positive_tie_count += 1
        else:
            contribution = min(slope)
            new_records += contribution
            if sum(slope) > 0:
                new_record_count += 1
            if contribution > 0:
                new_two_sector_count += 1
    total = strict + positive_ties + new_records
    return {
        "right_derivative_exact": str(total),
        "right_derivative": float(total),
        "strict_smaller_sector_contribution_exact": str(strict),
        "positive_tie_contribution_exact": str(positive_ties),
        "new_record_contribution_exact": str(new_records),
        "strict_records": strict_count,
        "positive_mass_sector_ties": positive_tie_count,
        "newly_accessible_first_order_records": new_record_count,
        "new_records_with_both_sectors": new_two_sector_count,
    }


def joint_response(intercept, derivative, epsilon: Fraction):
    out = {
        record: tuple(base[h] + epsilon * derivative[record][h] for h in (0, 1))
        for record, base in intercept.items()
    }
    assert all(x >= 0 for pair in out.values() for x in pair)
    assert sum(sum(x) for x in out.values()) == 1
    return out


def physical_masses(groups, edge_count: int, p: Fraction, epsilon: Fraction):
    idle = 1 - p
    forward = p * (1 - epsilon)
    reverse = p * epsilon
    out = {}
    for record, sectors in groups.items():
        pair = [Fraction(0), Fraction(0)]
        for sector, counts in enumerate(sectors):
            pair[sector] = sum(
                multiplicity
                * idle ** (edge_count - plus - minus)
                * forward**plus
                * reverse**minus
                for (plus, minus), multiplicity in counts.items()
            )
        out[record] = tuple(pair)
    assert sum(sum(x) for x in out.values()) == 1
    return out


def total_variation_formula(edge_count: int, p: Fraction, epsilon: Fraction):
    exact = edge_count * p * epsilon * (1 - (1 - p * epsilon) ** (edge_count - 1))
    quadratic = edge_count * (edge_count - 1) * p * p * epsilon * epsilon
    assert exact <= quadratic
    return exact, quadratic


def sector_switch_count(intercept, approximated) -> int:
    switches = 0
    for record, base in intercept.items():
        trial = approximated[record]
        base_sign = (base[0] > base[1]) - (base[0] < base[1])
        trial_sign = (trial[0] > trial[1]) - (trial[0] < trial[1])
        if base_sign and trial_sign and base_sign != trial_sign:
            switches += 1
    return switches


def main() -> None:
    started = time.monotonic()
    graph, incidence, groups, states = enumerate_l3()
    edge_count = len(graph.edges)
    assert edge_count == 8 and len(states) == 3**edge_count

    cells = []
    responses = []
    for p in map(f, (".05", ".08", ".10", ".30", ".46")):
        intercept, derivative = sector_coefficients(groups, edge_count, p)
        verify_insertion_operator(states, incidence, edge_count, p, derivative)
        base_risk = risk(intercept)
        summary = response_summary(intercept, derivative)
        summary.update({"p": float(p), "directed_LER_exact": str(base_risk), "directed_LER": float(base_risk)})
        # The exact one-sided derivative must equal a sufficiently small
        # positive finite difference of the piecewise-affine joint law.
        delta = Fraction(1, 10**12)
        delta_risk = risk(joint_response(intercept, derivative, delta))
        assert delta_risk == base_risk + delta * Fraction(summary["right_derivative_exact"])
        responses.append(summary)

        for epsilon in map(f, (".005", ".01", ".03")):
            physical = physical_masses(groups, edge_count, p, epsilon)
            approximate = joint_response(intercept, derivative, epsilon)
            physical_risk = risk(physical)
            approximate_risk = risk(approximate)
            error = abs(physical_risk - approximate_risk)
            tv, quadratic = total_variation_formula(edge_count, p, epsilon)
            assert error <= tv <= quadratic
            cells.append(
                {
                    "p": float(p),
                    "epsilon": float(epsilon),
                    "q": float(1 - epsilon),
                    "physical_LER_exact": str(physical_risk),
                    "physical_LER": float(physical_risk),
                    "joint_response_LER_exact": str(approximate_risk),
                    "joint_response_LER": float(approximate_risk),
                    "absolute_error_exact": str(error),
                    "absolute_error": float(error),
                    "TV_bound_exact": str(tv),
                    "TV_bound": float(tv),
                    "quadratic_bound_exact": str(quadratic),
                    "quadratic_bound": float(quadratic),
                    "error_over_TV": float(error / tv) if tv else 0.0,
                    "strict_sector_switches_in_response": sector_switch_count(intercept, approximate),
                }
            )

    guarantee_only = []
    for p in map(f, (".08", ".30")):
        for epsilon in map(f, (".005", ".01", ".03")):
            tv, quadratic = total_variation_formula(32, p, epsilon)
            guarantee_only.append(
                {
                    "edge_count": 32,
                    "p": float(p),
                    "epsilon": float(epsilon),
                    "q": float(1 - epsilon),
                    "TV_bound_exact": str(tv),
                    "TV_bound": float(tv),
                    "quadratic_bound_exact": str(quadratic),
                    "quadratic_bound": float(quadratic),
                    "claim": "error guarantee only; no L5 response LER was evaluated",
                }
            )

    elapsed = time.monotonic() - started
    assert elapsed < 120
    source_files = [
        "scripts/check_reverse_sector_response.py",
        "scripts/current_oracle.py",
        "manifests/reverse-sector-response-2026-09-19.json",
    ]
    hashes = {
        str((LAB / path).relative_to(ROOT)): hashlib.sha256((LAB / path).read_bytes()).hexdigest()
        for path in source_files
    }
    lattice = ROOT / "src/herald_decoder/lattice_model.py"
    hashes[str(lattice.relative_to(ROOT))] = hashlib.sha256(lattice.read_bytes()).hexdigest()
    output = {
        "status": "passed",
        "scope": (
            "Normalized fixed-p first-order joint-law response at epsilon=1-q, "
            "with the record-sector minimum retained; no fit, threshold or L5 LER claim."
        ),
        "theorem": {
            "joint_law": "J_epsilon=P_0+epsilon*(dP_epsilon/depsilon)|_0",
            "conditional_weights": {
                "zero_reverse_given_occupied_set_size_N": "1-N*epsilon",
                "each_single_reverse": "epsilon",
                "two_or_more_reverse": "0",
            },
            "positivity_domain": "0<=epsilon<=1/E",
            "TV_exact": "E*p*epsilon*[1-(1-p*epsilon)^(E-1)]",
            "TV_quadratic_upper": "E*(E-1)*p^2*epsilon^2",
            "LER_stability": "|LER(P_epsilon)-LER(J_epsilon)|<=TV(P_epsilon,J_epsilon)",
            "right_derivative_rule": (
                "For each record choose the derivative of the strictly smaller zero-order sector; "
                "at a sector tie, including a newly accessible zero-mass record, choose the smaller derivative."
            ),
        },
        "proof_checks": {
            "states": len(states),
            "records": len(groups),
            "exact_normalization": True,
            "independent_insertion_operator_match": True,
            "one_sided_derivative_checks": len(responses),
            "full_support_cells": len(cells),
            "all_LER_errors_within_exact_TV": True,
            "all_exact_TV_within_quadratic_bound": True,
        },
        "L3_response": responses,
        "L3_full_support_validation": cells,
        "E32_guarantee_only": guarantee_only,
        "new_physical_record_samples": 0,
        "elapsed_seconds": elapsed,
        "source_sha256": hashes,
    }
    result = LAB / "results/reverse-sector-response-2026-09-19.json"
    result.write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": output["status"],
                "states": len(states),
                "records": len(groups),
                "cells": len(cells),
                "max_absolute_error": max(row["absolute_error"] for row in cells),
                "max_error_over_TV": max(row["error_over_TV"] for row in cells),
                "E32_guarantees": guarantee_only,
                "seconds": elapsed,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
