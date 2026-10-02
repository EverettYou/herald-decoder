"""Two other-flux representative first-law feasibility certificates; no second law."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction
from math import comb
from pathlib import Path

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8o-other-flux-representative-feasibility-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def weight(edges: tuple[int, ...]) -> Fraction:
    return Fraction(9 ** (36 - len(edges)), 10 ** 36)


def flux_basis(red: dict) -> list[int]:
    columns = [sum(bit << site for site, bit in
                   enumerate(red_boundary(red, [edge])[1])) for edge in range(36)]
    pivots: dict[int, tuple[int, int]] = {}
    kernel = []
    for edge, column in enumerate(columns):
        residual, combination = column, 1 << edge
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = residual, combination
                break
            residual ^= pivots[pivot][0]
            combination ^= pivots[pivot][1]
        if not residual:
            kernel.append(combination)
    assert len(pivots) == 23 and len(kernel) == 13
    return kernel


def branch(base: tuple[int, ...], red: dict, sites: dict, flips: list[int],
           pairs: list[dict], kernel: list[int], started: float, cap: int) -> dict:
    base_physical, target_flux = red_boundary(red, list(base))
    assert len(target_flux) == 24
    eligible, means = sector_sites(sites, base_physical, flips, pairs)
    assert eligible == [site for site, bit in enumerate(target_flux) if not bit]
    assert all(mean != -1 for mean in means.values())
    variable = [site for site in eligible if means[site] == 0]
    exact_terms = 1 << len(variable)
    assert exact_terms <= cap
    operators = [conjugated_star(sites[site], base_physical) for site in variable]
    base_first_likelihood = ordered_probability([(operators, (1,) * len(operators))], flips)
    assert 0 < base_first_likelihood <= 1
    base_mask = sum(1 << edge for edge in base)
    seen = set()
    sector_prior = omitted_upper = Fraction()
    excluded = fair = deterministic = 0
    for free_bits in range(1 << len(kernel)):
        error_mask = base_mask
        for index, vector in enumerate(kernel):
            if free_bits >> index & 1:
                error_mask ^= vector
        edges = tuple(edge for edge in range(36) if error_mask >> edge & 1)
        assert edges not in seen
        seen.add(edges)
        physical, flux = red_boundary(red, list(edges))
        assert flux == target_flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, bit in enumerate(flux) if not bit]
        operators = [conjugated_star(sites[site], physical) for site in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for index, left in enumerate(operators)
                   for right in operators[:index])
        prior = weight(edges)
        sector_prior += prior
        if edges != base:
            if -1 in means.values():
                excluded += 1
            elif 0 in means.values():
                fair += 1
                omitted_upper += prior / 2
            else:
                deterministic += 1
                omitted_upper += prior
        assert time.process_time() - started <= 60
    assert len(seen) == 8192 and base in seen
    base_joint = weight(base) * base_first_likelihood
    assert 0 <= omitted_upper <= sector_prior - weight(base)
    assert excluded + fair + deterministic == 8191
    public = {"flux": target_flux, "charge": [0] * 24, "vacuum": [1] * 24}
    return {"base_error_edges_private": list(base), "first_public": public,
            "compatible_error_count": len(seen), "sector_prior_mass": str(sector_prior),
            "sector_prior_mass_decimal": round(float(sector_prior), 15),
            "base_prior_mass": str(weight(base)),
            "base_fraction_of_sector": str(weight(base) / sector_prior),
            "base_first_variable_sites_private": variable,
            "base_first_likelihood": str(base_first_likelihood),
            "base_first_joint_mass": str(base_joint),
            "exact_first_terms": exact_terms,
            "omitted_joint_mass_upper_bound": str(omitted_upper),
            "omitted_posterior_upper_bound": str(omitted_upper / (base_joint + omitted_upper)),
            "omitted_posterior_upper_bound_decimal": round(float(omitted_upper / (base_joint + omitted_upper)), 12),
            "omitted_error_counts": {"excluded": excluded, "fair_one_site": fair,
                                     "deterministic_compatible": deterministic}}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    prior = load("results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json")
    old = load("results/j8n-four-record-channel-coverage-2026-09-27.json")
    assert prior["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert (prior["boundary_rank"], prior["kernel_dimension"],
            prior["same_first_flux_error_count"]) == (23, 13, 8192)
    assert sum((Fraction(comb(36, w) * 9 ** (36 - w), 10 ** 36)
                for w in range(37)), Fraction()) == 1
    red, sites, flips, pairs = setup(load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
                                     load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    kernel = flux_basis(red)
    rows = [branch(tuple(base), red, sites, flips, pairs, kernel, started,
                   contract["budget"]["max_total_terms"])
            for base in contract["matrix"]["base_error_edges_private"]]
    assert len(rows) == 2
    assert rows[0]["first_public"]["flux"] != rows[1]["first_public"]["flux"]
    selected_flux = load("results/j8i-all-support-complete-second-laws-verified-2026-09-27.json")["first_public"]["flux"]
    assert all(row["first_public"]["flux"] != selected_flux for row in rows)
    terms = sum(row["exact_first_terms"] for row in rows)
    assert terms <= contract["budget"]["max_total_terms"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    total = sum((Fraction(row["sector_prior_mass"]) for row in rows), Fraction())
    assert total < Fraction(old["other_first_flux_prior_mass"])
    return {"schema_version": 1, "id": contract["id"],
            "status": "two_other_flux_representative_feasibility_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"], "rows": rows,
            "two_representative_flux_sectors_prior_mass": str(total),
            "two_representative_flux_sectors_prior_mass_decimal": round(float(total), 15),
            "two_sector_fraction_of_other_flux_mass": str(total / Fraction(old["other_first_flux_prior_mass"])),
            "counters": {"physical_errors_structurally_checked": 16384,
                         "new_born_terms": terms, "new_first_masses": 2,
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Two selected other-flux representatives only, at frozen ideal L=2 p_X=1/10. Exact sector priors and base first laws with one-site omitted upper bounds. Not all other flux sectors, full-IID information/risk, noisy JIT, size scaling, or threshold."}


if __name__ == "__main__":
    output = LAB / "results/j8o-other-flux-representative-feasibility-2026-09-28.json"
    assert not output.exists(), "Refuse to overwrite existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "sector_priors": [row["sector_prior_mass_decimal"] for row in result["rows"]],
                      "omitted_bounds": [row["omitted_posterior_upper_bound_decimal"] for row in result["rows"]],
                      "cpu_seconds": result["cpu_seconds"]}))
