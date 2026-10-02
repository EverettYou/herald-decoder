"""Source-pinned necessary-condition screen for exact cross-round D4 memory."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask, parity
from run_j6n_sequential_local_projector_moments import conjugated_star, eligible
from run_j6o_full_binary_sequential_public_record import red_boundary


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7d-cross-round-commutation-screen-2026-09-25.json"
RESULT = LAB / "results/j7d-cross-round-commutation-screen-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6s_result": LAB / "results/j6s-repeat-transfer-four-site-2026-09-25.json",
    "j6u_result": LAB / "results/j6u-four-edge-path-branch-2026-09-25.json",
    "j6z_result": LAB / "results/j6z-full-second-stateful-readiness-2026-09-25.json",
    "j7c_result": LAB / "results/j7c-three-edge-history-memory-discriminator-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross_vacuum_anticommutes(left: tuple[int, int, int],
                              right: tuple[int, int, int]) -> bool:
    """The base-star commutator is triangle-vacuum-trivial (J6M)."""
    _, left_z, left_flip = left
    _, right_z, right_flip = right
    return bool(parity(left_flip & right_z) ^ parity(right_flip & left_z))


def subsets(edges: list[int]):
    for count in range(1, len(edges) + 1):
        yield from itertools.combinations(edges, count)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pinned_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                     for name, path in INPUTS.items()}
    assert all(pinned_before.values()), pinned_before
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    assert embedding["counts"]["physical_qubits"] == 108
    assert state["operator_counts"]["outer_x_flip_rank"] == 33
    assert state["checks"]["all_adjacent_commutators_vanish_on_triangle_vacuum"]
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(name.split(":")[1]): star for name, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    red = {qubit["lab004_red_edge_id"]: qubit
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    assert set(sites) == set(range(24)) and len(red) == 36
    pair_base = {frozenset((row["left"], row["right"])):
                 int(row["commutator_z_mask_hex"], 16)
                 for row in state["pair_rows"]}
    assert len(pair_base) == 630
    matrix = contract["matrix"]
    fixture_names = ("two_edge_path", "three_edge_chain", "four_edge_path",
                     "four_edge_branch", "six_edge_loop")
    fixtures = {name: matrix[name] for name in fixture_names}
    assert all(isinstance(edges, list) for edges in fixtures.values())
    j6u = json.loads(INPUTS["j6u_result"].read_text())
    j6z = json.loads(INPUTS["j6z_result"].read_text())
    j7c = json.loads(INPUTS["j7c_result"].read_text())
    assert j7c["status"] == "exact_three_edge_history_discriminator_complete"
    assert j7c["matrix"]["exact_total_variation_by_first_charge"] == {
        "00": "0", "10": "0", "01": "0", "11": "0"}
    assert fixtures["three_edge_chain"] == [0, 4, 3]
    assert fixtures["four_edge_path"] == [0, 4, 3, 7]
    assert fixtures["four_edge_branch"] == [0, 4, 3, 5]
    assert fixtures["six_edge_loop"] == [0, 1, 32, 30, 34, 35]
    assert j6z["full_second_loop"]["status"] == "passed_exact_one_geometry_full_binary_second_public_law"
    assert j6u["status"]  # pinned topology provenance, not a probability input

    budget = contract["budget"]
    checks = {"same_sector_pairs": 0, "cross_round_pairs": 0, "matched_pairs": 0}
    branch_rows = []
    pair_rows = []
    fixture_counts = {}
    for name, edges in fixtures.items():
        physical, first_flux = red_boundary(red, edges)
        first_sites = [site for site in range(24) if eligible(sites[site], physical)]
        assert first_sites == [site for site, bit in enumerate(first_flux) if bit == 0]
        groups = defaultdict(list)
        sector_cache = {}

        def sector(edge_ids):
            key = tuple(sorted(edge_ids))
            if key not in sector_cache:
                support, flux = red_boundary(red, list(key))
                measured = [s for s in range(24) if eligible(sites[s], support)]
                assert measured == [s for s, bit in enumerate(flux) if bit == 0]
                operators = {s: conjugated_star(sites[s], support) for s in measured}
                for left, right in itertools.combinations(measured, 2):
                    base = pair_base[frozenset((sites[left]["center"],
                                               sites[right]["center"]))]
                    assert parity(base & support) == 0
                    assert not cross_vacuum_anticommutes(operators[left], operators[right])
                    checks["same_sector_pairs"] += 1
                sector_cache[key] = (support, measured, operators)
            return sector_cache[key]

        sector(edges)
        first_index = len(branch_rows)
        matched_here = 0
        open_here = 0
        for action in subsets(edges):
            residual_edges = tuple(edge for edge in edges if edge not in action)
            _, second_sites, second_ops = sector(residual_edges)
            for future in (None, *edges):
                final_edges = tuple(edge for edge in edges
                                    if ((edge not in action) ^ (edge == future)))
                _, next_sites, next_ops = sector(final_edges)
                witnesses = []
                for second_site in second_sites:
                    for next_site in next_sites:
                        checks["cross_round_pairs"] += 1
                        if cross_vacuum_anticommutes(second_ops[second_site],
                                                     next_ops[next_site]):
                            witnesses.append([second_site, next_site])
                row = {"fixture": name, "physical_edges_private": edges,
                       "public_action_edges": list(action),
                       "future_fault_edge_private": future,
                       "final_edges_private": list(final_edges),
                       "second_eligible_sites_private": second_sites,
                       "next_eligible_sites_private": next_sites,
                       "second_next_anticommuting_pairs": len(witnesses),
                       "first_witness_sites_private": witnesses[0] if witnesses else None}
                branch_rows.append(row)
                groups[tuple(final_edges)].append(row)
                assert len(branch_rows) <= budget["max_histories"]
                assert checks["cross_round_pairs"] <= budget["max_pair_operator_checks"]
        for final, rows in groups.items():
            for left, right in itertools.combinations(rows, 2):
                if left["public_action_edges"] == right["public_action_edges"]:
                    continue
                checks["matched_pairs"] += 1
                matched_here += 1
                assert checks["matched_pairs"] <= budget["max_matched_pairs"]
                if left["second_next_anticommuting_pairs"] or right["second_next_anticommuting_pairs"]:
                    open_here += 1
                    pair_rows.append({"fixture": name, "final_edges_private": list(final),
                                      "a_action": left["public_action_edges"],
                                      "a_future": left["future_fault_edge_private"],
                                      "a_anticommuting_pairs": left["second_next_anticommuting_pairs"],
                                      "b_action": right["public_action_edges"],
                                      "b_future": right["future_fault_edge_private"],
                                      "b_anticommuting_pairs": right["second_next_anticommuting_pairs"]})
        fixture_counts[name] = {"histories": len(branch_rows) - first_index,
                                "matched_pairs": matched_here,
                                "structurally_open_matched_pairs": open_here,
                                "structurally_open_histories": sum(
                                    row["second_next_anticommuting_pairs"] > 0
                                    for row in branch_rows[first_index:])}
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    j7c_a = any(row["fixture"] == "three_edge_chain" and
                row["public_action_edges"] == [0] and row["future_fault_edge_private"] == 4
                and row["final_edges_private"] == [3] for row in branch_rows)
    j7c_b = any(row["fixture"] == "three_edge_chain" and
                row["public_action_edges"] == [0, 4] and row["future_fault_edge_private"] is None
                and row["final_edges_private"] == [3] for row in branch_rows)
    assert j7c_a and j7c_b
    pinned_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                    for name, path in INPUTS.items()}
    assert all(pinned_after.values())
    ranked = sorted(pair_rows, key=lambda row: (
        len(fixtures[row["fixture"]]),
        -(row["a_anticommuting_pairs"] + row["b_anticommuting_pairs"]),
        row["fixture"], row["a_action"], row["b_action"],
        -1 if row["a_future"] is None else row["a_future"],
        -1 if row["b_future"] is None else row["b_future"]))
    return {"schema_version": 1, "id": contract["id"],
            "status": ("finite_structural_opening_found" if ranked else
                       "finite_all_commuting_screen"),
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": pinned_before,
            "pinned_input_checks_after": pinned_after,
            "fixture_counts": fixture_counts, "counts": {
                **checks, "histories": len(branch_rows),
                "structurally_open_matched_pairs": len(pair_rows)},
            "j7c_history_coverage": {"branch_a": j7c_a, "branch_b": j7c_b,
                                      "prior_exact_total_variation_all_four_first": "0"},
            "ranked_open_pairs_first_32": ranked[:32],
            "branch_rows": branch_rows,
            "inference_boundary": "A cross-round anticommutator is only a necessary structural opening for dephasing-induced unconditional next-law change at matched first/final support. It does not prove nonzero Born-law TV, random second outcomes, isolated action causality, a general D4 channel or noisy schedule advantage.",
            "stochastic_histories": 0, "schedule_arm_evaluations": 0,
            "bootstrap_replicates": 0,
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
