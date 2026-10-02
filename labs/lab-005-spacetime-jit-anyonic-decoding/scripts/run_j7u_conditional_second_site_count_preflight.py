"""Four-cell exact one-site preflight under the frozen first public record."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7b_future_fault_next_first_and_caller_gate import Censor, exact


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7u-conditional-second-site-count-preflight-2026-09-27.json"
RESULT = LAB / "results/j7u-conditional-second-site-count-preflight-2026-09-27.json"
INPUTS = {
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "boundary_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "exact_source": LAB / "scripts/run_j7b_future_fault_next_first_and_caller_gate.py",
    "ordered_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
    "full_law_source": LAB / "scripts/run_j7e_two_edge_complete_next_law.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    prior = json.loads(INPUTS["j7t_result"].read_text())
    source = json.loads(INPUTS["j7m_result"].read_text())
    assert prior["status"] == "peer_candidates_identified"
    peers = prior["selected_peer_initial_errors_private"]
    assert peers == spec["private_peer_initial_errors"] and len(peers) == 2
    assert source["first_public"]["charge"] == [0] * 24
    assert source["first_public"]["vacuum"] == [1] * 24
    assert [cell["public_action_red_edges"] for cell in source["cells"]] == spec["public_actions"]
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    red, sites, flips, pairs = setup(embedding, orbit)
    assert len(red) == 36 and len(sites) == 24
    usage = {"ordered_moment_terms": 0}
    rows = []
    for edges in peers:
        prior_row = next(row for row in prior["candidate_rows"]
                         if row["candidate_initial_error_red_edges_private"] == edges)
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == source["first_public"]["flux"]
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(mean != -1 for mean in means.values())
        variable_first = sorted(site for site, mean in means.items() if mean == 0)
        assert len(variable_first) == prior_row["first_variable_site_count_private"] == 4
        first_ops = [conjugated_star(sites[site], physical) for site in variable_first]
        first_block = (first_ops, (1,) * len(first_ops))
        first_mass = exact([first_block], flips, usage, budget, started)
        assert first_mass == Fraction(prior_row["selected_first_public_mass_given_candidate"])
        assert first_mass == Fraction(1, 16)
        cells = []
        for action, frozen_cell in zip(spec["public_actions"], source["cells"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            residual_edges = sorted(set(edges) ^ set(action))
            residual_mask, second_flux = red_boundary(red, residual_edges)
            assert residual_mask == residual
            assert second_flux == frozen_cell["second_public_flux"]
            second_eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert second_eligible == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(second_eligible) == budget["second_eligible_sites_per_cell"] == 22
            marginals, variable = {}, []
            for site in second_eligible:
                op = conjugated_star(sites[site], residual)
                plus = exact([first_block, ([op], (1,))], flips, usage,
                             budget, started) / first_mass
                assert 0 <= plus <= 1
                marginals[str(site)] = str(plus)
                if plus not in (0, 1):
                    variable.append(site)
            cells.append({"public_action_red_edges": action,
                          "second_public_flux": second_flux,
                          "second_eligible_site_count": len(second_eligible),
                          "charge_zero_marginals_given_first": marginals,
                          "variable_second_sites_private": variable,
                          "variable_second_site_count": len(variable)})
        k0, k1 = [cell["variable_second_site_count"] for cell in cells]
        projected = 3 * (1 << 4) + 44 * (1 << 9) + (1 << (8 + 2*k0)) + (1 << (8 + 2*k1))
        rows.append({"initial_error_red_edges_private": edges,
                     "first_variable_sites_private": variable_first,
                     "selected_first_public_mass": str(first_mass),
                     "cells": cells,
                     "projected_frozen_full_law_terms": projected,
                     "under_inherited_full_law_term_ceiling": projected < budget["inherited_full_law_term_ceiling"]})
    assert len(rows) == 2 and sum(len(row["cells"]) for row in rows) == 4
    assert usage["ordered_moment_terms"] == 2 * 16 + 4 * 22 * 512 == 45088
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "conditional_second_site_count_preflight_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "four_cells_checked": 4, "rows": rows, "counters": {
                "ordered_moment_terms": usage["ordered_moment_terms"],
                "complete_second_law_evaluations": 0,
                "new_stochastic_histories": 0, "schedule_arm_evaluations": 0,
                "bootstrap_replicates": 0},
            "claim_boundary": "Only exact one-site second marginals and current-engine full-law cost projections conditional on one selected complete first record. No complete joint second law, error mutual information, unconditional risk, or policy benefit.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
