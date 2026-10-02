"""Exact selected-flux prior coverage and first-record structural cost audit."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import time

from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
CONTRACT = LAB / "manifests/j8j-full-prior-coverage-feasibility-2026-09-27.json"
RESULT = LAB / "results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json"
INPUTS = {
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7s_contract": LAB / "manifests/j7s-same-first-error-pair-preflight-2026-09-27.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j8i_result": LAB / "results/j8i-all-support-complete-second-laws-verified-2026-09-27.json",
    "r6af_contract": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json",
    "boundary_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget = contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j6l_result", "j6m_result", "j7s_contract", "j7t_result", "j8i_result", "r6af_contract")}
    assert old["j7s_contract"]["matrix"]["iid_red_x_rate"] == "1/10"
    assert "IID red-X edge errors" in old["r6af_contract"]["frozen_model"]["physical_channel"]
    assert old["j8i_result"]["status"] == "all_support_complete_second_laws_closed"
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    selected_flux = old["j8i_result"]["first_public"]["flux"]
    assert len(selected_flux) == 24
    base = old["j8i_result"]["rows"][0]["error_edges_private"]
    _, base_flux = red_boundary(red, base)
    assert base_flux == selected_flux
    columns = []
    for edge in range(36):
        _, flux = red_boundary(red, [edge])
        columns.append(sum(bit << i for i, bit in enumerate(flux)))
    basis: dict[int, tuple[int, int]] = {}
    null_vectors = []
    for edge, column in enumerate(columns):
        residual, combination = column, 1 << edge
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (residual, combination)
                break
            old_residual, old_combination = basis[pivot]
            residual ^= old_residual
            combination ^= old_combination
        if residual == 0:
            null_vectors.append(combination)
    assert len(basis) == 23 and len(null_vectors) == 13
    known = {tuple(sorted(row["error_edges_private"])) for row in old["j8i_result"]["rows"]}
    known.update(tuple(sorted(row["candidate_initial_error_red_edges_private"]))
                 for row in old["j7t_result"]["candidate_rows"])
    assert len(known) == 67 and len(old["j8i_result"]["rows"]) == 55
    base_mask = sum(1 << edge for edge in base)
    weight_by_error: dict[tuple[int, ...], Fraction] = {}
    first_variable_hist = Counter()
    first_branch_total = 0
    projected_first_terms = 0
    conflicts = 0
    for free_bits in range(1 << len(null_vectors)):
        mask = base_mask
        for i, vector in enumerate(null_vectors):
            if free_bits >> i & 1:
                mask ^= vector
        edges = tuple(i for i in range(36) if mask >> i & 1)
        assert edges not in weight_by_error
        physical, flux = red_boundary(red, list(edges))
        assert flux == selected_flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [i for i, bit in enumerate(flux) if not bit]
        variable_count = sum(mean == 0 for mean in means.values())
        assert all(mean in (-1, 0, 1) for mean in means.values())
        conflicts += any(mean == -1 for mean in means.values())
        first_variable_hist[variable_count] += 1
        first_branch_total += 1 << variable_count
        projected_first_terms += 1 << variable_count
        weight_by_error[edges] = Fraction(9 ** (36 - len(edges)), 10 ** 36)
        assert time.process_time() - started < budget["max_cpu_seconds"]
    assert len(weight_by_error) == budget["max_errors"] == 8192
    assert known <= weight_by_error.keys()
    full_iid_weight = sum((Fraction(comb(36, weight) * 9 ** (36 - weight), 10 ** 36)
                           for weight in range(37)), Fraction())
    assert full_iid_weight == 1
    sector_weight = sum(weight_by_error.values(), Fraction())
    known_weight = sum((weight_by_error[edges] for edges in known), Fraction())
    assert 0 < known_weight < sector_weight < 1
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {
        "schema_version": 1, "id": contract["id"],
        "status": "selected_flux_prior_coverage_audit_closed",
        "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
        "pinned_input_checks_before": before, "pinned_input_checks_after": after,
        "physical_prior": {"p_X": "1/10", "p_Z": "0", "red_edges": 36},
        "boundary_rank": len(basis), "kernel_dimension": len(null_vectors),
        "same_first_flux_error_count": len(weight_by_error),
        "known_complete_law_error_count": len(known),
        "uncovered_same_flux_error_count": len(weight_by_error) - len(known),
        "selected_flux_prior_mass": str(sector_weight),
        "known_support_prior_mass": str(known_weight),
        "known_fraction_of_selected_flux_prior_mass": str(known_weight / sector_weight),
        "first_variable_site_histogram": {str(k): v for k, v in sorted(first_variable_hist.items())},
        "structurally_possible_error_first_record_cells": first_branch_total,
        "projected_first_projector_terms": projected_first_terms,
        "first_work_fits_inherited_cap": projected_first_terms <= budget["max_projected_first_terms"],
        "errors_with_deterministic_minus_sites": conflicts,
        "counters": {"first_record_probabilities": 0, "complete_second_laws": 0,
                     "full_prior_mixtures": 0, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
        "claim_boundary": "Exact support/prior-weight and structural first-record cost only in one selected first-flux sector. Variable-site branches are an upper structural count, not positive-mass public laws. No full-IID information, logical risk, noisy JIT, L=3 or threshold.",
        "cpu_seconds": round(time.process_time() - started, 6),
    }


if __name__ == "__main__":
    result = run()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
          ("status", "same_first_flux_error_count", "known_complete_law_error_count",
           "uncovered_same_flux_error_count", "known_fraction_of_selected_flux_prior_mass",
           "projected_first_projector_terms", "first_work_fits_inherited_cap", "cpu_seconds")}, indent=2))
