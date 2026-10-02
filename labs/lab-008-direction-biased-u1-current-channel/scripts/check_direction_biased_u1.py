#!/usr/bin/env python3
"""Exact finite checks for the biased signed-current U(1) channel."""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
MANIFEST = LAB / "manifests/direction-biased-u1-checks-2026-09-18.json"
OUT = LAB / "results/direction-biased-u1-checks-2026-09-18.json"


def zero_charge_weight(n, p, q):
    """Exhaustive current sum on an n-edge cycle, all arrows circulating."""
    total = F(0)
    for j in product((-1, 0, 1), repeat=n):
        if any(j[a] - j[a - 1] for a in range(n)):
            continue
        weight = F(1)
        for value in j:
            weight *= (1 - p) if value == 0 else p * (q if value == 1 else 1 - q)
        total += weight
    return total


def closed_form_cycle(n, p, q):
    return (1 - p) ** n + (p * q) ** n + (p * (1 - q)) ** n


def circulation(one_form, cycle):
    return sum(sign * one_form[edge] for edge, sign in cycle)


def main():
    p = F(1, 3)
    rows = []
    for q in (F(1, 2), F(3, 4), F(1)):
        enumerated = zero_charge_weight(4, p, q)
        expected = closed_form_cycle(4, p, q)
        assert enumerated == expected
        rows.append({"p": str(p), "bias_q": str(q), "Z_Q0_cycle4": str(enumerated)})
    assert len({row["Z_Q0_cycle4"] for row in rows}) == 3

    # A square with right/up arrows has A=d psi: its plaquette circulation is zero.
    square_A = [1, 1, 1, 1]
    square_cycle = [(0, 1), (1, 1), (2, -1), (3, -1)]
    # A periodic directed ring carries holonomy even though it has no local plaquette flux.
    ring_A = [1, 1, 1, 1]
    ring_cycle = [(0, 1), (1, 1), (2, 1), (3, 1)]
    assert circulation(square_A, square_cycle) == 0
    assert circulation(ring_A, ring_cycle) == 4

    output = {
        "status": "passed",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "arithmetic": "fractions.Fraction; exhaustive enumeration, no sampling uncertainty",
        "cycle_partition_sums": rows,
        "gauge_tests": {
            "open_tree": "always exact: solve vertex potentials recursively",
            "square_gradient_plaquette_circulation_in_units_of_h": circulation(square_A, square_cycle),
            "periodic_ring_holonomy_in_units_of_h": circulation(ring_A, ring_cycle),
            "criterion": "A_e=h s_e is removable by a single-valued vertex shift iff its signed circulation is zero on every graph cycle."
        },
        "conclusions": [
            "Bias changes a zero-charge cycle partition sum whenever the bias one-form has nonzero holonomy.",
            "The q=1 directed endpoint is a singular h=log(q/(1-q))/2 -> infinity limit, not an ordinary finite complex gauge transform.",
            "Finite motifs establish the gauge obstruction but do not determine a thermodynamic transition or decoder threshold."
        ]
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
