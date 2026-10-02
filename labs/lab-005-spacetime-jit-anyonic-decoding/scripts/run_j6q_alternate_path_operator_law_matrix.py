"""Exact two-geometry extension of the J6O ideal projector law.

This stays outside the phenomenological five-round history generator. All
physical error support and operator details remain private result diagnostics.
"""

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


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6q-alternate-path-operator-law-matrix-2026-09-25.json"
RESULT = LAB / "results/j6q-alternate-path-operator-law-matrix-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6o_result": LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projection_probability(
    first_ops: list[tuple[int, int, int]], first_outcomes: tuple[int, ...],
    second_ops: list[tuple[int, int, int]], second_outcomes: tuple[int, ...],
    flips: list[int],
) -> Fraction:
    """Exact <P_first P_second P_first>, retaining causal operator order."""
    assert len(first_ops) == len(first_outcomes)
    assert len(second_ops) == len(second_outcomes)
    operators = [*first_ops, *second_ops, *first_ops]
    eigenvalues = [*first_outcomes, *second_outcomes, *first_outcomes]
    total = 0
    for subset in range(1 << len(operators)):
        selected = []
        sign = 1
        for index, operator in enumerate(operators):
            if (subset >> index) & 1:
                selected.append(operator)
                sign *= eigenvalues[index]
        total += sign * moment(selected, flips)
    return Fraction(total, 1 << len(operators))


def first_probability(
    first_ops: list[tuple[int, int, int]], first_outcomes: tuple[int, ...],
    flips: list[int],
) -> Fraction:
    """Use the sandwich formula, including the no-first-operator limit."""
    return projection_probability(first_ops, first_outcomes, [], (), flips)


