"""Fixed-action symmetry prerequisite and one high-prior two-edge omitted-tail bound."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j8o_other_flux_representative_feasibility import flux_basis


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8r-action-binding-and-two-edge-tail-2026-09-28.json"


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
    first = load("results/j8q-low-weight-base-first-laws-2026-09-28.json")
    assert prior["physical_prior"] == first["physical_prior"] == {
        "p_X": "1/10", "p_Z": "0", "red_edges": 36}
    red, sites, flips, pairs = setup(
        load("results/j6l-periodic-kagome-incidence-2026-09-24.json"),
        load("results/j6m-periodic-operator-ground-orbit-2026-09-24.json"))
    assert len(red) == 36 and len(sites) == 24
    action_edges = [tuple(branch) for branch in contract["matrix"]["fixed_action_red_edges"]]
    assert action_edges == [(0,), (1, 30, 32, 34, 35)]
    one_edges = [row for row in prior["sector_rows"]
                 if row["minimum_observed_error_weight"] == 1]
    assert len(one_edges) == 36
    membership_counts = Counter(tuple(int(edge in action) for action in action_edges)
                                for edge in range(36))
    assert membership_counts == {(1, 0): 1, (0, 1): 5, (0, 0): 30}
    one_edge_sector_priors = {Fraction(int(row["sector_prior_numerator_over_10_pow_36"]),
                                       10 ** 36) for row in one_edges}
    assert len(one_edge_sector_priors) == 1
    one_edge_prior = next(iter(one_edge_sector_priors))
    action_rows = []
    for action in action_edges:
        masks = set()
        for edge in range(36):
            remaining = sorted(set((edge,)) ^ set(action))
            _, second_flux = red_boundary(red, remaining)
            flux_mask = sum(bit << site for site, bit in enumerate(second_flux))
            assert flux_mask not in masks
            masks.add(flux_mask)
            if edge == 0:
                assert second_flux == red_boundary(red, sorted(set(action) ^ {0}))[1]
        action_rows.append({"public_action_red_edge_ids": list(action),
                            "distinct_action_conditioned_second_fluxes_for_36_one_edge_bases": len(masks)})
    assert all(row["distinct_action_conditioned_second_fluxes_for_36_one_edge_bases"] == 36
               for row in action_rows)
    membership = [{"in_singleton_action": key[0], "in_five_edge_action": key[1],
                   "one_edge_sector_count": count,
                   "one_edge_sector_prior_mass": str(one_edge_prior * count)}
                  for key, count in sorted(membership_counts.items(), reverse=True)]
    # Strict action-preserving relabelings must preserve these membership
    # classes; this is a necessary obstruction, not an automorphism census.
    assert len(membership) == 3 and membership_counts[(1, 0)] == 1

    pairs_only = [row for row in prior["sector_rows"]
                  if row["minimum_observed_error_weight"] == 2]
    assert len(pairs_only) == 630
    selected = min(pairs_only,
                   key=lambda row: (-int(row["sector_prior_numerator_over_10_pow_36"]),
                                    tuple(row["representative_error_edges_private"])))
    base = tuple(selected["representative_error_edges_private"])
    first_row = next(row for row in first["rows"]
                     if row["representative_error_edges_private"] == list(base))
    assert first_row["first_public"]["flux_mask"] == selected["first_flux_mask"]
    assert first_row["first_public"]["charge"] == [0] * 24
    assert first_row["first_public"]["vacuum"] == [1] * 24
    assert Fraction(first_row["base_first_likelihood"]) > 0
    target_flux = red_boundary(red, list(base))[1]
    kernel = flux_basis(red)
    kernel_masks = [0]
    for vector in kernel:
        kernel_masks += [mask ^ vector for mask in kernel_masks]
    assert len(set(kernel_masks)) == 8192
    base_mask = sum(1 << edge for edge in base)
    sector_prior = excluded_prior = fair_prior = deterministic_prior = Fraction()
    counts = Counter()
    seen = set()
    for kernel_mask in kernel_masks:
        error_mask = base_mask ^ kernel_mask
        edges = tuple(edge for edge in range(36) if error_mask >> edge & 1)
        assert edges not in seen
        seen.add(edges)
        physical, flux = red_boundary(red, list(edges))
        assert flux == target_flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, bit in enumerate(flux) if bit == 0]
        operators = [conjugated_star(sites[site], physical) for site in eligible]
        assert all((((left[1] & right[2]).bit_count() +
                     (left[2] & right[1]).bit_count()) & 1) == 0
                   for index, left in enumerate(operators)
                   for right in operators[:index])
        w = Fraction(9 ** (36 - len(edges)), 10 ** 36)
        sector_prior += w
        if edges != base:
            if -1 in means.values():
                excluded_prior += w
                counts["deterministic_conflict"] += 1
            elif 0 in means.values():
                fair_prior += w
                counts["fair_one_site"] += 1
            else:
                deterministic_prior += w
                counts["all_deterministic_positive"] += 1
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert len(seen) == 8192 and base in seen
    assert sector_prior == Fraction(first_row["sector_prior_mass"])
    base_prior = Fraction(first_row["base_prior_mass"])
    assert excluded_prior + fair_prior + deterministic_prior == sector_prior - base_prior
    U = fair_prior / 2 + deterministic_prior
    A = Fraction(first_row["base_first_joint_mass"])
    bound = U / (A + U)
    crude = Fraction(first_row["worst_case_omitted_posterior_upper_bound"])
    assert 0 <= bound <= crude <= 1
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "fixed_action_binding_and_high_prior_two_edge_tail_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "physical_prior": prior["physical_prior"],
            "fixed_action_gate": {"membership_classes": membership,
                                  "minimum_action_preserving_one_edge_classes": 3,
                                  "edge_zero_can_map_to_another_edge_while_singleton_action_fixed": False,
                                  "action_conditioned_second_flux_rows": action_rows,
                                  "operator_law_symmetry_proved": False},
            "two_edge_tail": {"selection_rule": "maximum exact J8P two-edge sector prior; lexicographically smallest representative on ties",
                              "base_error_edges_private": list(base),
                              "first_public": first_row["first_public"],
                              "sector_prior_mass": str(sector_prior),
                              "base_prior_mass": str(base_prior),
                              "base_first_likelihood": first_row["base_first_likelihood"],
                              "base_first_joint_mass": str(A),
                              "omitted_error_counts": dict(counts),
                              "excluded_omitted_prior": str(excluded_prior),
                              "fair_omitted_prior": str(fair_prior),
                              "deterministic_compatible_omitted_prior": str(deterministic_prior),
                              "one_site_omitted_joint_mass_upper_bound": str(U),
                              "one_site_omitted_posterior_upper_bound": str(bound),
                              "one_site_omitted_posterior_upper_bound_decimal": round(float(bound), 12),
                              "previous_crude_omitted_posterior_upper_bound": str(crude)},
            "counters": {"one_edge_action_signatures_checked": 36,
                         "two_edge_sector_errors_structurally_checked": 8192,
                         "new_born_terms": 0, "new_first_masses": 0,
                         "new_second_laws": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Fixed-action edge-membership obstruction and one representative high-prior two-edge all-zero first-record omitted posterior upper bound at ideal L=2 p_X=1/10. No complete omitted law, operator automorphism, other first record, second charge law, full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    output = LAB / "results/j8r-action-binding-and-two-edge-tail-2026-09-28.json"
    assert not output.exists(), "Refuse to overwrite existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "selected_error": result["two_edge_tail"]["base_error_edges_private"],
                      "omitted_bound": result["two_edge_tail"]["one_site_omitted_posterior_upper_bound_decimal"],
                      "cpu_seconds": result["cpu_seconds"]}))
