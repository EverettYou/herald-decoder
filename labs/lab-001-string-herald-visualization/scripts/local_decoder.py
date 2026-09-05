"""Local herald-assisted bond predictor for lab 001."""

from __future__ import annotations

from collections import deque
from typing import Hashable, TypeVar

Vertex = tuple[int, int]
Edge = tuple[Vertex, Vertex]
Node = TypeVar("Node", bound=Hashable)

STAGE_ONE_SOURCE = "scripts/local_decoder.py"
STAGE_ONE_RULE_ORDER = (
    "herald_distance_1",
    "syndrome_herald_syndrome",
    "herald_distance_2",
)


def lattice_edges(size: int) -> list[Edge]:
    """Return every nearest-neighbor bond in a square size-by-size lattice."""
    bonds: list[Edge] = []
    for y in range(size):
        for x in range(size):
            if x + 1 < size:
                bonds.append(((x, y), (x + 1, y)))
            if y + 1 < size and 0 < x < size - 1:
                bonds.append(((x, y), (x, y + 1)))
    return bonds


def logical_boundary_edges(size: int, side: str = "right") -> set[Edge]:
    """Return data edges crossed by the open-plaquette center line."""
    if size < 2:
        raise ValueError("size must be at least 2")
    if side not in {"left", "right"}:
        raise ValueError("side must be 'left' or 'right'")
    boundary_x = 0 if side == "left" else size - 1
    interior_x = 1 if side == "left" else size - 2
    return {
        _canonical_edge((boundary_x, y), (interior_x, y))
        for y in range(size)
    }


def logical_parity(errors: set[Edge], size: int, side: str = "right") -> int:
    """Return parity of errors crossed by the selected logical check line."""
    return len(errors & logical_boundary_edges(size, side)) % 2


def _canonical_edge(a: Vertex, b: Vertex) -> Edge:
    return (a, b) if a < b else (b, a)


def _graph_adjacency(edges: list[tuple[Node, Node]]) -> dict[Node, list[tuple[Node, int]]]:
    neighbors: dict[Node, list[tuple[Node, int]]] = {}
    for edge_index, (a, b) in enumerate(edges):
        neighbors.setdefault(a, []).append((b, edge_index))
        neighbors.setdefault(b, []).append((a, edge_index))
    for vertex in neighbors:
        neighbors[vertex].sort(key=lambda item: (item[0], item[1]))
    return neighbors


def _shortest_edge_path(
    neighbors: dict[Node, list[tuple[Node, int]]],
    start: Node,
    goal: Node,
    maximum_distance: int,
) -> tuple[int, ...] | None:
    """Return one deterministic shortest path up to the requested distance."""
    queue = deque([(start, tuple())])
    visited = {start}
    while queue:
        vertex, path = queue.popleft()
        if vertex == goal:
            return path
        if len(path) == maximum_distance:
            continue
        for neighbor, edge_index in neighbors.get(vertex, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + (edge_index,)))
    return None


def _evaluate_graph_rules(
    edges: list[tuple[Node, Node]],
    detector_vertices: set[Node],
    syndromes: set[Node],
    heralds: set[Node],
) -> tuple[dict[str, set[int]], set[Node]]:
    """Evaluate Stage 1 once; all public adapters delegate to this implementation."""
    neighbors = _graph_adjacency(edges)
    syndromes &= detector_vertices
    heralds &= detector_vertices
    rules = {name: set() for name in STAGE_ONE_RULE_ORDER}
    remaining_heralds = set(heralds)
    consumed_heralds: set[Node] = set()

    def apply_herald_distance(distance: int, name: str) -> None:
        # Evaluate every qualifying pair against one immutable stage snapshot.
        # A herald may support more than one path during this parallel update;
        # only after all proposals are collected are touched heralds consumed.
        touched_this_stage: set[Node] = set()
        candidates = sorted(remaining_heralds)
        for index, a in enumerate(candidates):
            for b in candidates[index + 1:]:
                path = _shortest_edge_path(neighbors, a, b, distance)
                if path is not None and len(path) == distance:
                    rules[name].update(path)
                    touched_this_stage.update((a, b))
        remaining_heralds.difference_update(touched_this_stage)
        consumed_heralds.update(touched_this_stage)

    apply_herald_distance(1, "herald_distance_1")

    for herald in sorted(remaining_heralds):
        syndrome_incidents = [
            edge_index
            for neighbor, edge_index in neighbors.get(herald, [])
            if neighbor in syndromes
        ]
        if len(syndrome_incidents) == 2:
            rules["syndrome_herald_syndrome"].update(syndrome_incidents)
            consumed_heralds.add(herald)
    remaining_heralds.difference_update(consumed_heralds)

    apply_herald_distance(2, "herald_distance_2")
    return rules, consumed_heralds


def _evaluate_local_rules(
    size: int,
    syndromes: set[Vertex],
    heralds: set[Vertex],
) -> tuple[dict[str, set[Edge]], set[Vertex]]:
    """Adapt the square-lattice coordinate API to the graph implementation."""
    edges = lattice_edges(size)
    detectors = {(x, y) for y in range(size) for x in range(1, size - 1)}
    indexed_rules, consumed_heralds = _evaluate_graph_rules(
        edges,
        detectors,
        set(syndromes),
        set(heralds),
    )
    return {
        name: {edges[edge_index] for edge_index in indexed_rules[name]}
        for name in STAGE_ONE_RULE_ORDER
    }, consumed_heralds


