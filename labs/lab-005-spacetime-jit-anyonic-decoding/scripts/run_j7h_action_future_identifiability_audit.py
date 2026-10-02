"""Deterministic red-X action/future support-identifiability audit."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6o_full_binary_sequential_public_record import red_boundary


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7h-action-future-identifiability-audit-2026-09-26.json"
RESULT = LAB / "results/j7h-action-future-identifiability-audit-2026-09-26.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j7d_result": LAB / "results/j7d-cross-round-commutation-screen-2026-09-25.json",
    "j7g_result": LAB / "results/j7g-three-edge-matched-complete-next-law-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xor_support(*edge_sets) -> list[int]:
    support = set()
    for edges in edge_sets:
        support.symmetric_difference_update(edges)
    return sorted(support)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget = contract["budget"]
    pins_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                   for name, path in INPUTS.items()}
    assert all(pins_before.values()), pins_before
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    j7d = json.loads(INPUTS["j7d_result"].read_text())
    j7g = json.loads(INPUTS["j7g_result"].read_text())
    assert j7g["status"] == "exact_three_edge_one_first_complete_public_contrast_closed"
    assert j7g["matrix"]["exact_total_variation"] == "1/2"
    red = {int(qubit["lab004_red_edge_id"]): qubit
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    assert len(red) == 36
    spec = contract["matrix"]
    physical = spec["initial_physical_red_edges_private"]
    actions, futures = spec["actions"], spec["future_fault_keys_private"]
    assert physical == [0, 4, 3] and actions == [[0], [4]]
    assert futures == [[0], [4]]
    physical_mask, first_flux = red_boundary(red, physical)
    primary = []
    for action in actions:
        action_mask, _ = red_boundary(red, action)
        for future in futures:
            future_mask, _ = red_boundary(red, future)
            final = xor_support(physical, action, future)
            final_mask, final_flux = red_boundary(red, final)
            assert final_mask == physical_mask ^ action_mask ^ future_mask
            source = [row for row in j7d["branch_rows"]
                      if row["fixture"] == "three_edge_chain" and
                      row["public_action_edges"] == action and
                      row["future_fault_edge_private"] == future[0]]
            assert len(source) == 1
            assert sorted(source[0]["final_edges_private"]) == final
            primary.append({"public_action_red_edges": action,
                            "future_physical_red_edges_private": future,
                            "final_red_edges_private": final,
                            "final_public_flux": final_flux,
                            "final_physical_mask_hex_private": hex(final_mask)})
    assert len(primary) == 4
    diagonal = [row for row in primary
                if row["public_action_red_edges"] == row["future_physical_red_edges_private"]]
    assert len(diagonal) == 2
    assert all(row["final_red_edges_private"] == sorted(physical) for row in diagonal)
    assert primary[0]["final_red_edges_private"] == primary[3]["final_red_edges_private"]
    assert primary[1]["final_red_edges_private"] == primary[2]["final_red_edges_private"] == [3]
    assert primary[0]["future_physical_red_edges_private"] != primary[3]["future_physical_red_edges_private"]
    assert j7g["matrix"]["branch_a"]["public_action_red_edge_ids"] == actions[0]
    assert j7g["matrix"]["branch_b"]["public_action_red_edge_ids"] == actions[1]
    assert j7g["matrix"]["branch_a"]["future_physical_red_edge_private"] == futures[0][0]
    assert j7g["matrix"]["branch_b"]["future_physical_red_edge_private"] == futures[1][0]
    assert all(row["final_public_flux"] == first_flux for row in diagonal)

    all_actions = [list(combo) for size in range(len(physical) + 1)
                   for combo in itertools.combinations(physical, size)]
    all_futures = [[], *[[edge] for edge in physical]]
    control_rows = []
    pair_checks = 0
    for future in all_futures:
        by_action = {}
        for action in all_actions:
            final = xor_support(physical, action, future)
            action_mask, _ = red_boundary(red, action)
            future_mask, _ = red_boundary(red, future)
            final_mask, final_flux = red_boundary(red, final)
            assert final_mask == physical_mask ^ action_mask ^ future_mask
            assert all(bit in (0, 1) for bit in final_flux) and len(final_flux) == 24
            by_action[tuple(action)] = final
            control_rows.append({"public_action_red_edges": action,
                                 "future_physical_red_edges_private": future,
                                 "final_red_edges_private": final})
        for left, right in itertools.combinations(all_actions, 2):
            pair_checks += 1
            assert left != right
            assert by_action[tuple(left)] != by_action[tuple(right)]
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert len(control_rows) == budget["max_cells"] == 32
    assert pair_checks == budget["max_pair_checks"] == 112
    pins_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                  for name, path in INPUTS.items()}
    assert all(pins_after.values()), pins_after
    return {"schema_version": 1, "id": contract["id"],
            "status": "additive_red_x_action_future_identifiability_boundary_passed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": pins_before,
            "pinned_input_checks_after": pins_after,
            "primary_matrix": primary,
            "control_rows": control_rows,
            "counts": {"primary_cells": len(primary),
                       "exhaustive_control_cells": len(control_rows),
                       "distinct_action_same_future_pair_checks": pair_checks},
            "j7g_history_tv_control": "1/2, diagonal cells have different future fault keys",
            "algebraic_result": "For fixed E and F, (E xor A1 xor F)=(E xor A2 xor F) iff A1=A2. The fixed-E, same-F, distinct-A total action effect and the fixed-E, same-final-support, distinct-A history contrast therefore cannot share all conditioning keys in this red-X model.",
            "next_estimand_boundary": "A same-future-key action contrast must allow final support to differ; J7G remains a same-final-support history contrast with differing future keys. Neither is a noisy schedule or decoder-risk result.",
            "stochastic_histories": 0, "schedule_arm_evaluations": 0,
            "bootstrap_replicates": 0,
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
