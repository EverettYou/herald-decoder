from __future__ import annotations

import numpy as np

from d4_elimination_width import (
    exact_bucket_partition,
    exact_cutset_partition,
    greedy_elimination_audit,
    mini_bucket_partition,
    mini_bucket_partition_content,
)
from d4_local_bp import BinaryFactor, BinaryFactorGraph, exact_marginals
from run_r6m_approximation_family_preflight import build_join_graph_decomposition


def graph(scopes):
    variable_count = 1 + max(variable for scope in scopes for variable in scope)
    factors = tuple(
        BinaryFactor(f"f{index}", tuple(scope), np.ones((2,) * len(scope)))
        for index, scope in enumerate(scopes)
    )
    return BinaryFactorGraph(
        variable_count, np.tile((0.6, 0.4), (variable_count, 1)), factors
    )


def test_registered_width_controls():
    path = graph(((0, 1), (1, 2), (2, 3)))
    cycle = graph(((0, 1), (1, 2), (2, 3), (3, 0)))
    clique = graph(((0, 1, 2, 3),))
    assert greedy_elimination_audit(
        path, physical_variable_count=4, strategy="global_min_fill"
    ).induced_width == 1
    assert greedy_elimination_audit(
        cycle, physical_variable_count=4, strategy="global_min_fill"
    ).induced_width == 2
    assert greedy_elimination_audit(
        clique, physical_variable_count=4, strategy="global_min_fill"
    ).induced_width == 3


def test_bucket_partition_matches_brute_force_and_obeys_cap():
    model = BinaryFactorGraph(
        4,
        np.asarray(((0.7, 0.3), (0.6, 0.4), (0.8, 0.2), (0.55, 0.45))),
        (
            BinaryFactor("a", (0, 1), np.asarray(((1.0, 0.2), (0.4, 1.3)))),
            BinaryFactor("b", (1, 2), np.asarray(((0.7, 1.1), (1.2, 0.3)))),
            BinaryFactor("c", (2, 3), np.asarray(((1.4, 0.5), (0.6, 1.0)))),
        ),
    )
    _marginals, exact_evidence = exact_marginals(model)
    audit = greedy_elimination_audit(
        model, physical_variable_count=4, strategy="global_min_fill"
    )
    result = exact_bucket_partition(model, audit.order, maximum_cluster_cap=4)
    assert result.status == "computed"
    assert np.isclose(result.evidence, exact_evidence, rtol=1e-12, atol=1e-14)
    censored = exact_bucket_partition(model, audit.order, maximum_cluster_cap=1)
    assert censored.status == "censored_peak_table"
    assert censored.evidence is None


def test_cutset_partition_reconstructs_exact_evidence_and_reduces_structure():
    model = graph(((0, 1, 2), (1, 2, 3)))
    _marginals, exact_evidence = exact_marginals(model)
    full = greedy_elimination_audit(
        model, physical_variable_count=4, strategy="global_min_fill"
    )
    residual = greedy_elimination_audit(
        model,
        physical_variable_count=4,
        strategy="global_min_fill",
        excluded_variables=(1,),
    )
    result = exact_cutset_partition(
        model, full.order, (1,), maximum_cluster_cap=4
    )
    assert result.status == "computed"
    assert result.branch_count == 2
    assert np.isclose(result.evidence, exact_evidence, rtol=1e-12, atol=1e-14)
    assert residual.maximum_cluster_variables < full.maximum_cluster_variables


def test_mini_bucket_is_an_upper_bound_and_reaches_exact_ceiling():
    model = BinaryFactorGraph(
        4,
        np.asarray(((0.7, 0.3), (0.6, 0.4), (0.8, 0.2), (0.55, 0.45))),
        (
            BinaryFactor("a", (0, 1), np.asarray(((1.0, 0.2), (0.4, 1.3)))),
            BinaryFactor("b", (1, 2), np.asarray(((0.7, 1.1), (1.2, 0.3)))),
            BinaryFactor("c", (1, 3), np.asarray(((1.4, 0.5), (0.6, 1.0)))),
        ),
    )
    _marginals, exact_evidence = exact_marginals(model)
    order = (1, 0, 2, 3)
    approximate = mini_bucket_partition(model, order, i_bound=2)
    ceiling = mini_bucket_partition(model, order, i_bound=4)
    assert approximate.evidence_upper_bound >= exact_evidence - 1e-14
    assert approximate.split_bucket_count > 0
    assert np.isclose(ceiling.evidence_upper_bound, exact_evidence, rtol=1e-12)
    assert ceiling.split_bucket_count == 0


def test_content_mini_bucket_is_deterministic_valid_and_exact_at_ceiling():
    model = BinaryFactorGraph(
        4,
        np.asarray(((0.7, 0.3), (0.6, 0.4), (0.8, 0.2), (0.55, 0.45))),
        (
            BinaryFactor("a", (0, 1), np.asarray(((1.0, 0.0), (0.4, 1.3)))),
            BinaryFactor("b", (1, 2), np.asarray(((0.7, 1.1), (1.2, 0.0)))),
            BinaryFactor("c", (1, 3), np.asarray(((1.4, 0.5), (0.0, 1.0)))),
        ),
    )
    _marginals, exact_evidence = exact_marginals(model)
    order = (1, 0, 2, 3)
    first = mini_bucket_partition_content(model, order, i_bound=2)
    second = mini_bucket_partition_content(model, order, i_bound=2)
    ceiling = mini_bucket_partition_content(model, order, i_bound=4)
    assert first == second
    assert first.evidence_upper_bound >= exact_evidence - 1e-14
    assert first.content_candidate_evaluation_count > 0
    assert first.partition_heuristic == "content_local_absolute_tightening"
    assert np.isclose(ceiling.evidence_upper_bound, exact_evidence, rtol=1e-12)
    assert ceiling.split_bucket_count == 0


def test_join_graph_trace_obeys_assignment_cap_labels_and_running_intersection():
    model = BinaryFactorGraph(
        4,
        np.asarray(((0.7, 0.3), (0.6, 0.4), (0.8, 0.2), (0.55, 0.45))),
        (
            BinaryFactor("a", (0, 1), np.asarray(((1.0, 0.2), (0.4, 1.3)))),
            BinaryFactor("b", (1, 2), np.asarray(((0.7, 1.1), (1.2, 0.3)))),
            BinaryFactor("c", (1, 3), np.asarray(((1.4, 0.5), (0.6, 1.0)))),
        ),
    )
    result = build_join_graph_decomposition(model, (1, 0, 2, 3), i_bound=2)
    assert result["valid"]
    assert result["factor_assignment_valid"]
    assert result["scope_cap_valid"]
    assert result["arc_labels_valid"]
    assert result["running_intersection_valid"]
    assert result["maximum_cluster_variables"] <= 2
