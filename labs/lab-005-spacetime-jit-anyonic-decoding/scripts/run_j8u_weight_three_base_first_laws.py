"""Complete all-zero-charge first laws for new weight-three canonical bases."""

from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8u-weight-three-base-first-laws-2026-09-28.json"
RESULT = LAB / "results/j8u-weight-three-base-first-laws-2026-09-28.json"


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
    preflight = load("results/j8t-weight-three-prior-and-law-cost-2026-09-28.json")
    old = load("results/j8q-low-weight-base-first-laws-2026-09-28.json")
    assert preflight["physical_prior"] == old["physical_prior"] == {
        "p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert preflight["new_weight_three_flux_sectors"] == 7020
    assert len(preflight["sector_rows"]) == 7020
    assert preflight["new_base_first_projected_terms"] == 9360
    assert preflight["new_base_first_laws_fit_inherited_term_cap"]
    assert {row["first_flux_mask"] for row in preflight["sector_rows"]}.isdisjoint(
        {row["first_public"]["flux_mask"] for row in old["rows"]})
    red, sites, flips, pairs = setup(load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
                                      load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    projected = sum(row["base_first_projected_terms"] for row in preflight["sector_rows"])
    assert projected == 9360 <= budget["max_born_terms"]
    base_prior = Fraction(9 ** 33, 10 ** 36)
    rows = []
    q_counts = Counter()
    q_by_prior_group: dict[tuple[int, int], set[Fraction]] = defaultdict(set)
    new_joint = Fraction()
    for index, item in enumerate(preflight["sector_rows"]):
        edges = tuple(item["representative_error_edges_private"])
        assert len(edges) == 3
        physical, flux = red_boundary(red, list(edges))
        assert sum(bit << site for site, bit in enumerate(flux)) == item["first_flux_mask"]
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, bit in enumerate(flux) if bit == 0]
        operators = [conjugated_star(sites[site], physical) for site in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for i, left in enumerate(operators) for right in operators[:i])
        conflict = any(value == -1 for value in means.values())
        variable = sorted(site for site in eligible if means[site] == 0)
        assert variable == item["base_first_variable_sites_private"]
        terms = 0 if conflict else 1 << len(variable)
        assert terms == item["base_first_projected_terms"]
        if conflict:
            q = Fraction()
        else:
            selected = [conjugated_star(sites[site], physical) for site in variable]
            q = ordered_probability([(selected, (1,) * len(selected))], flips)
        assert 0 <= q <= 1
        if len(variable) == 0 and not conflict:
            assert q == 1
        if len(variable) == 1 and not conflict:
            assert q == Fraction(1, 2)
        sector_prior = Fraction(int(item["sector_prior_numerator_over_10_pow_36"]), 10 ** 36)
        assert base_prior <= sector_prior
        joint = base_prior * q
        assert joint <= sector_prior
        new_joint += joint
        q_counts[str(q)] += 1
        q_by_prior_group[(item["first_flux_weight"],
                          int(item["sector_prior_numerator_over_10_pow_36"]))].add(q)
        rows.append({"representative_error_edges_private": list(edges),
                     "first_flux_mask": item["first_flux_mask"],
                     "first_flux_weight": item["first_flux_weight"],
                     "first_public": {"charge": [0] * 24, "vacuum": [1] * 24},
                     "base_first_variable_sites_private": variable,
                     "base_first_likelihood": str(q),
                     "base_first_joint_mass": str(joint),
                     "exact_first_terms": terms})
        if index % 64 == 0:
            assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert len(rows) == 7020 and sum(row["exact_first_terms"] for row in rows) == projected
    old_joint = Fraction(old["total_disjoint_base_record_joint_mass"])
    cumulative_joint = old_joint + new_joint
    assert 0 <= new_joint <= Fraction(preflight["new_sector_prior_mass"])
    assert cumulative_joint <= Fraction(preflight["cumulative_reached_flux_sector_prior_mass"])
    assert sum(q_counts.values()) == 7020
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "weight_three_base_first_laws_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": preflight["physical_prior"],
            "new_sector_count": len(rows),
            "first_public_record_convention": "pre-action full-binary flux per row, all 24 charge bits zero and vacuum=1-charge",
            "base_prior_mass_each": str(base_prior),
            "first_likelihood_counts": [{"likelihood": key, "sectors": count}
                                         for key, count in sorted(q_counts.items(), key=lambda pair: Fraction(pair[0]))],
            "prior_group_first_likelihood_diversity": [
                {"first_flux_weight": flux_weight,
                 "sector_prior_numerator_over_10_pow_36": str(numerator),
                 "distinct_base_first_likelihoods": len(values),
                 "base_first_likelihoods": sorted((str(value) for value in values), key=Fraction)}
                for (flux_weight, numerator), values in sorted(q_by_prior_group.items())],
            "total_new_disjoint_base_record_joint_mass": str(new_joint),
            "total_new_disjoint_base_record_joint_mass_decimal": round(float(new_joint), 15),
            "total_cumulative_at_most_three_base_record_joint_mass": str(cumulative_joint),
            "total_cumulative_at_most_three_base_record_joint_mass_decimal": round(float(cumulative_joint), 15),
            "reached_sector_prior_mass": preflight["cumulative_reached_flux_sector_prior_mass"],
            "unreached_sector_prior_mass": preflight["complementary_unreached_flux_sector_prior_mass"],
            "rows": rows,
            "counters": {"new_born_terms": projected, "new_first_masses": len(rows),
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Complete specified all-zero-charge first law for one canonical weight-three private base per new first-flux sector, plus disjoint base-record joint contributions. Not a law for other same-flux errors, alternate first records, second laws, operator symmetry, full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "new_base_joint": result["total_new_disjoint_base_record_joint_mass_decimal"],
                      "cumulative_base_joint": result["total_cumulative_at_most_three_base_record_joint_mass_decimal"],
                      "likelihood_counts": result["first_likelihood_counts"],
                      "cpu_seconds": result["cpu_seconds"]}))
