"""Bounded new-support and changed-geometry prerequisite matrix."""

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
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability  # noqa: E402
from run_j6x_full_first_dephasing_new_third import sector_sites  # noqa: E402
from run_j7a_postselected_next_first_limiting_fixtures import setup  # noqa: E402


CONTRACT = LAB / "manifests/j8c-support-geometry-cost-matrix-2026-09-27.json"
RESULT = LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json"
INPUTS = {
    "r6af_contract": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json",
    "j7l_result": LAB / "results/j7l-alternative-same-flux-loop-screen-2026-09-26.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j8b_result": LAB / "results/j8b-alternate-first-complete-second-laws-2026-09-27.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "topology_source": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_honeycomb.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "probability_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
    "boundary_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simple_cycles(lattice, length: int, cap: int) -> list[tuple[int, ...]]:
    adjacency = [[] for _ in range(lattice.vertex_count)]
    for edge_id, (left, right) in enumerate(lattice.edge_vertices):
        left, right = int(left), int(right)
        adjacency[left].append((right, edge_id))
        adjacency[right].append((left, edge_id))
    found = set()

    def walk(start, here, vertices, edges):
        if len(edges) == length:
            if here == start:
                found.add(tuple(sorted(edges)))
                assert len(found) <= cap
            return
        for neighbor, edge_id in adjacency[here]:
            if neighbor == start:
                if len(edges) == length - 1:
                    walk(start, start, vertices, edges + (edge_id,))
            elif neighbor not in vertices and len(edges) < length - 1:
                walk(start, neighbor, vertices | {neighbor}, edges + (edge_id,))

    for start in range(lattice.vertex_count):
        walk(start, start, {start}, ())
    return sorted(found)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {key: digest(path) == contract["pinned_inputs"][key + "_sha256"]
              for key, path in INPUTS.items()}
    assert all(before.values()), before
    old = {key: json.loads(INPUTS[key].read_text()) for key in
           ("r6af_contract", "j7l_result", "j7m_result", "j8b_result", "j6l_result", "j6m_result")}
    assert "IID red-X edge errors" in old["r6af_contract"]["frozen_model"]["physical_channel"]
    assert old["j8b_result"]["complete_second_law_cells"] == 96
    assert old["j8b_result"]["different_alternate_candidate_action_cells"] == 0
    assert spec["base_error_private"] == [0, 4, 3]
    assert spec["new_cycle_lengths"] == [4, 8]
    lattice = paper_periodic_honeycomb(2)
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert (lattice.vertex_count, lattice.edge_count, len(red), len(sites)) == (24, 36, 36, 24)
    for edge_id in range(36):
        blue, green = (int(x) for x in lattice.edge_vertices[edge_id])
        assert red[edge_id]["star_endpoints"] == [f"blue:{blue}", f"green:{green}"]
    replay_six = simple_cycles(lattice, 6, budget["max_cycles_per_length"])
    expected_six = sorted(tuple(row["loop_red_edges_private"]) for row in old["j7l_result"]["rows"])
    assert replay_six == expected_six and len(replay_six) == 12
    base_mask, base_flux = red_boundary(red, spec["base_error_private"])
    assert base_flux == old["j7m_result"]["first_public"]["flux"]
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    branches = []
    projected_terms = 0
    for length in spec["new_cycle_lengths"]:
        cycles = simple_cycles(lattice, length, budget["max_cycles_per_length"])
        rows = []
        for cycle in cycles:
            loop_mask = np.zeros(36, dtype=np.bool_)
            loop_mask[list(cycle)] = True
            analysis = generate_loop_constraints(lattice, loop_mask)
            assert len(analysis.components) == 1
            component = analysis.components[0]
            assert component.nonbranching_closed and tuple(component.edges) == cycle
            candidate = sorted(set(spec["base_error_private"]) ^ set(cycle))
            error_mask, flux = red_boundary(red, candidate)
            assert error_mask == base_mask ^ red_boundary(red, list(cycle))[0]
            assert flux == base_flux
            eligible, means = sector_sites(sites, error_mask, flips, pairs)
            assert eligible == [i for i, bit in enumerate(flux) if bit == 0]
            variable = sorted(i for i, value in means.items() if value == 0)
            conflict = any(value == -1 for value in means.values())
            cost = 0 if conflict else 1 << len(variable)
            projected_terms += cost
            rows.append({"loop_red_edges_private": list(cycle),
                         "winding_vectors": [list(item) for item in component.winding_vectors],
                         "homologically_trivial": component.homologically_trivial,
                         "candidate_error_red_edges_private": candidate,
                         "candidate_weight": len(candidate),
                         "same_full_first_flux": True,
                         "first_variable_sites_private": variable,
                         "deterministic_minus_conflict_with_allplus": conflict,
                         "projected_exact_first_terms": cost,
                         "selected_allplus_first_mass": None})
            assert time.process_time() - started < budget["max_cpu_seconds"]
        branches.append({"cycle_length": length, "cycle_count": len(rows), "rows": rows})
    projected_max_v = max((len(row["first_variable_sites_private"]) for branch in branches
                           for row in branch["rows"] if not row["deterministic_minus_conflict_with_allplus"]),
                          default=0)
    mass_gate = projected_terms <= budget["max_ordered_first_terms"] and projected_max_v <= budget["max_first_variable_sites"]
    used_terms = 0
    if mass_gate:
        for branch in branches:
            for row in branch["rows"]:
                if row["deterministic_minus_conflict_with_allplus"]:
                    row["selected_allplus_first_mass"] = "0"
                    continue
                error_mask, _ = red_boundary(red, row["candidate_error_red_edges_private"])
                variable = row["first_variable_sites_private"]
                ops = [conjugated_star(sites[site], error_mask) for site in variable]
                mass = ordered_probability([(ops, (1,) * len(ops))], flips)
                assert 0 <= mass <= 1
                row["selected_allplus_first_mass"] = str(mass)
                used_terms += 1 << len(ops)
                assert used_terms <= budget["max_ordered_first_terms"]
                assert time.process_time() - started < budget["max_cpu_seconds"]
        assert used_terms == projected_terms
    larger = paper_periodic_honeycomb(spec["larger_geometry_size"])
    assert spec["larger_geometry_size"] == 3
    assert (larger.vertex_count, larger.edge_count) == (54, 81)
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {key: digest(path) == contract["pinned_inputs"][key + "_sha256"]
             for key, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "support_geometry_cost_matrix_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "six_cycle_replay_count": len(replay_six), "new_support_branches": branches,
            "new_support_projected_first_terms": projected_terms,
            "new_support_projected_max_first_variable_sites": projected_max_v,
            "new_support_exact_mass_gate_pass": mass_gate,
            "larger_geometry_topology_only": {"paper_size": 3, "vertices": larger.vertex_count,
                                              "red_edges": larger.edge_count,
                                              "ideal_orbit_and_sequential_instrument_available": False,
                                              "reason": "J6L/J6M exact operator orbit and public-instrument pins exist only at paper L=2; no L=3 physical or conditional-law evaluation in this tick."},
            "counters": {"ordered_first_terms": used_terms, "complete_second_laws": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Topology, selected-first structural cost, and optionally exact first mass for shortest new loop-support classes at fixed L=2; L=3 geometry size is topology-only. No second public law, full-IID posterior, unconditional logical risk, noisy JIT or threshold inference.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
