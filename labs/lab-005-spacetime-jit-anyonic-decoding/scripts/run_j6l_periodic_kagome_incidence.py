"""Exact L=2 kagome incidence completion of the Lab 004 honeycomb.

This constructs operator *supports* only. It does not prepare a quantum state
or evaluate a measurement probability.
"""

from __future__ import annotations

from collections import Counter, defaultdict
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

from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_r3 import geometry_trivial_loop_catalog  # noqa: E402


CONTRACT = LAB / "manifests/j6l-periodic-kagome-incidence-2026-09-24.json"
RESULT = LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "iqbal_pdf": ROOT / "references/iqbal2023-nonabelian-topological-order/paper.pdf",
    "j6k_result": LAB / "results/j6k-full-local-star-action-algebra-2026-09-24.json",
    "lab004_honeycomb": LAB004_SCRIPTS / "d4_honeycomb.py",
    "lab004_cycle_catalog": LAB004_SCRIPTS / "d4_r3.py",
}
COLORS = ("blue", "green", "red")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node(color: str, index: int) -> str:
    return f"{color}:{index}"


def pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def cyclic_order(neighbors: set[str], links: dict[tuple[str, str], int]) -> list[str]:
    """Require the induced neighbor graph to be one unambiguous hexagon."""
    assert len(neighbors) == 6
    induced = {n: sorted(m for m in neighbors if m != n and pair(n, m) in links)
               for n in neighbors}
    assert all(len(adjacent) == 2 for adjacent in induced.values())
    start = min(neighbors)
    order = [start, induced[start][0]]
    while len(order) < 6:
        options = [n for n in induced[order[-1]] if n != order[-2]]
        assert len(options) == 1 and options[0] not in order
        order.append(options[0])
    assert order[-1] in induced[start]
    assert len(set(order)) == 6
    return order


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pinned = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
              for name, path in INPUTS.items()}
    assert all(pinned.values()), f"pinned input drift: {pinned}"
    lattice = paper_periodic_honeycomb(2)
    assert (lattice.vertex_count, lattice.edge_count) == (24, 36)
    catalog = geometry_trivial_loop_catalog(
        lattice, maximum_cycle_length=6, cycle_limit=10_000
    )
    assert len(catalog) == contract["budget"]["max_faces"] == 12

    face_edges = [tuple(int(e) for e in np.flatnonzero(chain))
                  for chain, _, _ in catalog]
    face_vertices = [tuple(sorted(set(int(v) for e in edges
                                      for v in lattice.edge_vertices[e])))
                     for edges in face_edges]
    assert len(set(face_edges)) == 12
    assert all(len(edges) == len(vertices) == 6
               for edges, vertices in zip(face_edges, face_vertices))
    edge_faces = Counter(e for edges in face_edges for e in edges)
    vertex_faces = Counter(v for vertices in face_vertices for v in vertices)
    assert set(edge_faces) == set(range(36)) and set(edge_faces.values()) == {2}
    assert set(vertex_faces) == set(range(24)) and set(vertex_faces.values()) == {3}

    # The physical qubit is the edge between two differently colored star
    # centers in the face-completed triangulation. BG links inherit Lab 004
    # red-edge IDs exactly; B/R and G/R incidence links complete the other
    # two color classes.
    links: dict[tuple[str, str], int] = {}
    qubits: list[dict] = []

    def add_qubit(left: str, right: str, color: str, *, source_edge: int | None = None) -> None:
        key = pair(left, right)
        assert key not in links
        assert color not in {left.split(":")[0], right.split(":")[0]}
        qubit_id = len(qubits)
        links[key] = qubit_id
        qubits.append({"id": qubit_id, "color": color,
                       "star_endpoints": list(key), "lab004_red_edge_id": source_edge})

    for edge_id, (left, right) in enumerate(lattice.edge_vertices):
        assert int(lattice.vertex_colors[left]) == BLUE
        assert int(lattice.vertex_colors[right]) == GREEN
        add_qubit(node("blue", int(left)), node("green", int(right)),
                  "red", source_edge=edge_id)
        assert links[pair(node("blue", int(left)), node("green", int(right)))] == edge_id
    for face_id, vertices in enumerate(face_vertices):
        for vertex in vertices:
            color = "blue" if int(lattice.vertex_colors[vertex]) == BLUE else "green"
            add_qubit(node(color, vertex), node("red", face_id),
                      "green" if color == "blue" else "blue")

    assert len(qubits) == contract["budget"]["max_physical_qubits"] == 108
    assert Counter(q["color"] for q in qubits) == Counter({c: 36 for c in COLORS})
    centers = [node("blue" if int(lattice.vertex_colors[v]) == BLUE else "green", v)
               for v in range(24)] + [node("red", f) for f in range(12)]
    assert Counter(n.split(":")[0] for n in centers) == Counter({c: 12 for c in COLORS})

    neighbor_sets: dict[str, set[str]] = defaultdict(set)
    for left, right in links:
        neighbor_sets[left].add(right)
        neighbor_sets[right].add(left)
    assert set(neighbor_sets) == set(centers)
    assert all(len(neighbor_sets[n]) == 6 for n in centers)

    inner_uses: Counter[int] = Counter()
    outer_uses: Counter[int] = Counter()
    stars: list[dict] = []
    for center in centers:
        center_color = center.split(":")[0]
        ring = cyclic_order(neighbor_sets[center], links)
        inner = [links[pair(center, other)] for other in ring]
        outer = [links[pair(ring[i], ring[(i + 1) % 6])] for i in range(6)]
        assert len(set(inner)) == len(set(outer)) == 6
        assert not set(inner) & set(outer)
        assert all(qubits[q]["color"] == center_color for q in outer)
        inner_colors = [qubits[q]["color"] for q in inner]
        assert all(inner_colors[i] != inner_colors[(i + 1) % 6] for i in range(6))
        assert set(inner_colors) == set(COLORS) - {center_color}
        triangles = {color: [inner[i] for i in range(6) if inner_colors[i] == color]
                     for color in COLORS if color != center_color}
        assert all(len(triangle) == 3 for triangle in triangles.values())
        inner_uses.update(inner)
        outer_uses.update(outer)
        stars.append({"center": center, "center_color": center_color,
                      "ring_neighbor_centers": ring,
                      "inner_cz_ring_qubits": inner,
                      "six_cz_pairs": [[inner[i], inner[(i + 1) % 6]] for i in range(6)],
                      "outer_x_qubits": outer,
                      "triangle_z_qubits_by_color": triangles})
    assert len(stars) == contract["budget"]["max_stars"] == 36
    assert set(inner_uses) == set(outer_uses) == set(range(108))
    assert set(inner_uses.values()) == set(outer_uses.values()) == {2}

    representative_blue = next(s for s in stars if s["center_color"] == "blue")
    blue_ring = representative_blue["inner_cz_ring_qubits"][:]
    if qubits[blue_ring[0]]["color"] != "green":
        blue_ring = blue_ring[1:] + blue_ring[:1]
    assert [qubits[q]["color"] for q in blue_ring] == ["green", "red"] * 3
    local_action_rows = []
    for red_pair, expected_green_sites in (((1, 3), (0, 4)), ((1, 5), (2, 4))):
        assert all(qubits[blue_ring[i]]["lab004_red_edge_id"] == blue_ring[i]
                   for i in red_pair)
        dressing = Counter((red - 1) % 6 for red in red_pair)
        dressing.update((red + 1) % 6 for red in red_pair)
        green_sites = tuple(i for i in (0, 2, 4) if dressing[i] % 2)
        assert green_sites == expected_green_sites
        local_action_rows.append({"j6k_red_ring_sites": list(red_pair),
                                  "embedded_lab004_red_edge_ids": [blue_ring[i] for i in red_pair],
                                  "dressed_green_ring_sites": list(green_sites),
                                  "dressed_green_qubit_ids": [blue_ring[i] for i in green_sites]})

    for qubit in qubits:
        color = qubit["color"]
        q = qubit["id"]
        assert {s["center"] for s in stars if q in s["inner_cz_ring_qubits"]} == set(qubit["star_endpoints"])
        assert len([s for s in stars if s["center_color"] == color
                    and q in s["outer_x_qubits"]]) == 2

    # Fixed two-edge path through one shared blue/green center. This checks
    # only the exact red-qubit/topological-boundary identity, not charge law.
    first_edge = 0
    shared = int(lattice.edge_vertices[first_edge, 1])
    second_edge = next(int(e) for e, endpoints in enumerate(lattice.edge_vertices)
                       if e != first_edge and shared in endpoints)
    red_cases = [[edge] for edge in range(36)] + [[first_edge, second_edge]]
    red_rows = []
    for selected in red_cases:
        boundary = np.zeros(24, dtype=np.uint8)
        for edge in selected:
            assert qubits[edge]["color"] == "red"
            left, right = (int(v) for v in lattice.edge_vertices[edge])
            boundary[left] ^= 1
            boundary[right] ^= 1
            assert qubits[edge]["star_endpoints"] == list(pair(node("blue", left), node("green", right)))
        direct = np.bincount(lattice.edge_vertices[selected].ravel(), minlength=24) % 2
        assert np.array_equal(boundary, direct)
        red_rows.append({"lab004_red_edges": selected,
                         "kagome_red_qubits": selected,
                         "flux_boundary_vertices": [int(v) for v in np.flatnonzero(boundary)]})

    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_exact_incidence_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": pinned,
        "counts": {"honeycomb_vertices": 24, "honeycomb_red_edges": 36,
                   "hexagonal_red_faces": len(face_edges), "star_centers": len(stars),
                   "physical_qubits": len(qubits), "inner_uses_per_qubit": 2,
                   "outer_uses_per_qubit": 2},
        "face_edge_ids": [list(edges) for edges in face_edges],
        "physical_qubits": qubits,
        "star_supports": stars,
        "j6k_representative_blue_star": {"center": representative_blue["center"],
                                         "ring_qubit_ids_green_even_red_odd": blue_ring,
                                         "local_action_rows": local_action_rows},
        "red_edge_identity_rows": red_rows,
        "inference_boundary": "Exact L=2 combinatorial incidence and source-local operator supports only. No inter-star operator algebra, prepared D4 ground state, sequential projector update, public E2 probability, histories, risk or threshold.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