def assignments(count: int):
    for bits in range(1 << count):
        yield tuple(-1 if (bits >> index) & 1 else 1 for index in range(count))


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    reference = json.loads(INPUTS["j6o_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert reference["status"] == "passed_exact_one_geometry_full_binary_joint_record_only"
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(key.split(":")[1]): value for key, value in stars.items()
             if value["center_color"] in ("blue", "green")}
    assert len(stars) == 36 and set(sites) == set(range(24))
    red = {qubit["lab004_red_edge_id"]: qubit
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    assert len(red) == 36
    assert set(red[0]["star_endpoints"]) & set(red[1]["star_endpoints"]) == {"blue:0"}
    assert not set(red[0]["star_endpoints"]) & set(red[3]["star_endpoints"])
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]

    cases = []
    for geometry, pair in contract["physical_and_observation_contract"]["private_physical_red_x_pairs"].items():
        physical, first_flux = red_boundary(red, pair)
        first_sites = [site for site in range(24) if eligible(sites[site], physical)]
        assert first_sites == [site for site in range(24) if not first_flux[site]]
        first_pairs_checked = assert_eligible_commute(
            [sites[site]["center"] for site in first_sites], physical, state["pair_rows"])
        first_means = {site: moment([conjugated_star(sites[site], physical)], flips)
                       for site in first_sites}
        assert set(first_means.values()) <= {-1, 0, 1}
        first_random = sorted(site for site, mean in first_means.items() if mean == 0)
        first_fixed = {site: mean for site, mean in first_means.items() if mean != 0}
        first_ops = [conjugated_star(sites[site], physical) for site in first_random]
        first_rows = []
        first_censored = len(first_random) > contract["matrix"]["maximum_nondeterministic_first_sites"]
        if not first_censored:
            for first_outcomes in assignments(len(first_ops)):
                first_mass = first_probability(first_ops, first_outcomes, flips)
                assert first_mass >= 0
                if first_mass == 0:
                    continue
                first_charge = [0] * 24
                for site, outcome in first_fixed.items():
                    first_charge[site] = int(outcome == -1)
                for site, outcome in zip(first_random, first_outcomes):
                    first_charge[site] = int(outcome == -1)
                first_rows.append({"outcomes": first_outcomes,
                                   "probability": first_mass,
                                   "public": public_record(first_flux, first_charge)})
            assert sum((row["probability"] for row in first_rows), Fraction()) == 1

        for action_name in ("defer", "partial", "matched"):
            action_edges = [] if action_name == "defer" else pair[:1] if action_name == "partial" else pair
            action_mask, _ = red_boundary(red, action_edges)
            residual = physical ^ action_mask
            _, second_flux = red_boundary(red, [edge for edge in pair if edge not in action_edges])
            second_sites = [site for site in range(24) if eligible(sites[site], residual)]
            assert second_sites == [site for site in range(24) if not second_flux[site]]
            second_pairs_checked = assert_eligible_commute(
                [sites[site]["center"] for site in second_sites], residual, state["pair_rows"])
            rows = []
            second_counts = []
            branch_censored = first_censored
            if not first_censored:
                for first_row in first_rows:
                    if action_name == "defer":
                        rows.append({"first_public": first_row["public"],
                                     "first_probability": str(first_row["probability"]),
                                     "second_public": None,
                                     "second_conditional_probability": None})
                        continue
                    second_random = []
                    second_fixed = {}
                    for site in second_sites:
                        second_op = conjugated_star(sites[site], residual)
                        joint_plus = projection_probability(
                            first_ops, first_row["outcomes"], [second_op], (1,), flips)
                        conditional_plus = joint_plus / first_row["probability"]
                        assert conditional_plus in (0, Fraction(1, 2), 1)
                        if conditional_plus == Fraction(1, 2):
                            second_random.append(site)
                        else:
                            second_fixed[site] = 1 if conditional_plus == 1 else -1
                    second_counts.append(len(second_random))
                    if len(second_random) > contract["matrix"]["maximum_nondeterministic_second_sites"]:
                        branch_censored = True
                        continue
                    second_ops = [conjugated_star(sites[site], residual)
                                  for site in second_random]
                    conditional_total = Fraction()
                    for second_outcomes in assignments(len(second_ops)):
                        joint = projection_probability(first_ops, first_row["outcomes"],
                                                       second_ops, second_outcomes, flips)
                        assert joint >= 0
                        conditional = joint / first_row["probability"]
                        conditional_total += conditional
                        if conditional == 0:
                            continue
                        second_charge = [0] * 24
                        for site, outcome in second_fixed.items():
                            second_charge[site] = int(outcome == -1)
                        for site, outcome in zip(second_random, second_outcomes):
                            second_charge[site] = int(outcome == -1)
                        rows.append({"first_public": first_row["public"],
                                     "first_probability": str(first_row["probability"]),
                                     "second_public": public_record(second_flux, second_charge),
                                     "second_conditional_probability": str(conditional)})
                    assert conditional_total == 1
            if branch_censored:
                rows = []  # no partial public law can masquerade as a complete branch
            cases.append({
                "geometry": geometry,
                "physical_pair_private": pair,
                "action": action_name,
                "public_action_red_edge_ids": action_edges,
                "first_flux_sites": [site for site, bit in enumerate(first_flux) if bit],
                "second_flux_sites": [site for site, bit in enumerate(second_flux) if bit],
                "first_eligible_pair_checks": first_pairs_checked,
                "second_eligible_pair_checks": second_pairs_checked,
                "first_random_sites_private": first_random,
                "second_random_counts_private": second_counts,
                "status": "censored_support_exceeds_bound" if branch_censored else "exact_full_public_law",
                "public_law_rows": rows,
            })
            assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    assert len(cases) == 6
    assert digest(INPUTS["frozen_integrated_history"]) == \
           contract["pinned_inputs"]["frozen_integrated_history_sha256"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_two_geometry_exact_matrix" if all(
            row["status"] == "exact_full_public_law" for row in cases)
            else "partially_censored_two_geometry_exact_matrix",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pins,
        "cases": cases,
        "checks": {"incidence_classes_verified": True,
                   "all_eligible_projectors_commute": True,
                   "causal_first_action_second_born_order": True,
                   "exact_normalization_or_explicit_censoring": True,
                   "old_five_round_caller_byte_identical": True},
        "inference_boundary": "Two additional ideal L=2 red-X pairs on one J6M orbit only. No general D4 kernel, physical noisy-history sampler, schedule risk, decoder comparison or threshold follows.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.process_time() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
