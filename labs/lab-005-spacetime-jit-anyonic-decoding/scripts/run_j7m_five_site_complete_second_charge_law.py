"""Exact complete-second charge law for one preregistered equal-flux action pair."""

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
from run_j7e_two_edge_complete_next_law import full_law


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7m-five-site-complete-second-charge-law-2026-09-26.json"
RESULT = LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json"
INPUTS = {
    "j7l_result": LAB / "results/j7l-alternative-same-flux-loop-screen-2026-09-26.json",
    "j7k_result": LAB / "results/j7k-loop-action-charge-law-preflight-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7f_result": LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json",
    "full_law_source": LAB / "scripts/run_j7e_two_edge_complete_next_law.py",
    "exact_source": LAB / "scripts/run_j7b_future_fault_next_first_and_caller_gate.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "public_record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def law(rows: list[dict]) -> dict[tuple[int, ...], Fraction]:
    result: dict[tuple[int, ...], Fraction] = {}
    for row in rows:
        public = row["public"]
        assert set(public) == {"flux", "charge", "vacuum"}
        assert all(len(public[key]) == 24 for key in public)
        assert public["vacuum"] == [1 - bit for bit in public["charge"]]
        key = tuple(public["charge"])
        assert key not in result
        result[key] = Fraction(row["conditional_probability"])
    assert sum(result.values(), Fraction()) == 1
    return result


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7l = json.loads(INPUTS["j7l_result"].read_text())
    j7k = json.loads(INPUTS["j7k_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    j7f = json.loads(INPUTS["j7f_result"].read_text())
    assert j7l["status"] == "alternative_shortest_loop_screen_closed"
    assert j7l["passing_trivial_loop_count"] == 0
    assert j7k["loop_homologically_trivial"] and j7k["public_action_boundary_equal"]
    assert spec["public_actions"] == [[0], [1, 30, 32, 34, 35]]
    assert sorted(set(spec["public_actions"][0]) ^ set(spec["public_actions"][1])) == \
        sorted(j7k["loop_red_edges_private"])
    prior_loop = next(row for row in j7l["rows"] if row["loop_red_edges_private"] ==
                      sorted(j7k["loop_red_edges_private"]))
    assert prior_loop["variable_second_sites_private"] == [0, 17, 20, 21, 22]
    red, sites, flips, pairs = setup(embedding, orbit)
    assert len(red) == 36 and len(sites) == 24
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    frozen = next(row for row in j7f["rows"] if row["fixture"] == "three_edge_chain")
    first = frozen["first_public"]
    assert set(first) == {"flux", "charge", "vacuum"}
    assert first["flux"] == first_flux and first["charge"] == [0] * 24
    first_ops = [conjugated_star(sites[site], physical)
                 for site in spec["first_variable_sites_private"]]
    first_block = (first_ops, tuple(spec["first_bits"]))
    usage = {"ordered_moment_terms": 0, "second_rows": 0}
    first_mass = exact([first_block], flips, usage, budget, started)
    assert first_mass == Fraction(spec["first_mass"]) == Fraction(1, 4)
    cells = []
    try:
        for action, prior in zip(spec["public_actions"], j7k["action_rows"]):
            assert action == prior["public_action_red_edges"]
            action_mask, action_flux = red_boundary(red, action)
            residual = physical ^ action_mask
            residual_edges = sorted(set(spec["physical_red_edges_private"]) ^ set(action))
            residual_check, second_flux = red_boundary(red, residual_edges)
            assert residual_check == residual
            assert second_flux == [a ^ b for a, b in zip(first_flux, action_flux)]
            eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible == [site for site, bit in enumerate(second_flux) if bit == 0]
            variable, rows = full_law(
                blocks=[first_block], candidate_sites=eligible,
                error_mask=residual, flux=second_flux, sites=sites, flips=flips,
                usage=usage, budget=budget, started=started,
                variable_cap="max_variable_second_sites", row_key="second_rows")
            assert variable == prior["variable_second_sites_private"]
            assert len(rows) <= budget["max_positive_second_rows_per_action"]
            for row in rows:
                assert row["public"]["flux"] == second_flux
            conditional = law(rows)
            for marginal in prior["conditional_one_site_second_marginals_private"]:
                site = marginal["site"]
                plus = sum((mass for charge, mass in conditional.items()
                            if charge[site] == 0), Fraction())
                assert plus == Fraction(marginal["plus_probability"])
            cells.append({"public_action_red_edges": action,
                          "residual_red_edges_private": residual_edges,
                          "second_public_flux": second_flux,
                          "variable_second_sites_private": variable,
                          "positive_second_public_rows": len(rows),
                          "rows": rows})
        assert len(cells) == budget["max_actions"] == 2
        assert cells[0]["second_public_flux"] == cells[1]["second_public_flux"]
        assert cells[0]["second_public_flux"] == [a ^ b for a, b in zip(
            first_flux, j7k["action_rows"][0]["public_action_flux"])]
        left, right = (law(cell["rows"]) for cell in cells)
        assert len(left) == 2 and set(left.values()) == {Fraction(1, 2)}
        tv = sum((abs(left.get(key, Fraction()) - right.get(key, Fraction()))
                  for key in set(left) | set(right)), Fraction()) / 2
        assert 0 <= tv <= 1
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    except Censor as error:
        return {"schema_version": 1, "id": contract["id"],
                "status": "five_site_joint_law_censored", "reason": str(error),
                "contract_sha256": digest(CONTRACT),
                "pinned_input_checks_before": before,
                "first_public_mass": str(first_mass), "cells": cells,
                "usage": usage,
                "counters": {"next_first_law_evaluations": 0,
                             "stochastic_histories": 0,
                             "schedule_arm_evaluations": 0,
                             "bootstrap_replicates": 0}}
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "five_site_complete_second_charge_law_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "first_public": first, "first_public_mass": str(first_mass),
            "same_second_public_flux": True,
            "cells": cells,
            "exact_complete_second_public_total_variation": str(tv),
            "charge_laws_distinct": tv > 0,
            "one_site_marginal_replay": True,
            "usage": usage,
            "frozen_jit_policy_emits_toggled_action": "not_established",
            "counters": {"next_first_law_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "One finite ideal selected-record action-conditioned complete second charge law, not information gain, expected-risk reduction, policy-emitted JIT correction, noisy schedule benefit or threshold",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
