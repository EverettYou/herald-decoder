"""Read-only registered posterior-entropy and exact-engine term-cost matrix."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7t-candidate-prior-cost-matrix-2026-09-27.json"
RESULT = LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json"
INPUTS = {
    "j7s_contract": LAB / "manifests/j7s-same-first-error-pair-preflight-2026-09-27.json",
    "j7s_result": LAB / "results/j7s-same-first-error-pair-preflight-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "full_law_source": LAB / "scripts/run_j7e_two_edge_complete_next_law.py",
    "exact_source": LAB / "scripts/run_j7b_future_fault_next_first_and_caller_gate.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary_entropy(q: Fraction) -> float:
    value = float(q)
    if value in (0.0, 1.0):
        return 0.0
    return -value * math.log2(value) - (1.0 - value) * math.log2(1.0 - value)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old_contract = json.loads(INPUTS["j7s_contract"].read_text())
    old = json.loads(INPUTS["j7s_result"].read_text())
    j7m = json.loads(INPUTS["j7m_result"].read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert old["status"] == "same_first_error_pair_found"
    assert old["cycles_examined"] == old["positive_candidate_count"] == budget["max_candidates"] == 12
    assert old_contract["matrix"]["iid_red_x_rate"] == spec["iid_red_x_rate"] == "1/10"
    assert old["base_first_public_mass"] == j7m["first_public_mass"] == "1/4"
    assert j7m["same_second_public_flux"] and len(j7m["cells"]) == 2
    assert {len([bit for bit in cell["second_public_flux"] if bit == 0])
            for cell in j7m["cells"]} == {spec["complete_second_eligible_sites_per_action"]} == {22}
    assert {tuple(cell["public_action_red_edges"]) for cell in j7m["cells"]} == {
        tuple(action) for action in old_contract["matrix"]["public_actions"]}
    assert old_contract["matrix"]["base_private_error_red_edges"] == [0, 4, 3]
    p = Fraction(spec["iid_red_x_rate"])
    base_edges = old_contract["matrix"]["base_private_error_red_edges"]
    base_joint = p ** len(base_edges) * (1 - p) ** (36 - len(base_edges)) * Fraction(1, 4)
    assert base_joint > 0
    rows = []
    cell_count = 0
    for prior in old["candidate_rows"]:
        assert prior["positive_selected_first_mass"] and prior["status"] == "evaluated"
        edges = prior["candidate_initial_error_red_edges_private"]
        v = prior["first_variable_site_count_private"]
        first_mass = Fraction(prior["selected_first_public_mass_given_candidate"])
        joint = p ** len(edges) * (1 - p) ** (36 - len(edges)) * first_mass
        assert joint > 0 and 0 < first_mass <= 1
        q = joint / (base_joint + joint)
        assert 0 < q < 1
        cells = []
        for k0 in spec["candidate_second_variable_count_per_action"]:
            costs = []
            for k1 in spec["candidate_second_variable_count_per_action"]:
                # One first mass; for each of two actions: denominator,
                # 22 one-site checks, and all complete binary assignments.
                cost = 3 * (1 << v) + 44 * (1 << (2 * v + 1)) + \
                    (1 << (2 * v + 2 * k0)) + (1 << (2 * v + 2 * k1))
                costs.append(cost)
                cell_count += 1
            cells.append(costs)
        allowed = [(k0, k1) for k0 in range(6) for k1 in range(6)
                   if cells[k0][k1] < budget["prior_ordered_moment_ceiling"]]
        rows.append({
            "cycle_red_edges_private": prior["cycle_red_edges_private"],
            "candidate_initial_error_red_edges_private": edges,
            "initial_error_weight": len(edges),
            "first_variable_site_count_private": v,
            "selected_first_public_mass_given_candidate": str(first_mass),
            "candidate_weight_given_pair_and_first": str(q),
            "binary_error_entropy_upper_bound_bits": round(binary_entropy(q), 12),
            "selection_score_exact": str(min(q, 1 - q)),
            "projected_two_action_terms_by_k0_k1": cells,
            "minimum_projected_two_action_terms": cells[0][0],
            "under_prior_ceiling_k0_k1": [list(pair) for pair in allowed],
            "any_conditional_cost_cell_under_prior_ceiling": bool(allowed)
        })
    assert len(rows) == budget["max_candidates"] and cell_count == budget["max_cost_cells"] == 432
    assert rows[0]["candidate_initial_error_red_edges_private"] == \
        old["selected_candidate_initial_error_red_edges_private"]
    assert rows[0]["candidate_weight_given_pair_and_first"] == \
        old["selected_pair_posterior"]["candidate_error_weight_given_pair_and_first"]
    eligible_rows = [row for row in rows if row["any_conditional_cost_cell_under_prior_ceiling"]]
    peer_score = max((Fraction(row["selection_score_exact"]) for row in eligible_rows),
                     default=None)
    selected = [] if peer_score is None else [row["candidate_initial_error_red_edges_private"]
                                               for row in eligible_rows
                                               if Fraction(row["selection_score_exact"]) == peer_score]
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "peer_candidates_identified" if selected else "no_candidate_under_prior_term_ceiling",
            "contract_sha256": digest(CONTRACT),
            "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "candidate_rows": rows,
            "selected_peer_initial_errors_private": selected,
            "selected_peer_count": len(selected),
            "cost_cells_checked": cell_count,
            "counters": {"new_ordered_moment_terms": 0, "new_physical_errors": 0,
                         "complete_second_law_evaluations": 0, "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0, "bootstrap_replicates": 0},
            "claim_boundary": "This is a restricted-binary-prior entropy ceiling and conditional exact-engine term projection only; actual second-variable counts, candidate second public laws, mutual information, unconditional risk and policy benefit remain unmeasured.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
