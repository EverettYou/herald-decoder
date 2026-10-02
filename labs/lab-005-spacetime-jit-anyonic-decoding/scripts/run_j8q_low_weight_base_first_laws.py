"""Exact all-zero-charge first law for each <=2-edge reached-flux base error."""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8q-low-weight-base-first-laws-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    prior = load("results/j8p-low-weight-flux-coset-screen-2026-09-28.json")
    j8o = load("results/j8o-other-flux-representative-feasibility-2026-09-28.json")
    assert prior["status"] == "low_weight_flux_coset_prior_screen_verified"
    assert prior["physical_prior"] == j8o["physical_prior"] == {
        "p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert len(prior["sector_rows"]) == prior["distinct_reached_first_flux_sectors"] == 667
    red, sites, flips, pairs = setup(
        load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
        load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    prepared = []
    projected = 0
    for row in prior["sector_rows"]:
        edges = tuple(row["representative_error_edges_private"])
        assert len(edges) == row["minimum_observed_error_weight"] <= 2
        physical, flux = red_boundary(red, list(edges))
        assert sum(bit << site for site, bit in enumerate(flux)) == row["first_flux_mask"]
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, bit in enumerate(flux) if bit == 0]
        operators = [conjugated_star(sites[site], physical) for site in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for index, left in enumerate(operators)
                   for right in operators[:index])
        conflict = any(mean == -1 for mean in means.values())
        variable = [site for site in eligible if means[site] == 0]
        terms = 0 if conflict else 1 << len(variable)
        projected += terms
        prepared.append((row, physical, variable, conflict, terms))
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert projected <= contract["budget"]["max_born_terms"], "Censor before any Born law if projected work exceeds cap"
    rows = []
    q_by_prior_group = defaultdict(set)
    total_base_joint = Fraction()
    for item, physical, variable, conflict, terms in prepared:
        base = tuple(item["representative_error_edges_private"])
        if conflict:
            q = Fraction()
        else:
            operators = [conjugated_star(sites[site], physical) for site in variable]
            q = ordered_probability([(operators, (1,) * len(operators))], flips)
        assert 0 <= q <= 1
        weight = Fraction(9 ** (36 - len(base)), 10 ** 36)
        sector = Fraction(int(item["sector_prior_numerator_over_10_pow_36"]), 10 ** 36)
        assert weight <= sector
        A = weight * q
        U = sector - weight
        posterior_upper = U / (A + U) if A + U else Fraction()
        total_base_joint += A
        key = (item["minimum_observed_error_weight"], item["first_flux_weight"],
               item["sector_prior_numerator_over_10_pow_36"])
        q_by_prior_group[key].add(q)
        rows.append({"representative_error_edges_private": list(base),
                     "first_public": {"flux_mask": item["first_flux_mask"],
                                      "charge": [0] * 24, "vacuum": [1] * 24},
                     "minimum_observed_error_weight": len(base),
                     "first_flux_weight": item["first_flux_weight"],
                     "sector_prior_mass": str(sector), "base_prior_mass": str(weight),
                     "base_first_variable_sites_private": variable,
                     "base_first_likelihood": str(q), "base_first_joint_mass": str(A),
                     "exact_first_terms": terms,
                     "worst_case_omitted_posterior_upper_bound": str(posterior_upper)})
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert len(rows) == 667 and sum(row["exact_first_terms"] for row in rows) == projected
    assert rows[0]["base_first_likelihood"] == j8o["rows"][0]["base_first_likelihood"]
    edge0 = next(row for row in rows if row["representative_error_edges_private"] == [0])
    assert edge0["base_first_likelihood"] == j8o["rows"][1]["base_first_likelihood"]
    assert sum((Fraction(row["sector_prior_mass"]) for row in rows), Fraction()) == Fraction(
        prior["reached_flux_sector_prior_mass"])
    assert 0 <= total_base_joint <= Fraction(prior["reached_flux_sector_prior_mass"])
    groups = [{"minimum_observed_error_weight": minimum,
               "first_flux_weight": flux_weight,
               "sector_prior_numerator_over_10_pow_36": numerator,
               "distinct_base_first_likelihoods": len(values),
               "base_first_likelihoods": sorted(str(value) for value in values)}
              for (minimum, flux_weight, numerator), values in sorted(q_by_prior_group.items())]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "low_weight_base_first_law_census_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"], "rows": rows,
            "prior_group_base_first_likelihood_diversity": groups,
            "total_disjoint_base_record_joint_mass": str(total_base_joint),
            "total_disjoint_base_record_joint_mass_decimal": round(float(total_base_joint), 15),
            "unresolved_channel_prior_mass_lower_bound": str(1 - Fraction(prior["reached_flux_sector_prior_mass"])),
            "counters": {"reached_flux_sectors": len(rows),
                         "new_born_terms": projected,
                         "new_positive_first_masses": sum(Fraction(row["base_first_likelihood"]) > 0 for row in rows),
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Exact specified all-zero-charge base-error complete first law in 667 <=2-edge reached flux sectors, plus crude omitted-prior posterior upper bounds. Not an all-error first-law census, operator-law symmetry proof, full-IID information/risk, noisy JIT, size scaling or threshold."}


if __name__ == "__main__":
    output = LAB / "results/j8q-low-weight-base-first-laws-2026-09-28.json"
    assert not output.exists(), "Refuse to overwrite existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "terms": result["counters"]["new_born_terms"],
                      "diverse_prior_groups": sum(g["distinct_base_first_likelihoods"] > 1
                                                  for g in result["prior_group_base_first_likelihood_diversity"]),
                      "cpu_seconds": result["cpu_seconds"]}))
