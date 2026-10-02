"""Exact L3 control for the square-midpoint posterior-balance route.

This script does not sample.  It repackages the registered 256-current table
as fixed-charge boundary-flux polynomials and checks every algebraic identity
used by the proposed real-root/variance argument.  Root structure at L3 is a
diagnostic only: fixed-divergence conditioning is not among the standard
strong-Rayleigh closure operations, so no all-size stability claim is made.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import math
import time

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results/posterior-balance-polynomial-2026-09-20.json"
PREDECESSOR = LAB / "results/square-midpoint-thermodynamics-2026-09-20.json"


def _fraction(value: Fraction) -> str:
    return str(value)


def analyze() -> dict:
    start = time.monotonic()
    graph = square_graph(3)
    incidence = charge_matrix(graph)
    edge_count = len(graph.edges)
    cut_degree = len(graph.logical_edges)
    assert edge_count == 8 and cut_degree == 3

    coefficients: dict[tuple[int, ...], list[int]] = defaultdict(
        lambda: [0] * (cut_degree + 1)
    )
    for mask in range(1 << edge_count):
        current = np.array(
            [(mask >> edge) & 1 for edge in range(edge_count)], dtype=int
        )
        charge = tuple(map(int, incidence @ current))
        flux = sum(int(current[edge]) for edge in graph.logical_edges)
        coefficients[charge][flux] += 1

    predecessor = json.loads(PREDECESSOR.read_text())
    predecessor_rows = {
        tuple(row["Q"]): row["sector_counts"]
        for row in predecessor["record_sector_table"]
    }

    rows = []
    identity_failures = 0
    real_root_failures = 0
    bound_failures = 0
    ambiguous_weight = 0
    weighted_risk = Fraction(0)
    weighted_variance = Fraction(0)
    real_roots: list[float] = []

    for charge, coeff in sorted(coefficients.items()):
        even = sum(coeff[0::2])
        odd = sum(coeff[1::2])
        total = even + odd
        f_plus = sum(coeff)
        f_minus = sum((-1) ** degree * count for degree, count in enumerate(coeff))
        if [even, odd] != predecessor_rows[charge]:
            identity_failures += 1
        if f_plus != total or f_minus != even - odd:
            identity_failures += 1

        degree = max(index for index, count in enumerate(coeff) if count)
        roots = (
            np.roots(np.asarray(coeff[: degree + 1], dtype=float)[::-1])
            if degree
            else np.asarray([], dtype=complex)
        )
        roots_ok = all(abs(root.imag) <= 1e-9 and root.real <= 1e-9 for root in roots)
        real_root_failures += int(not roots_ok)
        if roots_ok:
            real_roots.extend(float(root.real) for root in roots)

        mean = Fraction(sum(k * count for k, count in enumerate(coeff)), total)
        second = Fraction(sum(k * k * count for k, count in enumerate(coeff)), total)
        variance = second - mean * mean
        risk = Fraction(min(even, odd), total)
        magnetization = Fraction(f_minus, f_plus)
        exact_identity = risk == (1 - abs(magnetization)) / 2
        if not exact_identity:
            identity_failures += 1

        variance_bound = (1 - math.exp(-2 * float(variance))) / 2
        if roots_ok and float(risk) + 1e-12 < variance_bound:
            bound_failures += 1

        ambiguous = even > 0 and odd > 0
        if ambiguous:
            ambiguous_weight += total
            weighted_risk += total * risk
            weighted_variance += total * variance

        rows.append(
            {
                "Q": list(charge),
                "F_coefficients_low_to_high": coeff,
                "sector_counts": [even, odd],
                "F_at_1": f_plus,
                "F_at_minus_1": f_minus,
                "conditional_risk_exact": _fraction(risk),
                "conditional_flux_mean_exact": _fraction(mean),
                "conditional_flux_variance_exact": _fraction(variance),
                "roots": [
                    {"real": float(root.real), "imag": float(root.imag)} for root in roots
                ],
                "real_nonpositive_roots_at_L3": roots_ok,
                "variance_risk_lower_bound": variance_bound,
                "ambiguous": ambiguous,
            }
        )

    ambiguous_rows = [row for row in rows if row["ambiguous"]]
    bayes_numerator = sum(min(row["sector_counts"]) for row in rows)
    elapsed = time.monotonic() - start
    assert identity_failures == 0
    assert bayes_numerator == 112
    assert len(rows) == 64 and len(ambiguous_rows) == 46
    assert real_root_failures == 0 and bound_failures == 0
    assert elapsed < 120

    source_files = [
        LAB / "scripts/check_posterior_balance_polynomial.py",
        LAB / "scripts/current_oracle.py",
        PREDECESSOR,
    ]
    result = {
        "status": "complete_obstruction",
        "physical_parameters": {"geometry": "square", "L": 3, "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "current_states_reused": 1 << edge_count,
        "records": len(rows),
        "ambiguous_records": len(ambiguous_rows),
        "boundary_flux_polynomial": "F_Q(t)=sum_{j:D_M j=Q} t^{K(j)}",
        "identities": {
            "F_Q(1)": "N_0(Q)+N_1(Q)",
            "F_Q(-1)": "N_0(Q)-N_1(Q)",
            "posterior_magnetization": "m(Q)=F_Q(-1)/F_Q(1)",
            "conditional_risk": "r(Q)=(1-|m(Q)|)/2",
            "Bayes_LER": "2^{-E-1} sum_Q [F_Q(1)-|F_Q(-1)|]",
        },
        "identity_failures": identity_failures,
        "Bayes_LER_exact": _fraction(Fraction(bayes_numerator, 1 << edge_count)),
        "conditional_posterior_balance_exact": _fraction(
            weighted_risk / ambiguous_weight
        ),
        "L3_root_control": {
            "all_records_real_nonpositive": real_root_failures == 0,
            "failed_records": real_root_failures,
            "smallest_root": min(real_roots),
            "largest_root": max(real_roots),
            "interpretation": "finite L3 diagnostic only; not an all-size theorem",
        },
        "L3_variance_control": {
            "minimum_ambiguous_variance_exact": min(
                ambiguous_rows,
                key=lambda row: Fraction(row["conditional_flux_variance_exact"]),
            )["conditional_flux_variance_exact"],
            "maximum_ambiguous_variance_exact": max(
                ambiguous_rows,
                key=lambda row: Fraction(row["conditional_flux_variance_exact"]),
            )["conditional_flux_variance_exact"],
            "physical_ambiguous_record_average_variance_exact": _fraction(
                weighted_variance / ambiguous_weight
            ),
            "variance_bound_failures": bound_failures,
            "bound_if_real_rooted": "r(Q)>=[1-exp(-2 Var(K|Q))]/2",
        },
        "primary_source_review": {
            "source": "Borcea, Branden and Liggett, Negative dependence and the geometry of polynomials, JAMS 2009 / arXiv:0707.2340",
            "url": "https://arxiv.org/abs/0707.2340",
            "applicable_closures": [
                "coordinate conditioning",
                "projection",
                "external fields",
                "diagonal specialization",
            ],
            "missing_interface": "conditioning on D_M j=Q is a joint signed linear/divergence constraint (Laurent coefficient extraction), not one of the reviewed closure operations",
        },
        "decision": {
            "outcome": "obstruction",
            "established": "The boundary-flux polynomial exactly represents physical posterior balance; all L3 identities, real-root diagnostics and variance bounds pass.",
            "not_established": "Neither real stability of F_Q for arbitrary L nor a size-uniform positive lower bound on Var(K|Q) over positive physical ambiguous-record mass is proved.",
            "threshold_claim": "No square decoding threshold or midpoint noncorrectability follows from this bounded control.",
        },
        "record_polynomials": rows,
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
    summary = {key: value for key, value in result.items() if key != "record_polynomials"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
