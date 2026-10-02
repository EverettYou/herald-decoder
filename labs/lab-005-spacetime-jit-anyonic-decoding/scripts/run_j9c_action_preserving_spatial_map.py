"""Find full-operator spatial maps preserving both public actions, then replay held-out laws."""

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j8b_alternate_first_complete_second_laws import law


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9c-action-preserving-spatial-map-2026-09-28.json"
RESULT = LAB / "results/j9c-action-preserving-spatial-map-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def keyed(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def mapped_public(record: dict, vertex_map: dict[int, int]) -> dict:
    result = {}
    for field in ("flux", "charge", "vacuum"):
        bits = [0] * 24
        for old, bit in enumerate(record[field]):
            bits[vertex_map[old]] = bit
        result[field] = bits
    return result


def run() -> dict:
    start = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    geometry = json.loads((LAB / spec["geometry_result"]).read_text())
    source = json.loads((LAB / spec["source_result"]).read_text())
    assert source["status"] == "deterministic_first_collision_census_verified"
    assert len(source["rows"]) == 12
    assert spec["public_actions_red_edges"] == [[0], [1, 30, 32, 34, 35]]
    # Lab 004's flux-boundary vertex labels are not the kagome star-center
    # labels. Spatial operator maps must use the latter, from physical qubits.
    edges = {q["lab004_red_edge_id"]:
             tuple(int(center.split(":")[1]) for center in q["star_endpoints"])
             for q in geometry["physical_qubits"] if q["color"] == "red"}
    assert len(edges) == 36 and set(edges) == set(range(36))
    assert all(len(edge) == 2 and edge[0] % 2 != edge[1] % 2 for edge in edges.values())
    lookup = {frozenset(pair): edge for edge, pair in edges.items()}
    assert len(lookup) == 36
    adjacent = {vertex: {} for vertex in range(24)}
    action_sets = [set(action) for action in spec["public_actions_red_edges"]]
    edge_class = {edge: (2 if edge in action_sets[0] else 1 if edge in action_sets[1] else 0)
                  for edge in edges}
    for edge, (a, b) in edges.items():
        adjacent[a][b] = adjacent[b][a] = edge_class[edge]
    assert all(len(value) == 3 for value in adjacent.values())
    blue, green = edges[0]
    if blue % 2:
        blue, green = green, blue
    assert edges[0] == (blue, green)
    visits = 0
    graph_maps = []

    def candidates(vertex: int, mapping: dict[int, int]) -> list[int]:
        used = set(mapping.values())
        return [target for target in range(24) if target % 2 == vertex % 2 and target not in used
                and all(adjacent[vertex].get(old, -1) == adjacent[target].get(new, -1)
                        for old, new in mapping.items())]

    def search(mapping: dict[int, int]) -> None:
        nonlocal visits
        visits += 1
        assert visits <= budget["max_backtracking_nodes"]
        assert time.process_time() - start <= budget["max_cpu_seconds"]
        if len(mapping) == 24:
            graph_maps.append(mapping.copy())
            assert len(graph_maps) <= budget["max_graph_maps"]
            return
        frontier = [v for v in range(24) if v not in mapping
                    and any(u in mapping for u in adjacent[v])]
        assert frontier, "Red-edge graph unexpectedly disconnected"
        vertex, options = min(((v, candidates(v, mapping)) for v in frontier),
                              key=lambda item: (len(item[1]), item[0]))
        for target in options:
            mapping[vertex] = target
            search(mapping)
            del mapping[vertex]

    search({blue: blue, green: green})
    assert graph_maps
    star_by_center = {row["center"]: row for row in geometry["star_supports"]}
    qubits = geometry["physical_qubits"]
    qubit_lookup = {(q["color"], frozenset(q["star_endpoints"])): q["id"] for q in qubits}
    assert len(star_by_center) == 36 and len(qubit_lookup) == len(qubits) == 108
    faces = geometry["face_edge_ids"]
    assert len(faces) == 12 and len({frozenset(face) for face in faces}) == 12
    source_by_pair = {frozenset(tuple(row["error_edges_private"]) for row in sector["pair_rows"]): sector
                      for sector in source["rows"]}
    assert len(source_by_pair) == 12
    fully_valid = []
    rejected = defaultdict(int)
    for vertex_map in graph_maps:
        edge_map = {edge: lookup[frozenset(vertex_map[v] for v in pair)]
                    for edge, pair in edges.items()}
        assert set(edge_map.values()) == set(edges)
        assert all({edge_map[edge] for edge in action} == set(action)
                   for action in spec["public_actions_red_edges"])
        face_map = {}
        face_lookup = {frozenset(face): index for index, face in enumerate(faces)}
        for face_index, face in enumerate(faces):
            image = face_lookup.get(frozenset(edge_map[edge] for edge in face))
            if image is None:
                break
            face_map[face_index] = image
        if len(face_map) != 12 or len(set(face_map.values())) != 12:
            rejected["face_incidence"] += 1
            continue
        center_map = {f"{color}:{vertex}": f"{color}:{vertex_map[vertex]}"
                      for vertex in range(24) for color in ("blue", "green")
                      if (color == "blue") == (vertex % 2 == 0)}
        center_map.update({f"red:{old}": f"red:{new}" for old, new in face_map.items()})
        qubit_map = {}
        for q in qubits:
            image = qubit_lookup.get((q["color"],
                                      frozenset(center_map[center] for center in q["star_endpoints"])))
            if image is None:
                break
            qubit_map[q["id"]] = image
        if len(qubit_map) != 108 or len(set(qubit_map.values())) != 108:
            rejected["physical_qubit_incidence"] += 1
            continue
        def mapped_set(values):
            return {qubit_map[q] for q in values}
        geometry_ok = True
        for center, star in star_by_center.items():
            target = star_by_center[center_map[center]]
            mapped_cz = {frozenset((qubit_map[a], qubit_map[b])) for a, b in star["six_cz_pairs"]}
            target_cz = {frozenset(pair) for pair in target["six_cz_pairs"]}
            if (mapped_set(star["outer_x_qubits"]) != set(target["outer_x_qubits"])
                or mapped_cz != target_cz
                or any(mapped_set(values) != set(target["triangle_z_qubits_by_color"][color])
                       for color, values in star["triangle_z_qubits_by_color"].items())):
                geometry_ok = False
                break
        if not geometry_ok:
            rejected["d4_star_cz_geometry"] += 1
            continue
        matched_pairs = 0
        law_tests = 0
        law_replays = 0
        for sector in source["rows"]:
            mapped_pair = frozenset(tuple(sorted(edge_map[e] for e in row["error_edges_private"]))
                                    for row in sector["pair_rows"])
            target_sector = source_by_pair.get(mapped_pair)
            if target_sector is None:
                continue
            matched_pairs += 1
            target_errors = {tuple(row["error_edges_private"]): row
                             for row in target_sector["pair_rows"]}
            for old_row in sector["pair_rows"]:
                new_error = tuple(sorted(edge_map[e] for e in old_row["error_edges_private"]))
                target_row = target_errors[new_error]
                assert old_row["first_public_mass"] == target_row["first_public_mass"] == "1"
                for action_index in range(2):
                    old_cell = old_row["cells"][action_index]
                    target_cell = target_row["cells"][action_index]
                    transformed = {keyed(mapped_public(item["public"], vertex_map)):
                                   Fraction(item["conditional_probability"])
                                   for item in old_cell["rows"]}
                    law_tests += 1
                    law_replays += transformed == law(target_cell["rows"])
        fully_valid.append({"nontrivial": any(vertex_map[v] != v for v in range(24)),
                            "vertex_permutation": [vertex_map[v] for v in range(24)],
                            "red_edge_permutation": [edge_map[e] for e in range(36)],
                            "mapped_class_pairs": matched_pairs,
                            "held_out_direct_law_tests": law_tests,
                            "held_out_direct_law_replays": law_replays,
                            "held_out_direct_law_mismatches": law_tests - law_replays})
    assert len(fully_valid) + sum(rejected.values()) == len(graph_maps)
    assert any(not row["nontrivial"] for row in fully_valid)
    assert all(row["held_out_direct_law_mismatches"] == 0
               for row in fully_valid if not row["nontrivial"])
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - start
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "action_preserving_spatial_map_gate_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "graph_backtracking_nodes": visits, "colored_graph_action_maps": len(graph_maps),
            "rejected_necessary_geometry_counts": dict(sorted(rejected.items())),
            "full_d4_operator_geometry_maps": len(fully_valid),
            "nontrivial_full_geometry_maps": sum(row["nontrivial"] for row in fully_valid),
            "nontrivial_held_out_class_law_replays": sum(row["held_out_direct_law_replays"]
                                                       for row in fully_valid if row["nontrivial"]),
            "nontrivial_held_out_class_law_mismatches": sum(row["held_out_direct_law_mismatches"]
                                                          for row in fully_valid if row["nontrivial"]),
            "maps": fully_valid,
            "counters": {"new_born_terms": 0, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Only colored red-edge graph maps fixing the singleton and five-edge action sets and preserving the full frozen D4 star/CZ geometry are audited. Direct J8X public laws validate eligible maps inside the already-evaluated deterministic-first class. An empty/nonempty symmetry family neither supplies other first-record laws nor permits full-IID information/risk, noisy JIT or threshold inference."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "graph_maps": result["colored_graph_action_maps"],
                      "full_maps": result["full_d4_operator_geometry_maps"],
                      "nontrivial_full_maps": result["nontrivial_full_geometry_maps"],
                      "nontrivial_law_replays": result["nontrivial_held_out_class_law_replays"],
                      "cpu_seconds": result["cpu_seconds"]}))
