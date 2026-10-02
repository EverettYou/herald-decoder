"""Audit exact Z-character reuse and nonselective batching cost for 54 loops."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment, orbit_z_expectation
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8f-orbit-character-reuse-audit-2026-09-27.json"
RESULT = LAB / "results/j8f-orbit-character-reuse-audit-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8d_result": LAB / "results/j8d-winding-class-second-law-witness-2026-09-27.json",
    "j8e_result": LAB / "results/j8e-remaining-support-second-law-cost-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "orbit_source": LAB / "scripts/run_j6m_periodic_operator_ground_orbit.py",
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
           ("j8c_result", "j8d_result", "j8e_result", "j7m_result", "j6l_result", "j6m_result")}
    assert old["j8c_result"]["status"] == "support_geometry_cost_matrix_closed"
    assert old["j8d_result"]["status"] == "winding_class_second_law_witness_closed"
    assert old["j8e_result"]["status"] == "cost_preflight_censored"
    assert spec["actions"] == [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
    assert spec["base_error_private"] == [0, 4, 3]
    branches = [branch for branch in old["j8c_result"]["new_support_branches"] if branch["cycle_length"] == 8]
    assert len(branches) == 1 and len(branches[0]["rows"]) == 54
    source_rows = branches[0]["rows"]
    assert len({tuple(row["candidate_error_red_edges_private"]) for row in source_rows}) == 54
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    char_cache: dict[int, int] = {}
    signature_cache: dict[int, int] = {}
    projected_characters: set[int] = set()
    usage = {"nominal_first_terms": 0, "nominal_singleton_terms": 0,
             "nominal_higher_terms": 0, "relation_index_builds": 0,
             "relation_lookups": 0, "direct_moment_replay_checks": 0,
             "complete_second_laws": 0, "histories": 0, "schedule_arms": 0, "bootstraps": 0}

    def signature(zmask: int) -> int:
        if zmask not in signature_cache:
            signature_cache[zmask] = sum(parity(zmask & flip) << i for i, flip in enumerate(flips))
        return signature_cache[zmask]

    def character(zmask: int) -> int:
        if zmask not in char_cache:
            if len(char_cache) >= budget["max_unique_orbit_characters"]:
                raise BudgetExhausted("unique_orbit_character_cap")
            char_cache[zmask] = orbit_z_expectation(zmask, flips)
        return char_cache[zmask]

    def exact_value(factors) -> int:
        sign, zmask, _ = compose(factors)
        answer = sign * character(zmask)
        if usage["direct_moment_replay_checks"] < budget["direct_moment_replay_checks"]:
            assert answer == moment(factors, flips)
            usage["direct_moment_replay_checks"] += 1
        return answer

    rows = []
    censored_at = None
    prior_singletons = {tuple(row["candidate_error_red_edges_private"]): row
                        for row in old["j8e_result"]["rows"]}
    prior_controls = {tuple(row["error_edges_private"]): row
                      for row in old["j8d_result"]["rows"][1:]}
    assert len(prior_singletons) == 40 and len(prior_controls) == 3
    for source in source_rows:
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
        try:
            first_sum = sum(exact_value(subset) for subset in first_subsets)
            usage["nominal_first_terms"] += len(first_subsets)
            assert Fraction(first_sum, 1 << len(first_variable)) == Fraction(source["selected_allplus_first_mass"]) > 0
            relation_index = {}
            for subset in first_subsets:
                _, zmask, _ = compose(subset)
                relation_index.setdefault(signature(zmask), subset)
            usage["relation_index_builds"] += len(first_subsets)
            cells = []
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
                    usage["relation_lookups"] += 1
                    if usage["relation_lookups"] > budget["max_relation_lookups"]:
                        raise BudgetExhausted("relation_lookup_cap")
                    subset = relation_index.get(signature(product[1]))
                    if subset is not None:
                        relation = exact_value([product, *subset])
                        assert relation in (-1, 1)
                        return "operator_relation", Fraction(relation) if singleton else None
                    keys = [compose([*first, product])[1] for first in first_subsets]
                    if singleton:
                        usage["nominal_singleton_terms"] += len(keys)
                        total = sum(exact_value([*first, product]) for first in first_subsets)
                        return "character_sum", Fraction(total, first_sum)
                    usage["nominal_higher_terms"] += len(keys)
                    projected_characters.update(keys)
                    return "projected_character_sum", None

                singles = {site: structural((site,), singleton=True)[1] for site in eligible_second}
                assert all(value in (-1, 0, 1) for value in singles.values())
                variable = sorted(site for site, value in singles.items() if value == 0)
                if tuple(edges) in prior_singletons:
                    old_cell = prior_singletons[tuple(edges)]["cells"][action_index]
                    assert variable == old_cell["variable_second_sites_private"]
                if tuple(edges) in prior_controls:
                    old_cell = prior_controls[tuple(edges)]["cells"][action_index]
                    assert variable == old_cell["variable_second_sites_private"]
                if len(variable) <= budget["max_variable_second_sites_per_cell"]:
                    for order in range(2, len(variable) + 1):
                        for group in itertools.combinations(variable, order):
                            structural(group, singleton=False)
                cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                              "variable_second_sites_private": variable,
                              "complete_law_site_gate_pass": len(variable) <= budget["max_variable_second_sites_per_cell"]})
                if time.process_time() - started >= budget["max_cpu_seconds"]:
                    raise BudgetExhausted("cpu_cap")
            rows.append({"loop_red_edges_private": source["loop_red_edges_private"],
                         "candidate_error_red_edges_private": edges, "winding_vectors": source["winding_vectors"],
                         "first_public_mass": source["selected_allplus_first_mass"], "cells": cells})
        except BudgetExhausted as exc:
            censored_at = {"loop_red_edges_private": source["loop_red_edges_private"], "gate": str(exc)}
            break
    complete = censored_at is None and len(rows) == 54 and sum(len(row["cells"]) for row in rows) == 108
    assert usage["complete_second_laws"] == usage["histories"] == usage["schedule_arms"] == usage["bootstraps"] == 0
    all_sites_fit = complete and all(cell["complete_law_site_gate_pass"] for row in rows for cell in row["cells"])
    effective_unique = len(set(char_cache) | projected_characters)
    compressed_feasible = complete and all_sites_fit and effective_unique <= budget["max_unique_orbit_characters"]
    batch_feasible_without_reuse = old["j8e_result"]["projected_all_error_orbit_terms"] <= budget["max_legacy_expanded_terms"]
    assert not batch_feasible_without_reuse
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "orbit_character_reuse_cost_closed" if complete else "orbit_character_reuse_cost_censored",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "completed_supports": len(rows), "completed_action_cells": sum(len(row["cells"]) for row in rows),
            "j8e_singleton_replay_supports": sum(tuple(row["candidate_error_red_edges_private"]) in prior_singletons for row in rows),
            "j8d_control_replay_supports": sum(tuple(row["candidate_error_red_edges_private"]) in prior_controls for row in rows),
            "censored_at": censored_at, "all_complete_law_site_gates_pass": all_sites_fit,
            "unique_characters_evaluated": len(char_cache), "projected_unique_characters_for_all_groups": effective_unique,
            "compressed_full_law_cost_within_existing_unique_work_cap": compressed_feasible,
            "legacy_expanded_prefix_terms": old["j8e_result"]["projected_all_error_orbit_terms"],
            "fixed_batching_without_reuse_within_total_expanded_cap": batch_feasible_without_reuse,
            "rows": rows, "counters": usage,
            "claim_boundary": "Exact first masses, second-site one-bit means and structural character-reuse cost on all 54 same-first-flux ideal L=2 supports if complete. No higher-order conditional expectations, complete second public laws, full-IID posterior, logical risk, noisy JIT or threshold computed. A reuse cost gate is not a new information result.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
