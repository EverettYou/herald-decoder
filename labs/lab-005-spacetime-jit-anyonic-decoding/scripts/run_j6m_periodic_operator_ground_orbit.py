"""Exact symbolic D4 star/triangle algebra on the pinned periodic support.

The result is a compact existence proof for one vacuum common-eigenstate
orbit. It does not enumerate its amplitudes or perform a quantum measurement.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6m-periodic-operator-ground-orbit-2026-09-24.json"
RESULT = LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "iqbal_pdf": ROOT / "references/iqbal2023-nonabelian-topological-order/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask(sites: list[int]) -> int:
    return sum(1 << site for site in sites)


def parity(value: int) -> int:
    return value.bit_count() & 1


def qphase(pairs: list[tuple[int, int]], state: int) -> int:
    return sum(((state >> left) & 1) * ((state >> right) & 1)
               for left, right in pairs) & 1


def phase_difference(pairs: list[tuple[int, int]], flip: int) -> tuple[int, int]:
    """q(x XOR flip) XOR q(x) = parity(linear & x) XOR constant."""
    linear = 0
    constant = 0
    for left, right in pairs:
        left_flip = (flip >> left) & 1
        right_flip = (flip >> right) & 1
        if left_flip:
            linear ^= 1 << right
        if right_flip:
            linear ^= 1 << left
        constant ^= left_flip & right_flip
    return linear, constant


def row_basis(masks: list[int]) -> dict[int, int]:
    basis: dict[int, int] = {}
    for original in masks:
        value = original
        for pivot in sorted(basis, reverse=True):
            if (value >> pivot) & 1:
                value ^= basis[pivot]
        if value:
            basis[value.bit_length() - 1] = value
    return basis


def reduced(value: int, basis: dict[int, int]) -> int:
    for pivot in sorted(basis, reverse=True):
        if (value >> pivot) & 1:
            value ^= basis[pivot]
    return value


def flip_basis_and_relations(flips: list[int]) -> tuple[int, list[int]]:
    basis: dict[int, tuple[int, int]] = {}
    relations: list[int] = []
    for index, original in enumerate(flips):
        value = original
        combination = 1 << index
        for pivot in sorted(basis, reverse=True):
            if (value >> pivot) & 1:
                previous_value, previous_combination = basis[pivot]
                value ^= previous_value
                combination ^= previous_combination
        if value:
            basis[value.bit_length() - 1] = (value, combination)
        else:
            assert combination and parity(combination & (1 << index)) == 1
            relations.append(combination)
    return len(basis), relations


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pinned = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
              for name, path in INPUTS.items()}
    assert all(pinned.values()), f"pinned input drift: {pinned}"
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    assert embedding["status"] == "passed_exact_incidence_only"
    qubit_count = embedding["counts"]["physical_qubits"]
    stars = embedding["star_supports"]
    assert qubit_count == contract["budget"]["max_qubits"] == 108
    assert len(stars) == contract["budget"]["max_stars"] == 36

    centers = [star["center"] for star in stars]
    adjacent = {frozenset(qubit["star_endpoints"])
                for qubit in embedding["physical_qubits"]}
    edge_color = {frozenset(qubit["star_endpoints"]): qubit["color"]
                  for qubit in embedding["physical_qubits"]}
    assert len(adjacent) == 108
    assert all(len(edge) == 2 for edge in adjacent)
    flips = [mask(star["outer_x_qubits"]) for star in stars]
    rings = [[tuple(pair) for pair in star["six_cz_pairs"]] for star in stars]
    triangles = [mask(sites)
                 for star in stars
                 for sites in star["triangle_z_qubits_by_color"].values()]
    assert len(triangles) == contract["budget"]["max_triangles"] == 72
    assert all(triangle.bit_count() == 3 for triangle in triangles)
    assert all(flip.bit_count() == 6 for flip in flips)
    assert all(len(pairs) == 6 for pairs in rings)
    for flip, pairs in zip(flips, rings):
        assert all(not ((flip >> left) & 1) and not ((flip >> right) & 1)
                   for left, right in pairs)
        assert phase_difference(pairs, flip) == (0, 0)  # A_s^2=I and Hermitian.

    star_triangle_cases = 0
    for flip in flips:
        for triangle in triangles:
            assert parity(flip & triangle) == 0
            star_triangle_cases += 1
    assert star_triangle_cases == contract["matrix"]["star_triangle_cases"] == 2592
    triangle_basis = row_basis(triangles)

    pair_rows = []
    nonzero_adjacent = 0
    for left in range(len(stars)):
        for right in range(left + 1, len(stars)):
            linear_left, constant_left = phase_difference(rings[left], flips[right])
            linear_right, constant_right = phase_difference(rings[right], flips[left])
            linear = linear_left ^ linear_right
            constant = constant_left ^ constant_right
            is_adjacent = frozenset((centers[left], centers[right])) in adjacent
            # Independently check the affine formula on all single-bit basis
            # perturbations and the all-zero basis state, not just one pair.
            for state in [0] + [1 << bit for bit in range(qubit_count)]:
                direct = (qphase(rings[left], state ^ flips[right])
                          ^ qphase(rings[left], state)
                          ^ qphase(rings[right], state ^ flips[left])
                          ^ qphase(rings[right], state))
                assert direct == parity(linear & state) ^ constant
            assert constant == 0
            assert is_adjacent or linear == 0
            assert reduced(linear, triangle_basis) == 0
            if is_adjacent:
                color = edge_color[frozenset((centers[left], centers[right]))]
                left_triangle = mask(stars[left]["triangle_z_qubits_by_color"][color])
                right_triangle = mask(stars[right]["triangle_z_qubits_by_color"][color])
                # Supplemental source-image cross-check: the A3 commutator is
                # exactly the product of its two local same-color triangles.
                assert linear == left_triangle ^ right_triangle
                if linear:
                    nonzero_adjacent += 1
            pair_rows.append({"left": centers[left], "right": centers[right],
                              "adjacent": is_adjacent,
                              "commutator_z_mask_hex": hex(linear),
                              "commutator_z_weight": linear.bit_count(),
                              "vacuum_triangle_span": True})
    assert len(pair_rows) == contract["matrix"]["star_pair_cases_per_model"] == 630
    assert nonzero_adjacent > 0
    assert sum(row["adjacent"] for row in pair_rows) == 108
    # Deleting all CZ factors makes q=0 for every star: the same 630 null
    # pairs globally commute. The physical source branch must not be replaced.
    null_nonzero_pairs = 0

    rank, relations = flip_basis_and_relations(flips)
    assert rank + len(relations) == len(stars)
    relation_rows = []
    for combination in relations:
        state = 0
        sign = 0
        members = []
        for index, (flip, pairs) in enumerate(zip(flips, rings)):
            if (combination >> index) & 1:
                sign ^= qphase(pairs, state)
                state ^= flip
                members.append(centers[index])
        assert state == 0
        assert sign == 0
        relation_rows.append({"star_centers": members,
                              "identity_flip": True,
                              "phase_on_zero": 1})
    # A_s commutes with every B_t; every orbit word from |0> therefore stays
    # in B_t=+1. Pair commutators vanish throughout that vacuum sector, and
    # all flip-mask relations have positive phase. Distinct independent-flip
    # words have distinct basis targets, so their signed sum is nonzero and
    # all 36 A_s act as +1 on it.
    assert all(reduced(int(row["commutator_z_mask_hex"], 16), triangle_basis) == 0
               for row in pair_rows)
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_symbolic_vacuum_orbit_existence_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pinned,
        "operator_counts": {"qubits": qubit_count, "stars": len(stars),
                            "triangles": len(triangles),
                            "star_triangle_cases": star_triangle_cases,
                            "star_pair_cases_per_model": len(pair_rows),
                            "adjacent_pairs": 108,
                            "nonadjacent_pairs": 522,
                            "source_nonzero_adjacent_commutators": nonzero_adjacent,
                            "cz_deleted_null_nonzero_commutators": null_nonzero_pairs,
                            "triangle_mask_rank": len(triangle_basis),
                            "outer_x_flip_rank": rank,
                            "outer_x_flip_relation_count": len(relations)},
        "checks": {"all_source_stars_hermitian_involutions": True,
                   "all_star_triangle_pairs_commute": True,
                   "all_pair_formulas_match_109_basis_probes": True,
                   "nonadjacent_stars_commute_globally": True,
                   "all_adjacent_commutators_vanish_on_triangle_vacuum": True,
                   "all_adjacent_commutators_match_two_local_triangle_products": True,
                   "at_least_one_fluxful_noncommuting_adjacent_pair": True,
                   "all_dependent_orbit_relations_positive": True,
                   "nonzero_common_plus_state_exists_as_compact_orbit": True},
        "pair_rows": pair_rows,
        "dependent_relation_rows": relation_rows,
        "inference_boundary": "Exact symbolic operator algebra and nonzero common plus-state orbit existence only. The 2^rank orbit is not enumerated or assigned a logical sector; no sequential measurement, public E2, histories, schedule risk, ground-space degeneracy or threshold is calculated.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
