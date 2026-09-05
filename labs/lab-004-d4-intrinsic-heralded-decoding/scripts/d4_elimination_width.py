"""Deterministic induced-width audits and capped exact bucket elimination."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np

from d4_local_bp import BinaryFactor, BinaryFactorGraph


@dataclass(frozen=True)
class EliminationAudit:
    order: tuple[int, ...]
    induced_width: int
    maximum_cluster_variables: int
    total_fill_edges: int
    elimination_degrees: tuple[int, ...]
    peak_cluster: tuple[int, ...]


@dataclass(frozen=True)
class BucketResult:
    status: str
    evidence: float | None
    maximum_cluster_variables: int
    censored_at_variable: int | None


@dataclass(frozen=True)
class CutsetResult:
    status: str
    evidence: float | None
    branch_count: int
    maximum_cluster_variables: int


@dataclass(frozen=True)
class MiniBucketResult:
    evidence_upper_bound: float
    maximum_cluster_variables: int
    split_bucket_count: int
    mini_bucket_count: int
    partition_heuristic: str = "scope_first_fit"
    positive_content_merge_count: int = 0
    content_candidate_evaluation_count: int = 0


def primal_adjacency(graph: BinaryFactorGraph) -> tuple[frozenset[int], ...]:
    adjacency = [set() for _ in range(graph.variable_count)]
    for factor in graph.factors:
        scope = factor.variables
        for left_index, left in enumerate(scope):
            for right in scope[left_index + 1 :]:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return tuple(frozenset(neighbours) for neighbours in adjacency)


def _fill_count(adjacency: dict[int, set[int]], variable: int) -> int:
    neighbours = sorted(adjacency[variable])
    return sum(
        right not in adjacency[left]
        for index, left in enumerate(neighbours)
        for right in neighbours[index + 1 :]
    )


def _eliminate(adjacency: dict[int, set[int]], variable: int) -> tuple[int, int]:
    neighbours = sorted(adjacency[variable])
    fill = 0
    for index, left in enumerate(neighbours):
        for right in neighbours[index + 1 :]:
            if right not in adjacency[left]:
                adjacency[left].add(right)
                adjacency[right].add(left)
                fill += 1
    for neighbour in neighbours:
        adjacency[neighbour].remove(variable)
    del adjacency[variable]
    return len(neighbours), fill


def greedy_elimination_audit(
    graph: BinaryFactorGraph,
    *,
    physical_variable_count: int,
    strategy: str,
    excluded_variables: Iterable[int] = (),
) -> EliminationAudit:
    """Audit one registered min-fill order on the factor primal graph."""

    if strategy not in {
        "auxiliary_first_min_fill",
        "physical_first_min_fill",
        "global_min_fill",
    }:
        raise ValueError("unknown elimination strategy")
    if not 0 < physical_variable_count <= graph.variable_count:
        raise ValueError("invalid physical variable count")
    base = primal_adjacency(graph)
    excluded = set(excluded_variables)
    if any(variable < 0 or variable >= graph.variable_count for variable in excluded):
        raise ValueError("excluded variable is out of range")
    adjacency = {
        variable: set(neighbours).difference(excluded)
        for variable, neighbours in enumerate(base)
        if variable not in excluded
    }
    order: list[int] = []
    degrees: list[int] = []
    total_fill = 0
    maximum_degree = 0
    peak_cluster: tuple[int, ...] = ()
    while adjacency:
        remaining = set(adjacency)
        physical = {variable for variable in remaining if variable < physical_variable_count}
        auxiliary = remaining.difference(physical)
        if strategy == "auxiliary_first_min_fill":
            eligible = auxiliary or physical
        elif strategy == "physical_first_min_fill":
            eligible = physical or auxiliary
        else:
            eligible = remaining
        variable = min(
            eligible,
            key=lambda item: (
                _fill_count(adjacency, item),
                len(adjacency[item]),
                0 if item < physical_variable_count else 1,
                item,
            ),
        )
        cluster = tuple(sorted({variable, *adjacency[variable]}))
        degree, fill = _eliminate(adjacency, variable)
        order.append(variable)
        degrees.append(degree)
        total_fill += fill
        if degree > maximum_degree or not peak_cluster:
            maximum_degree = degree
            peak_cluster = cluster
    return EliminationAudit(
        tuple(order),
        maximum_degree,
        maximum_degree + 1,
        total_fill,
        tuple(degrees),
        peak_cluster,
    )


def condition_graph(
    graph: BinaryFactorGraph,
    assignment: dict[int, int],
) -> tuple[BinaryFactorGraph, float, dict[int, int]]:
    """Condition binary variables, returning a reindexed residual graph and scalar."""

    if any(variable < 0 or variable >= graph.variable_count for variable in assignment):
        raise ValueError("conditioned variable is out of range")
    if any(state not in (0, 1) for state in assignment.values()):
        raise ValueError("conditioned state must be binary")
    surviving = [v for v in range(graph.variable_count) if v not in assignment]
    remap = {old: new for new, old in enumerate(surviving)}
    scalar = float(np.prod([graph.priors[v, s] for v, s in assignment.items()]))
    factors: list[BinaryFactor] = []
    for factor in graph.factors:
        index = tuple(
            assignment.get(variable, slice(None)) for variable in factor.variables
        )
        table = np.asarray(factor.table[index], dtype=float)
        scope = tuple(remap[v] for v in factor.variables if v not in assignment)
        if scope:
            factors.append(BinaryFactor(factor.name, scope, table))
        else:
            scalar *= float(table)
    priors = graph.priors[surviving] if surviving else np.empty((0, 2), dtype=float)
    return BinaryFactorGraph(len(surviving), priors, tuple(factors)), scalar, remap


def exact_cutset_partition(
    graph: BinaryFactorGraph,
    order: Iterable[int],
    cutset: Iterable[int],
    *,
    maximum_cluster_cap: int,
) -> CutsetResult:
    """Enumerate a cutset and exactly eliminate every residual branch."""

    order = tuple(order)
    cutset = tuple(sorted(set(cutset)))
    if set(order) != set(range(graph.variable_count)):
        raise ValueError("order is not a complete variable permutation")
    evidence = 0.0
    maximum_cluster = 0
    branches = 0
    for states in product((0, 1), repeat=len(cutset)):
        residual, scalar, remap = condition_graph(graph, dict(zip(cutset, states)))
        residual_order = tuple(remap[v] for v in order if v in remap)
        result = exact_bucket_partition(
            residual, residual_order, maximum_cluster_cap=maximum_cluster_cap
        )
        branches += 1
        maximum_cluster = max(maximum_cluster, result.maximum_cluster_variables)
        if result.evidence is None:
            return CutsetResult(
                "censored_peak_table", None, branches, maximum_cluster
            )
        evidence += scalar * result.evidence
    return CutsetResult("computed", evidence, branches, maximum_cluster)


def _aligned_table(factor: BinaryFactor, union_scope: tuple[int, ...]) -> np.ndarray:
    positions = [union_scope.index(variable) for variable in factor.variables]
    permutation = np.argsort(positions)
    ordered_positions = [positions[index] for index in permutation]
    table = factor.table.transpose(tuple(int(index) for index in permutation))
    shape = [1] * len(union_scope)
    for position in ordered_positions:
        shape[position] = 2
    return table.reshape(shape)


def exact_bucket_partition(
    graph: BinaryFactorGraph,
    order: Iterable[int],
    *,
    maximum_cluster_cap: int,
) -> BucketResult:
    """Compute one exact partition function, censoring before an oversized bucket."""

    if maximum_cluster_cap < 1:
        raise ValueError("maximum_cluster_cap must be positive")
    factors = list(graph.factors)
    factors.extend(
        BinaryFactor(f"prior-v{variable}", (variable,), graph.priors[variable])
        for variable in range(graph.variable_count)
    )
    scalar = 1.0
    maximum_cluster = 0
    seen: set[int] = set()
    for variable in order:
        if variable in seen or variable < 0 or variable >= graph.variable_count:
            raise ValueError("order is not a variable permutation")
        seen.add(variable)
        bucket = [factor for factor in factors if variable in factor.variables]
        factors = [factor for factor in factors if variable not in factor.variables]
        if not bucket:
            continue
        union_scope = tuple(sorted({item for factor in bucket for item in factor.variables}))
        maximum_cluster = max(maximum_cluster, len(union_scope))
        if len(union_scope) > maximum_cluster_cap:
            return BucketResult("censored_peak_table", None, maximum_cluster, variable)
        product_table = np.ones((2,) * len(union_scope), dtype=float)
        for factor in bucket:
            product_table *= _aligned_table(factor, union_scope)
        axis = union_scope.index(variable)
        reduced = product_table.sum(axis=axis)
        reduced_scope = tuple(item for item in union_scope if item != variable)
        if reduced_scope:
            factors.append(BinaryFactor(f"eliminate-v{variable}", reduced_scope, reduced))
        else:
            scalar *= float(reduced)
    if len(seen) != graph.variable_count:
        raise ValueError("order omits variables")
    if factors:
        raise AssertionError("factors remain after a complete elimination order")
    return BucketResult("computed", scalar, maximum_cluster, None)


def mini_bucket_partition(
    graph: BinaryFactorGraph,
    order: Iterable[int],
    *,
    i_bound: int,
) -> MiniBucketResult:
    """Approximate a nonnegative partition function with bounded mini-buckets."""

    if i_bound < 1:
        raise ValueError("i_bound must be positive")
    factors = list(graph.factors)
    factors.extend(
        BinaryFactor(f"prior-v{variable}", (variable,), graph.priors[variable])
        for variable in range(graph.variable_count)
    )
    if any(len(factor.variables) > i_bound for factor in factors):
        raise ValueError("i_bound is smaller than an input factor scope")
    scalar = 1.0
    maximum_cluster = 0
    split_buckets = 0
    mini_bucket_count = 0
    seen: set[int] = set()
    for variable in order:
        if variable in seen or variable < 0 or variable >= graph.variable_count:
            raise ValueError("order is not a variable permutation")
        seen.add(variable)
        bucket = [factor for factor in factors if variable in factor.variables]
        factors = [factor for factor in factors if variable not in factor.variables]
        if not bucket:
            continue
        bucket.sort(key=lambda factor: (-len(factor.variables), factor.variables, factor.name))
        groups: list[list[BinaryFactor]] = []
        scopes: list[set[int]] = []
        for factor in bucket:
            candidates = [
                (len(scope.union(factor.variables)), index)
                for index, scope in enumerate(scopes)
                if len(scope.union(factor.variables)) <= i_bound
            ]
            if candidates:
                _size, index = min(candidates)
                groups[index].append(factor)
                scopes[index].update(factor.variables)
            else:
                groups.append([factor])
                scopes.append(set(factor.variables))
        if len(groups) > 1:
            split_buckets += 1
        mini_bucket_count += len(groups)
        for group, scope in zip(groups, scopes):
            union_scope = tuple(sorted(scope))
            maximum_cluster = max(maximum_cluster, len(union_scope))
            product_table = np.ones((2,) * len(union_scope), dtype=float)
            for factor in group:
                product_table *= _aligned_table(factor, union_scope)
            axis = union_scope.index(variable)
            reduced = product_table.sum(axis=axis)
            reduced_scope = tuple(item for item in union_scope if item != variable)
            if reduced_scope:
                factors.append(
                    BinaryFactor(
                        f"mini-eliminate-v{variable}-{mini_bucket_count}",
                        reduced_scope,
                        reduced,
                    )
                )
            else:
                scalar *= float(reduced)
    if len(seen) != graph.variable_count:
        raise ValueError("order omits variables")
    if factors:
        raise AssertionError("factors remain after a complete mini-bucket order")
    return MiniBucketResult(
        scalar,
        maximum_cluster,
        split_buckets,
        mini_bucket_count,
    )


def _content_merge_gain(
    left: list[BinaryFactor],
    right: list[BinaryFactor],
    variable: int,
) -> float:
    """Return a zero-safe local sum-product tightening score for one merge."""

    union_scope = tuple(sorted({
        item for factor in (*left, *right) for item in factor.variables
    }))
    left_table = np.ones((2,) * len(union_scope), dtype=float)
    right_table = np.ones((2,) * len(union_scope), dtype=float)
    for factor in left:
        left_table *= _aligned_table(factor, union_scope)
    for factor in right:
        right_table *= _aligned_table(factor, union_scope)
    axis = union_scope.index(variable)
    separated = left_table.sum(axis=axis) * right_table.sum(axis=axis)
    merged = (left_table * right_table).sum(axis=axis)
    denominator = float(separated.sum())
    if denominator <= 0.0:
        return 0.0
    gap = float((separated - merged).sum())
    return max(0.0, gap / denominator)


def mini_bucket_partition_content(
    graph: BinaryFactorGraph,
    order: Iterable[int],
    *,
    i_bound: int,
) -> MiniBucketResult:
    """Mini-bucket upper bound using factor-content-aware greedy merges.

    Starting from singleton mini-buckets, each legal pair is scored by the
    normalized local absolute tightening obtained by merging before summing
    the bucket variable.  This is the zero-safe analogue of content-based
    partition traversal for graphs containing deterministic zero factors.
    """

    if i_bound < 1:
        raise ValueError("i_bound must be positive")
    factors = list(graph.factors)
    factors.extend(
        BinaryFactor(f"prior-v{variable}", (variable,), graph.priors[variable])
        for variable in range(graph.variable_count)
    )
    if any(len(factor.variables) > i_bound for factor in factors):
        raise ValueError("i_bound is smaller than an input factor scope")
    scalar = 1.0
    maximum_cluster = 0
    split_buckets = 0
    mini_bucket_count = 0
    positive_merges = 0
    candidate_evaluations = 0
    seen: set[int] = set()
    for variable in order:
        if variable in seen or variable < 0 or variable >= graph.variable_count:
            raise ValueError("order is not a variable permutation")
        seen.add(variable)
        bucket = [factor for factor in factors if variable in factor.variables]
        factors = [factor for factor in factors if variable not in factor.variables]
        if not bucket:
            continue
        bucket.sort(key=lambda factor: (-len(factor.variables), factor.variables, factor.name))
        groups: list[list[BinaryFactor]] = [[factor] for factor in bucket]
        scopes: list[set[int]] = [set(factor.variables) for factor in bucket]
        while True:
            candidates = []
            for left in range(len(groups)):
                for right in range(left + 1, len(groups)):
                    union = scopes[left].union(scopes[right])
                    if len(union) > i_bound:
                        continue
                    gain = _content_merge_gain(groups[left], groups[right], variable)
                    candidate_evaluations += 1
                    candidates.append((-gain, len(union), left, right))
            if not candidates:
                break
            negative_gain, _scope_size, left, right = min(candidates)
            if -negative_gain > 1e-15:
                positive_merges += 1
            groups[left].extend(groups[right])
            scopes[left].update(scopes[right])
            del groups[right]
            del scopes[right]
        if len(groups) > 1:
            split_buckets += 1
        mini_bucket_count += len(groups)
        for group, scope in zip(groups, scopes):
            union_scope = tuple(sorted(scope))
            maximum_cluster = max(maximum_cluster, len(union_scope))
            product_table = np.ones((2,) * len(union_scope), dtype=float)
            for factor in group:
                product_table *= _aligned_table(factor, union_scope)
            axis = union_scope.index(variable)
            reduced = product_table.sum(axis=axis)
            reduced_scope = tuple(item for item in union_scope if item != variable)
            if reduced_scope:
                factors.append(BinaryFactor(
                    f"content-mini-eliminate-v{variable}-{mini_bucket_count}",
                    reduced_scope,
                    reduced,
                ))
            else:
                scalar *= float(reduced)
    if len(seen) != graph.variable_count:
        raise ValueError("order omits variables")
    if factors:
        raise AssertionError("factors remain after a complete mini-bucket order")
    return MiniBucketResult(
        scalar,
        maximum_cluster,
        split_buckets,
        mini_bucket_count,
        "content_local_absolute_tightening",
        positive_merges,
        candidate_evaluations,
    )
