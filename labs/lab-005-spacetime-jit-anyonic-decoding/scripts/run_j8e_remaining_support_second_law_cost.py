"""Prospective exact singleton and structural full-law cost for remaining loops."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8e-remaining-support-second-law-cost-2026-09-27.json"
RESULT = LAB / "results/j8e-remaining-support-second-law-cost-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8d_result": LAB / "results/j8d-winding-class-second-law-witness-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "compose_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
    "j8b_source": LAB / "scripts/run_j8b_alternate_first_complete_second_laws.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BudgetExhausted(Exception):
    pass


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8c_result", "j8d_result", "j7m_result", "j6l_result", "j6m_result")}
    assert old["j8c_result"]["status"] == "support_geometry_cost_matrix_closed"
    assert old["j8d_result"]["status"] == "winding_class_second_law_witness_closed"
    assert old["j8d_result"]["different_candidate_action_cells"] == 0
    assert spec["actions"] == [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
    assert spec["base_error_private"] == [0, 4, 3]
    branches = [branch for branch in old["j8c_result"]["new_support_branches"] if branch["cycle_length"] == 8]
    assert len(branches) == 1 and len(branches[0]["rows"]) == 54
    selected = {tuple(loop) for loop in old["j8d_result"]["selected_loop_red_edges_private"]}
    assert len(selected) == 3
    candidates = [row for row in branches[0]["rows"] if tuple(row["loop_red_edges_private"]) not in selected]
    controls = [row for row in branches[0]["rows"] if tuple(row["loop_red_edges_private"]) in selected]
    assert len(candidates) == 51 and len(controls) == 3
    assert len({tuple(row["candidate_error_red_edges_private"]) for row in branches[0]["rows"]}) == 54
    assert sorted(tuple(row["loop_red_edges_private"]) for row in controls) == sorted(selected)
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    usage = {"first_orbit_moments": 0, "second_singleton_orbit_moments": 0,
             "algebraic_relation_probes": 0, "projected_higher_orbit_moments": 0,
             "projected_higher_relation_probes": 0, "complete_second_laws": 0,
             "histories": 0, "schedule_arms": 0, "bootstraps": 0}
    rows = []
    censored_at = None
    for source in [*candidates, *controls]:
        is_control = tuple(source["loop_red_edges_private"]) in selected
        edges = source["candidate_error_red_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, first_means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in first_means.values())
        first_variable = sorted(site for site, value in first_means.items() if value == 0)
        assert first_variable == source["first_variable_sites_private"]
        assert len(first_variable) <= budget["max_first_variable_sites"]
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(left, right) for left in first_ops for right in first_ops)
        first_subsets = [[first_ops[i] for i in range(len(first_ops)) if (mask >> i) & 1]
                         for mask in range(1 << len(first_ops))]
        if usage["first_orbit_moments"] + len(first_subsets) > budget["max_orbit_moment_terms"]:
            censored_at = {"loop_red_edges_private": source["loop_red_edges_private"], "gate": "first_orbit_term_cap"}
            break
        first_sum = sum(moment(subset, flips) for subset in first_subsets)
        usage["first_orbit_moments"] += len(first_subsets)
        assert Fraction(first_sum, 1 << len(first_variable)) == Fraction(source["selected_allplus_first_mass"]) > 0
        cells = []
        try:
            for action_index, action in enumerate(spec["actions"]):
                action_mask, _ = red_boundary(red, action)
                residual = physical ^ action_mask
                check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
                assert residual == check_mask
                assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
                eligible_second, _ = sector_sites(sites, residual, flips, pairs)
                assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
                assert len(eligible_second) == budget["eligible_second_sites_per_cell"]
                second_ops = {site: conjugated_star(sites[site], residual) for site in eligible_second}
                assert all(commute(left, right) for left in second_ops.values() for right in second_ops.values())

                def structural(group: tuple[int, ...], *, singleton: bool):
                    product = compose([second_ops[site] for site in group])
                    assert compose([product, product]) == (1, 0, 0)
                    if any(not commute(product, first) for first in first_ops):
                        return "anticommuting_zero", Fraction(0) if singleton else None
                    for subset in first_subsets:
                        key = "algebraic_relation_probes" if singleton else "projected_higher_relation_probes"
                        if usage["algebraic_relation_probes"] + usage["projected_higher_relation_probes"] >= budget["max_algebraic_relation_probes"]:
                            raise BudgetExhausted("relation_probe_cap")
                        usage[key] += 1
                        observed = moment([product, *subset], flips)
                        if observed in (-1, 1):
                            return "operator_relation", Fraction(observed) if singleton else None
                    if singleton:
                        if usage["first_orbit_moments"] + usage["second_singleton_orbit_moments"] + len(first_subsets) > budget["max_orbit_moment_terms"]:
                            raise BudgetExhausted("singleton_orbit_term_cap")
                        total = sum(moment([*subset, product], flips) for subset in first_subsets)
                        usage["second_singleton_orbit_moments"] += len(first_subsets)
                        return "singleton_orbit_expansion", Fraction(total, first_sum)
                    usage["projected_higher_orbit_moments"] += len(first_subsets)
                    return "requires_orbit_expansion", None

                singleton_values = {site: structural((site,), singleton=True)[1] for site in eligible_second}
                assert all(value in (-1, 0, 1) for value in singleton_values.values())
                variable = sorted(site for site, value in singleton_values.items() if value == 0)
                if is_control:
                    control = next(row for row in old["j8d_result"]["rows"][1:] if row["error_edges_private"] == edges)
                    assert variable == control["cells"][action_index]["variable_second_sites_private"]
                higher_groups = 0
                if len(variable) <= budget["max_variable_second_sites_per_cell"]:
                    for order in range(2, len(variable) + 1):
                        for group in itertools.combinations(variable, order):
                            structural(group, singleton=False)
                            higher_groups += 1
                cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                              "variable_second_sites_private": variable,
                              "variable_second_site_count": len(variable),
                              "higher_groups_structurally_costed": higher_groups,
                              "complete_law_site_gate_pass": len(variable) <= budget["max_variable_second_sites_per_cell"]})
                if time.process_time() - started >= budget["max_cpu_seconds"]:
                    raise BudgetExhausted("cpu_cap")
        except BudgetExhausted as exc:
            censored_at = {"loop_red_edges_private": source["loop_red_edges_private"],
                           "gate": str(exc), "completed_action_cells_for_error": len(cells)}
            break
        rows.append({"loop_red_edges_private": source["loop_red_edges_private"],
                     "candidate_error_red_edges_private": edges, "winding_vectors": source["winding_vectors"],
                     "prior_j8d_control": is_control,
                     "projected_first_terms": source["projected_exact_first_terms"],
                     "selected_first_mass": source["selected_allplus_first_mass"], "cells": cells})
    complete = censored_at is None and len(rows) == 54 and sum(len(row["cells"]) for row in rows) == 108
    projected_total_orbit = (usage["first_orbit_moments"] + usage["second_singleton_orbit_moments"]
                             + usage["projected_higher_orbit_moments"])
    projected_total_relations = usage["algebraic_relation_probes"] + usage["projected_higher_relation_probes"]
    all_site_gates = complete and all(cell["complete_law_site_gate_pass"] for row in rows for cell in row["cells"])
    full_law_cap_pass = complete and all_site_gates and projected_total_orbit <= budget["max_orbit_moment_terms"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "all_remaining_support_cost_closed" if complete else "cost_preflight_censored",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "candidate_count": 51, "replay_control_count": 3,
            "completed_error_count": len(rows), "completed_action_cells": sum(len(row["cells"]) for row in rows),
            "censored_at": censored_at, "all_complete_law_site_gates_pass": all_site_gates,
            "projected_all_error_orbit_terms": projected_total_orbit,
            "projected_all_error_relation_probes": projected_total_relations,
            "full_law_within_existing_cap": full_law_cap_pass, "rows": rows,
            "counters": usage,
            "claim_boundary": "Exact one-site second-charge means and relation-aware structural cost only for 51 previously untested plus three replay L=2 same-first-flux errors and two fixed actions. Higher-order moments and complete second laws are not computed; no full-IID, logical-risk, noisy-JIT or threshold inference.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
