"""Exact selected-first second singleton/pair parity moments for all 12 errors."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7y-low-order-second-moments-2026-09-27.json"
RESULT = LAB / "results/j7y-low-order-second-moments-2026-09-27.json"
INPUTS = {
    "j7x_result": LAB / "results/j7x-all-error-operator-discriminator-2026-09-27.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j7w_result": LAB / "results/j7w-pair-information-audit-2026-09-27.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "relation_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commute(left, right):
    return compose([left, right]) == compose([right, left])


def subset_terms(first_ops, flips, usage, budget):
    terms = []
    for subset in range(1 << len(first_ops)):
        selected = [op for i, op in enumerate(first_ops) if (subset >> i) & 1]
        terms.append(selected)
    total = 0
    for selected in terms:
        usage["orbit_moment_terms"] += 1
        assert usage["orbit_moment_terms"] <= budget["max_orbit_moment_terms"]
        total += moment(selected, flips)
    return terms, total


def conditional_parity(second_ops, first_ops, first_subsets, first_sum,
                       flips, usage, budget):
    product = compose(second_ops)
    if any(not commute(product, first) for first in first_ops):
        return Fraction(0), "first_projector_anticommutation"
    numerator = 0
    for selected in first_subsets:
        usage["orbit_moment_terms"] += 1
        assert usage["orbit_moment_terms"] <= budget["max_orbit_moment_terms"]
        numerator += moment([*selected, product], flips)
    value = Fraction(numerator, first_sum)
    assert -1 <= value <= 1
    return value, "commuting_projector_expansion"


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget, spec = contract["budget"], contract["matrix"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j7x_result", "j7t_result", "j7m_result", "j7w_result", "j6l_result", "j6m_result")}
    assert old["j7x_result"]["status"] == "all_candidate_structural_discriminator_closed"
    assert old["j7x_result"]["candidate_count"] == 12
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    assert old["j7m_result"]["first_public"]["vacuum"] == [1] * 24
    assert spec["actions"] == [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
    assert spec["variable_second_sites_by_action"] == [[0], [0, 17, 20, 21, 22]]
    errors = [spec["base_error_private"]] + [
        row["candidate_initial_error_red_edges_private"] for row in old["j7t_result"]["candidate_rows"]]
    assert errors == [row["initial_error_red_edges_private"] for row in old["j7x_result"]["rows"]]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    usage = {"orbit_moment_terms": 0, "ordered_projector_terms": 0}
    rows = []
    for error_index, edges in enumerate(errors):
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [i for i, bit in enumerate(first_flux) if bit == 0]
        assert all(mean != -1 for mean in means.values())
        first_variable = sorted(i for i, mean in means.items() if mean == 0)
        assert first_variable == old["j7x_result"]["rows"][error_index]["first_variable_sites_private"]
        first_ops = [conjugated_star(sites[i], physical) for i in first_variable]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_subsets, first_sum = subset_terms(first_ops, flips, usage, budget)
        first_mass = Fraction(first_sum, 1 << len(first_ops))
        expected_mass = (Fraction(old["j7m_result"]["first_public_mass"]) if error_index == 0
                         else Fraction(old["j7t_result"]["candidate_rows"][error_index-1]["selected_first_public_mass_given_candidate"]))
        assert first_mass == expected_mass > 0
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask == residual
            assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
            selected_sites = spec["variable_second_sites_by_action"][action_index]
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [i for i, bit in enumerate(second_flux) if bit == 0]
            assert set(selected_sites) <= set(eligible_second)
            x_labels = old["j7x_result"]["rows"][error_index]["cells"][action_index]["one_site_law_labels"]
            assert {int(i) for i, label in x_labels.items() if label != "plus"} == set(selected_sites)
            second_ops = {i: conjugated_star(sites[i], residual) for i in selected_sites}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
            observations = []
            for group in [*[(i,) for i in selected_sites],
                          *itertools.combinations(selected_sites, 2)]:
                value, derivation = conditional_parity(
                    [second_ops[i] for i in group], first_ops, first_subsets,
                    first_sum, flips, usage, budget)
                if len(group) == 1:
                    label = x_labels[str(group[0])]
                    if label != "unresolved":
                        assert value == {"plus": 1, "minus": -1, "fair": 0}[label]
                observations.append({"sites": list(group), "parity_mean": str(value),
                                     "derivation": derivation})
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "moments": observations})
        rows.append({"initial_error_red_edges_private": edges,
                     "first_public_mass": str(first_mass), "cells": cells})
        assert time.process_time() - started < budget["max_cpu_seconds"]
    base = rows[0]
    peer_errors = {tuple(error) for error in old["j7t_result"]["selected_peer_initial_errors_private"]}
    assert len(peer_errors) == 2
    for row in rows:
        for action_index, cell in enumerate(row["cells"]):
            expected_count = 1 if action_index == 0 else 15
            assert len(cell["moments"]) == expected_count
            if row is base or tuple(row["initial_error_red_edges_private"]) in peer_errors:
                assert all(Fraction(item["parity_mean"]) == 0 for item in cell["moments"])
            if row is not base:
                reference = {tuple(item["sites"]): item["parity_mean"]
                             for item in base["cells"][action_index]["moments"]}
                cell["different_moment_sites_vs_base"] = [item["sites"] for item in cell["moments"]
                    if item["parity_mean"] != reference[tuple(item["sites"])]]
                cell["complete_law_difference_proven_by_low_order_moment"] = bool(cell["different_moment_sites_vs_base"])
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "all_candidate_low_order_moments_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "candidate_count": 12, "candidate_action_cells": 24,
            "different_candidate_action_cells": sum(cell["complete_law_difference_proven_by_low_order_moment"]
                                                    for row in rows[1:] for cell in row["cells"]),
            "rows": rows,
            "counters": {**usage, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Exact selected-first second single/pair parity moments only on one ideal L=2 orbit. A changed moment proves a changed complete public law; matching moments do not prove complete-law equality, private-error information, logical risk or JIT benefit.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
