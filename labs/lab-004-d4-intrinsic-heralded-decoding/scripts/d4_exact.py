"""Independent exhaustive binary-chain oracle for bounded D4 graphs."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from functools import lru_cache

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ExhaustiveChainMinimum:
    minimum_weight: float
    minimizers: NDArray[np.uint8]
    affine_dimension: int


@dataclass(frozen=True)
class ExactChargeMinimum:
    """All unit-weight minimum T-joins found without using PyMatching."""

    minimum_weight: int
    minimizers: NDArray[np.uint8]
    candidate_count: int


def _gf2_affine_space(
    check_matrix: NDArray[np.generic],
    syndrome: NDArray[np.generic],
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """Return one solution and a nullspace basis for Hx=s over GF(2)."""

    check = np.asarray(check_matrix, dtype=np.uint8)
    target = np.asarray(syndrome, dtype=np.uint8)
    if check.ndim != 2 or target.shape != (check.shape[0],):
        raise ValueError("invalid check-matrix or syndrome shape")
    if np.any(check > 1) or np.any(target > 1):
        raise ValueError("GF(2) inputs must be binary")
    rows, columns = check.shape
    augmented = np.concatenate((check.copy(), target[:, None]), axis=1)
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(columns):
        candidates = np.flatnonzero(augmented[pivot_row:, column])
        if len(candidates) == 0:
            continue
        selected = pivot_row + int(candidates[0])
        augmented[[pivot_row, selected]] = augmented[[selected, pivot_row]]
        for row in range(rows):
            if row != pivot_row and augmented[row, column]:
                augmented[row] ^= augmented[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    if any(not np.any(row[:columns]) and row[columns] for row in augmented):
        raise ValueError("syndrome is outside the check-matrix image")
    free_columns = [column for column in range(columns) if column not in pivot_columns]
    particular = np.zeros(columns, dtype=np.uint8)
    for row, column in enumerate(pivot_columns):
        particular[column] = augmented[row, columns]
    basis = np.zeros((len(free_columns), columns), dtype=np.uint8)
    for basis_row, free in enumerate(free_columns):
        basis[basis_row, free] = 1
        for row, pivot in enumerate(pivot_columns):
            basis[basis_row, pivot] = augmented[row, free]
    return particular, basis


def enumerate_affine_chains(
    check_matrix: NDArray[np.generic],
    syndrome: NDArray[np.generic],
) -> NDArray[np.uint8]:
    """Enumerate every binary chain satisfying Hx=s in stable bit order."""

    particular, basis = _gf2_affine_space(check_matrix, syndrome)
    dimension = len(basis)
    if dimension > 20:
        raise ValueError("affine space exceeds bounded exhaustive limit")
    coefficients = (
        np.arange(1 << dimension, dtype=np.uint64)[:, None]
        >> np.arange(dimension, dtype=np.uint64)[None, :]
    ) & 1
    return np.asarray(
        particular[None, :] ^ ((coefficients.astype(np.uint8) @ basis) % 2),
        dtype=np.uint8,
    )


def exhaustive_chain_minimum(
    check_matrix: NDArray[np.generic],
    syndrome: NDArray[np.generic],
    weights: NDArray[np.generic],
) -> ExhaustiveChainMinimum:
    """Return every globally minimum-weight chain in the affine space."""

    chains = enumerate_affine_chains(check_matrix, syndrome)
    objective = chains @ np.asarray(weights, dtype=np.float64)
    minimum = float(np.min(objective))
    optimal = np.isclose(objective, minimum, rtol=0.0, atol=1e-9)
    return ExhaustiveChainMinimum(
        minimum_weight=minimum,
        minimizers=chains[optimal],
        affine_dimension=int(round(np.log2(len(chains)))),
    )


def exact_unit_t_join_minimum(
    vertex_count: int,
    edge_vertices: NDArray[np.generic],
    syndrome: NDArray[np.generic],
    *,
    candidate_limit: int = 1_000_000,
) -> ExactChargeMinimum:
    """Enumerate every unit-weight minimum T-join on a bounded graph.

    For positive unit weights, a minimum T-join decomposes into pairwise
    edge-disjoint shortest paths between syndrome defects; any cycle or
    non-shortest segment could be removed or shortened.  We therefore
    enumerate every defect pairing and every shortest path for each pair,
    combine the paths over GF(2), and retain all globally lightest chains.
    This is independent of the production MWPM implementation and is bounded
    by ``candidate_limit``.
    """

    edges = np.asarray(edge_vertices, dtype=np.int64)
    target = np.asarray(syndrome, dtype=np.uint8)
    if edges.ndim != 2 or edges.shape[1] != 2:
        raise ValueError("edge_vertices must have shape (edge_count, 2)")
    if target.shape != (vertex_count,) or np.any(target > 1):
        raise ValueError("syndrome must be binary with one value per vertex")
    if np.any(edges < 0) or np.any(edges >= vertex_count):
        raise ValueError("edge endpoint lies outside the graph")
    defects = tuple(int(vertex) for vertex in np.flatnonzero(target))
    if len(defects) % 2:
        raise ValueError("T-join syndrome must have even parity")
    edge_count = len(edges)
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(vertex_count)]
    for edge, (left, right) in enumerate(edges):
        adjacency[int(left)].append((int(right), edge))
        adjacency[int(right)].append((int(left), edge))
    for neighbors in adjacency:
        neighbors.sort()

    @lru_cache(maxsize=None)
    def shortest_path_masks(source: int, target_vertex: int) -> tuple[int, ...]:
        distance = [-1] * vertex_count
        distance[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            for neighbor, _ in adjacency[vertex]:
                if distance[neighbor] < 0:
                    distance[neighbor] = distance[vertex] + 1
                    queue.append(neighbor)
        if distance[target_vertex] < 0:
            raise ValueError("defects lie in disconnected graph components")

        @lru_cache(maxsize=None)
        def descend(vertex: int) -> tuple[int, ...]:
            if vertex == source:
                return (0,)
            masks: set[int] = set()
            for neighbor, edge in adjacency[vertex]:
                if distance[neighbor] == distance[vertex] - 1:
                    masks.update(mask ^ (1 << edge) for mask in descend(neighbor))
            return tuple(sorted(masks))

        return descend(target_vertex)

    @lru_cache(maxsize=None)
    def pairings(vertices: tuple[int, ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
        if not vertices:
            return ((),)
        first = vertices[0]
        result = []
        for index in range(1, len(vertices)):
            second = vertices[index]
            remainder = vertices[1:index] + vertices[index + 1 :]
            for suffix in pairings(remainder):
                result.append(((first, second),) + suffix)
        return tuple(result)

    candidates: set[int] = set()
    for pairing in pairings(defects):
        partial = {0}
        for left, right in pairing:
            paths = shortest_path_masks(left, right)
            partial = {chain ^ path for chain in partial for path in paths}
            if len(partial) + len(candidates) > candidate_limit:
                raise ValueError("T-join candidate limit exceeded")
        candidates.update(partial)
        if len(candidates) > candidate_limit:
            raise ValueError("T-join candidate limit exceeded")
    if not candidates:
        candidates.add(0)
    minimum = min(mask.bit_count() for mask in candidates)
    optimal_masks = sorted(mask for mask in candidates if mask.bit_count() == minimum)
    minimizers = np.zeros((len(optimal_masks), edge_count), dtype=np.uint8)
    for row, mask in enumerate(optimal_masks):
        for edge in range(edge_count):
            minimizers[row, edge] = (mask >> edge) & 1
    return ExactChargeMinimum(minimum, minimizers, len(candidates))
