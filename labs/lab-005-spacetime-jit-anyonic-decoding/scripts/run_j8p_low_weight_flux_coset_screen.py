"""Exact prior/cost screen of every flux reached by zero, one or two red-X edges."""

from __future__ import annotations

import hashlib
import itertools
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb
from pathlib import Path

from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j8o_other_flux_representative_feasibility import flux_basis


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8p-low-weight-flux-coset-screen-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == expected for path, expected in contract["pinned_inputs"].items())
    prior = load("results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json")
    j8o = load("results/j8o-other-flux-representative-feasibility-2026-09-28.json")
    assert prior["physical_prior"] == j8o["physical_prior"] == {
        "p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert (prior["boundary_rank"], prior["kernel_dimension"],
            prior["same_first_flux_error_count"]) == (23, 13, 8192)
    assert sum((Fraction(comb(36, w) * 9 ** (36 - w), 10 ** 36)
                for w in range(37)), Fraction()) == 1
    red, sites, flips, pairs = setup(
        load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
        load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    kernel = flux_basis(red)
    cosets = [0]
    for vector in kernel:
        cosets += [mask ^ vector for mask in cosets]
    assert len(set(cosets)) == 8192 and len(cosets) == 8192
    columns = [sum(bit << site for site, bit in enumerate(red_boundary(red, [edge])[1]))
               for edge in range(36)]
    representatives: dict[int, tuple[int, ...]] = {}
    support_counts = Counter()
    for w in range(contract["matrix"]["maximum_support_weight"] + 1):
        for edges in itertools.combinations(range(36), w):
            flux = 0
            for edge in edges:
                flux ^= columns[edge]
            support_counts[w] += 1
            representatives.setdefault(flux, edges)
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert sum(support_counts.values()) == 1 + 36 + comb(36, 2)
    assert 0 in representatives and columns[0] in representatives
    weights = [9 ** (36 - w) for w in range(37)]
    denominator = 10 ** 36
    rows = []
    total_numerator = 0
    group_counts = defaultdict(int)
    weight_group_values = defaultdict(set)
    for flux, edges in sorted(representatives.items(), key=lambda item: (len(item[1]), item[1])):
        base = sum(1 << edge for edge in edges)
        numerator = sum(weights[(base ^ kernel_mask).bit_count()] for kernel_mask in cosets)
        assert numerator > 0
        total_numerator += numerator
        flux_weight = flux.bit_count()
        group_counts[(len(edges), flux_weight, numerator)] += 1
        weight_group_values[(len(edges), flux_weight)].add(numerator)
        rows.append({"representative_error_edges_private": list(edges),
                     "minimum_observed_error_weight": len(edges),
                     "first_flux_mask": flux, "first_flux_weight": flux_weight,
                     "sector_prior_numerator_over_10_pow_36": str(numerator)})
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert len(rows) <= sum(support_counts.values())
    assert total_numerator <= denominator
    assert Fraction(int(rows[0]["sector_prior_numerator_over_10_pow_36"]), denominator) == Fraction(
        j8o["rows"][0]["sector_prior_mass"])
    one_edge = next(row for row in rows if row["representative_error_edges_private"] == [0])
    assert Fraction(int(one_edge["sector_prior_numerator_over_10_pow_36"]), denominator) == Fraction(
        j8o["rows"][1]["sector_prior_mass"])
    selected_flux = load("results/j8i-all-support-complete-second-laws-verified-2026-09-27.json")["first_public"]["flux"]
    selected_mask = sum(bit << site for site, bit in enumerate(selected_flux))
    selected_reached = selected_mask in representatives
    if selected_reached:
        selected_row = next(row for row in rows if row["first_flux_mask"] == selected_mask)
        assert Fraction(int(selected_row["sector_prior_numerator_over_10_pow_36"]), denominator) == Fraction(
            prior["selected_flux_prior_mass"])
    cohort = Fraction(total_numerator, denominator)
    low_weight_physical = sum((Fraction(comb(36, w) * 9 ** (36 - w), denominator)
                               for w in range(3)), Fraction())
    assert cohort >= low_weight_physical
    one_edge_values = weight_group_values[(1, 2)]
    assert len(one_edge_values) == 1 and sum(1 for row in rows if row["minimum_observed_error_weight"] == 1) == 36
    groups = [{"minimum_observed_error_weight": minimum,
               "first_flux_weight": flux_weight,
               "sector_prior_numerator_over_10_pow_36": str(numerator),
               "sector_count": count}
              for (minimum, flux_weight, numerator), count in sorted(group_counts.items())]
    arithmetic_checks = len(rows) * len(cosets)
    assert arithmetic_checks <= contract["budget"]["max_prior_weight_evaluations"]
    assert all(sha(LAB / path) == expected for path, expected in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "low_weight_flux_coset_prior_screen_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"],
            "support_counts_by_weight": {str(w): n for w, n in sorted(support_counts.items())},
            "distinct_reached_first_flux_sectors": len(rows),
            "reached_flux_sector_prior_mass": str(cohort),
            "reached_flux_sector_prior_mass_decimal": round(float(cohort), 15),
            "unreached_flux_sector_prior_mass": str(1 - cohort),
            "unreached_flux_sector_prior_mass_decimal": round(float(1 - cohort), 15),
            "physical_prior_weight_at_most_two": str(low_weight_physical),
            "physical_prior_weight_at_most_two_decimal": round(float(low_weight_physical), 15),
            "selected_j8i_flux_reached": selected_reached,
            "all_single_edge_sectors_equal_prior": len(one_edge_values) == 1,
            "prior_mass_distinct_values_by_minimum_weight_and_flux_weight": [
                {"minimum_observed_error_weight": minimum, "first_flux_weight": flux_weight,
                 "distinct_prior_values": len(values)}
                for (minimum, flux_weight), values in sorted(weight_group_values.items())],
            "prior_equivalence_groups": groups,
            "sector_rows": rows,
            "full_per_error_first_law_direct_term_lower_bound": arithmetic_checks,
            "counters": {"distinct_flux_prior_cosets": len(rows),
                         "exact_prior_weight_evaluations": arithmetic_checks,
                         "new_born_terms": 0, "new_first_masses": 0,
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Exact prior-mass and direct per-error first-law cost screen for flux sectors reached by <=2 physical red-X edges, not a geometric or operator-law symmetry proof. No new Born/public law, full-IID information/risk, noisy JIT, size scaling or threshold."}


if __name__ == "__main__":
    output = LAB / "results/j8p-low-weight-flux-coset-screen-2026-09-28.json"
    assert not output.exists(), "Refuse to overwrite existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "sectors": result["distinct_reached_first_flux_sectors"],
                      "mass": result["reached_flux_sector_prior_mass_decimal"],
                      "groups": len(result["prior_equivalence_groups"]),
                      "cpu_seconds": result["cpu_seconds"]}))
