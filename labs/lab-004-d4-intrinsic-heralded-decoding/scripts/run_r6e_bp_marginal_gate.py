#!/usr/bin/env python3
"""Run the registered R6E exact-message and small-loopy marginal gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation, local_edge_flow_factor_weight
from d4_honeycomb import generate_loop_constraints
from d4_local_bp import (
    BinaryFactor,
    BinaryFactorGraph,
    build_r6d_factor_graph,
    exact_marginals,
    run_sum_product,
)
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6e-bp-marginal-gate-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6e-bp-marginal-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6e-bp-marginal-gate.md"
SCHEDULES = (
    ("synchronous_raw", 0.0),
    ("synchronous_damped_025", 0.25),
)
ERROR_RATES = (0.10, 0.30)
MAX_ITERATIONS = 200
MESSAGE_TOLERANCE = 1e-10


def synthetic_graph(single_cycle: bool) -> BinaryFactorGraph:
    priors = np.asarray(
        [[0.68, 0.32], [0.57, 0.43], [0.74, 0.26], [0.61, 0.39]], dtype=float
    )
    pair_tables = (
        np.asarray([[1.4, 0.3], [0.5, 1.2]], dtype=float),
        np.asarray([[1.1, 0.6], [0.2, 1.7]], dtype=float),
        np.asarray([[1.3, 0.4], [0.7, 1.0]], dtype=float),
        np.asarray([[0.9, 1.2], [1.5, 0.3]], dtype=float),
    )
    scopes = [(0, 1), (1, 2), (2, 3)]
    if single_cycle:
        scopes.append((3, 0))
    factors = tuple(
        BinaryFactor(f"pair-{index}", scope, pair_tables[index])
        for index, scope in enumerate(scopes)
    )
    return BinaryFactorGraph(4, priors, factors)


def exact_d4_marginals(lattice, observation, error_rate, terminal_screened):
    weights = np.zeros(1 << lattice.edge_count, dtype=float)
    terminal_prior_weight = 0.0
    for mask in range(1 << lattice.edge_count):
        selected = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)], dtype=bool
        )
        local = local_edge_flow_factor_weight(
            lattice,
            selected,
            observation,
            terminal_winding=terminal_screened,
        )
        prior = (error_rate ** int(selected.sum())) * (
            (1.0 - error_rate) ** (lattice.edge_count - int(selected.sum()))
        )
        analysis = generate_loop_constraints(lattice, selected)
        if any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        ):
            terminal_prior_weight += prior
        weights[mask] = prior * local.probability
    evidence = float(weights.sum())
    if evidence <= 0:
        raise ValueError("D4 control observation has zero evidence")
    probabilities = weights / evidence
    marginals = np.zeros(lattice.edge_count, dtype=float)
    for mask, probability in enumerate(probabilities):
        for edge in range(lattice.edge_count):
            if (mask >> edge) & 1:
                marginals[edge] += probability
    return marginals, evidence, terminal_prior_weight


def selected_observations(catalog):
    rows = sorted(
        (
            (len(candidates), key)
            for key, candidates in catalog.observations.items()
            if len(candidates) > 1
        ),
        key=lambda item: (item[0], item[1]),
    )
    indices = (0, (len(rows) - 1) // 3, 2 * (len(rows) - 1) // 3, len(rows) - 1)
    labels = ("minimum_multi", "lower_stratum", "upper_stratum", "maximum")
    return tuple(
        (label, rows[index][0], PublicD4Observation(*rows[index][1]))
        for label, index in zip(labels, indices, strict=True)
    )


def error_summary(approximate, exact):
    errors = np.abs(np.asarray(approximate) - np.asarray(exact))
    return {
        "maximum_absolute_error": float(errors.max()),
        "mean_absolute_error": float(errors.mean()),
    }


def run() -> dict:
    synthetic_rows = []
    tree_failures = 0
    for graph_kind, graph in (
        ("factor_tree", synthetic_graph(False)),
        ("single_cycle", synthetic_graph(True)),
    ):
        exact, evidence = exact_marginals(graph)
        for schedule, damping in SCHEDULES:
            bp = run_sum_product(
                graph,
                old_message_weight=damping,
                max_iterations=MAX_ITERATIONS,
                tolerance=MESSAGE_TOLERANCE,
            )
            summary = error_summary(bp.marginals[:, 1], exact[:, 1])
            if graph_kind == "factor_tree" and (
                not bp.converged or summary["maximum_absolute_error"] > 1e-10
            ):
                tree_failures += 1
            synthetic_rows.append({
                "graph": graph_kind,
                "schedule": schedule,
                "old_message_weight": damping,
                "exact_evidence": evidence,
                "converged": bp.converged,
                "iterations": bp.iterations,
                "final_maximum_message_delta": bp.max_message_delta,
                **summary,
            })

    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    controls = selected_observations(catalog)
    d4_rows = []
    for observation_label, candidate_count, observation in controls:
        for error_rate in ERROR_RATES:
            for terminal_screened in (False, True):
                exact, evidence, terminal_prior_weight = exact_d4_marginals(
                    lattice, observation, error_rate, terminal_screened
                )
                graph = build_r6d_factor_graph(
                    lattice,
                    observation,
                    error_rate=error_rate,
                    terminal_screened=terminal_screened,
                )
                for schedule, damping in SCHEDULES:
                    base_row = {
                        "observation": observation_label,
                        "registered_nonwinding_candidate_count": candidate_count,
                        "p": error_rate,
                        "graph_mode": "terminal_screened" if terminal_screened else "local_only",
                        "schedule": schedule,
                        "old_message_weight": damping,
                        "exact_evidence": evidence,
                        "terminal_mask_unconditioned_prior_weight": terminal_prior_weight,
                    }
                    try:
                        bp = run_sum_product(
                            graph,
                            old_message_weight=damping,
                            max_iterations=MAX_ITERATIONS,
                            tolerance=MESSAGE_TOLERANCE,
                        )
                    except ValueError as error:
                        d4_rows.append({
                            **base_row,
                            "converged": False,
                            "iterations": None,
                            "final_maximum_message_delta": None,
                            "maximum_absolute_error": None,
                            "mean_absolute_error": None,
                            "failure_reason": str(error),
                        })
                        continue
                    summary = error_summary(bp.marginals[: lattice.edge_count, 1], exact)
                    d4_rows.append({
                        **base_row,
                        "converged": bp.converged,
                        "iterations": bp.iterations,
                        "final_maximum_message_delta": bp.max_message_delta,
                        "failure_reason": None,
                        **summary,
                    })

    if tree_failures:
        raise AssertionError("R6E exact factor-tree gate failed")
    converged_rows = [row for row in d4_rows if row["converged"]]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "tree_messages_verified_loopy_matrix_analyzed",
        "synthetic": {
            "rows": synthetic_rows,
            "tree_failure_count": tree_failures,
            "tree_maximum_absolute_error": max(
                row["maximum_absolute_error"]
                for row in synthetic_rows
                if row["graph"] == "factor_tree"
            ),
        },
        "primitive_d4": {
            "observation_selection": [
                {"label": label, "registered_nonwinding_candidate_count": count}
                for label, count, _observation in controls
            ],
            "rows": d4_rows,
            "row_count": len(d4_rows),
            "converged_count": len(converged_rows),
            "maximum_marginal_error_among_converged": (
                max(row["maximum_absolute_error"] for row in converged_rows)
                if converged_rows else None
            ),
            "exact_within_1e_8_count": sum(
                row["converged"] and row["maximum_absolute_error"] <= 1e-8
                for row in d4_rows
            ),
        },
        "implementation": {
            "factor_messages": "exact enumeration of every nonnegative binary factor table",
            "variable_messages": "prior times all other incoming factor messages",
            "schedules": [schedule for schedule, _damping in SCHEDULES],
            "maximum_iterations": MAX_ITERATIONS,
            "message_tolerance": MESSAGE_TOLERANCE,
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Tree message correctness and descriptive finite primitive loopy-BP marginal evidence only. No correction, LER, threshold, scalable convergence, runtime scaling, or fault-tolerance claim.",
    }
    return payload


def render(payload):
    synthetic = payload["synthetic"]
    primitive = payload["primitive_d4"]
    rows = primitive["rows"]
    by_schedule = {}
    for schedule in ("synchronous_raw", "synchronous_damped_025"):
        selected = [row for row in rows if row["schedule"] == schedule]
        converged = [row for row in selected if row["converged"]]
        by_schedule[schedule] = {
            "converged": len(converged),
            "total": len(selected),
            "max_error": max((row["maximum_absolute_error"] for row in converged), default=None),
        }
    local = [row for row in rows if row["graph_mode"] == "local_only"]
    screened = [row for row in rows if row["graph_mode"] == "terminal_screened"]
    return "\n".join([
        "# R6E exact-message and small-graph BP marginal gate",
        "",
        "## Implementation gate",
        "",
        f"Both registered schedules reproduce the brute-force factor-tree marginals; the largest tree error is {synthetic['tree_maximum_absolute_error']:.3e}. Factor-to-variable messages explicitly sum every assignment of each nonnegative R6D table, and variable messages multiply the prior by every other incoming factor message.",
        "",
        "## Loopy primitive result",
        "",
        f"The matrix contains {primitive['row_count']} matched primitive-D4 runs across four observation strata, two physical error rates, local-only versus terminal-screened graphs, and two schedules. Raw synchronous BP converges on {by_schedule['synchronous_raw']['converged']}/{by_schedule['synchronous_raw']['total']} rows; damping 0.25 converges on {by_schedule['synchronous_damped_025']['converged']}/{by_schedule['synchronous_damped_025']['total']} rows. Among converged rows, the largest physical-edge marginal error is {primitive['maximum_marginal_error_among_converged']!r}; {primitive['exact_within_1e_8_count']}/{primitive['row_count']} rows both converge and agree within `1e-8`.",
        "",
        f"The local-only and terminal-screened branches each contain {len(local)} and {len(screened)} matched rows. They are intentionally separate: the local R6D factors represent the observation likelihood, whereas the finite 12-edge terminal projector enforces the current ground-state-relative winding policy. The projector is an exact primitive control, not a scalable localization.",
        "",
        "## Interpretation",
        "",
        "Passing the tree gate verifies message arithmetic. Any loopy bias or nonconvergence is an algorithmic property of this factorization and schedule, not a likelihood error and not something that can be removed by relabeling the result. The next gate must be chosen from the observed failure mode: fixed-point approximation if converged but biased, or schedule/region-graph work if nonconvergent.",
        "",
        "## Claim boundary",
        "",
        payload["claim_boundary"],
        "",
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    json.loads(args.manifest.read_text())
    payload = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render(payload))
    print(json.dumps({
        "status": payload["status"],
        "synthetic": {k: v for k, v in payload["synthetic"].items() if k != "rows"},
        "primitive": {k: v for k, v in payload["primitive_d4"].items() if k != "rows"},
    }, indent=2))


if __name__ == "__main__":
    main()
