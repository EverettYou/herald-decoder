"""Exact paired second-public laws for one high-prior same-flux error pair."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute, law
from run_j8h_signed_affine_solver_gate import affine_solutions
from run_j8o_other_flux_representative_feasibility import flux_basis


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8s-high-prior-pair-second-laws-2026-09-28.json"
RESULT = LAB / "results/j8s-high-prior-pair-second-laws-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> dict:
    return json.loads((LAB / name).read_text())


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    budget = contract["budget"]
    old = load("results/j8r-action-binding-and-two-edge-tail-2026-09-28.json")
    red, sites, flips, pairs = setup(load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
                                      load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    base = tuple(old["two_edge_tail"]["base_error_edges_private"])
    assert base == (0, 1)
    kernel = flux_basis(red)
    masks = [0]
    for vector in kernel:
        masks.extend(mask ^ vector for mask in masks[:])
    base_mask = sum(1 << edge for edge in base)
    alternatives = [tuple(edge for edge in range(36) if (base_mask ^ mask) >> edge & 1)
                    for mask in masks if mask]
    minimum = min(map(len, alternatives))
    selected = sorted(error for error in alternatives if len(error) == minimum)
    assert minimum == 4 and selected == [(30, 32, 34, 35)]
    actions = contract["matrix"]["public_actions_red_edges"]
    assert actions == [[0], [1, 30, 32, 34, 35]]
    assert old["two_edge_tail"]["first_public"]["charge"] == [0] * 24
    target_flux = red_boundary(red, list(base))[1]
    assert sum(bit << site for site, bit in enumerate(target_flux)) == old["two_edge_tail"]["first_public"]["flux_mask"]
    terms = direct_checks = 0

    def signature(zmask: int) -> int:
        return sum(parity(zmask & flip) << index for index, flip in enumerate(flips))

    rows = []
    for edges in (base, selected[0]):
        physical, first_flux = red_boundary(red, list(edges))
        assert first_flux == target_flux
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [i for i, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in means.values())
        variable_first = sorted(i for i, value in means.items() if value == 0)
        first_ops = [conjugated_star(sites[i], physical) for i in variable_first]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_signatures = [signature(op[1]) for op in first_ops]

        def signed_sum(tail=()) -> int:
            nonlocal terms
            product = compose(list(tail))
            solutions = affine_solutions(first_signatures, signature(product[1]))
            assert len(solutions) <= budget["max_affine_class_size"]
            total = 0
            for bits in solutions:
                factors = [first_ops[i] for i in range(len(first_ops)) if bits >> i & 1]
                factors.extend(tail)
                sign, zmask, _ = compose(factors)
                assert signature(zmask) == 0
                total += sign
                terms += 1
                assert terms + direct_checks <= budget["max_total_terms"]
            return total

        first_sum = signed_sum()
        first_mass = Fraction(first_sum, 1 << len(first_ops))
        assert first_mass > 0
        if edges == base:
            assert first_mass == Fraction(old["two_edge_tail"]["base_first_likelihood"])
        cells = []
        for action in actions:
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [i for i, bit in enumerate(second_flux) if bit == 0]
            second_ops = {i: conjugated_star(sites[i], residual) for i in eligible_second}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
            cache: dict[tuple[int, ...], Fraction] = {}

            def conditional(group: tuple[int, ...]) -> Fraction:
                if group in cache:
                    return cache[group]
                product = compose([second_ops[i] for i in group])
                assert compose([product, product]) == (1, 0, 0)
                value = (Fraction(0) if any(not commute(product, op) for op in first_ops)
                         else Fraction(signed_sum((product,)), first_sum))
                assert -1 <= value <= 1
                cache[group] = value
                return value

            singles = {i: conditional((i,)) for i in eligible_second}
            assert all(value in (-1, 0, 1) for value in singles.values())
            fixed = {i: int(value == -1) for i, value in singles.items() if value != 0}
            variable = sorted(i for i, value in singles.items() if value == 0)
            assert len(variable) <= budget["max_variable_second_sites"]
            moments = {(): Fraction(1)}
            for order in range(1, len(variable) + 1):
                for group in itertools.combinations(variable, order):
                    moments[group] = conditional(group)
            public_rows = []
            for bits in itertools.product((0, 1), repeat=len(variable)):
                probability = sum((value * (-1 if sum(bits[variable.index(i)] for i in group) % 2 else 1)
                                   for group, value in moments.items()), Fraction()) / (1 << len(variable))
                assert 0 <= probability <= 1
                if probability:
                    charge = [0] * 24
                    for i, bit in fixed.items():
                        charge[i] = bit
                    for i, bit in zip(variable, bits):
                        charge[i] = bit
                    public_rows.append({"public": public_record(second_flux, charge),
                                        "conditional_probability": str(probability)})
            assert sum((Fraction(row["conditional_probability"]) for row in public_rows), Fraction()) == 1
            checked = False
            for i in eligible_second:
                product = second_ops[i]
                if singles[i] == 0 or any(not commute(product, op) for op in first_ops):
                    continue
                solutions = affine_solutions(first_signatures, signature(product[1]))
                if solutions:
                    bits = solutions[0]
                    factors = [first_ops[j] for j in range(len(first_ops)) if bits >> j & 1]
                    factors.append(product)
                    assert compose(factors)[0] == moment(factors, flips)
                    direct_checks += 1
                    checked = True
                    break
            assert checked
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "variable_second_sites_private": variable,
                          "positive_public_rows": len(public_rows), "rows": public_rows})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
        rows.append({"error_edges_private": list(edges), "first_public_mass": str(first_mass), "cells": cells})

    differences = []
    for index, action in enumerate(actions):
        a, b = (law(row["cells"][index]["rows"]) for row in rows)
        tv = sum((abs(a.get(key, Fraction()) - b.get(key, Fraction())) for key in a.keys() | b.keys()), Fraction()) / 2
        differences.append({"public_action_red_edges": action, "conditional_second_total_variation": str(tv)})
    assert direct_checks == 4 and terms + direct_checks <= budget["max_total_terms"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"], "status": "paired_high_prior_second_laws_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "first_public": old["two_edge_tail"]["first_public"], "rows": rows,
            "paired_action_differences": differences,
            "counters": {"signed_affine_terms": terms, "direct_moment_checks": direct_checks,
                         "complete_first_laws": 2, "complete_second_law_cells": 4,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "One same-flux highest-prior nonbase error pair and two fixed public actions at ideal L2; no full-IID information/risk, operator automorphism, noisy JIT, size scaling or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "differences": result["paired_action_differences"],
                      "terms": result["counters"]["signed_affine_terms"], "cpu_seconds": result["cpu_seconds"]}))
