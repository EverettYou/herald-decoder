"""Exact full-second laws via parity-projector moments and Walsh inversion."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7b_future_fault_next_first_and_caller_gate import exact


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7v-joint-second-walsh-reduction-2026-09-27.json"
RESULT = LAB / "results/j7v-joint-second-walsh-reduction-2026-09-27.json"
INPUTS = {
    "j7u_result": LAB / "results/j7u-conditional-second-site-count-preflight-2026-09-27.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "orbit_source": LAB / "scripts/run_j6m_periodic_operator_ground_orbit.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "boundary_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "exact_source": LAB / "scripts/run_j7b_future_fault_next_first_and_caller_gate.py",
    "ordered_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(operators: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Compose sign*Z*A operators, preserving the ordered Z/flip phase."""
    sign, zmask, flip = 1, 0, 0
    for next_sign, next_z, next_flip in operators:
        sign *= next_sign * (-1 if parity(flip & next_z) else 1)
        zmask ^= next_z
        flip ^= next_flip
    return sign, zmask, flip


def one_law(*, edges, action, expected_flux, expected_variable, expected_marginals,
            source_first, red, sites, flips, pairs, usage, budget, started):
    physical, first_flux = red_boundary(red, edges)
    assert first_flux == source_first["flux"]
    first_eligible, first_means = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [site for site, bit in enumerate(first_flux) if bit == 0]
    assert all(mean != -1 for mean in first_means.values())
    variable_first = sorted(site for site, mean in first_means.items() if mean == 0)
    first_ops = [conjugated_star(sites[site], physical) for site in variable_first]
    first_block = (first_ops, (1,) * len(first_ops))
    denominator = exact([first_block], flips, usage, budget, started)
    expected_first_mass = Fraction(1, 4) if edges == [0, 4, 3] else Fraction(1, 16)
    assert denominator == expected_first_mass
    action_mask, _ = red_boundary(red, action)
    residual = physical ^ action_mask
    residual_edges = sorted(set(edges) ^ set(action))
    check_mask, second_flux = red_boundary(red, residual_edges)
    assert check_mask == residual and second_flux == expected_flux
    eligible, _ = sector_sites(sites, residual, flips, pairs)
    assert eligible == [site for site, bit in enumerate(second_flux) if bit == 0]
    assert len(eligible) == budget["eligible_second_sites_per_cell"] == 22
    variable = expected_variable
    assert len(variable) in (1, 5) and set(variable) <= set(eligible)
    operators = [conjugated_star(sites[site], residual) for site in variable]
    moments = {0: Fraction(1)}
    for subset in range(1, 1 << len(variable)):
        selected = [op for index, op in enumerate(operators) if (subset >> index) & 1]
        composite = compose(selected)
        assert compose([composite, composite]) == (1, 0, 0)
        assert moment(selected, flips) == moment([composite], flips)
        plus = exact([first_block, ([composite], (1,))], flips,
                     usage, budget, started) / denominator
        assert 0 <= plus <= 1
        moments[subset] = 2 * plus - 1
    reconstructed = []
    for bits in itertools.product((1, -1), repeat=len(variable)):
        probability = sum((moments[subset] *
                           (1 if not parity(sum(1 << index for index, bit in enumerate(bits)
                                                if bit == -1) & subset) else -1)
                           for subset in moments), Fraction()) / (1 << len(variable))
        assert 0 <= probability <= 1
        charge = [0] * 24
        for site, value in expected_marginals.items():
            if int(site) not in variable:
                assert Fraction(value) in (0, 1)
                charge[int(site)] = int(Fraction(value) == 0)
        for site, bit in zip(variable, bits):
            charge[site] = int(bit == -1)
        if probability:
            reconstructed.append({"public": public_record(second_flux, charge),
                                  "conditional_probability": str(probability),
                                  "variable_eigenvalues": list(bits)})
        if all(bit == 1 for bit in bits):
            direct = exact([first_block, (operators, bits)], flips,
                           usage, budget, started) / denominator
            assert direct == probability
    assert sum((Fraction(row["conditional_probability"]) for row in reconstructed),
               Fraction()) == 1
    for index, site in enumerate(variable):
        marginal = sum((Fraction(row["conditional_probability"])
                        for row in reconstructed if row["variable_eigenvalues"][index] == 1),
                       Fraction())
        assert str(marginal) == str(expected_marginals[str(site)])
    assert time.process_time() - started < budget["max_cpu_seconds"]
    return {"private_initial_error_red_edges": edges,
            "public_action_red_edges": action,
            "first_public_mass": str(denominator),
            "variable_first_sites_private": variable_first,
            "variable_second_sites_private": variable,
            "second_public_flux": second_flux,
            "positive_second_public_rows": len(reconstructed),
            "rows": reconstructed}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget, spec = contract["budget"], contract["matrix"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    previous = json.loads(INPUTS["j7u_result"].read_text())
    prior = json.loads(INPUTS["j7t_result"].read_text())
    control = json.loads(INPUTS["j7m_result"].read_text())
    assert previous["status"] == "conditional_second_site_count_preflight_closed"
    assert prior["selected_peer_initial_errors_private"] == spec["peer_errors_private"]
    assert [row["initial_error_red_edges_private"] for row in previous["rows"]] == spec["peer_errors_private"]
    assert [cell["public_action_red_edges"] for cell in control["cells"]] == spec["public_actions"]
    assert control["first_public"]["charge"] == [0] * 24
    assert control["first_public"]["vacuum"] == [1] * 24
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    red, sites, flips, pairs = setup(embedding, orbit)
    usage = {"ordered_moment_terms": 0}
    control_rows = []
    for control_cell in control["cells"]:
        variable = control_cell["variable_second_sites_private"]
        marginal = {str(site): ("1/2" if site in variable else "1")
                    for site, bit in enumerate(control_cell["second_public_flux"]) if bit == 0}
        calculated = one_law(edges=spec["control_error_private"],
                             action=control_cell["public_action_red_edges"],
                             expected_flux=control_cell["second_public_flux"],
                             expected_variable=variable, expected_marginals=marginal,
                             source_first=control["first_public"], red=red, sites=sites,
                             flips=flips, pairs=pairs, usage=usage, budget=budget,
                             started=started)
        old_rows = {json.dumps(row["public"], sort_keys=True): Fraction(row["conditional_probability"])
                    for row in control_cell["rows"]}
        new_rows = {json.dumps(row["public"], sort_keys=True): Fraction(row["conditional_probability"])
                    for row in calculated["rows"]}
        assert new_rows == old_rows
        control_rows.append({"public_action_red_edges": control_cell["public_action_red_edges"],
                             "replays_j7m_complete_second_law": True,
                             "positive_second_public_rows": calculated["positive_second_public_rows"]})
    peer_rows = []
    for previous_row in previous["rows"]:
        cells = []
        for prior_cell in previous_row["cells"]:
            cells.append(one_law(edges=previous_row["initial_error_red_edges_private"],
                                action=prior_cell["public_action_red_edges"],
                                expected_flux=prior_cell["second_public_flux"],
                                expected_variable=prior_cell["variable_second_sites_private"],
                                expected_marginals=prior_cell["charge_zero_marginals_given_first"],
                                source_first=control["first_public"], red=red, sites=sites,
                                flips=flips, pairs=pairs, usage=usage, budget=budget,
                                started=started))
        peer_rows.append({"initial_error_red_edges_private": previous_row["initial_error_red_edges_private"],
                          "cells": cells})
    assert len(control_rows) == 2 and len(peer_rows) == 2
    assert usage["ordered_moment_terms"] == budget["expected_ordered_moment_terms"] == 51816
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "complete_second_joint_laws_reconstructed_under_cap",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "control_replays": control_rows, "peer_rows": peer_rows,
            "counters": {"ordered_moment_terms": usage["ordered_moment_terms"],
                         "direct_full_row_replays": 6,
                         "stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Complete exact conditional second public laws for two restricted private initial-error peers under one selected full first record and two predeclared actions. No binary-error information calculation, full-IID posterior, unconditional logical risk or policy JIT result.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
