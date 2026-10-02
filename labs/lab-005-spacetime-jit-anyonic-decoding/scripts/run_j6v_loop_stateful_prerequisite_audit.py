"""Pinned, zero-sampling loop-geometry and multiround-interface audit."""

from __future__ import annotations

import ast
from collections import deque
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6v-loop-stateful-prerequisite-audit-2026-09-25.json"
RESULT = LAB / "results/j6v-loop-stateful-prerequisite-audit-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6q_runner": LAB / "scripts/run_j6q_alternate_path_operator_law_matrix.py",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shortest_path_without_edge(adjacency: dict, start: str, end: str, excluded: int):
    queue = deque([(start, (), (start,))])
    visited = {start}
    while queue:
        vertex, edges, vertices = queue.popleft()
        for neighbor, edge in sorted(adjacency[vertex], key=lambda pair: (pair[1], pair[0])):
            if edge == excluded or neighbor in visited:
                continue
            new_edges = (*edges, edge)
            new_vertices = (*vertices, neighbor)
            if neighbor == end:
                return new_edges, new_vertices
            visited.add(neighbor)
            queue.append((neighbor, new_edges, new_vertices))
    return None


def canonical_cycle(edges: tuple[int, ...]) -> tuple[int, ...]:
    return min(tuple(seq[index:] + seq[:index])
               for seq in (edges, edges[::-1])
               for index in range(len(seq)))


def function(tree: ast.AST, name: str) -> ast.FunctionDef:
    matches = [node for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, name
    return matches[0]


def call_names(node: ast.AST) -> set[str]:
    return {call.func.id if isinstance(call.func, ast.Name) else call.func.attr
            for call in ast.walk(node) if isinstance(call, ast.Call)
            for _ in [0] if isinstance(call.func, (ast.Name, ast.Attribute))}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    red = {int(q["lab004_red_edge_id"]): tuple(q["star_endpoints"])
           for q in embedding["physical_qubits"] if q["color"] == "red"}
    assert len(red) == 36 and all(len(set(pair)) == 2 for pair in red.values())
    adjacency: dict[str, list[tuple[str, int]]] = {}
    for edge, (left, right) in red.items():
        adjacency.setdefault(left, []).append((right, edge))
        adjacency.setdefault(right, []).append((left, edge))
    assert len(adjacency) == 24
    candidates = []
    for edge, (left, right) in sorted(red.items()):
        path = shortest_path_without_edge(adjacency, left, right, edge)
        if path is None:
            continue
        path_edges, vertices = path
        cycle_edges = (edge, *path_edges)
        assert len(cycle_edges) >= 3 and len(set(cycle_edges)) == len(cycle_edges)
        assert len(set(vertices)) == len(vertices)
        candidates.append((len(cycle_edges), canonical_cycle(cycle_edges), cycle_edges, vertices))
    assert candidates
    _, canonical, edges, vertices = min(candidates)
    degree = {vertex: 0 for vertex in vertices}
    for edge in edges:
        for vertex in red[edge]:
            degree[vertex] += 1
    assert len(vertices) == len(edges) and set(degree.values()) == {2}
    assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]

    qtree = ast.parse(INPUTS["j6q_runner"].read_text())
    htree = ast.parse(INPUTS["frozen_integrated_history"].read_text())
    projector = function(qtree, "projection_probability")
    builder = function(htree, "build_integrated_d4_history_from_draws")
    provider = function(htree, "provide_action_conditioned_second_record")
    projector_args = [arg.arg for arg in projector.args.args]
    builder_args = [arg.arg for arg in builder.args.kwonlyargs]
    provider_args = [arg.arg for arg in provider.args.args]
    builder_calls = call_names(builder)
    provider_calls = call_names(provider)
    assert projector_args == ["first_ops", "first_outcomes", "second_ops", "second_outcomes", "flips"]
    assert "observation_from_error_edges" in builder_calls
    assert "sample_postflux_charge_outcomes" in provider_calls
    assert builder_args.index("transition_edge_faults") < builder_args.index("first_observation_seeds")
    assert provider_args == ["history", "invocation"]
    assert not any("action" in arg or "correction" in arg for arg in builder_args)
    assert "observation_from_error_edges" not in provider_calls
    assert "project_hidden_state" not in provider_calls
    third_block = "third_ops" in projector_args
    prior_action = any("action" in arg or "correction" in arg for arg in builder_args)
    next_first_update = "observation_from_error_edges" in provider_calls
    next_hidden_update = "project_hidden_state" in provider_calls
    stateful_present = all((third_block, prior_action, next_first_update, next_hidden_update))
    return {
        "schema_version": 1, "id": contract["id"],
        "status": "passed_two_prerequisite_diagnostics_stateful_kernel_absent",
        "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
        "simple_loop_geometry": {
            "minimum_cycle_length": len(edges),
            "canonical_red_edge_ids_private": list(canonical),
            "witness_red_edge_ids_private": list(edges),
            "witness_vertices_private": list(vertices),
            "all_red_edges_deleted_once": len(red),
            "cycle_candidates_found": len(candidates),
            "unique_edges_and_vertices": True, "all_witness_vertex_degrees_two": True,
            "claim_boundary": "Graph incidence only; no flux, charge, Born law or winding class inferred"
        },
        "stateful_multiround_interface": {
            "three_block_projector_signature_present": third_block,
            "builder_accepts_prior_action": prior_action,
            "provider_updates_next_first_observation": next_first_update,
            "provider_updates_hidden_projector_state": next_hidden_update,
            "action_feedback_kernel_present": stateful_present,
            "first_missing_interface": "ordered third projector block plus action-conditioned postselected state carried into next first observation",
            "claim_boundary": "Pinned source/data-flow audit only; absence in this caller does not prove physical D4 feedback absent"
        },
        "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0, "bootstrap_replicates": 0},
        "cpu_seconds": time.process_time() - started,
        "next_gate": "Preregister a capped exact ideal simple-loop first/action/second law and a separate action-conditioned three-block projector-state propagation fixture before any numeric multi-round kernel or noisy schedule sampling"
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
