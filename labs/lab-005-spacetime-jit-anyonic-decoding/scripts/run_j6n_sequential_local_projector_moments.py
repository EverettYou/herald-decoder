"""Exact local sequential Born probabilities on J6M's compact periodic state.

Only local eligible star projectors are evaluated. This does not produce a
full public E2 record or change the five-round phenomenological caller.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask, parity, phase_difference


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6n-sequential-local-projector-moments-2026-09-25.json"
RESULT = LAB / "results/j6n-sequential-local-projector-moments-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def orbit_z_expectation(zmask: int, flips: list[int]) -> int:
    """Uniform orbit basis support makes every diagonal Z character 0 or 1."""
    return int(all(parity(zmask & flip) == 0 for flip in flips))


def conjugated_star(star: dict, error_mask: int) -> tuple[int, int, int]:
    """X_error A_s X_error = sign * Z_mask A_s."""
    pairs = [tuple(pair) for pair in star["six_cz_pairs"]]
    zmask, constant = phase_difference(pairs, error_mask)
    return (-1 if constant else 1, zmask, mask(star["outer_x_qubits"]))


def moment(factors: list[tuple[int, int, int]], flips: list[int]) -> int:
    """Ordered <psi|product(sign Z A_s)|psi>, with every A_s|psi>=|psi>."""
    coefficient, zmask, earlier_star_flips = 1, 0, 0
    for sign, z, flip in factors:
        coefficient *= sign
        if parity(earlier_star_flips & z):
            coefficient = -coefficient
        zmask ^= z
        earlier_star_flips ^= flip
    return coefficient * orbit_z_expectation(zmask, flips)


def sequential_probability(
    first: tuple[int, int, int],
    second: list[tuple[int, int, int]],
    first_outcome: int,
    second_outcomes: tuple[int, ...],
    flips: list[int],
) -> Fraction:
    """Expand P_first * product(P_second) * P_first exactly."""
    assert len(second) == len(second_outcomes)
    operators = [first, *second, first]
    outcomes = [first_outcome, *second_outcomes, first_outcome]
    numerator = 0
    for subset in range(1 << len(operators)):
        selected = []
        sign = 1
        for index, operator in enumerate(operators):
            if (subset >> index) & 1:
                selected.append(operator)
                sign *= outcomes[index]
        numerator += sign * moment(selected, flips)
    return Fraction(numerator, 1 << len(operators))


def eligible(star: dict, error_mask: int) -> bool:
    return all(parity(mask(triangle) & error_mask) == 0
               for triangle in star["triangle_z_qubits_by_color"].values())


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pins = {key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
            for key, path in INPUTS.items()}
    assert all(pins.values()), f"pinned input drift: {pins}"
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    assert embedding["counts"]["physical_qubits"] == 108
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert state["operator_counts"]["outer_x_flip_rank"] == 33
    stars = {star["center"]: star for star in embedding["star_supports"]}
    assert len(stars) == 36
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    red_qubits = {qubit["lab004_red_edge_id"]: qubit["id"]
                  for qubit in embedding["physical_qubits"]
                  if qubit["color"] == "red"}
    assert len(red_qubits) == 36 and red_qubits[0] == 0 and red_qubits[4] == 4
    first_star = stars["green:1"]
    physical_error = mask([red_qubits[0], red_qubits[4]])
    assert eligible(first_star, physical_error)
    first = conjugated_star(first_star, physical_error)
    first_probabilities = {
        str(outcome): sequential_probability(first, [], outcome, (), flips)
        for outcome in (+1, -1)
    }
    assert first_probabilities == {"1": Fraction(1, 2), "-1": Fraction(1, 2)}
    rows = []
    for action, edges in contract["fixed_case"]["actions"].items():
        action_mask = mask([red_qubits[edge] for edge in edges])
        residual = physical_error ^ action_mask
        sites = contract["fixed_case"]["second_measurements"][action]
        for site in sites:
            assert eligible(stars[site], residual), (action, site)
        second = [conjugated_star(stars[site], residual) for site in sites]
        if action == "defer":
            assert not sites
        for first_outcome in (+1, -1):
            rows_here = []
            for bits in range(1 << len(sites)):
                second_outcomes = tuple(1 if not ((bits >> i) & 1) else -1
                                        for i in range(len(sites)))
                joint = sequential_probability(first, second, first_outcome,
                                               second_outcomes, flips)
                assert joint >= 0
                conditional = joint / first_probabilities[str(first_outcome)]
                rows_here.append({
                    "action": action,
                    "action_red_edge_ids": edges,
                    "residual_red_edge_ids": sorted(edge for edge in [0, 4] if edge not in edges),
                    "first_green_eigenvalue": first_outcome,
                    "second_measured_centers": sites,
                    "second_eigenvalues": list(second_outcomes),
                    "joint_probability": float(joint),
                    "conditional_probability": float(conditional),
                    "second_record_scope": "eligible_local_stars_only" if sites else "unavailable_defer",
                })
            assert sum(Fraction(str(row["joint_probability"])) for row in rows_here) == first_probabilities[str(first_outcome)]
            rows.extend(rows_here)
    matched = [row for row in rows if row["action"] == "matched"]
    assert len(matched) == 8
    assert all(row["second_eigenvalues"][0] == row["second_eigenvalues"][1]
               for row in matched if row["joint_probability"] > 0)
    for first_outcome in (+1, -1):
        conditioned = [row for row in matched if row["first_green_eigenvalue"] == first_outcome]
        assert [row["conditional_probability"] for row in conditioned] == [0.5, 0, 0, 0.5]
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_exact_local_sequential_projector_moments_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pins,
        "first_green_probabilities": {key: float(value) for key, value in first_probabilities.items()},
        "rows": rows,
        "checks": {
            "same_j6m_orbit_all_actions": True,
            "first_green_source_half_half": True,
            "all_second_sites_flux_free": True,
            "all_conditional_rows_normalized": True,
            "matched_blue_pair_equal_and_half_half": True,
            "defer_second_record_unavailable": True,
            "no_full_binary_public_e2_inferred": True,
        },
        "inference_boundary": "Exact local first-projector/action/second-projector Born moments on one fixed periodic vacuum orbit. Only eligible local stars are measured; no full 24-site E2 joint law, first-record-aware adapter, five-round physical history, schedule risk or threshold follows.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
