"""Complete the 5-bit exact second law from preregistered high-order moments."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7y_low_order_second_moments import commute, conditional_parity, subset_terms


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7z-higher-order-second-law-2026-09-27.json"
RESULT = LAB / "results/j7z-higher-order-second-law-2026-09-27.json"
INPUTS = {
    "j7y_contract": LAB / "manifests/j7y-low-order-second-moments-2026-09-27.json",
    "j7y_result": LAB / "results/j7y-low-order-second-moments-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j7v_result": LAB / "results/j7v-joint-second-walsh-reduction-2026-09-27.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7y_source": LAB / "scripts/run_j7y_low_order_second_moments.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def as_law(rows: list[dict]) -> dict[str, Fraction]:
    law = {key(row["public"]): Fraction(row["conditional_probability"]) for row in rows}
    assert len(law) == len(rows)
    assert all(value > 0 for value in law.values())
    assert sum(law.values(), Fraction()) == 1
    return law


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j7y_contract", "j7y_result", "j7m_result", "j7v_result", "j7t_result", "j6l_result", "j6m_result")}
    prior = old["j7y_result"]
    assert prior["status"] == "all_candidate_low_order_moments_closed"
    assert prior["candidate_count"] == 12 and prior["different_candidate_action_cells"] == 0
    assert old["j7y_contract"]["matrix"]["actions"] == spec["actions"]
    assert old["j7y_contract"]["matrix"]["variable_second_sites_by_action"] == spec["sites_by_action"]
    assert spec["sites_by_action"] == [[0], [0, 17, 20, 21, 22]]
    assert spec["base_error_private"] == [0, 4, 3]
    assert [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]] == spec["actions"]
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    assert old["j7m_result"]["first_public"]["vacuum"] == [1] * 24
    errors = [row["initial_error_red_edges_private"] for row in prior["rows"]]
    assert errors == [spec["base_error_private"]] + [
        row["candidate_initial_error_red_edges_private"] for row in old["j7t_result"]["candidate_rows"]]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    usage = {"orbit_moment_terms": 0, "ordered_projector_terms": 0}
    control_laws = [as_law(cell["rows"]) for cell in old["j7m_result"]["cells"]]
    peer_laws = {
        tuple(peer["initial_error_red_edges_private"]): [as_law(cell["rows"]) for cell in peer["cells"]]
        for peer in old["j7v_result"]["peer_rows"]}
    assert len(peer_laws) == 2
    rows = []
    for index, edges in enumerate(errors):
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in means.values())
        first_variable = sorted(site for site, value in means.items() if value == 0)
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_subsets, first_sum = subset_terms(first_ops, flips, usage, budget)
        assert Fraction(first_sum, 1 << len(first_ops)) == Fraction(prior["rows"][index]["first_public_mass"])
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
            selected_sites = spec["sites_by_action"][action_index]
            assert set(selected_sites) <= set(eligible_second)
            second_ops = {site: conjugated_star(sites[site], residual) for site in selected_sites}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
            low = prior["rows"][index]["cells"][action_index]
            assert low["public_action_red_edges"] == action and low["second_public_flux"] == second_flux
            moments = {tuple(row["sites"]): Fraction(row["parity_mean"]) for row in low["moments"]}
            assert len(moments) == (1 if action_index == 0 else 15)
            higher = []
            for order in range(3, len(selected_sites) + 1):
                for group in itertools.combinations(selected_sites, order):
                    value, derivation = conditional_parity(
                        [second_ops[site] for site in group], first_ops,
                        first_subsets, first_sum, flips, usage, budget)
                    moments[group] = value
                    higher.append({"sites": list(group), "parity_mean": str(value),
                                   "derivation": derivation})
            assert len(moments) == (1 << len(selected_sites)) - 1
            assert len(higher) == (0 if action_index == 0 else 16)
            assignments = []
            for bits in itertools.product((0, 1), repeat=len(selected_sites)):
                probability = sum((
                    value * (-1 if sum(bits[selected_sites.index(site)] for site in group) % 2 else 1)
                    for group, value in moments.items()), Fraction(1)) / (1 << len(selected_sites))
                assert 0 <= probability <= 1
                charge = [0] * 24
                for site, bit in zip(selected_sites, bits):
                    charge[site] = bit
                if probability:
                    assignments.append({"public": public_record(second_flux, charge),
                                        "conditional_probability": str(probability),
                                        "variable_charge_bits": list(bits)})
            law = as_law(assignments)
            if index == 0:
                assert law == control_laws[action_index]
            if tuple(edges) in peer_laws:
                assert law == peer_laws[tuple(edges)][action_index]
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "higher_order_moments": higher, "positive_public_rows": len(assignments),
                          "same_complete_law_as_base": law == control_laws[action_index],
                          "rows": assignments})
        rows.append({"initial_error_red_edges_private": edges,
                     "first_public_mass": str(Fraction(first_sum, 1 << len(first_ops))),
                     "cells": cells})
        assert time.process_time() - started < budget["max_cpu_seconds"]
    assert len(rows) == 13 and sum(len(row["cells"]) for row in rows) == 26
    assert sum(len(cell["higher_order_moments"]) for row in rows for cell in row["cells"]) == 208
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "all_candidate_higher_order_complete_laws_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "candidate_count": 12, "candidate_action_cells": 24,
            "different_complete_law_candidate_action_cells": sum(
                not cell["same_complete_law_as_base"] for row in rows[1:] for cell in row["cells"]),
            "rows": rows,
            "counters": {**usage, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Exact complete second public laws for only thirteen pre-existing private errors, one selected complete first record, two frozen actions and the ideal L=2 orbit. No full-IID information, unconditional logical risk, policy JIT effect, noisy schedule or threshold claim.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
