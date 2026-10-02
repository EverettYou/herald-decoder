"""Exact one-geometry full-binary D4 public record from sequential projectors.

This is a fixed-state evidence fixture, not the production E2 sampler.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask, parity
from run_j6n_sequential_local_projector_moments import (
    conjugated_star, eligible, moment, sequential_probability,
)


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6o-full-binary-sequential-public-record-2026-09-25.json"
RESULT = LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6n_result": LAB / "results/j6n-sequential-local-projector-moments-2026-09-25.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def red_boundary(red_qubits: dict[int, dict], edge_ids: list[int]) -> tuple[int, list[int]]:
    support = 0
    flux = [0] * 24
    for edge_id in edge_ids:
        qubit = red_qubits[edge_id]
        support ^= 1 << qubit["id"]
        for endpoint in qubit["star_endpoints"]:
            color, site = endpoint.split(":")
            assert color in ("blue", "green")
            flux[int(site)] ^= 1
    return support, flux


def public_record(flux: list[int], charge: list[int]) -> dict:
    assert len(flux) == len(charge) == 24
    assert set(flux + charge) <= {0, 1}
    assert all(not (f and c) for f, c in zip(flux, charge))
    # Frozen J6H public convention: vacuum is complement of e-charge. A
    # fluxful site may still have vacuum=1 as an independent membership bit.
    record = {"flux": flux.copy(), "charge": charge.copy(),
              "vacuum": [1 - bit for bit in charge]}
    assert set(record) == {"flux", "charge", "vacuum"}
    return record


def assert_eligible_commute(
    sites: list[str], residual: int, pair_rows: list[dict]
) -> int:
    eligible_set = set(sites)
    checked = 0
    for pair in pair_rows:
        if pair["left"] in eligible_set and pair["right"] in eligible_set:
            assert parity(int(pair["commutator_z_mask_hex"], 16) & residual) == 0
            checked += 1
    assert checked == len(sites) * (len(sites) - 1) // 2
    return checked


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pins = {key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
            for key, path in INPUTS.items()}
    assert all(pins.values()), f"pinned input drift: {pins}"
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    local = json.loads(INPUTS["j6n_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert local["status"] == "passed_exact_local_sequential_projector_moments_only"
    assert embedding["counts"]["honeycomb_vertices"] == 24
    all_stars = {star["center"]: star for star in embedding["star_supports"]}
    assert len(all_stars) == 36
    sites = {int(center.split(":")[1]): star
             for center, star in all_stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(sites) == 24 and set(sites) == set(range(24))
    assert all(star["center"].split(":")[0] == star["center_color"]
               for star in sites.values())
    red_qubits = {qubit["lab004_red_edge_id"]: qubit
                  for qubit in embedding["physical_qubits"]
                  if qubit["color"] == "red"}
    assert len(red_qubits) == 36 and [red_qubits[e]["id"] for e in (0, 4)] == [0, 4]
    flips = [mask(star["outer_x_qubits"]) for star in all_stars.values()]
    physical_error, first_flux = red_boundary(red_qubits, [0, 4])
    assert [site for site, bit in enumerate(first_flux) if bit] == [0, 2]
    first_eligible = [site for site in range(24) if eligible(sites[site], physical_error)]
    assert first_eligible == [site for site in range(24) if not first_flux[site]]
    first_commutation_cases = assert_eligible_commute(
        [sites[site]["center"] for site in first_eligible],
        physical_error, state["pair_rows"])
    first_means = {site: moment([conjugated_star(sites[site], physical_error)], flips)
                   for site in first_eligible}
    assert {site for site, mean in first_means.items() if mean == 0} == {1}
    assert all(mean == 1 for site, mean in first_means.items() if site != 1)
    first = conjugated_star(sites[1], physical_error)
    first_probs = {outcome: sequential_probability(first, [], outcome, (), flips)
                   for outcome in (+1, -1)}
    assert first_probs == {1: Fraction(1, 2), -1: Fraction(1, 2)}
    first_rows = {}
    for outcome in (+1, -1):
        charges = [0] * 24
        charges[1] = int(outcome == -1)
        first_rows[outcome] = public_record(first_flux, charges)

    output = []
    branch_diagnostics = []
    total_second_pair_checks = 0
    for action, action_edges in contract["fixed_case"]["action_branches"].items():
        _, second_flux = red_boundary(red_qubits,
                                      [edge for edge in (0, 4) if edge not in action_edges])
        residual = physical_error ^ red_boundary(red_qubits, action_edges)[0]
        eligible_sites = [site for site in range(24) if eligible(sites[site], residual)]
        assert eligible_sites == [site for site in range(24) if not second_flux[site]]
        second_pair_checks = assert_eligible_commute(
            [sites[site]["center"] for site in eligible_sites],
            residual, state["pair_rows"])
        total_second_pair_checks += second_pair_checks
        if action == "defer":
            assert action_edges == [] and [i for i, bit in enumerate(second_flux) if bit] == [0, 2]
            for first_outcome in (+1, -1):
                output.append({"action": action,
                               "public_action_red_edge_ids": action_edges,
                               "first_public": first_rows[first_outcome],
                               "first_probability": float(first_probs[first_outcome]),
                               "second_public": None,
                               "second_conditional_probability": None})
            branch_diagnostics.append({"action": action,
                                       "eligible_second_sites": eligible_sites,
                                       "second_pair_commutation_cases": second_pair_checks,
                                       "second_joint_status": "unavailable_defer"})
            continue
        for first_outcome in (+1, -1):
            deterministic = {}
            random_sites = []
            marginal_rows = []
            for site in eligible_sites:
                second_op = conjugated_star(sites[site], residual)
                joint_plus = sequential_probability(first, [second_op],
                                                    first_outcome, (+1,), flips)
                conditional_plus = joint_plus / first_probs[first_outcome]
                assert conditional_plus in (Fraction(0), Fraction(1, 2), Fraction(1))
                marginal_rows.append({"site": site, "p_plus": float(conditional_plus)})
                if conditional_plus == Fraction(1, 2):
                    random_sites.append(site)
                else:
                    deterministic[site] = +1 if conditional_plus == 1 else -1
            assert len(random_sites) <= contract["matrix"]["nontrivial_joint_sites_max"]
            random_ops = [conjugated_star(sites[site], residual)
                          for site in random_sites]
            conditional_mass = Fraction(0)
            for bits in range(1 << len(random_sites)):
                outcomes = tuple(+1 if not ((bits >> index) & 1) else -1
                                 for index in range(len(random_sites)))
                joint = sequential_probability(first, random_ops,
                                               first_outcome, outcomes, flips)
                assert joint >= 0
                conditional = joint / first_probs[first_outcome]
                conditional_mass += conditional
                if conditional == 0:
                    continue
                charges = [0] * 24
                for site, eigenvalue in deterministic.items():
                    charges[site] = int(eigenvalue == -1)
                for site, eigenvalue in zip(random_sites, outcomes):
                    charges[site] = int(eigenvalue == -1)
                second_public = public_record(second_flux, charges)
                assert set(first_rows[first_outcome]) == set(second_public)
                assert [len(value) for value in second_public.values()] == [24, 24, 24]
                output.append({"action": action,
                               "public_action_red_edge_ids": action_edges,
                               "first_public": first_rows[first_outcome],
                               "first_probability": float(first_probs[first_outcome]),
                               "second_public": second_public,
                               "second_conditional_probability": float(conditional),
                               "joint_probability": float(joint)})
            assert conditional_mass == 1
            branch_diagnostics.append({"action": action,
                                       "first_green_eigenvalue": first_outcome,
                                       "eligible_second_sites": eligible_sites,
                                       "second_pair_commutation_cases": second_pair_checks,
                                       "deterministic_second_sites": deterministic,
                                       "random_second_sites": random_sites,
                                       "marginals": marginal_rows,
                                       "conditional_total": float(conditional_mass)})
    matched_rows = [row for row in output if row["action"] == "matched"]
    assert len(matched_rows) == 4
    for row in matched_rows:
        charge = row["second_public"]["charge"]
        assert charge[0] == charge[2]
        assert sum(charge) in (0, 2)
        assert row["second_conditional_probability"] == 0.5
        assert row["second_public"]["flux"] == [0] * 24
    partial_rows = [row for row in output if row["action"] == "partial"]
    assert len(partial_rows) == 4
    for row in partial_rows:
        assert [i for i, bit in enumerate(row["second_public"]["flux"]) if bit] == [1, 2]
        assert row["second_conditional_probability"] == 0.5
    # Exact local branch projection must agree with the prior J6N matrix.
    for branch in ("partial", "matched"):
        for first_outcome in (+1, -1):
            prior = [row for row in local["rows"] if row["action"] == branch
                     and row["first_green_eigenvalue"] == first_outcome
                     and row["conditional_probability"] > 0]
            current = [row for row in output if row["action"] == branch
                       and row["first_public"]["charge"][1] == int(first_outcome == -1)]
            projection_sites = [0] if branch == "partial" else [0, 2]
            assert sorted((tuple(row["second_public"]["charge"][site]
                                 for site in projection_sites),
                           row["second_conditional_probability"]) for row in current) == \
                   sorted((tuple(int(value == -1) for value in row["second_eigenvalues"]),
                           row["conditional_probability"]) for row in prior)
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_exact_one_geometry_full_binary_joint_record_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pins,
        "first_eligible_sites": first_eligible,
        "first_pair_commutation_cases": first_commutation_cases,
        "second_pair_commutation_cases": total_second_pair_checks,
        "first_means_by_site": {str(site): mean for site, mean in first_means.items()},
        "branch_diagnostics_private": branch_diagnostics,
        "public_law_rows": output,
        "checks": {
            "first_and_second_full_length_binary": True,
            "first_record_source_limit": True,
            "all_eligible_projectors_commute_in_sector": True,
            "all_conditioned_joint_rows_normalized": True,
            "matched_source_pair_limit": True,
            "partial_action_residual_flux_bound": True,
            "defer_e2_unavailable": True,
            "no_private_support_or_relation_in_public_record": True,
            "j6n_local_projection_replay": True,
        },
        "inference_boundary": "Exact same-state full-binary first and action-conditioned second public record for one ideal L=2 two-edge geometry only. The output is not a general D4 sampler, first-record-aware production adapter, noisy five-round history, schedule-risk estimate or threshold.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
