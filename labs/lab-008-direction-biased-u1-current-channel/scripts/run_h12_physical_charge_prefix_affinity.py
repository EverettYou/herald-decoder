"""Exact L=3 physical-charge prefix-affinity audit; no stochastic acquisition."""

from __future__ import annotations

from collections import defaultdict
from itertools import permutations
import hashlib
import json
from math import sqrt
from pathlib import Path

from current_oracle import exact_enumeration
from herald_decoder.lattice_model import square_graph


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results/h12-physical-charge-prefix-affinity-2026-09-23.json"
TOL = 1e-12


def grouped_sector_mass(table, order, count):
    grouped = defaultdict(lambda: [0.0, 0.0])
    for charge, value in table.items():
        key = tuple(charge[index] for index in order[:count])
        grouped[key][0] += float(value[0][0])
        grouped[key][1] += float(value[0][1])
    return grouped


def affinity(mass):
    return sum(sqrt(max(0.0, a * b)) for a, b in mass.values())


def main():
    model = square_graph(3)
    assert len(model.detector_vertices) == 3
    cells = []
    maximum_gate_error = 0.0
    for q in (0.5, 0.9, 1.0):
        table = exact_enumeration(model, 0.3, q)
        full = [value[0] for value in table.values()]
        total_mass = sum(float(z[0] + z[1]) for z in full)
        risk = sum(float(min(z[0], z[1])) for z in full)
        contrast = sum(float(abs(z[0] - z[1])) for z in full)
        maximum_gate_error = max(maximum_gate_error, abs(total_mass - 1.0), abs(contrast - (1.0 - 2.0 * risk)))
        if abs(total_mass - 1.0) > TOL or abs(contrast - (1.0 - 2.0 * risk)) > TOL:
            raise AssertionError("physical normalization or H12 risk identity failed")
        q_cells = []
        for order in permutations(range(3)):
            masses = [grouped_sector_mass(table, order, k) for k in range(4)]
            f = [affinity(mass) for mass in masses]
            stages = []
            for k in range(1, 4):
                parent, child = masses[k - 1], masses[k]
                conditional = []
                weighted_sum = 0.0
                support_zero = 0
                for prefix, (a, b) in parent.items():
                    if a <= 0.0 or b <= 0.0:
                        support_zero += 1
                        continue
                    alpha = sum(
                        sqrt(x * y / (a * b))
                        for name, (x, y) in child.items()
                        if name[: k - 1] == prefix
                    )
                    if alpha > 1.0 + TOL or alpha < -TOL:
                        raise AssertionError("conditional affinity outside [0,1]")
                    conditional.append(alpha)
                    weighted_sum += sqrt(a * b) * alpha
                factor = f[k] / f[k - 1]
                maximum_gate_error = max(maximum_gate_error, abs(weighted_sum - f[k]))
                if abs(weighted_sum - f[k]) > TOL or f[k] > f[k - 1] + TOL:
                    raise AssertionError("prefix affinity chain or monotonicity failed")
                stages.append({
                    "revealed_charge_index": order[k - 1],
                    "supported_parent_prefixes": len(conditional),
                    "sector_zero_parent_prefixes": support_zero,
                    "conditional_affinity_min": min(conditional),
                    "conditional_affinity_max": max(conditional),
                    "physical_affinity_weighted_factor": factor,
                })
            lower = 1.0 - 2.0 * f[-1]
            upper = sqrt(max(0.0, 1.0 - 4.0 * f[-1] ** 2))
            maximum_gate_error = max(maximum_gate_error, max(0.0, lower - contrast, contrast - upper))
            if not lower - TOL <= contrast <= upper + TOL:
                raise AssertionError("two-sided physical H12 affinity bound failed")
            q_cells.append({
                "charge_index_order": list(order),
                "prefix_affinity": f,
                "stages": stages,
                "contrast_lower_bound": lower,
                "contrast_upper_bound": upper,
            })
        final_values = [cell["prefix_affinity"][-1] for cell in q_cells]
        final_spread = max(final_values) - min(final_values)
        maximum_gate_error = max(maximum_gate_error, final_spread)
        if final_spread > TOL:
            raise AssertionError("full-record affinity depends on reveal order")
        cells.append({
            "p": 0.3,
            "q": q,
            "distinct_full_charge_records": len(table),
            "physical_bayes_risk": risk,
            "physical_h12_absolute_contrast": contrast,
            "full_record_affinity": final_values[0],
            "summary": {
                "minimum_stage_weighted_factor": min(
                    stage["physical_affinity_weighted_factor"]
                    for cell in q_cells for stage in cell["stages"]
                ),
                "maximum_stage_weighted_factor": max(
                    stage["physical_affinity_weighted_factor"]
                    for cell in q_cells for stage in cell["stages"]
                ),
                "orders_with_unit_conditional_affinity": sum(
                    any(stage["conditional_affinity_max"] >= 1.0 - TOL for stage in cell["stages"])
                    for cell in q_cells
                ),
                "best_order_worst_prefix_affinity": min(
                    max(stage["conditional_affinity_max"] for stage in cell["stages"])
                    for cell in q_cells
                ),
            },
            "orders": q_cells,
        })
    result = {
        "id": "lab008-h12-physical-charge-prefix-affinity-2026-09-23",
        "status": "passed_exact_finite_control_no_thermodynamic_claim",
        "source_manifest": "../manifests/h12-physical-charge-prefix-affinity-2026-09-23.json",
        "source_sha256": hashlib.sha256((LAB / "scripts/current_oracle.py").read_bytes()).hexdigest(),
        "sampling": {"new_sizes": 0, "stochastic_samples": 0, "bootstrap_replicates": 0, "deterministic_q_order_cells": 18},
        "exact_identity": "For nested physical charge prefixes, F_k=sum_prefix sqrt(Z0^k Z1^k); F_k/F_(k-1) is the sqrt(Z0 Z1)-weighted mean of conditional sector-charge Hellinger affinities. At full Q, 1-2F_m<=A_m=1-2R_m<=sqrt(1-4F_m^2).",
        "maximum_gate_error": maximum_gate_error,
        "cells": cells,
        "claim_boundary": "This is an exact physical-observation factorization and L=3 control. A size-uniform p=.30 conclusion requires a theorem on the accumulated physical weighted factors; no measured L=3 factor is extrapolated.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "cells": 18, "maximum_gate_error": maximum_gate_error, "result": str(RESULT)}))


if __name__ == "__main__":
    main()
