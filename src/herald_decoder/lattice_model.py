#!/usr/bin/env python3
"""Canonical square and honeycomb graph models for Lab 002 simulations."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

import numpy as np
from scipy.sparse import csc_matrix


@dataclass(frozen=True)
class Vertex:
    x: float
    y: float
    detector: bool = True
    boundary_side: str | None = None


@dataclass(frozen=True)
class LatticeGraph:
    name: str
    size: int
    vertices: tuple[Vertex, ...]
    edges: tuple[tuple[int, int], ...]
    logical_edges: frozenset[int]
    logical_line: tuple[Vertex, ...]

    @property
    def detector_vertices(self) -> tuple[int, ...]:
        return tuple(index for index, vertex in enumerate(self.vertices) if vertex.detector)

    @property
    def boundary_vertices(self) -> tuple[int, ...]:
        return tuple(index for index, vertex in enumerate(self.vertices) if not vertex.detector)

    @property
    def detector_row(self) -> dict[int, int]:
        return {vertex: row for row, vertex in enumerate(self.detector_vertices)}

    @property
    def check_matrix(self) -> csc_matrix:
        row_for_vertex = self.detector_row
        rows: list[int] = []
        columns: list[int] = []
        for edge_index, edge in enumerate(self.edges):
            incident = [row_for_vertex[vertex] for vertex in edge if vertex in row_for_vertex]
            if not incident:
                raise ValueError(f"edge {edge_index} has no incident detector")
            rows.extend(incident)
            columns.extend([edge_index] * len(incident))
        return csc_matrix(
            (np.ones(len(rows), dtype=np.uint8), (rows, columns)),
            shape=(len(row_for_vertex), len(self.edges)),
            dtype=np.uint8,
        )

    @property
    def incident_edges(self) -> tuple[tuple[int, ...], ...]:
        incident: list[list[int]] = [[] for _ in self.vertices]
        for edge_index, (a, b) in enumerate(self.edges):
            incident[a].append(edge_index)
            incident[b].append(edge_index)
        return tuple(tuple(edges) for edges in incident)

    def degrees(self, error: np.ndarray) -> np.ndarray:
        if error.shape != (len(self.edges),):
            raise ValueError("error vector has the wrong shape")
        degree = np.zeros(len(self.vertices), dtype=np.uint8)
        for edge_index, (a, b) in enumerate(self.edges):
            if error[edge_index]:
                degree[a] += 1
                degree[b] += 1
        return degree

    def true_syndrome(self, error: np.ndarray) -> np.ndarray:
        degree = self.degrees(error)
        return np.asarray([degree[vertex] & 1 for vertex in self.detector_vertices], dtype=np.uint8)

    def logical_parity(self, chain: np.ndarray) -> int:
        if chain.shape != (len(self.edges),):
            raise ValueError("chain vector has the wrong shape")
        return int(np.sum(chain[list(self.logical_edges)], dtype=np.int64) & 1)


@dataclass(frozen=True)
class Observation:
    error: np.ndarray
    syndrome: np.ndarray
    herald: np.ndarray
    detector_degrees: np.ndarray


def sample_observation(
    graph: LatticeGraph,
    rng: np.random.Generator,
    *,
    p: float,
    q: float,
    p_m: float = 0.0,
    p_h: float = 0.0,
) -> Observation:
    """Sample the Lab 002 edge noise and fusion-remnant observation model."""
    for name, value, upper in (("p", p, 1.0), ("q", q, 1.0), ("p_m", p_m, 0.5), ("p_h", p_h, 1.0)):
        if not 0.0 <= value <= upper:
            raise ValueError(f"{name} must lie in [0, {upper}]")
    error = (rng.random(len(graph.edges)) < p).astype(np.uint8)
    degree = graph.degrees(error)
    detector_degree = degree[list(graph.detector_vertices)]
    syndrome = ((detector_degree & 1) ^ (rng.random(len(detector_degree)) < p_m)).astype(np.uint8)
    eligible = detector_degree >= 2
    herald = (eligible & (rng.random(len(detector_degree)) < q) & (rng.random(len(detector_degree)) >= p_h)).astype(np.uint8)
    return Observation(error=error, syndrome=syndrome, herald=herald, detector_degrees=detector_degree)


def square_graph(size: int) -> LatticeGraph:
    if size < 3:
        raise ValueError("square size must be at least 3")
    vertices = tuple(
        Vertex(
            x=float(x),
            y=float(y),
            detector=0 < x < size - 1,
            boundary_side="left" if x == 0 else "right" if x == size - 1 else None,
        )
        for y in range(size)
        for x in range(size)
    )
    edges: list[tuple[int, int]] = []
    for y in range(size):
        for x in range(size):
            vertex = y * size + x
            if x + 1 < size:
                edges.append((vertex, vertex + 1))
            if y + 1 < size and 0 < x < size - 1:
                edges.append((vertex, vertex + size))
    logical_edges = frozenset(
        edge_index
        for edge_index, (a, b) in enumerate(edges)
        if {a % size, b % size} == {size - 2, size - 1}
    )
    line_x = size - 1.5
    logical_line = (
        Vertex(line_x, -0.65),
        *(Vertex(line_x, row + 0.5) for row in range(size - 1)),
        Vertex(line_x, size - 0.35),
    )
    graph = LatticeGraph("square", size, vertices, tuple(edges), logical_edges, logical_line)
    _validate_graph(graph)
    return graph


def _segments_cross(p1: Vertex, p2: Vertex, q1: Vertex, q2: Vertex) -> bool:
    rx, ry = p2.x - p1.x, p2.y - p1.y
    sx, sy = q2.x - q1.x, q2.y - q1.y
    denominator = rx * sy - ry * sx
    if abs(denominator) < 1e-10:
        return False
    qpx, qpy = q1.x - p1.x, q1.y - p1.y
    t = (qpx * sy - qpy * sx) / denominator
    u = (qpx * ry - qpy * rx) / denominator
    return 1e-8 < t < 1 - 1e-8 and 1e-8 < u < 1 - 1e-8


def honeycomb_graph(size: int) -> LatticeGraph:
    """Translate the Results viewer's open-rough/armchair-smooth graph exactly."""
    if size < 2:
        raise ValueError("honeycomb size must be at least 2")
    raw_vertices: list[Vertex] = []
    vertex_ids: dict[tuple[float, float], int] = {}
    records: dict[tuple[int, int], dict] = {}

    def vertex_id(x: float, y: float) -> int:
        key = (round(x, 4), round(y, 4))
        if key not in vertex_ids:
            vertex_ids[key] = len(raw_vertices)
            raw_vertices.append(Vertex(x=x, y=y))
        return vertex_ids[key]

    for column in range(size):
        for row in range(size):
            center_x = 1.5 * column
            center_y = sqrt(3) * (row + 0.5 * (column % 2))
            corners = [
                vertex_id(center_x + cos(pi * side / 3), center_y + sin(pi * side / 3))
                for side in range(6)
            ]
            for side in range(6):
                a, b = sorted((corners[side], corners[(side + 1) % 6]))
                record = records.setdefault((a, b), {"count": 0, "occurrences": []})
                record["count"] += 1
                record["occurrences"].append((column, row, side))

    record_items = list(records.items())
    removed: set[int] = set()
    boundary_sides: dict[int, str] = {}
    for index, ((a, b), record) in enumerate(record_items):
        if record["count"] != 1:
            continue
        column, _row, side = record["occurrences"][0]
        boundary_side = None
        if column == 0 and side in (2, 3):
            boundary_side = "left"
        elif column == size - 1 and side in (0, 5):
            boundary_side = "right"
        if boundary_side is not None:
            removed.add(index)
            boundary_sides[a] = boundary_side
            boundary_sides[b] = boundary_side

    vertices = tuple(
        Vertex(vertex.x, vertex.y, detector=index not in boundary_sides, boundary_side=boundary_sides.get(index))
        for index, vertex in enumerate(raw_vertices)
    )
    edges = tuple(edge for index, (edge, _record) in enumerate(record_items) if index not in removed)
    min_y = min(vertex.y for vertex in vertices)
    max_y = max(vertex.y for vertex in vertices)
    centers = [Vertex(1.5 * (size - 1), sqrt(3) * (row + 0.5 * ((size - 1) % 2))) for row in range(size)]
    logical_line = [Vertex(centers[0].x, min_y - 0.65), *centers, Vertex(centers[-1].x, max_y + 0.65)]
    logical_edges: set[int] = set()
    for segment in range(len(logical_line) - 1):
        for edge_index, (a, b) in enumerate(edges):
            if _segments_cross(logical_line[segment], logical_line[segment + 1], vertices[a], vertices[b]):
                logical_edges.add(edge_index)
    graph = LatticeGraph(
        "honeycomb", size, vertices, edges, frozenset(logical_edges), tuple(logical_line)
    )
    _validate_graph(graph)
    return graph


def _validate_graph(graph: LatticeGraph) -> None:
    if not graph.edges or not graph.logical_edges:
        raise ValueError("graph needs retained edges and a nonempty logical cut")
    boundary_sides = {graph.vertices[index].boundary_side for index in graph.boundary_vertices}
    if boundary_sides != {"left", "right"}:
        raise ValueError("graph needs both rough boundaries")
    matrix = graph.check_matrix
    column_weights = np.asarray(matrix.sum(axis=0)).ravel()
    if np.any((column_weights < 1) | (column_weights > 2)):
        raise ValueError("every retained edge must touch one or two detectors")
