"""Direct complete-law census of every deterministic-base three-edge collision."""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute, law
from run_j8h_signed_affine_solver_gate import affine_solutions


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8x-deterministic-first-collision-census-2026-09-28.json"
RESULT = LAB / "results/j8x-deterministic-first-collision-census-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    prior = load("results/j8t-weight-three-prior-and-law-cost-2026-09-28.json")
    base = load("results/j8u-weight-three-base-first-laws-2026-09-28.json")
    previous = load("results/j8v-equal-prior-collision-second-laws-2026-09-28.json")
    assert prior["physical_prior"] == base["physical_prior"] == previous["physical_prior"] == {
        "p_X": "1/10", "p_Z": "0", "red_edges": 36}
    red, sites, flips, pairs = setup(load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
                                      load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    base_by_flux = {row["first_flux_mask"]: row for row in base["rows"]}
    prior_by_flux = {row["first_flux_mask"]: row for row in prior["sector_rows"]}
    columns = [sum(bit << i for i, bit in enumerate(red_boundary(red, [edge])[1]))
               for edge in range(36)]
    collisions = defaultdict(list)
    for edges in itertools.combinations(range(36), 3):
        flux = columns[edges[0]] ^ columns[edges[1]] ^ columns[edges[2]]
        if flux in base_by_flux:
            collisions[flux].append(edges)
    double = {flux: sorted(errors) for flux, errors in collisions.items() if len(errors) == 2}
    assert len(double) == 120
    selected = sorted((flux, errors) for flux, errors in double.items()
                      if base_by_flux[flux]["base_first_likelihood"] == "1")
    assert len(selected) == 12
    for flux, errors in selected:
        assert list(errors[0]) == base_by_flux[flux]["representative_error_edges_private"]
    actions = contract["matrix"]["public_actions_red_edges"]
    assert actions == [[0], [1, 30, 32, 34, 35]]
    budget = contract["budget"]
    counters = {"signed_affine_terms": 0, "direct_first_terms": 0,
                "direct_second_moment_checks": 0, "new_first_laws": 0,
                "complete_second_laws": 0, "histories": 0,
                "schedule_arms": 0, "bootstraps": 0}

    def signature(zmask: int) -> int:
        return sum(parity(zmask & flip) << i for i, flip in enumerate(flips))

    rows = []
    for flux_mask, errors in selected:
        target_flux = red_boundary(red, list(errors[0]))[1]
        assert sum(bit << i for i, bit in enumerate(target_flux)) == flux_mask
        pair_rows = []
        for edges in errors:
            physical, first_flux = red_boundary(red, list(edges))
            assert first_flux == target_flux
            eligible_first, means = sector_sites(sites, physical, flips, pairs)
            assert eligible_first == [i for i, bit in enumerate(first_flux) if bit == 0]
            first_conflict = any(value == -1 for value in means.values())
            variable_first = sorted(i for i in eligible_first if means[i] == 0)
            first_ops = [conjugated_star(sites[i], physical) for i in variable_first]
            assert all(commute(a, b) for a in first_ops for b in first_ops)
            first_signatures = [signature(op[1]) for op in first_ops]

            def signed_sum(tail=()) -> int:
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
                    counters["signed_affine_terms"] += 1
                    assert sum(counters[key] for key in ("signed_affine_terms", "direct_first_terms",
                                                        "direct_second_moment_checks")) <= budget["max_total_terms"]
                return total

            first_sum = 0 if first_conflict else signed_sum()
            first_mass = Fraction(first_sum, 1 << len(first_ops))
            direct = (Fraction() if first_conflict else
                      ordered_probability([(first_ops, (1,) * len(first_ops))], flips))
            counters["direct_first_terms"] += 0 if first_conflict else 1 << len(first_ops)
            assert first_mass == direct and 0 <= first_mass <= 1
            if edges == errors[0]:
                assert first_mass == 1
            counters["new_first_laws"] += 1
            cells = []
            if first_mass:
                for action in actions:
                    action_mask, _ = red_boundary(red, action)
                    residual = physical ^ action_mask
                    check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
                    assert residual == check_mask
                    eligible_second, _ = sector_sites(sites, residual, flips, pairs)
                    assert eligible_second == [i for i, bit in enumerate(second_flux) if bit == 0]
                    second_ops = {i: conjugated_star(sites[i], residual) for i in eligible_second}
                    assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
                    cache = {}

                    def conditional(group: tuple[int, ...]) -> Fraction:
                        if group not in cache:
                            product = compose([second_ops[i] for i in group])
                            assert compose([product, product]) == (1, 0, 0)
                            cache[group] = (Fraction(0) if any(not commute(product, op) for op in first_ops)
                                            else Fraction(signed_sum((product,)), first_sum))
                            assert -1 <= cache[group] <= 1
                        return cache[group]

                    singles = {i: conditional((i,)) for i in eligible_second}
                    assert all(value in (-1, 0, 1) for value in singles.values())
                    fixed = {i: int(value == -1) for i, value in singles.items() if value}
                    variable = sorted(i for i, value in singles.items() if not value)
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
                            counters["direct_second_moment_checks"] += 1
                            checked = True
                            break
                    assert checked
                    counters["complete_second_laws"] += 1
                    cells.append({"public_action_red_edges": action, "rows": public_rows,
                                  "variable_second_sites_private": variable})
                    assert time.process_time() - started <= budget["max_cpu_seconds"]
            pair_rows.append({"error_edges_private": list(edges), "first_public_mass": str(first_mass),
                              "cells": cells})
        differences = []
        for index, action in enumerate(actions):
            if all(row["first_public_mass"] != "0" for row in pair_rows):
                a, b = (law(row["cells"][index]["rows"]) for row in pair_rows)
                tv = sum((abs(a.get(key, Fraction()) - b.get(key, Fraction()))
                          for key in a.keys() | b.keys()), Fraction()) / 2
                assert 0 <= tv <= 1
                value = str(tv)
            else:
                value = None
            differences.append({"public_action_red_edges": action,
                                "conditional_second_total_variation": value})
        rows.append({"first_flux_mask": flux_mask, "sector_prior_mass": str(Fraction(
            int(prior_by_flux[flux_mask]["sector_prior_numerator_over_10_pow_36"]), 10 ** 36)),
                     "first_public": {"flux": target_flux, "charge": [0] * 24, "vacuum": [1] * 24},
                     "pair_rows": pair_rows, "paired_action_differences": differences})
    previous_row = next(row for row in previous["rows"] if row["base_first_likelihood_stratum"] == "1")
    replay = next(row for row in rows if row["first_flux_mask"] == previous_row["first_flux_mask"])
    assert [row["error_edges_private"] for row in replay["pair_rows"]] == [
        row["error_edges_private"] for row in previous_row["pair_rows"]]
    assert [row["first_public_mass"] for row in replay["pair_rows"]] == [
        row["first_public_mass"] for row in previous_row["pair_rows"]]
    assert replay["paired_action_differences"] == previous_row["paired_action_differences"]
    assert counters["new_first_laws"] == 24
    assert counters["complete_second_laws"] == counters["direct_second_moment_checks"]
    assert sum(counters[key] for key in ("signed_affine_terms", "direct_first_terms",
                                            "direct_second_moment_checks")) <= budget["max_total_terms"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "deterministic_first_collision_census_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"], "rows": rows,
            "tv_pattern_counts": {"/".join("undefined" if value is None else value for value in pattern): count
                                  for pattern, count in Counter(
                                      tuple(cell["conditional_second_total_variation"]
                                            for cell in row["paired_action_differences"])
                                      for row in rows).items()},
            "counters": counters, "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Direct exact complete first and action-conditioned second laws for all 12 equal-prior three-edge collision sectors with deterministic canonical-base first record; no operator symmetry inferred, no other sectors/records or full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "patterns": result["tv_pattern_counts"],
                      "terms": result["counters"]["signed_affine_terms"],
                      "cpu_seconds": result["cpu_seconds"]}))
