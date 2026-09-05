#!/usr/bin/env python3
"""Exact and BP inference for the bounded-degree SU(3) fusion instrument.

The executable model implements the SU(3) channels needed by paths and a
plaquette (degree <= 2).  The paper derivation permits arbitrary SU(N): only
the local fusion table must then be replaced by an LR-coefficient routine.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Iterable

import numpy as np

IRREP_DIM = {
    "1": 1, "3": 3, "3bar": 3, "6": 6, "6bar": 6, "8": 8,
    "10": 10, "10bar": 10, "15": 15, "15bar": 15,
    "15prime": 15, "15primebar": 15, "24": 24, "24bar": 24, "27": 27,
}

SU3_MULTIPLICITIES = {
    (0, 0): {"1": 1},
    (1, 0): {"3": 1},
    (0, 1): {"3bar": 1},
    (2, 0): {"6": 1, "3bar": 1},
    (0, 2): {"6bar": 1, "3": 1},
    (1, 1): {"1": 1, "8": 1},
    (3, 0): {"10": 1, "8": 2, "1": 1},
    (0, 3): {"10bar": 1, "8": 2, "1": 1},
    (2, 1): {"15": 1, "6bar": 1, "3": 2},
    (1, 2): {"15bar": 1, "6": 1, "3bar": 2},
    (4, 0): {"15prime": 1, "15": 3, "6bar": 2, "3": 3},
    (0, 4): {"15primebar": 1, "15bar": 3, "6": 2, "3bar": 3},
    (3, 1): {"24": 1, "15bar": 2, "6": 3, "3bar": 3},
    (1, 3): {"24bar": 1, "15": 2, "6bar": 3, "3": 3},
    (2, 2): {"1": 2, "8": 4, "10": 1, "10bar": 1, "27": 1},
}


@dataclass(frozen=True)
class Graph:
    vertices: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]  # oriented tail -> head

    @property
    def incident(self) -> tuple[tuple[tuple[int, str], ...], ...]:
        answer = []
        for v in self.vertices:
            leaves = []
            for a, (tail, head) in enumerate(self.edges):
                if head == v:
                    leaves.append((a, "3"))
                if tail == v:
                    leaves.append((a, "3bar"))
            answer.append(tuple(leaves))
        return tuple(answer)


def fusion_distribution(leaves: Iterable[str]) -> dict[str, float]:
    """P(R | leaf irreps) for SU(3) fundamental/antifundamental degree <= 4."""
    leaves = tuple(leaves)
    if any(leaf not in {"3", "3bar"} for leaf in leaves) or len(leaves) > 4:
        raise ValueError("SU(3) fusion table supports only 3/3bar leaf lists through degree four")
    multiplicities = SU3_MULTIPLICITIES[(leaves.count("3"), leaves.count("3bar"))]
    denominator = prod(IRREP_DIM[x] for x in leaves)
    result = {r: mult * IRREP_DIM[r] / denominator for r, mult in multiplicities.items()}
    assert abs(sum(result.values()) - 1.0) < 1e-12
    return result


def local_likelihood(
    leaves: tuple[str, ...],
    observation: tuple[int, str],
    m_flip: float = 0.0,
) -> float:
    syndrome, irrep = observation
    parity = len(leaves) & 1
    parity_report = (1.0 - m_flip) if syndrome == parity else m_flip
    channel = fusion_distribution(leaves)
    if irrep not in channel:
        return 0.0
    return parity_report * channel[irrep]


def factor_table(
    graph: Graph,
    observations: tuple[tuple[int, str], ...],
    m_flip: float = 0.0,
) -> list[np.ndarray]:
    tables = []
    for leaves, obs in zip(graph.incident, observations, strict=True):
        table = np.zeros(2 ** len(leaves))
        for bits in product((0, 1), repeat=len(leaves)):
            reps = tuple(rep for bit, (_, rep) in zip(bits, leaves, strict=True) if bit)
            table[sum(bit << j for j, bit in enumerate(bits))] = local_likelihood(
                reps, obs, m_flip
            )
        tables.append(table)
    return tables


def exact_posterior(
    graph: Graph,
    observations: tuple[tuple[int, str], ...],
    p: float,
    m_flip: float = 0.0,
) -> np.ndarray:
    tables = factor_table(graph, observations, m_flip)
    posterior = np.zeros(2 ** len(graph.edges))
    for configuration in product((0, 1), repeat=len(graph.edges)):
        weight = prod(p if x else 1 - p for x in configuration)
        for leaves, table in zip(graph.incident, tables, strict=True):
            index = sum(configuration[a] << j for j, (a, _) in enumerate(leaves))
            weight *= table[index]
        posterior[sum(x << a for a, x in enumerate(configuration))] = weight
    normalizer = posterior.sum()
    if normalizer == 0:
        raise ValueError("impossible observation")
    return posterior / normalizer


def exact_marginals(posterior: np.ndarray, n_edges: int) -> np.ndarray:
    return np.array([posterior[[i for i in range(len(posterior)) if (i >> a) & 1]].sum() for a in range(n_edges)])


def bp_marginals(
    graph: Graph,
    observations: tuple[tuple[int, str], ...],
    p: float,
    max_iter: int = 400,
    tol: float = 1e-13,
    damping: float = 0.0,
    m_flip: float = 0.0,
) -> tuple[np.ndarray, bool, int]:
    """Synchronous sum-product BP; messages have coordinate order e=0,1."""
    tables = factor_table(graph, observations, m_flip)
    edge_factors = [[v for v, leaves in enumerate(graph.incident) if any(a == e for a, _ in leaves)] for e in range(len(graph.edges))]
    v_to_f = {(e, v): np.array([1 - p, p], float) for e in range(len(graph.edges)) for v in edge_factors[e]}
    f_to_v = {
        (v, e): np.full(2, 0.5)
        for v in range(len(graph.vertices))
        for e, _ in graph.incident[v]
    }
    for iteration in range(1, max_iter + 1):
        new_f = {}
        for v, leaves in enumerate(graph.incident):
            for target_j, (target, _) in enumerate(leaves):
                msg = np.zeros(2)
                for bits in product((0, 1), repeat=len(leaves)):
                    index = sum(bit << j for j, bit in enumerate(bits))
                    term = tables[v][index]
                    for j, (edge, _) in enumerate(leaves):
                        if j != target_j:
                            term *= v_to_f[edge, v][bits[j]]
                    msg[bits[target_j]] += term
                msg /= msg.sum()
                mixed = damping * f_to_v[v, target] + (1.0 - damping) * msg
                new_f[v, target] = mixed / mixed.sum()
        new_v = {}
        for e, factors in enumerate(edge_factors):
            for v in factors:
                msg = np.array([1 - p, p], float)
                for other in factors:
                    if other != v:
                        msg *= new_f[other, e]
                new_v[e, v] = msg / msg.sum()
        delta = max(
            max(np.max(np.abs(new_f[key] - f_to_v[key])) for key in new_f),
            max(np.max(np.abs(new_v[key] - v_to_f[key])) for key in new_v),
        )
        f_to_v, v_to_f = new_f, new_v
        if delta < tol:
            break
    beliefs = []
    for e, factors in enumerate(edge_factors):
        belief = np.array([1 - p, p], float)
        for v in factors:
            belief *= f_to_v[v, e]
        beliefs.append(belief[1] / belief.sum())
    return np.array(beliefs), delta < tol, iteration


def path_graph() -> Graph:
    return Graph(("v0", "v1", "v2", "v3"), (("v0", "v1"), ("v1", "v2"), ("v2", "v3")))


def plaquette_graph() -> Graph:
    return Graph(("v0", "v1", "v2", "v3"), (("v0", "v1"), ("v1", "v2"), ("v2", "v3"), ("v3", "v0")))


def ring_graph(size: int) -> Graph:
    if size < 3:
        raise ValueError("ring size must be at least three")
    vertices = tuple(f"v{i}" for i in range(size))
    return Graph(vertices, tuple((vertices[i], vertices[(i + 1) % size]) for i in range(size)))
