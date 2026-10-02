"""Exact topology/action/one-site marginal gate for a same-flux loop toggle."""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
LAB004_SCRIPTS = ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts"
sys.path.insert(0, str(LAB004_SCRIPTS))

from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb  # noqa: E402
from run_j6n_sequential_local_projector_moments import conjugated_star  # noqa: E402
from run_j6o_full_binary_sequential_public_record import red_boundary  # noqa: E402
from run_j6x_full_first_dephasing_new_third import sector_sites  # noqa: E402
from run_j7a_postselected_next_first_limiting_fixtures import setup  # noqa: E402
from run_j7b_future_fault_next_first_and_caller_gate import Censor, exact  # noqa: E402


CONTRACT = LAB / "manifests/j7k-loop-action-charge-law-preflight-2026-09-26.json"
RESULT = LAB / "results/j7k-loop-action-charge-law-preflight-2026-09-26.json"
INPUTS = {
    "j7j_result": LAB / "results/j7j-charge-risk-estimand-feasibility-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7f_result": LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json",
    "token_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "lab004_topology_source": LAB004_SCRIPTS / "d4_honeycomb.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7j = json.loads(INPUTS["j7j_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    j7f = json.loads(INPUTS["j7f_result"].read_text())
    assert j7j["status"] == "same_flux_geometry_candidate_risk_not_identified"
    assert j7j["loop_public_flux_zero"]
    loop = j7j["loop_red_edges_private"]
    assert loop == [0, 1, 32, 30, 34, 35]
    assert spec["public_actions"] == [j7j["baseline_public_action"],
                                       j7j["loop_toggled_public_action"]]
    lattice = paper_periodic_honeycomb(2)
    red, sites, flips, pairs = setup(embedding, orbit)
    assert lattice.edge_count == len(red) == 36
    assert lattice.vertex_count == 24
    edge_bijection = []
    for edge_id in range(36):
        blue, green = (int(x) for x in lattice.edge_vertices[edge_id])
        actual = red[edge_id]["star_endpoints"]
        expected = [f"blue:{blue}", f"green:{green}"]
        assert actual == expected, (edge_id, actual, expected)
        edge_bijection.append(edge_id)
    loop_mask = np.zeros(lattice.edge_count, dtype=np.bool_)
    loop_mask[loop] = True
    analysis = generate_loop_constraints(lattice, loop_mask)
    assert len(analysis.components) == 1
    component = analysis.components[0]
    assert component.nonbranching_closed
    assert list(component.edges) == sorted(loop)
    loop_trivial = component.homologically_trivial
    if loop_trivial:
        assert len(analysis.constraints) == 2
    else:
        assert not analysis.constraints
    action_masks = []
    action_fluxes = []
    for action in spec["public_actions"]:
        mask, flux = red_boundary(red, action)
        action_masks.append(mask)
        action_fluxes.append(flux)
    assert action_masks[0] != action_masks[1]
    assert action_fluxes[0] == action_fluxes[1]
    assert set(spec["public_actions"][0]) ^ set(spec["public_actions"][1]) == set(loop)
    source_tree = ast.parse(INPUTS["token_source"].read_text())
    token_def = next(node for node in source_tree.body
                     if isinstance(node, ast.FunctionDef) and node.name == "make_token")
    token_args = {arg.arg for arg in token_def.args.kwonlyargs}
    assert {"action_edges", "allowed_actions", "action_mask"} <= token_args
    assert any(isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
               and node.left.id == "action_edges" and
               any(isinstance(comparator, ast.Name) and comparator.id == "allowed_actions"
                   for comparator in node.comparators)
               for node in ast.walk(token_def))
    frozen = next(row for row in j7f["rows"] if row["fixture"] == "three_edge_chain")
    first = frozen["first_public"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    assert first["flux"] == first_flux
    assert first["charge"] == [0] * 24
    first_ops = [conjugated_star(sites[site], physical)
                 for site in spec["first_variable_sites_private"]]
    first_block = (first_ops, tuple(spec["first_bits"]))
    usage = {"ordered_moment_terms": 0}
    first_mass = exact([first_block], flips, usage, budget, started)
    assert first_mass == Fraction(spec["first_mass"]) == Fraction(1, 4)
    action_rows = []
    try:
        for action, action_mask, action_flux in zip(
                spec["public_actions"], action_masks, action_fluxes):
            residual = physical ^ action_mask
            residual_edges = sorted(set(spec["physical_red_edges_private"]) ^ set(action))
            actual_residual, residual_flux = red_boundary(red, residual_edges)
            assert residual == actual_residual
            eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible == [site for site, bit in enumerate(residual_flux) if bit == 0]
            assert len(eligible) <= budget["max_eligible_second_sites_per_action"]
            marginals = []
            for site in eligible:
                op = conjugated_star(sites[site], residual)
                plus = exact([first_block, ([op], (1,))], flips,
                             usage, budget, started) / first_mass
                assert 0 <= plus <= 1
                marginals.append({"site": site, "plus_probability": str(plus)})
            variable = [row["site"] for row in marginals
                        if Fraction(row["plus_probability"]) not in (0, 1)]
            action_rows.append({"public_action_red_edges": action,
                                "public_action_flux": action_flux,
                                "residual_red_edges_private": residual_edges,
                                "eligible_second_sites_private": eligible,
                                "conditional_one_site_second_marginals_private": marginals,
                                "variable_second_sites_private": variable,
                                "complete_second_law_site_cap_pass": len(variable) <=
                                    budget["max_variable_second_sites"]})
    except Censor as error:
        return {"schema_version": 1, "id": contract["id"],
                "status": "censored_at_registered_cap", "reason": str(error),
                "contract_sha256": digest(CONTRACT),
                "pinned_input_checks_before": before,
                "topology_edge_bijection_count": len(edge_bijection),
                "loop_winding_vectors": [list(x) for x in component.winding_vectors],
                "action_rows": action_rows, "usage": usage,
                "counters": {"joint_second_or_next_law_evaluations": 0,
                             "stochastic_histories": 0,
                             "schedule_arm_evaluations": 0,
                             "bootstrap_replicates": 0}}
    assert len(action_rows) == budget["max_actions"] == 2
    assert time.process_time() - started <= budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "loop_action_exact_preflight_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "topology_edge_bijection_count": len(edge_bijection),
            "loop_red_edges_private": loop,
            "loop_nonbranching_closed": component.nonbranching_closed,
            "loop_winding_vectors": [list(x) for x in component.winding_vectors],
            "loop_homologically_trivial": loop_trivial,
            "loop_colour_parity_constraints": len(analysis.constraints),
            "public_action_boundary_equal": True,
            "token_interface_can_whitelist_declared_actions": True,
            "frozen_jit_policy_emits_toggled_action": "not_established",
            "first_public_mass": str(first_mass),
            "action_rows": action_rows,
            "complete_second_law_site_cap_pass": all(row["complete_second_law_site_cap_pass"]
                                                     for row in action_rows),
            "usage": usage,
            "counters": {"joint_second_or_next_law_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Exact topology and conditional one-site marginals only; no complete joint charge law, charge information gain, logical-risk contrast, policy-emitted long correction, noisy JIT benefit or threshold",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
