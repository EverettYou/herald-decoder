"""Exhaustive shortest-loop action feasibility under the frozen J7K exact cap."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts"))

from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb  # noqa: E402
from run_j6n_sequential_local_projector_moments import conjugated_star  # noqa: E402
from run_j6o_full_binary_sequential_public_record import red_boundary  # noqa: E402
from run_j6x_full_first_dephasing_new_third import sector_sites  # noqa: E402
from run_j7a_postselected_next_first_limiting_fixtures import setup  # noqa: E402
from run_j7b_future_fault_next_first_and_caller_gate import Censor, exact  # noqa: E402


CONTRACT = LAB / "manifests/j7l-alternative-same-flux-loop-screen-2026-09-26.json"
RESULT = LAB / "results/j7l-alternative-same-flux-loop-screen-2026-09-26.json"
INPUTS = {
    "j7k_result": LAB / "results/j7k-loop-action-charge-law-preflight-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7f_result": LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json",
    "lab004_topology_source": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_honeycomb.py",
    "exact_source": LAB / "scripts/run_j7b_future_fault_next_first_and_caller_gate.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simple_six_cycles(lattice) -> list[tuple[int, ...]]:
    """All unique edge sets of graph-simple length-six cycles, in lexical order."""
    adjacency = [[] for _ in range(lattice.vertex_count)]
    for edge_id, (left, right) in enumerate(lattice.edge_vertices):
        left, right = int(left), int(right)
        adjacency[left].append((right, edge_id))
        adjacency[right].append((left, edge_id))
    cycles: set[tuple[int, ...]] = set()

    def walk(start: int, here: int, vertices: set[int], edges: tuple[int, ...]):
        if len(edges) == 6:
            if here == start:
                cycles.add(tuple(sorted(edges)))
            return
        for neighbor, edge_id in adjacency[here]:
            if neighbor == start:
                if len(edges) == 5:
                    walk(start, start, vertices, edges + (edge_id,))
            elif neighbor not in vertices and len(edges) < 5:
                walk(start, neighbor, vertices | {neighbor}, edges + (edge_id,))

    for start in range(lattice.vertex_count):
        walk(start, start, {start}, ())
    return sorted(cycles)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7k = json.loads(INPUTS["j7k_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    j7f = json.loads(INPUTS["j7f_result"].read_text())
    assert j7k["status"] == "loop_action_exact_preflight_closed"
    assert j7k["loop_homologically_trivial"] and j7k["public_action_boundary_equal"]
    lattice = paper_periodic_honeycomb(2)
    red, sites, flips, pairs = setup(embedding, orbit)
    assert lattice.edge_count == len(red) == 36
    assert lattice.vertex_count == 24
    for edge_id in range(36):
        blue, green = (int(x) for x in lattice.edge_vertices[edge_id])
        assert red[edge_id]["star_endpoints"] == [f"blue:{blue}", f"green:{green}"]
    cycles = simple_six_cycles(lattice)
    if len(cycles) > budget["max_unique_six_edge_cycles"]:
        raise Censor("registered_unique_six_edge_cycle_cap")
    assert tuple(spec["prior_j7k_cycle_sorted"]) in cycles
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    frozen = next(row for row in j7f["rows"] if row["fixture"] == "three_edge_chain")
    first = frozen["first_public"]
    assert first["flux"] == first_flux and first["charge"] == [0] * 24
    first_ops = [conjugated_star(sites[site], physical)
                 for site in spec["first_variable_sites_private"]]
    first_block = (first_ops, tuple(spec["first_bits"]))
    usage = {"ordered_moment_terms": 0}
    first_mass = exact([first_block], flips, usage, budget, started)
    assert first_mass == Fraction(spec["first_mass"]) == Fraction(1, 4)
    baseline_action = spec["baseline_public_action"]
    baseline_mask, baseline_flux = red_boundary(red, baseline_action)

    def marginal_row(action: list[int]) -> dict:
        action_mask, action_flux = red_boundary(red, action)
        residual = physical ^ action_mask
        residual_edges = sorted(set(spec["physical_red_edges_private"]) ^ set(action))
        actual_residual, residual_flux = red_boundary(red, residual_edges)
        assert residual == actual_residual
        eligible, _ = sector_sites(sites, residual, flips, pairs)
        assert eligible == [site for site, bit in enumerate(residual_flux) if bit == 0]
        assert len(eligible) <= budget["max_eligible_second_sites_per_action"]
        marginals = []
        for site in eligible:
            plus = exact([first_block, ([conjugated_star(sites[site], residual)], (1,))],
                         flips, usage, budget, started) / first_mass
            assert 0 <= plus <= 1
            marginals.append({"site": site, "plus_probability": str(plus)})
        variable = [row["site"] for row in marginals
                    if Fraction(row["plus_probability"]) not in (0, 1)]
        return {"public_action_red_edges": action,
                "public_action_flux": action_flux,
                "residual_red_edges_private": residual_edges,
                "eligible_second_sites_private": eligible,
                "conditional_one_site_second_marginals_private": marginals,
                "variable_second_sites_private": variable,
                "complete_second_law_site_cap_pass":
                    len(variable) <= budget["max_variable_second_sites"]}

    baseline = marginal_row(baseline_action)
    assert baseline["variable_second_sites_private"] == [0]
    assert baseline["public_action_flux"] == j7k["action_rows"][0]["public_action_flux"]
    rows = []
    for loop in cycles:
        loop_mask = np.zeros(36, dtype=np.bool_)
        loop_mask[list(loop)] = True
        analysis = generate_loop_constraints(lattice, loop_mask)
        assert len(analysis.components) == 1
        component = analysis.components[0]
        assert component.nonbranching_closed and list(component.edges) == list(loop)
        row = {"loop_red_edges_private": list(loop),
               "loop_winding_vectors": [list(x) for x in component.winding_vectors],
               "loop_homologically_trivial": component.homologically_trivial}
        if component.homologically_trivial:
            assert len(analysis.constraints) == 2
            action = sorted(set(baseline_action) ^ set(loop))
            candidate = marginal_row(action)
            assert candidate["public_action_flux"] == baseline_flux
            row.update(candidate)
        else:
            assert not analysis.constraints
            row["excluded_reason"] = "nontrivial_ground_state_relative_winding"
        rows.append(row)
    prior = next(row for row in rows if row["loop_red_edges_private"] ==
                 spec["prior_j7k_cycle_sorted"])
    assert prior["loop_homologically_trivial"]
    assert prior["variable_second_sites_private"] == [0, 17, 20, 21, 22]
    assert prior["public_action_red_edges"] == sorted(j7k["action_rows"][1]
                                                     ["public_action_red_edges"])
    assert prior["conditional_one_site_second_marginals_private"] == \
        j7k["action_rows"][1]["conditional_one_site_second_marginals_private"]
    assert baseline["conditional_one_site_second_marginals_private"] == \
        j7k["action_rows"][0]["conditional_one_site_second_marginals_private"]
    passing = [row for row in rows if row.get("complete_second_law_site_cap_pass")]
    assert time.process_time() - started <= budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "alternative_shortest_loop_screen_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "topology_edge_bijection_count": 36,
            "first_public_mass": str(first_mass),
            "baseline": baseline,
            "unique_simple_six_edge_cycle_count": len(cycles),
            "homologically_trivial_cycle_count": sum(row["loop_homologically_trivial"]
                                                     for row in rows),
            "passing_trivial_loop_count": len(passing),
            "selected_prospective_loop_red_edges_private":
                passing[0]["loop_red_edges_private"] if passing else None,
            "rows": rows,
            "usage": usage,
            "frozen_jit_policy_emits_selected_action": "not_established",
            "counters": {"joint_second_or_next_law_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Finite exact one-site feasibility only; no joint charge law, charge-information gain, expected-risk contrast, policy-emitted correction, noisy schedule benefit or threshold",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
