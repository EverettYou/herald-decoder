"""Bounded two-branch geometry/risk-estimand prerequisite audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from run_j6o_full_binary_sequential_public_record import red_boundary


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7j-charge-risk-estimand-feasibility-2026-09-26.json"
RESULT = LAB / "results/j7j-charge-risk-estimand-feasibility-2026-09-26.json"
INPUTS = {
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6v_result": LAB / "results/j6v-loop-stateful-prerequisite-audit-2026-09-25.json",
    "j7h_result": LAB / "results/j7h-action-future-identifiability-audit-2026-09-26.json",
    "j7i_result": LAB / "results/j7i-same-future-total-action-law-2026-09-26.json",
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
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    j6v = json.loads(INPUTS["j6v_result"].read_text())
    j7h = json.loads(INPUTS["j7h_result"].read_text())
    j7i = json.loads(INPUTS["j7i_result"].read_text())
    assert j7i["status"] == "exact_same_future_total_action_law_closed"
    assert j7h["status"] == "additive_red_x_action_future_identifiability_boundary_passed"
    assert j6v["simple_loop_geometry"]["minimum_cycle_length"] == 6
    loop = j6v["simple_loop_geometry"]["canonical_red_edge_ids_private"]
    assert loop == j6v["simple_loop_geometry"]["witness_red_edge_ids_private"]
    assert len(loop) == len(set(loop)) == 6
    red = {int(row["lab004_red_edge_id"]): row for row in
           embedding["physical_qubits"] if row["color"] == "red"}
    assert len(red) == 36
    loop_mask, loop_flux = red_boundary(red, loop)
    assert loop_mask != 0 and loop_flux == [0] * 24
    baseline = spec["baseline_public_action"]
    toggled = xor_support(baseline, loop)
    assert baseline != toggled
    assert sorted(set(baseline) ^ set(toggled)) == sorted(loop)
    first = spec["common_private_initial_red_edges"]
    assert first == [0, 4, 3]
    assert spec["fixed_private_future_keys"] == [[0], [4]]
    cells = []
    for future in spec["fixed_private_future_keys"]:
        for action in (baseline, toggled):
            final = xor_support(first, action, future)
            _, flux = red_boundary(red, final)
            cells.append({"future_physical_red_edges_private": future,
                          "public_action_red_edges": action,
                          "final_red_edges_private": final,
                          "final_public_flux": flux})
        left, right = cells[-2:]
        assert left["final_red_edges_private"] != right["final_red_edges_private"]
        assert left["final_public_flux"] == right["final_public_flux"]
    assert len(cells) == budget["max_geometry_cells"] == 4
    # The original one-error exact laws are conditional distributions, not
    # an ensemble of scored independent physical histories.
    assert len(j7i["cells"]) == 4 and j7i["first_mass"] == "1/4"
    assert {tuple(cell["future_physical_red_edges_private"])
            for cell in j7i["cells"]} == {(0,), (4,)}
    required_risk_keys = ("physical_error_ensemble", "paired_loss_rows",
                          "risk_denominator", "boolean_union_loss")
    assert not any(key in j7i for key in required_risk_keys)
    risk = {"expected_logical_risk_identified": False,
            "existing_design": "One fixed private initial red-X error and one selected first record; exact conditional public laws, not scored sampled histories",
            "missing_inputs": ["registered physical-error ensemble and independent history unit",
                               "paired action-specific unconditional loss rows and denominator",
                               "ground-state-relative Boolean-union logical score applied to every outcome"],
            "allowed_inference": "A fixed-error conditional public-law difference cannot by itself estimate population expected logical failure or Bayes risk"}
    assert time.process_time() - started <= budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "same_flux_geometry_candidate_risk_not_identified",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "loop_red_edges_private": loop,
            "loop_public_flux_zero": True,
            "baseline_public_action": baseline,
            "loop_toggled_public_action": toggled,
            "geometry_cells": cells,
            "geometry_claim_boundary": "Same public flux is necessary, not sufficient, for a charge-specific causal contrast; logical homology, action admissibility, full first/second/next laws and finite compute caps remain unverified",
            "risk_branch": risk,
            "counters": {"born_law_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "frozen_caller": "unchanged",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
