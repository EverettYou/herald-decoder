"""One-site projector tail bounds and exact-work preflight; no new Born laws."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction
from pathlib import Path

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8m-structural-tail-and-cost-screen-2026-09-27.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def private_support(row: dict) -> tuple[int, ...]:
    edges = row["error_edges_private"]
    assert len(edges) == len(set(edges)) and all(0 <= edge < 36 for edge in edges)
    return tuple(sorted(edges))


def iid_weight(edges: tuple[int, ...]) -> Fraction:
    return Fraction(9 ** (36 - len(edges)), 10 ** 36)


def upper_likelihood(means: dict[int, int], charge_sites: tuple[int, ...]) -> Fraction:
    # All first-block stars are simultaneous conjugates of the commuting
    # frozen star family. Their complete-record projector is dominated by
    # every one-site projector. A conflicting deterministic site gives zero;
    # otherwise any fair one-site marginal gives an upper bound of 1/2.
    assert all(mean in (-1, 0, 1) for mean in means.values())
    if any((mean == 1 and site in charge_sites) or
           (mean == -1 and site not in charge_sites)
           for site, mean in means.items()):
        return Fraction()
    return Fraction(1, 2) if any(mean == 0 for mean in means.values()) else Fraction(1)


def run() -> dict:
    start = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    j6l = load("results/j6l-periodic-kagome-incidence-2026-09-24.json")
    j6m = load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json")
    j8j = load("results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json")
    j8l = load("results/j8l-first-record-tail-certificate-2026-09-27.json")
    j8k = load("results/j8k-corrected-alternate-first-record-masses-2026-09-27.json")
    j8i = load("results/j8i-all-support-complete-second-laws-verified-2026-09-27.json")
    j8c = load("results/j8c-support-geometry-cost-matrix-2026-09-27.json")
    assert j8j["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert j8j["same_first_flux_error_count"] == 8192
    assert len(j8l["rows"]) == 4 and len(j8k["rows"]) == 13 and len(j8i["rows"]) == 55
    red, sites, flips, pairs = setup(j6l, j6m)
    assert len(red) == 36 and len(sites) == 24
    flux_target = j8i["first_public"]["flux"]
    base = j8i["rows"][0]["error_edges_private"]
    assert red_boundary(red, base)[1] == flux_target
    columns = [sum(bit << i for i, bit in enumerate(red_boundary(red, [edge])[1])) for edge in range(36)]
    basis = {}
    kernel = []
    for edge, column in enumerate(columns):
        residual, combination = column, 1 << edge
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (residual, combination)
                break
            residual ^= basis[pivot][0]
            combination ^= basis[pivot][1]
        if residual == 0:
            kernel.append(combination)
    assert (len(basis), len(kernel)) == (23, 13)
    base_mask = sum(1 << edge for edge in base)
    known_short = {private_support(row) for row in j8k["rows"]}
    known_selected = known_short | {private_support(row) for row in j8i["rows"]}
    assert len(known_short) == 13 and len(known_selected) == 67
    known_masses = {(): {private_support(row): Fraction(row["first_public_mass"])
                         for row in j8i["rows"]}}
    for row in j8k["rows"]:
        edges = private_support(row)
        for case in row["cases"]:
            key = tuple(case["charge_sites"])
            mass = Fraction(case["mass"])
            if edges in known_masses.setdefault(key, {}):
                assert known_masses[key][edges] == mass
            known_masses[key][edges] = mass
    assert {key: len(masses) for key, masses in known_masses.items()} == {
        (): 67, (1,): 13, (2,): 13, (1, 2): 13}
    prior_sector = Fraction(j8j["selected_flux_prior_mass"])
    records = {}
    for row in j8l["rows"]:
        charge_sites = tuple(row["first_charge_sites"])
        public = row["first_public"]
        assert len(public["flux"]) == len(public["charge"]) == len(public["vacuum"]) == 24
        assert public["flux"] == flux_target
        assert all(v == 1 - c for v, c in zip(public["vacuum"], public["charge"]))
        assert charge_sites == tuple(i for i, c in enumerate(public["charge"]) if c)
        known = known_selected if not charge_sites else known_short
        assert len(known) == row["known_law_error_count"]
        records[charge_sites] = {"known": known, "baseline": row, "upper": Fraction(),
                                 "excluded_prior": Fraction(), "compatible_prior": Fraction(),
                                 "excluded_count": 0, "compatible_count": 0}
    assert set(records) == {(), (1,), (2,), (1, 2)}
    seen = set()
    weight_total = Fraction()
    for free_bits in range(1 << len(kernel)):
        error_mask = base_mask
        for index, vector in enumerate(kernel):
            if free_bits >> index & 1:
                error_mask ^= vector
        edges = tuple(edge for edge in range(36) if error_mask >> edge & 1)
        assert edges not in seen
        seen.add(edges)
        physical, flux = red_boundary(red, list(edges))
        assert flux == flux_target
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [i for i, bit in enumerate(flux) if bit == 0]
        operators = [conjugated_star(sites[site], physical) for site in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for index, left in enumerate(operators)
                   for right in operators[:index])
        assert sum(mean == 0 for mean in means.values()) >= 2
        assert all(mean != -1 for mean in means.values())
        weight = iid_weight(edges)
        weight_total += weight
        for charge_sites, record in records.items():
            qmax = upper_likelihood(means, charge_sites)
            if edges in record["known"]:
                assert known_masses[charge_sites][edges] <= qmax
                continue
            record["upper"] += weight * qmax
            if qmax:
                record["compatible_prior"] += weight
                record["compatible_count"] += 1
            else:
                record["excluded_prior"] += weight
                record["excluded_count"] += 1
        assert time.process_time() - start <= contract["budget"]["max_cpu_seconds"]
    assert len(seen) == 8192 and weight_total == prior_sector
    rows = []
    for charge_sites, record in records.items():
        known_prior = sum((iid_weight(edges) for edges in record["known"]), Fraction())
        omitted_prior = prior_sector - known_prior
        assert record["excluded_prior"] + record["compatible_prior"] == omitted_prior
        assert record["excluded_count"] + record["compatible_count"] == 8192 - len(record["known"])
        old = record["baseline"]
        assert Fraction(old["omitted_prior_mass_upper_bound"]) == omitted_prior
        A = Fraction(old["known_first_record_joint_mass"])
        new = record["upper"] / (A + record["upper"])
        baseline = Fraction(old["omitted_posterior_mass_upper_bound"])
        assert 0 <= new <= baseline <= 1
        rows.append({"first_charge_sites": list(charge_sites),
                     "omitted_error_count": 8192 - len(record["known"]),
                     "structurally_excluded_error_count": record["excluded_count"],
                     "structurally_excluded_prior_mass": str(record["excluded_prior"]),
                     "structurally_compatible_error_count": record["compatible_count"],
                     "structurally_compatible_prior_mass": str(record["compatible_prior"]),
                     "one_site_omitted_joint_mass_upper_bound": str(record["upper"]),
                     "one_site_omitted_posterior_upper_bound": str(new),
                     "one_site_omitted_posterior_upper_bound_decimal": round(float(new), 12),
                     "previous_worst_case_posterior_upper_bound": str(baseline)})
    cycles = [row for branch in j8c["new_support_branches"] if branch["cycle_length"] == 8
              for row in branch["rows"]]
    assert len(cycles) == 54
    costs = {}
    for charge_sites in ((1,), (2,), (1, 2)):
        costs[str(list(charge_sites))] = sum(
            row["projected_exact_first_terms"]
            for row in cycles if all(site in row["first_variable_sites_private"] for site in charge_sites)
        )
    total_cost = sum(costs.values())
    assert total_cost > contract["budget"]["max_total_terms"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - start
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "selected_flux_structural_tail_screen_closed",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "rows": rows,
            "eight_edge_alternate_exact_first_mass_projected_terms": costs,
            "eight_edge_three_record_total_projected_terms": total_cost,
            "eight_edge_three_record_exact_matrix_fits_inherited_cap": False,
            "counters": {"same_flux_errors_structurally_checked": len(seen),
                         "new_born_terms": 0, "new_first_record_masses": 0,
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Exact selected-flux one-site projector upper bounds and cost feasibility for four existing L=2 first records at p_X=1/10. Not an omitted-law evaluation, second-record mixture, full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    output = LAB / "results/j8m-structural-tail-and-cost-screen-verified-2026-09-27.json"
    assert not output.exists(), "Refuse to overwrite existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "bounds": [(r["first_charge_sites"], r["one_site_omitted_posterior_upper_bound_decimal"])
                                 for r in result["rows"]],
                      "projected_terms": result["eight_edge_three_record_total_projected_terms"]}))
