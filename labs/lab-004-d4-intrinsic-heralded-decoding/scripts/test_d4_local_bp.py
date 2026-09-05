from __future__ import annotations

import sys
import ast
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import PublicD4Observation  # noqa: E402
from d4_honeycomb import periodic_honeycomb  # noqa: E402
from d4_local_bp import (  # noqa: E402
    BinaryFactor,
    BinaryFactorGraph,
    build_r6d_dense_template,
    build_r6d_factor_graph,
    exact_marginals,
    run_sum_product,
    run_sum_product_dense_numba,
    run_r6d_dense_template,
    R6D_DENSE_BACKEND_ID,
    r6d_dense_backend_provenance,
    require_r6d_dense_backend,
    validate_r6d_dense_checkpoint,
)


def test_exact_table_messages_recover_factor_tree_marginals() -> None:
    graph = BinaryFactorGraph(
        3,
        np.asarray([[0.7, 0.3], [0.6, 0.4], [0.8, 0.2]]),
        (
            BinaryFactor("left", (0, 1), np.asarray([[1.2, 0.4], [0.3, 1.5]])),
            BinaryFactor("right", (1, 2), np.asarray([[0.9, 0.5], [0.2, 1.7]])),
        ),
    )
    exact, _evidence = exact_marginals(graph)
    for damping in (0.0, 0.25):
        result = run_sum_product(
            graph, old_message_weight=damping, max_iterations=100, tolerance=1e-12
        )
        assert result.converged
        assert np.allclose(result.marginals, exact, rtol=0.0, atol=1e-11)


def test_r6d_builder_is_nonnegative_and_terminal_projector_is_explicit() -> None:
    lattice = periodic_honeycomb(2)
    observation = PublicD4Observation(
        tuple(0 for _ in range(lattice.vertex_count)),
        tuple(-1 for _ in range(lattice.vertex_count)),
    )
    local = build_r6d_factor_graph(
        lattice, observation, error_rate=0.1, terminal_screened=False
    )
    screened = build_r6d_factor_graph(
        lattice, observation, error_rate=0.1, terminal_screened=True
    )
    assert local.variable_count == 3 * lattice.edge_count
    assert all(np.all(factor.table >= 0) for factor in local.factors)
    assert len(screened.factors) == len(local.factors) + 1
    assert screened.factors[-1].name == "finite-terminal-projector"
    assert screened.factors[-1].variables == tuple(range(lattice.edge_count))


def test_dense_numba_recurrence_matches_python_on_r6d_control() -> None:
    lattice = periodic_honeycomb(2)
    observation = PublicD4Observation(
        tuple(0 for _ in range(lattice.vertex_count)),
        tuple(-1 for _ in range(lattice.vertex_count)),
    )
    graph = build_r6d_factor_graph(
        lattice, observation, error_rate=0.2, terminal_screened=False
    )
    python = run_sum_product(
        graph, old_message_weight=0.25, max_iterations=40, tolerance=1e-8
    )
    dense = run_sum_product_dense_numba(
        graph, old_message_weight=0.25, max_iterations=40, tolerance=1e-8
    )
    assert python.converged == dense.converged
    assert python.iterations == dense.iterations
    assert python.max_message_delta == dense.max_message_delta
    assert np.array_equal(python.marginals, dense.marginals)


def test_dense_template_matches_rebuilt_r6d_graph() -> None:
    lattice = periodic_honeycomb(2)
    observation = PublicD4Observation((0,) * lattice.vertex_count, (-1,) * lattice.vertex_count)
    graph = build_r6d_factor_graph(lattice, observation, error_rate=0.2, terminal_screened=False)
    rebuilt = run_sum_product_dense_numba(graph, old_message_weight=0.25, max_iterations=40, tolerance=1e-8)
    cached = run_r6d_dense_template(build_r6d_dense_template(lattice, error_rate=0.2), observation, old_message_weight=0.25, max_iterations=40, tolerance=1e-8)
    assert rebuilt.converged == cached.converged
    assert rebuilt.iterations == cached.iterations
    assert rebuilt.max_message_delta == cached.max_message_delta
    assert np.array_equal(rebuilt.marginals, cached.marginals)


def test_production_backend_is_dense_numba_and_provenance_is_stable() -> None:
    provenance = require_r6d_dense_backend(R6D_DENSE_BACKEND_ID)
    assert provenance == r6d_dense_backend_provenance()
    assert provenance["implementation"] == R6D_DENSE_BACKEND_ID
    assert provenance["module"] == "d4_local_bp.py"
    assert len(provenance["source_sha256"]) == 64
    assert provenance["numba_available"] is True


def test_checkpoint_guard_rejects_missing_or_mismatched_backend_provenance() -> None:
    with pytest.raises(RuntimeError, match="dense-Numba provenance"):
        validate_r6d_dense_checkpoint({"rows": []})
    provenance = r6d_dense_backend_provenance()
    validate_r6d_dense_checkpoint({"backend_provenance": provenance, "rows": []})
    bad = dict(provenance, source_sha256="0" * 64)
    with pytest.raises(RuntimeError, match="dense-Numba provenance"):
        validate_r6d_dense_checkpoint({"backend_provenance": bad, "rows": []})


def test_production_scan_runners_do_not_call_python_reference_recurrence() -> None:
    scripts = [
        Path(__file__).with_name("run_r6n_default_flux_policy_comparison.py"),
        Path(__file__).with_name("run_r6v_x_only_flux_threshold_scan.py"),
    ]
    for script in scripts:
        tree = ast.parse(script.read_text(encoding="utf-8"))
        calls = [node.func.id for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        assert "run_sum_product" not in calls
        assert "run_r6d_dense_template" in calls