def _validated_vertex_list(raw: object, vertex_count: int, name: str) -> list[int]:
    if not isinstance(raw, list) or len(raw) > vertex_count:
        raise ValueError(f"{name} must be a list of lattice vertex ids")
    if any(isinstance(vertex, bool) or not isinstance(vertex, int) or not 0 <= vertex < vertex_count for vertex in raw):
        raise ValueError(f"{name} contains an out-of-range vertex")
    if len(set(raw)) != len(raw):
        raise ValueError(f"{name} contains duplicate vertices")
    return raw


def predecode_payload(body: dict) -> dict:
    """Run Stage 1 for the interactive artifact from this Python source of truth."""
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")
    vertex_count = body.get("vertex_count")
    raw_edges = body.get("edges")
    if isinstance(vertex_count, bool) or not isinstance(vertex_count, int) or not 1 <= vertex_count <= 1000:
        raise ValueError("vertex_count must be an integer in [1, 1000]")
    if not isinstance(raw_edges, list) or len(raw_edges) > 5000:
        raise ValueError("edges must be a list with at most 5000 entries")

    edges: list[tuple[int, int]] = []
    edge_keys: set[tuple[int, int]] = set()
    for raw_edge in raw_edges:
        if (
            not isinstance(raw_edge, list)
            or len(raw_edge) != 2
            or any(isinstance(vertex, bool) or not isinstance(vertex, int) for vertex in raw_edge)
        ):
            raise ValueError("each edge must contain two integer vertex ids")
        a, b = raw_edge
        if a == b or not 0 <= a < vertex_count or not 0 <= b < vertex_count:
            raise ValueError("edge vertex is out of range")
        key = tuple(sorted((a, b)))
        if key in edge_keys:
            raise ValueError("duplicate graph edge")
        edge_keys.add(key)
        edges.append((a, b))

    raw_detectors = body.get("detector_vertices", list(range(vertex_count)))
    detectors = set(_validated_vertex_list(raw_detectors, vertex_count, "detector_vertices"))
    syndromes = set(_validated_vertex_list(body.get("syndromes", []), vertex_count, "syndromes"))
    heralds = set(_validated_vertex_list(body.get("heralds", []), vertex_count, "heralds"))
    if not syndromes <= detectors:
        raise ValueError("every syndrome vertex must be a detector vertex")
    if not heralds <= detectors:
        raise ValueError("every herald vertex must be a detector vertex")

    rules, consumed_heralds = _evaluate_graph_rules(edges, detectors, syndromes, heralds)
    correction: set[int] = set()
    for name in STAGE_ONE_RULE_ORDER:
        correction.symmetric_difference_update(rules[name])
    return {
        "status": "ok",
        "algorithm_source": STAGE_ONE_SOURCE,
        "rule_order": list(STAGE_ONE_RULE_ORDER),
        "rules": {name: sorted(rules[name]) for name in STAGE_ONE_RULE_ORDER},
        "correction_edge_indices": sorted(correction),
        "consumed_herald_vertices": sorted(consumed_heralds),
        "remaining_herald_vertices": sorted(heralds - consumed_heralds),
    }


def predict_correction_by_rule(
    size: int,
    syndromes: set[Vertex],
    heralds: set[Vertex],
) -> dict[str, set[Edge]]:
    """Apply the three local rules in order and return their edge proposals."""
    return _evaluate_local_rules(size, syndromes, heralds)[0]


def decode_local(
    size: int,
    syndromes: set[Vertex],
    heralds: set[Vertex],
) -> tuple[set[Edge], set[Vertex]]:
    """Return the correction and the herald sites consumed during pairing."""
    rules, consumed_heralds = _evaluate_local_rules(size, syndromes, heralds)
    correction: set[Edge] = set()
    for proposal in rules.values():
        correction.symmetric_difference_update(proposal)
    return correction, consumed_heralds


def predict_correction(size: int, syndromes: set[Vertex], heralds: set[Vertex]) -> set[Edge]:
    """Return the parity sum of the ordered local-rule correction paths.

    Applying the same edge twice cancels over GF(2). This is still a local
    heuristic rather than a globally valid surface-code decoder.
    """
    return decode_local(size, syndromes, heralds)[0]


def residual_state(
    size: int,
    errors: set[Edge],
    correction: set[Edge],
    original_heralds: set[Vertex],
) -> tuple[set[Edge], set[Vertex], set[Vertex]]:
    """Apply correction and recompute residual syndrome and unresolved heralds."""
    residual = errors ^ correction
    degree = {(x, y): 0 for y in range(size) for x in range(size)}
    for a, b in residual:
        degree[a] += 1
        degree[b] += 1
    syndromes = {vertex for vertex, value in degree.items() if value % 2}
    unresolved_heralds = {vertex for vertex in original_heralds if degree[vertex] >= 2}
    return residual, syndromes, unresolved_heralds
