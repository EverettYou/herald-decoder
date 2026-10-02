"""Registered exact J6R chain controls; no stochastic history generation."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star, eligible, moment
from run_j6o_full_binary_sequential_public_record import assert_eligible_commute, public_record, red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments, first_probability, projection_probability
from run_j6r_three_edge_topology_causal_law import conditional_comparison


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6s-repeat-transfer-four-site-2026-09-25.json"
RESULT = LAB / "results/j6s-repeat-transfer-four-site-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6q_result": LAB / "results/j6q-alternate-path-operator-law-matrix-2026-09-25.json",
    "j6r_result": LAB / "results/j6r-three-edge-topology-causal-law-2026-09-25.json",
    "j6r_runner": LAB / "scripts/run_j6r_three_edge_topology_causal_law.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
            for key, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    prior = json.loads(INPUTS["j6r_result"].read_text())
    assert prior["status"] == "partially_censored_two_topology_exact_matrix"
    chain = {case["action"]: case for case in prior["cases"]
             if case["topology"] == "connected_chain"}
    assert chain["matched"]["status"] == "censored_support_exceeds_bound"
    assert chain["matched"]["second_random_counts_private"] == [4] * 4
    assert chain["partial_one"]["first_dependence_full_public_law"] == "dependent_on_first_record"
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(key.split(":")[1]): star for key, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    red = {qubit["lab004_red_edge_id"]: qubit for qubit in embedding["physical_qubits"]
           if qubit["color"] == "red"}
    assert len(stars) == 36 and set(sites) == set(range(24)) and len(red) == 36
    endpoints = {edge: set(qubit["star_endpoints"]) for edge, qubit in red.items()}
    assert endpoints[0] & endpoints[4] == {"green:1"}
    assert endpoints[4] & endpoints[3] == {"blue:2"}
    assert not endpoints[0] & endpoints[3]
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    physical, first_flux = red_boundary(red, [0, 4, 3])
    first_sites = [site for site in range(24) if eligible(sites[site], physical)]
    assert first_sites == [site for site in range(24) if first_flux[site] == 0]
    first_pair_checks = assert_eligible_commute(
        [sites[site]["center"] for site in first_sites], physical, state["pair_rows"])
    first_ops_by_site = {site: conjugated_star(sites[site], physical) for site in first_sites}
    first_means = {site: moment([op], flips) for site, op in first_ops_by_site.items()}
    first_random = sorted(site for site, value in first_means.items() if value == 0)
    assert first_random == chain["matched"]["first_random_sites_private"]
    assert len(first_random) == contract["matrix"]["maximum_nondeterministic_first_sites"]
    first_fixed = {site: value for site, value in first_means.items() if value != 0}
    first_ops = [first_ops_by_site[site] for site in first_random]
    first_rows = []
    for outcomes in assignments(len(first_random)):
        probability = first_probability(first_ops, outcomes, flips)
        assert probability >= 0
        if not probability:
            continue
        charge = [0] * 24
        for site, value in first_fixed.items():
            charge[site] = int(value == -1)
        for site, value in zip(first_random, outcomes):
            charge[site] = int(value == -1)
        first_rows.append({"outcomes": outcomes, "probability": probability,
                           "public": public_record(first_flux, charge)})
    assert len(first_rows) == 4
    assert sum((row["probability"] for row in first_rows), Fraction()) == 1
    cases = []
    for action, action_edges in contract["physical_and_observation_contract"]["public_actions"].items():
        action_mask, _ = red_boundary(red, action_edges)
        residual = physical ^ action_mask
        _, second_flux = red_boundary(red, [edge for edge in [0, 4, 3]
                                            if edge not in action_edges])
        second_sites = [site for site in range(24) if eligible(sites[site], residual)]
        assert second_sites == [site for site in range(24) if second_flux[site] == 0]
        second_pair_checks = assert_eligible_commute(
            [sites[site]["center"] for site in second_sites], residual, state["pair_rows"])
        second_ops_by_site = {site: conjugated_star(sites[site], residual)
                              for site in second_sites}
        repeated_sites = sorted(site for site in first_sites if site in second_sites
                                and first_ops_by_site[site] == second_ops_by_site[site])
        changed_sites = sorted(site for site in first_sites if site in second_sites
                               and first_ops_by_site[site] != second_ops_by_site[site])
        new_sites = sorted(set(second_sites) - set(first_sites))
        rows = []
        random_sites_by_first = []
        new_site_plus_by_first = []
        for first_row in first_rows:
            random_sites = []
            fixed = {}
            plus_by_site = {}
            for site in second_sites:
                joint_plus = projection_probability(
                    first_ops, first_row["outcomes"], [second_ops_by_site[site]], (1,), flips)
                plus = joint_plus / first_row["probability"]
                assert plus in (0, Fraction(1, 2), 1)
                plus_by_site[site] = plus
                if plus == Fraction(1, 2):
                    random_sites.append(site)
                else:
                    fixed[site] = 1 if plus == 1 else -1
            random_sites_by_first.append(random_sites)
            new_site_plus_by_first.append({str(site): str(plus_by_site[site])
                                           for site in new_sites})
            assert len(random_sites) <= contract["matrix"]["maximum_nondeterministic_second_sites"]
            ops = [second_ops_by_site[site] for site in random_sites]
            total = Fraction()
            for outcomes in assignments(len(random_sites)):
                joint = projection_probability(
                    first_ops, first_row["outcomes"], ops, outcomes, flips)
                assert joint >= 0
                conditional = joint / first_row["probability"]
                total += conditional
                if not conditional:
                    continue
                charge = [0] * 24
                for site, value in fixed.items():
                    charge[site] = int(value == -1)
                for site, value in zip(random_sites, outcomes):
                    charge[site] = int(value == -1)
                second_public = public_record(second_flux, charge)
                assert set(first_row["public"]) == set(second_public) == {"flux", "charge", "vacuum"}
                assert all(len(first_row["public"][name]) == len(second_public[name]) == 24
                           for name in ("flux", "charge", "vacuum"))
                rows.append({"first_public": first_row["public"],
                             "first_probability": str(first_row["probability"]),
                             "second_public": second_public,
                             "second_conditional_probability": str(conditional)})
            assert total == 1
            assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
        if action == "matched":
            assert random_sites_by_first == [[0, 1, 2, 3]] * 4
        cases.append({"action": action, "public_action_red_edge_ids": action_edges,
                      "first_random_sites_private": first_random,
                      "second_random_sites_by_first_private": random_sites_by_first,
                      "unchanged_operator_repeat_sites_private": repeated_sites,
                      "changed_operator_sites_private": changed_sites,
                      "newly_eligible_sites_private": new_sites,
                      "new_site_conditional_plus_probabilities_private": new_site_plus_by_first,
                      "first_dependence_full_public_law": conditional_comparison(rows),
                      "first_eligible_pair_checks": first_pair_checks,
                      "second_eligible_pair_checks": second_pair_checks,
                      "status": "exact_full_public_law", "public_law_rows": rows})
    assert len(cases) == 3
    assert cases[0]["first_dependence_full_public_law"] == \
           chain["partial_one"]["first_dependence_full_public_law"]
    assert cases[1]["first_dependence_full_public_law"] == \
           chain["partial_two"]["first_dependence_full_public_law"]
    assert all(pins.values())
    return {"schema_version": 1, "id": contract["id"],
            "status": "passed_exact_repeat_control_and_four_site_completion",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "cases": cases,
            "checks": {"chain_incidence_verified": True,
                       "eligible_actual_sector_commutation": True,
                       "exact_first_and_conditional_normalization": True,
                       "full_public_records_only": True,
                       "j6r_uncensored_branch_reproduced": True,
                       "old_five_round_caller_byte_identical": True},
            "inference_boundary": "One ideal fixed L=2 chain only. Unchanged operator repetition is not new-site information transfer; no general D4 kernel, noisy repeated history, schedule risk, decoder or threshold.",
            "stochastic_histories": 0, "schedule_arm_evaluations": 0,
            "bootstrap_replicates": 0,
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
