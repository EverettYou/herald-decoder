"""Bounded all-candidate exact one-site operator-relation discriminator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7x-all-error-operator-discriminator-2026-09-27.json"
RESULT = LAB / "results/j7x-all-error-operator-discriminator-2026-09-27.json"
INPUTS = {
    "j7s_result": LAB / "results/j7s-same-first-error-pair-preflight-2026-09-27.json",
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


def commutes(left: tuple[int, int, int], right: tuple[int, int, int]) -> bool:
    return compose([left, right]) == compose([right, left])


def classify(second, first_ops, flips, usage, budget):
    # A measured +1 first projector kills any anticommuting second mean.
    if any(not commutes(second, first) for first in first_ops):
        return "fair"
    # If second times a product of first operators stabilizes the initial
    # orbit, its sign fixes the second bit after the selected all-+ record.
    for subset in range(1 << len(first_ops)):
        usage["algebraic_relation_probes"] += 1
        assert usage["algebraic_relation_probes"] <= budget["max_algebraic_relation_probes"]
        product = [first_ops[i] for i in range(len(first_ops)) if (subset >> i) & 1]
        value = moment([second, *product], flips)
        if value == 1:
            return "plus"
        if value == -1:
            return "minus"
    return "unresolved"


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget, spec = contract["budget"], contract["matrix"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j7s_result", "j7t_result", "j7m_result", "j7w_result", "j6l_result", "j6m_result")}
    assert old["j7s_result"]["positive_candidate_count"] == 12
    assert len(old["j7t_result"]["candidate_rows"]) == 12
    assert old["j7w_result"]["status"] == "restricted_pair_conditional_information_audit_closed"
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    assert old["j7m_result"]["first_public"]["vacuum"] == [1] * 24
    assert spec["public_actions"] == [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    errors = [spec["base_private_error_red_edges"]] + [
        row["candidate_initial_error_red_edges_private"] for row in old["j7t_result"]["candidate_rows"]]
    assert len(errors) == len({tuple(row) for row in errors}) == 13
    usage = {"algebraic_relation_probes": 0, "ordered_projector_terms": 0}
    rows = []
    for edges in errors:
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in means.values())
        first_variable = sorted(site for site, value in means.items() if value == 0)
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commutes(a, b) for a in first_ops for b in first_ops)
        cells = []
        for action, frozen in zip(spec["public_actions"], old["j7m_result"]["cells"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert check_mask == residual and second_flux == frozen["second_public_flux"]
            second_eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert second_eligible == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(second_eligible) == 22
            second_ops = [conjugated_star(sites[site], residual) for site in second_eligible]
            assert all(commutes(a, b) for a in second_ops for b in second_ops)
            labels = {str(site): classify(op, first_ops, flips, usage, budget)
                      for site, op in zip(second_eligible, second_ops)}
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "one_site_law_labels": labels,
                          "unresolved_site_count": list(labels.values()).count("unresolved")})
        rows.append({"initial_error_red_edges_private": edges,
                     "first_variable_sites_private": first_variable, "cells": cells})
        assert time.process_time() - started < budget["max_cpu_seconds"]
    base = rows[0]
    for row in rows[1:]:
        for cell, control in zip(row["cells"], base["cells"]):
            differences = [int(site) for site, label in cell["one_site_law_labels"].items()
                           if label != "unresolved" and control["one_site_law_labels"][site] != "unresolved"
                           and label != control["one_site_law_labels"][site]]
            cell["proven_different_one_site_sites_vs_base"] = differences
            cell["complete_law_difference_proven_by_marginal"] = bool(differences)
    assert len(rows) == 13 and sum(len(row["cells"]) for row in rows) == 26
    for cell, frozen in zip(base["cells"], old["j7m_result"]["cells"]):
        expected = set(cell["one_site_law_labels"])
        assert expected == {str(site) for site, bit in enumerate(cell["second_public_flux"]) if bit == 0}
        fair_sites = set(frozen["variable_second_sites_private"])
        assert all(label == "unresolved" or label == ("fair" if int(site) in fair_sites else "plus")
                   for site, label in cell["one_site_law_labels"].items())
    peer_errors = {tuple(error) for error in old["j7t_result"]["selected_peer_initial_errors_private"]}
    assert len(peer_errors) == 2
    for row in rows[1:]:
        if tuple(row["initial_error_red_edges_private"]) in peer_errors:
            for cell, frozen in zip(row["cells"], old["j7m_result"]["cells"]):
                fair_sites = set(frozen["variable_second_sites_private"])
                assert all(label == "unresolved" or label == ("fair" if int(site) in fair_sites else "plus")
                           for site, label in cell["one_site_law_labels"].items())
                assert not cell["complete_law_difference_proven_by_marginal"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "all_candidate_structural_discriminator_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "rows": rows, "candidate_count": 12, "pair_action_cells": 24,
            "proven_different_candidate_action_cells": sum(
                cell["complete_law_difference_proven_by_marginal"]
                for row in rows[1:] for cell in row["cells"]),
            "counters": {**usage, "new_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Exact one-site law classification only at one selected first record and fixed ideal L=2 orbit. A changed marginal proves a changed complete law; matching or unresolved marginals do not prove law equality, information, logical risk or JIT benefit.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
