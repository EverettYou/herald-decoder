"""Exact L4 diagnostic for fixed-charge boundary-flux polynomial closure.

The edge recurrence can be grouped into lattice columns and is an exact
coefficient-extraction transfer.  This script checks its finite L4 behavior
and deliberately distinguishes three statements:

1. every final fixed-charge polynomial is real-rooted at L4;
2. every *actual* two-summand transfer pair interlaces in this L4 order; and
3. the complete fixed-charge family has a common interlacing.

Only (1) and (2) pass.  The exact pair t and 1+5t+t^2 refutes (3), so the
standard one-family common-interlacing induction is unavailable.  This is not
a counterexample to all-size real-rootedness.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
import time

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results/posterior-polynomial-closure-2026-09-20.json"


def _column_order(graph) -> list[int]:
    """Deterministic left-to-right edge order, grouped by completed column."""
    return sorted(
        range(len(graph.edges)),
        key=lambda edge: (
            max(graph.vertices[v].x for v in graph.edges[edge]),
            min(graph.vertices[v].y for v in graph.edges[edge]),
            min(graph.vertices[v].x for v in graph.edges[edge]),
            edge,
        ),
    )


def _shift(coeff: tuple[int, ...], logical: int) -> tuple[int, ...]:
    if not logical:
        return coeff
    return (0,) + coeff[:-1]


@lru_cache(maxsize=None)
def _roots(coeff: tuple[int, ...]) -> tuple[tuple[complex, ...], bool]:
    degree = max((index for index, count in enumerate(coeff) if count), default=0)
    values = (
        np.roots(np.asarray(coeff[: degree + 1], dtype=float)[::-1])
        if degree
        else np.asarray([], dtype=complex)
    )
    values = tuple(sorted((complex(value) for value in values), key=lambda z: z.real))
    real_nonpositive = all(abs(value.imag) <= 1e-8 and value.real <= 1e-8 for value in values)
    return values, real_nonpositive


def _interlaces(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    roots_left, real_left = _roots(left)
    roots_right, real_right = _roots(right)
    if not (real_left and real_right):
        return False
    x = [root.real for root in roots_left]
    y = [root.real for root in roots_right]
    if abs(len(x) - len(y)) > 1:
        return False

    def orientation(longer, shorter):
        tolerance = 1e-7
        if len(longer) == len(shorter) + 1:
            return all(
                longer[index] - tolerance <= shorter[index] <= longer[index + 1] + tolerance
                for index in range(len(shorter))
            )
        if len(longer) == len(shorter):
            return all(
                longer[index] - tolerance <= shorter[index]
                and shorter[index] - tolerance <= longer[index + 1] + tolerance
                for index in range(len(longer) - 1)
            )
        return False

    return orientation(x, y) or orientation(y, x)


def _exhaustive_polynomials(graph, incidence) -> dict[tuple[int, ...], tuple[int, ...]]:
    degree = len(graph.logical_edges)
    table = defaultdict(lambda: [0] * (degree + 1))
    for mask in range(1 << len(graph.edges)):
        current = np.fromiter(
            ((mask >> edge) & 1 for edge in range(len(graph.edges))),
            dtype=np.int8,
            count=len(graph.edges),
        )
        charge = tuple(map(int, incidence @ current))
        flux = sum(int(current[edge]) for edge in graph.logical_edges)
        table[charge][flux] += 1
    return {charge: tuple(coeff) for charge, coeff in table.items()}


def analyze() -> dict:
    start = time.monotonic()
    graph = square_graph(4)
    incidence = charge_matrix(graph)
    edge_count = len(graph.edges)
    degree = len(graph.logical_edges)
    assert edge_count == 18 and degree == 4

    edge_order = _column_order(graph)
    zero_charge = (0,) * incidence.shape[0]
    zero_poly = (0,) * (degree + 1)
    transfer = {zero_charge: (1,) + (0,) * degree}
    local_pairs_tested = 0
    local_interlacing_failures = []

    for step, edge in enumerate(edge_order):
        delta = tuple(map(int, incidence[:, edge]))
        logical = int(edge in graph.logical_edges)
        next_charges = set(transfer)
        next_charges.update(
            tuple(charge[row] + delta[row] for row in range(len(charge)))
            for charge in transfer
        )
        updated = {}
        for charge in next_charges:
            absent = transfer.get(charge, zero_poly)
            predecessor = tuple(
                charge[row] - delta[row] for row in range(len(charge))
            )
            present = _shift(transfer.get(predecessor, zero_poly), logical)
            if any(absent) and any(present):
                local_pairs_tested += 1
                if not _interlaces(absent, present):
                    local_interlacing_failures.append(
                        {
                            "step": step,
                            "edge": edge,
                            "charge": list(charge),
                            "absent_coefficients": list(absent),
                            "present_coefficients": list(present),
                        }
                    )
            updated[charge] = tuple(a + b for a, b in zip(absent, present))
        transfer = updated

    exhaustive = _exhaustive_polynomials(graph, incidence)
    assert transfer == exhaustive
    assert sum(sum(coeff) for coeff in transfer.values()) == 1 << edge_count

    root_failures = []
    for charge, coeff in transfer.items():
        roots, real_nonpositive = _roots(coeff)
        if not real_nonpositive:
            root_failures.append(
                {
                    "charge": list(charge),
                    "coefficients": list(coeff),
                    "roots": [[root.real, root.imag] for root in roots],
                }
            )

    # An exact obstruction to the simplest common-interlacing-family induction.
    monomial = (0, 1, 0, 0, 0)
    quadratic = (1, 5, 1, 0, 0)
    representatives = {}
    for charge, coeff in transfer.items():
        if coeff in (monomial, quadratic) and coeff not in representatives:
            representatives[coeff] = charge
    assert set(representatives) == {monomial, quadratic}
    assert not _interlaces(monomial, quadratic)

    ambiguous_weight = 0
    bayes_numerator = 0
    ambiguous_records = 0
    asymmetric_records = 0
    variances = []
    for coeff in transfer.values():
        even = sum(coeff[0::2])
        odd = sum(coeff[1::2])
        bayes_numerator += min(even, odd)
        if even and odd:
            ambiguous_records += 1
            asymmetric_records += int(even != odd)
            total = even + odd
            ambiguous_weight += total
            mean = Fraction(sum(k * n for k, n in enumerate(coeff)), total)
            second = Fraction(sum(k * k * n for k, n in enumerate(coeff)), total)
            variances.append(second - mean * mean)

    elapsed = time.monotonic() - start
    assert not root_failures
    assert not local_interlacing_failures
    assert elapsed < 300

    source_files = [
        LAB / "scripts/check_posterior_polynomial_closure.py",
        LAB / "scripts/current_oracle.py",
        LAB / "manifests/posterior-polynomial-closure-2026-09-20.json",
    ]
    result = {
        "status": "complete_recurrence_obstruction",
        "physical_parameters": {"geometry": "square", "L": 4, "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "exhaustive_current_states": 1 << edge_count,
        "fixed_charge_records": len(transfer),
        "recurrence": "C_(s+1,Q)(t)=C_(s,Q)(t)+t^ell_s C_(s,Q-d_s)(t)",
        "recurrence_definitions": {
            "d_s": "measured signed-incidence column of processed edge s",
            "ell_s": "1 for a logical-cut edge and 0 otherwise",
            "column_grouping": "left-to-right by the maximum x coordinate of each edge",
            "edge_order": edge_order,
        },
        "transfer_validation": {
            "matches_independent_exhaustive_table": True,
            "actual_two_summand_pairs_tested": local_pairs_tested,
            "actual_pair_interlacing_failures": len(local_interlacing_failures),
            "final_real_nonpositive_root_failures": len(root_failures),
            "scope": "finite canonical L4 diagnostic only",
        },
        "common_family_interlacing_counterexample": {
            "meaning": "refutes the simplest induction requiring one common interlacing for the entire fixed-charge family",
            "first_polynomial_coefficients": list(monomial),
            "first_charge": list(representatives[monomial]),
            "first_polynomial": "t",
            "first_roots_exact": ["0"],
            "second_polynomial_coefficients": list(quadratic),
            "second_charge": list(representatives[quadratic]),
            "second_polynomial": "1+5t+t^2",
            "second_roots_exact": ["(-5-sqrt(21))/2", "(-5+sqrt(21))/2"],
            "why_no_interlacing": "the root 0 of t is not between the two strictly negative roots of 1+5t+t^2",
            "claim_boundary": "not a counterexample to real-rootedness and not a threshold result",
        },
        "L4_posterior_control": {
            "ambiguous_records": ambiguous_records,
            "asymmetric_ambiguous_records": asymmetric_records,
            "Bayes_LER_exact": str(Fraction(bayes_numerator, 1 << edge_count)),
            "ambiguous_record_probability_exact": str(Fraction(ambiguous_weight, 1 << edge_count)),
            "conditional_posterior_balance_exact": str(Fraction(bayes_numerator, ambiguous_weight)),
            "minimum_ambiguous_flux_variance_exact": str(min(variances)),
            "maximum_ambiguous_flux_variance_exact": str(max(variances)),
        },
        "primary_hypothesis_audit": {
            "source": "Borcea, Branden and Liggett, Negative dependence and the geometry of polynomials, JAMS 2009 / arXiv:0707.2340",
            "url": "https://arxiv.org/abs/0707.2340",
            "finding": "real-rootedness of a positive sum follows from suitable compatibility/interlacing hypotheses, but the full fixed-charge family fails a common interlacing and no theorem proving the observed structured local pairs for every L was found",
        },
        "decision": {
            "outcome": "recurrence_obstruction_without_real_root_counterexample",
            "established": "The exact transfer recurrence, exhaustive L4 table, final L4 real-rootedness, and every actual L4 local summand interlacing check pass.",
            "obstruction": "The complete fixed-charge family is not a common-interlacing family, so the direct global compatibility induction is false.",
            "not_established": "No all-size structured local-interlacing invariant and no size-uniform physical posterior-balance estimate are proved.",
            "threshold_claim": "No square midpoint or decoding-threshold claim is promoted.",
        },
        "elapsed_seconds": elapsed,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        },
    }
    return result


def main() -> None:
    result = analyze()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
