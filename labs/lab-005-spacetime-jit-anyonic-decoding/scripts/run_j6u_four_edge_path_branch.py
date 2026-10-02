"""Exact four-edge path/branch first-action-second public projector matrix."""

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
CONTRACT = LAB / "manifests/j6u-four-edge-path-branch-2026-09-25.json"
RESULT = LAB / "results/j6u-four-edge-path-branch-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6q_result": LAB / "results/j6q-alternate-path-operator-law-matrix-2026-09-25.json",
    "j6r_result": LAB / "results/j6r-three-edge-topology-causal-law-2026-09-25.json",
    "j6s_result": LAB / "results/j6s-repeat-transfer-four-site-2026-09-25.json",
    "j6t_result": LAB / "results/j6t-alternate-action-new-site-law-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projected_comparison(rows: list[dict], selected: list[int]) -> dict:
    """Compare complete exact joint charge laws on a fixed private site set."""
    by_first = {}
    for row in rows:
        first = tuple(row["first_public"]["charge"])
        second = tuple(row["second_public"]["charge"][site] for site in selected)
        distribution = by_first.setdefault(first, {})
        distribution[second] = distribution.get(second, Fraction()) + Fraction(
            row["second_conditional_probability"])
    assert all(sum(distribution.values(), Fraction()) == 1
               for distribution in by_first.values())
    values = list(by_first.values())
    status = ("no_sites_vacuous" if not selected else
              "single_positive_first_record" if len(values) < 2 else
              "dependent_on_first_record" if any(value != values[0]
                for value in values[1:]) else "identical_across_first_records")
    return {"sites_private": selected, "first_dependence": status,
            "distributions_by_first": [
                {"first_charge_private": list(first),
                 "second_support": [{"bits": list(bits), "probability": str(mass)}
                                    for bits, mass in sorted(distribution.items())]}
                for first, distribution in sorted(by_first.items())]}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    prior = json.loads(INPUTS["j6t_result"].read_text())
    assert prior["status"] == "passed_four_alternate_action_exact_matrix"
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    red = {qubit["lab004_red_edge_id"]: qubit for qubit in embedding["physical_qubits"]
           if qubit["color"] == "red"}
    assert len(stars) == 36 and set(sites) == set(range(24)) and len(red) == 36
    endpoints = {edge: set(qubit["star_endpoints"]) for edge, qubit in red.items()}
    expected_degrees = {
        "four_edge_nonbranching_path": {"blue:0": 1, "green:1": 2,
                                         "blue:2": 2, "green:3": 2, "blue:4": 1},
        "four_edge_branched_tree": {"blue:0": 1, "green:1": 2,
                                     "blue:2": 3, "green:3": 1, "green:11": 1},
    }
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    cases = []
    for topology, physical_edges in contract["physical_and_observation_contract"]["private_physical_red_x_topologies"].items():
        degrees = {}
        for edge in physical_edges:
            for endpoint in endpoints[edge]:
                degrees[endpoint] = degrees.get(endpoint, 0) + 1
        assert degrees == expected_degrees[topology]
        physical, first_flux = red_boundary(red, physical_edges)
        first_sites = [site for site in range(24) if eligible(sites[site], physical)]
        assert first_sites == [site for site in range(24) if first_flux[site] == 0]
        first_pair_checks = assert_eligible_commute(
            [sites[site]["center"] for site in first_sites], physical, state["pair_rows"])
        first_ops_by_site = {site: conjugated_star(sites[site], physical)
                             for site in first_sites}
        first_means = {site: moment([op], flips) for site, op in first_ops_by_site.items()}
        first_random = sorted(site for site, value in first_means.items() if value == 0)
        first_fixed = {site: value for site, value in first_means.items() if value != 0}
        first_censored = len(first_random) > contract["matrix"]["maximum_nondeterministic_first_sites"]
        first_ops = [first_ops_by_site[site] for site in first_random]
        first_rows = []
        if not first_censored:
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
            assert sum((row["probability"] for row in first_rows), Fraction()) == 1
        actions = {
            "correct_edge_0": [0], "correct_edge_3": [3],
            "correct_edges_0_3": [0, 3], "matched_all_four": physical_edges,
        }
        for action_name, action_edges in actions.items():
            action_mask, _ = red_boundary(red, action_edges)
            residual = physical ^ action_mask
            _, second_flux = red_boundary(red, [edge for edge in physical_edges
                                                if edge not in action_edges])
            second_sites = [site for site in range(24) if eligible(sites[site], residual)]
            assert second_sites == [site for site in range(24) if second_flux[site] == 0]
            second_pair_checks = assert_eligible_commute(
                [sites[site]["center"] for site in second_sites], residual,
                state["pair_rows"])
            second_ops = {site: conjugated_star(sites[site], residual)
                          for site in second_sites}
            repeated = sorted(site for site in set(first_sites) & set(second_sites)
                              if first_ops_by_site[site] == second_ops[site])
            changed = sorted(site for site in set(first_sites) & set(second_sites)
                             if first_ops_by_site[site] != second_ops[site])
            new = sorted(set(second_sites) - set(first_sites))
            assert set(repeated) | set(changed) | set(new) == set(second_sites)
            rows = []
            random_sites_by_first = []
            censored = first_censored
            if not first_censored:
                for first_row in first_rows:
                    random_sites = []
                    fixed = {}
                    for site in second_sites:
                        joint_plus = projection_probability(
                            first_ops, first_row["outcomes"], [second_ops[site]], (1,), flips)
                        plus = joint_plus / first_row["probability"]
                        assert plus in (0, Fraction(1, 2), 1)
                        if plus == Fraction(1, 2):
                            random_sites.append(site)
                        else:
                            fixed[site] = 1 if plus == 1 else -1
                    random_sites_by_first.append(random_sites)
                    if len(random_sites) > contract["matrix"]["maximum_nondeterministic_second_sites"]:
                        censored = True
                        continue
                    operators = [second_ops[site] for site in random_sites]
                    total = Fraction()
                    for outcomes in assignments(len(random_sites)):
                        joint = projection_probability(
                            first_ops, first_row["outcomes"], operators, outcomes, flips)
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
            if censored:
                rows = []
            cases.append({
                "topology": topology, "physical_edges_private": physical_edges,
                "action": action_name, "public_action_red_edge_ids": action_edges,
                "first_random_sites_private": first_random,
                "positive_first_record_count": len(first_rows),
                "second_random_sites_by_first_private": random_sites_by_first,
                "repeat_sites_private": repeated, "changed_sites_private": changed,
                "new_sites_private": new,
                "first_eligible_pair_checks": first_pair_checks,
                "second_eligible_pair_checks": second_pair_checks,
                "full_public_first_dependence": ("censored" if censored
                                                else conditional_comparison(rows)),
                "new_only_projected_law_private": (None if censored
                    else projected_comparison(rows, new)),
                "new_plus_changed_projected_law_private": (None if censored
                    else projected_comparison(rows, sorted(new + changed))),
                "status": ("censored_support_exceeds_bound" if censored
                           else "exact_full_public_law"),
                "public_law_rows": rows,
            })
            assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    assert len(cases) == 8 and all(pins.values())
    return {"schema_version": 1, "id": contract["id"],
            "status": ("passed_two_topology_exact_matrix" if all(
                case["status"] == "exact_full_public_law" for case in cases)
                else "partially_censored_two_topology_exact_matrix"),
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "cases": cases,
            "checks": {"path_and_branch_incidence_verified": True,
                       "eligible_actual_sector_commutation": True,
                       "exact_first_and_conditional_normalization_or_censoring": True,
                       "full_public_records_only": True,
                       "frozen_five_round_caller_byte_identical": True},
            "inference_boundary": "Two ideal four-edge topologies and four fixed actions on one L=2 orbit only; no general D4 kernel, noisy repeated history, schedule risk, decoder or threshold.",
            "stochastic_histories": 0, "schedule_arm_evaluations": 0,
            "bootstrap_replicates": 0,
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
