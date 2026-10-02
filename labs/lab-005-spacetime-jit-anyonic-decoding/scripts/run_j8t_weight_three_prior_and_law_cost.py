"""Exact weight-three first-flux prior coverage and base-first-law cost gate."""

from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from math import comb
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j8o_other_flux_representative_feasibility import flux_basis


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8t-weight-three-prior-and-law-cost-2026-09-28.json"
RESULT = LAB / "results/j8t-weight-three-prior-and-law-cost-2026-09-28.json"


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
    prior = load("results/j8p-low-weight-flux-coset-screen-2026-09-28.json")
    assert prior["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert len(prior["sector_rows"]) == 667
    red, sites, flips, pairs = setup(load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
                                      load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    kernel = flux_basis(red)
    cosets = [0]
    for vector in kernel:
        cosets.extend(mask ^ vector for mask in cosets[:])
    assert len(cosets) == len(set(cosets)) == 8192
    columns = [sum(bit << i for i, bit in enumerate(red_boundary(red, [edge])[1]))
               for edge in range(36)]
    old_flux = {row["first_flux_mask"] for row in prior["sector_rows"]}
    assert len(old_flux) == 667
    new: dict[int, tuple[int, int, int]] = {}
    overlap = 0
    duplicate_new = 0
    for edges in itertools.combinations(range(36), 3):
        flux = columns[edges[0]] ^ columns[edges[1]] ^ columns[edges[2]]
        if flux in old_flux:
            overlap += 1
        else:
            if flux in new:
                duplicate_new += 1
            else:
                new[flux] = edges
    assert len(new) + overlap + duplicate_new == comb(36, 3)
    assert len(new) * 8192 <= budget["max_prior_weight_evaluations"]
    weights = [9 ** (36 - weight) for weight in range(37)]
    numerator_new = 0
    projected_terms = 0
    variable_counts = Counter()
    prior_diversity: dict[int, set[int]] = defaultdict(set)
    rows = []
    for index, (flux, edges) in enumerate(sorted(new.items(), key=lambda item: item[1])):
        base_mask = sum(1 << edge for edge in edges)
        numerator = sum(weights[(base_mask ^ mask).bit_count()] for mask in cosets)
        assert numerator > 0
        numerator_new += numerator
        physical, actual_flux = red_boundary(red, list(edges))
        assert sum(bit << i for i, bit in enumerate(actual_flux)) == flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [i for i, bit in enumerate(actual_flux) if bit == 0]
        operators = [conjugated_star(sites[i], physical) for i in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for i, left in enumerate(operators) for right in operators[:i])
        conflict = any(value == -1 for value in means.values())
        variable = sorted(i for i in eligible if means[i] == 0)
        terms = 0 if conflict else 1 << len(variable)
        projected_terms += terms
        variable_counts[(len(variable), conflict)] += 1
        prior_diversity[flux.bit_count()].add(numerator)
        rows.append({"representative_error_edges_private": list(edges),
                     "first_flux_mask": flux, "first_flux_weight": flux.bit_count(),
                     "sector_prior_numerator_over_10_pow_36": str(numerator),
                     "base_first_variable_sites_private": variable,
                     "base_first_projected_terms": terms,
                     "base_first_deterministic_conflict": conflict})
        if index % 32 == 0:
            assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert len(rows) == len(new)
    old_numerator = sum(int(row["sector_prior_numerator_over_10_pow_36"])
                        for row in prior["sector_rows"])
    assert Fraction(old_numerator, 10 ** 36) == Fraction(prior["reached_flux_sector_prior_mass"])
    cumulative = Fraction(old_numerator + numerator_new, 10 ** 36)
    physical_at_most_three = sum((Fraction(comb(36, weight) * 9 ** (36 - weight), 10 ** 36)
                                  for weight in range(4)), Fraction())
    assert physical_at_most_three <= cumulative <= 1
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "weight_three_prior_and_base_law_cost_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"],
            "weight_three_support_count": comb(36, 3), "weight_three_supports_overlapping_old_flux": overlap,
            "weight_three_supports_duplicate_new_flux": duplicate_new,
            "new_weight_three_flux_sectors": len(rows),
            "cumulative_reached_flux_sectors": 667 + len(rows),
            "new_sector_prior_mass": str(Fraction(numerator_new, 10 ** 36)),
            "cumulative_reached_flux_sector_prior_mass": str(cumulative),
            "cumulative_reached_flux_sector_prior_mass_decimal": round(float(cumulative), 15),
            "complementary_unreached_flux_sector_prior_mass": str(1 - cumulative),
            "physical_prior_weight_at_most_three": str(physical_at_most_three),
            "new_base_first_projected_terms": projected_terms,
            "new_base_first_laws_fit_inherited_term_cap": projected_terms <= budget["inherited_exact_projector_term_ceiling"],
            "variable_site_classes": [{"variable_sites": n, "deterministic_conflict": conflict,
                                       "sectors": count}
                                      for (n, conflict), count in sorted(variable_counts.items())],
            "distinct_sector_priors_by_flux_weight": [{"flux_weight": weight, "distinct_prior_values": len(values)}
                                                     for weight, values in sorted(prior_diversity.items())],
            "sector_rows": rows,
            "counters": {"exact_prior_weight_evaluations": len(rows) * 8192,
                         "new_born_terms": 0, "new_first_masses": 0,
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Exact flux-sector prior coverage added by weight-three physical supports and projected base-first cost, not evaluated first/second laws, operator symmetry, full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "new_sectors": result["new_weight_three_flux_sectors"],
                      "cumulative_prior": result["cumulative_reached_flux_sector_prior_mass_decimal"],
                      "projected_terms": result["new_base_first_projected_terms"],
                      "fits_term_cap": result["new_base_first_laws_fit_inherited_term_cap"],
                      "cpu_seconds": result["cpu_seconds"]}))
