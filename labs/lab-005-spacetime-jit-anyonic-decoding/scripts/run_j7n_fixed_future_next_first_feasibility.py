"""Zero-Born four-cell next-first structure and current-engine work audit."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, eligible
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7d_cross_round_commutation_screen import cross_vacuum_anticommutes


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7n-fixed-future-next-first-feasibility-2026-09-26.json"
RESULT = LAB / "results/j7n-fixed-future-next-first-feasibility-2026-09-26.json"
INPUTS = {
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j7i_result": LAB / "results/j7i-same-future-total-action-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "commutation_source": LAB / "scripts/run_j7d_cross_round_commutation_screen.py",
    "full_law_source": LAB / "scripts/run_j7e_two_edge_complete_next_law.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_engine_cost(first_variables: int, second_variables: int,
                        eligible_next_sites: int, positive_prefixes: int) -> dict:
    """Frozen J7E exact() term-count formula, not an optimized lower bound."""
    denominator = 1 << (2 * first_variables + second_variables)
    one_site = 1 << (2 * first_variables + 2 * second_variables + 1)
    total = positive_prefixes * (denominator + eligible_next_sites * one_site)
    return {"per_prefix_denominator_terms": denominator,
            "per_next_site_one_bit_terms": one_site,
            "all_prefix_denominator_and_one_site_terms": total}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7m = json.loads(INPUTS["j7m_result"].read_text())
    j7i = json.loads(INPUTS["j7i_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    assert j7m["status"] == "five_site_complete_second_charge_law_closed"
    assert j7m["same_second_public_flux"]
    assert Fraction(j7m["first_public_mass"]) == Fraction(1, 4)
    assert j7i["status"] == "exact_same_future_total_action_law_closed"
    assert spec["public_actions"] == [cell["public_action_red_edges"]
                                      for cell in j7m["cells"]]
    assert spec["public_actions"] == [[0], [1, 30, 32, 34, 35]]
    assert spec["matched_later_fault_keys_private"] == [[0], [4]]
    assert set(tuple(cell["future_physical_red_edges_private"])
               for cell in j7i["cells"]) == {(0,), (4,)}
    red, sites, _flips, _pairs = setup(embedding, orbit)
    assert len(red) == 36 and len(sites) == 24
    physical, _ = red_boundary(red, spec["initial_physical_red_edges_private"])
    assert spec["initial_physical_red_edges_private"] == [0, 4, 3]
    matrix = []
    checked_pairs = 0
    for future in spec["matched_later_fault_keys_private"]:
        future_mask, _ = red_boundary(red, future)
        matched_flux = None
        for action, prior in zip(spec["public_actions"], j7m["cells"]):
            assert action == prior["public_action_red_edges"]
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            residual_edges = sorted(set(spec["initial_physical_red_edges_private"])
                                    ^ set(action))
            residual_check, second_flux = red_boundary(red, residual_edges)
            assert residual_check == residual
            assert second_flux == prior["second_public_flux"]
            final = residual ^ future_mask
            final_edges = sorted(set(residual_edges) ^ set(future))
            final_check, next_flux = red_boundary(red, final_edges)
            assert final_check == final
            if matched_flux is None:
                matched_flux = next_flux
            else:
                assert next_flux == matched_flux
            if action == [0]:
                reference = next(cell for cell in j7i["cells"]
                                 if cell["public_action_red_edges"] == [0]
                                 and cell["future_physical_red_edges_private"] == future)
                assert reference["final_red_edges_private"] == final_edges
                assert reference["final_public_flux"] == next_flux
            second_eligible = [site for site, bit in enumerate(second_flux)
                               if bit == 0]
            next_eligible = [site for site, bit in enumerate(next_flux)
                             if bit == 0]
            assert second_eligible == [site for site in range(24)
                                       if eligible(sites[site], residual)]
            assert next_eligible == [site for site in range(24)
                                     if eligible(sites[site], final)]
            second_ops = {site: conjugated_star(sites[site], residual)
                          for site in second_eligible}
            next_ops = {site: conjugated_star(sites[site], final)
                        for site in next_eligible}
            witnesses = []
            for second_site, second_op in second_ops.items():
                for next_site, next_op in next_ops.items():
                    checked_pairs += 1
                    if checked_pairs > budget["max_second_next_pair_checks"]:
                        raise RuntimeError("registered_second_next_pair_cap")
                    if cross_vacuum_anticommutes(second_op, next_op):
                        witnesses.append([second_site, next_site])
            assert len(prior["rows"]) == prior["positive_second_public_rows"]
            assert len(prior["rows"]) <= budget["max_positive_second_prefixes_total"]
            assert sum((Fraction(row["conditional_probability"])
                        for row in prior["rows"]), Fraction()) == 1
            for row in prior["rows"]:
                public = row["public"]
                assert set(public) == {"flux", "charge", "vacuum"}
                assert all(len(public[field]) == 24 for field in public)
                assert public["flux"] == second_flux
                assert public["vacuum"] == [1 - bit for bit in public["charge"]]
            k = len(prior["variable_second_sites_private"])
            cost = current_engine_cost(spec["first_variable_site_count"], k,
                                       len(next_eligible), len(prior["rows"]))
            matrix.append({"public_action_red_edges": action,
                           "future_physical_red_edges_private": future,
                           "final_red_edges_private": final_edges,
                           "next_public_flux": next_flux,
                           "positive_second_prefixes": len(prior["rows"]),
                           "second_variable_site_count": k,
                           "second_eligible_sites_private": second_eligible,
                           "next_eligible_sites_private": next_eligible,
                           "second_next_operator_pair_checks":
                               len(second_eligible) * len(next_eligible),
                           "second_next_anticommuting_pair_count": len(witnesses),
                           "first_anticommuting_witness_private":
                               witnesses[0] if witnesses else None,
                           "current_engine_work_projection": cost})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert len(matrix) == budget["max_actions"] * budget["max_future_keys"] == 4
    assert [row["positive_second_prefixes"] for row in matrix] == [2, 32, 2, 32]
    assert checked_pairs <= budget["max_second_next_pair_checks"]
    total_terms = sum(row["current_engine_work_projection"]
                      ["all_prefix_denominator_and_one_site_terms"] for row in matrix)
    prior_ceiling = spec["prior_exact_term_ceiling"]
    assert prior_ceiling == 65536
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "fixed_future_structural_cost_audit_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "matrix": matrix,
            "second_next_operator_pair_checks_total": checked_pairs,
            "current_engine_denominator_and_one_site_terms_total": total_terms,
            "prior_exact_term_ceiling": prior_ceiling,
            "current_engine_stage_fits_prior_ceiling": total_terms <= prior_ceiling,
            "interpretation_boundary": "Structural anticommutators are necessary-only openings; term totals are a projection of the current exact implementation, not a mathematical lower bound; no next-first Born law or risk/policy result",
            "counters": {"ordered_moment_terms_evaluated": 0,
                         "next_first_law_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
