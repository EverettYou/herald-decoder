from __future__ import annotations

import numpy as np

from d4_local_bp import (
    build_exact_physical_factor_graph,
    build_r6d_factor_graph,
    build_r6d_superfactor_graph,
    run_sum_product,
)
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations
from run_r6f_structural_inference_matrix import clustered_identity_error


def primitive_control():
    catalog = build_primitive_observation_catalog()
    _label, _count, observation = selected_observations(catalog)[0]
    return catalog.lattice, observation


def test_superfactor_tables_are_exact_products_of_r6d_tables():
    lattice, observation = primitive_control()
    raw = build_r6d_factor_graph(
        lattice, observation, error_rate=0.1, terminal_screened=False
    )
    clustered = build_r6d_superfactor_graph(
        lattice, observation, error_rate=0.1, terminal_screened=False
    )
    assert clustered_identity_error(raw, clustered, lattice.edge_count) == 0.0
    assert len(raw.factors) == (
        lattice.vertex_count + 2 * lattice.edge_count + 2 * lattice.vertex_count
    )
    assert len(clustered.factors) == lattice.edge_count + lattice.vertex_count
    assert max(len(factor.variables) for factor in clustered.factors) == 9


def test_global_physical_factor_is_exact_and_sum_product_recovers_marginals():
    lattice, observation = primitive_control()
    exact, _evidence, _terminal = exact_d4_marginals(
        lattice, observation, 0.1, False
    )
    graph = build_exact_physical_factor_graph(
        lattice, observation, error_rate=0.1, terminal_screened=False
    )
    result = run_sum_product(
        graph, old_message_weight=0.25, max_iterations=200, tolerance=1e-10
    )
    assert result.converged
    assert np.max(np.abs(result.marginals[:, 1] - exact)) <= 1e-8
