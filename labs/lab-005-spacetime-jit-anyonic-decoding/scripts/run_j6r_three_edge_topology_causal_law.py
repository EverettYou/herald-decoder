"""Exact first/action/second projector laws for one chain and one star triplet."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star, eligible, moment
from run_j6o_full_binary_sequential_public_record import (
    assert_eligible_commute, public_record, red_boundary,
)
from run_j6q_alternate_path_operator_law_matrix import (
    assignments, first_probability, projection_probability,
)


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6r-three-edge-topology-causal-law-2026-09-25.json"
RESULT = LAB / "results/j6r-three-edge-topology-causal-law-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6q_result": LAB / "results/j6q-alternate-path-operator-law-matrix-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_key(record: dict) -> tuple:
    return tuple(tuple(record[name]) for name in ("flux", "charge", "vacuum"))


def conditional_comparison(rows: list[dict]) -> str:
    """Compare full conditional public distributions, not isolated marginals."""
    by_first: dict[tuple, dict[tuple, Fraction]] = {}
    for row in rows:
        first = record_key(row["first_public"])
        second = record_key(row["second_public"])
        dist = by_first.setdefault(first, {})
        assert second not in dist
        dist[second] = Fraction(row["second_conditional_probability"])
    if len(by_first) < 2:
        return "single_positive_first_record"
    distributions = list(by_first.values())
    return ("dependent_on_first_record" if any(value != distributions[0]
            for value in distributions[1:]) else "identical_across_first_records")


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    previous = json.loads(INPUTS["j6q_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert previous["status"] == "passed_two_geometry_exact_matrix"
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(key.split(":")[1]): star for key, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(stars) == 36 and set(sites) == set(range(24))
    red = {qubit["lab004_red_edge_id"]: qubit
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    assert len(red) == 36
    endpoints = {edge: set(qubit["star_endpoints"]) for edge, qubit in red.items()}
    assert endpoints[0] & endpoints[4] == {"green:1"}
    assert endpoints[4] & endpoints[3] == {"blue:2"}
    assert not endpoints[0] & endpoints[3]
    assert endpoints[0] & endpoints[1] & endpoints[2] == {"blue:0"}
    assert len(set.union(endpoints[0], endpoints[1], endpoints[2])) == 4
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    bound_first = contract["matrix"]["maximum_nondeterministic_first_sites"]
    bound_second = contract["matrix"]["maximum_nondeterministic_second_sites"]
    cases = []
    for topology, triplet in contract["physical_and_observation_contract"]["private_physical_red_x_triplets"].items():
        physical, first_flux = red_boundary(red, triplet)
        first_sites = [site for site in range(24) if eligible(sites[site], physical)]
        assert first_sites == [site for site in range(24) if first_flux[site] == 0]
        first_pair_checks = assert_eligible_commute(
            [sites[site]["center"] for site in first_sites], physical, state["pair_rows"])
        first_means = {site: moment([conjugated_star(sites[site], physical)], flips)
                       for site in first_sites}
        assert set(first_means.values()) <= {-1, 0, 1}
        first_random = sorted(site for site, value in first_means.items() if value == 0)
        first_fixed = {site: value for site, value in first_means.items() if value != 0}
        first_ops = [conjugated_star(sites[site], physical) for site in first_random]
        first_censored = len(first_random) > bound_first
        first_rows = []
        if not first_censored:
            for outcomes in assignments(len(first_random)):
                probability = first_probability(first_ops, outcomes, flips)
                assert probability >= 0
                if probability == 0:
                    continue
                charge = [0] * 24
                for site, value in first_fixed.items():
                    charge[site] = int(value == -1)
                for site, value in zip(first_random, outcomes):
                    charge[site] = int(value == -1)
                first_rows.append({"outcomes": outcomes, "probability": probability,
                                   "public": public_record(first_flux, charge)})
            assert sum((row["probability"] for row in first_rows), Fraction()) == 1
        action_prefixes = {
            "defer": [], "partial_one": triplet[:1],
            "partial_two": triplet[:2], "matched": triplet,
        }
        for action, action_edges in action_prefixes.items():
            action_mask, _ = red_boundary(red, action_edges)
            residual = physical ^ action_mask
            _, second_flux = red_boundary(red, [edge for edge in triplet
                                                if edge not in action_edges])
            second_sites = [site for site in range(24) if eligible(sites[site], residual)]
            assert second_sites == [site for site in range(24) if second_flux[site] == 0]
            second_pair_checks = assert_eligible_commute(
                [sites[site]["center"] for site in second_sites], residual,
                state["pair_rows"])
            second_random_counts = []
            rows = []
            censored = first_censored
            if not first_censored:
                for first_row in first_rows:
                    if action == "defer":
                        rows.append({"first_public": first_row["public"],
                                     "first_probability": str(first_row["probability"]),
                                     "second_public": None,
                                     "second_conditional_probability": None})
                        continue
                    random_sites = []
                    fixed = {}
                    for site in second_sites:
                        op = conjugated_star(sites[site], residual)
                        joint_plus = projection_probability(
                            first_ops, first_row["outcomes"], [op], (1,), flips)
                        conditional_plus = joint_plus / first_row["probability"]
                        assert conditional_plus in (0, Fraction(1, 2), 1)
                        if conditional_plus == Fraction(1, 2):
                            random_sites.append(site)
                        else:
                            fixed[site] = 1 if conditional_plus == 1 else -1
                    second_random_counts.append(len(random_sites))
                    if len(random_sites) > bound_second:
                        censored = True
                        continue
                    ops = [conjugated_star(sites[site], residual) for site in random_sites]
                    conditional_total = Fraction()
                    for outcomes in assignments(len(random_sites)):
                        joint = projection_probability(
                            first_ops, first_row["outcomes"], ops, outcomes, flips)
                        assert joint >= 0
                        conditional = joint / first_row["probability"]
                        conditional_total += conditional
                        if conditional == 0:
                            continue
                        charge = [0] * 24
                        for site, value in fixed.items():
                            charge[site] = int(value == -1)
                        for site, value in zip(random_sites, outcomes):
                            charge[site] = int(value == -1)
                        rows.append({"first_public": first_row["public"],
                                     "first_probability": str(first_row["probability"]),
                                     "second_public": public_record(second_flux, charge),
                                     "second_conditional_probability": str(conditional)})
                    assert conditional_total == 1
                    assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
            if censored:
                rows = []
            comparison = ("censored" if censored else "not_applicable_defer"
                          if action == "defer" else conditional_comparison(rows))
            cases.append({
                "topology": topology,
                "physical_triplet_private": triplet,
                "action": action,
                "public_action_red_edge_ids": action_edges,
                "first_flux_sites": [site for site, bit in enumerate(first_flux) if bit],
                "second_flux_sites": [site for site, bit in enumerate(second_flux) if bit],
                "first_eligible_pair_checks": first_pair_checks,
                "second_eligible_pair_checks": second_pair_checks,
                "first_random_sites_private": first_random,
                "positive_first_record_count": len(first_rows),
                "second_random_counts_private": second_random_counts,
                "first_dependence_full_public_law": comparison,
                "status": "censored_support_exceeds_bound" if censored else "exact_full_public_law",
                "public_law_rows": rows,
            })
            assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    assert len(cases) == 8
    assert digest(INPUTS["frozen_integrated_history"]) == \
           contract["pinned_inputs"]["frozen_integrated_history_sha256"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_two_topology_exact_matrix" if all(
            case["status"] == "exact_full_public_law" for case in cases)
            else "partially_censored_two_topology_exact_matrix",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pins,
        "cases": cases,
        "checks": {"chain_and_star_incidence_verified": True,
                   "all_eligible_projectors_commute": True,
                   "causal_first_action_second_born_order": True,
                   "exact_normalization_or_explicit_censoring": True,
                   "full_conditional_public_law_compared": True,
                   "old_five_round_caller_byte_identical": True},
        "inference_boundary": "Two ideal three-edge topologies on one fixed L=2 D4 orbit only. No general physical kernel, noisy repeated history, schedule risk, optimal decoder or threshold.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.process_time() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
