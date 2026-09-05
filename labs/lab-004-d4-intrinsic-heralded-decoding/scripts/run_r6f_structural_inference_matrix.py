#!/usr/bin/env python3
"""Run the registered R6F exact-preserving structural inference matrix."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np

from d4_local_bp import (
    build_exact_physical_factor_graph,
    build_r6d_factor_graph,
    build_r6d_superfactor_graph,
    run_sum_product,
)
from run_r6e_bp_marginal_gate import (
    ERROR_RATES,
    MAX_ITERATIONS,
    MESSAGE_TOLERANCE,
    SCHEDULES,
    error_summary,
    exact_d4_marginals,
    selected_observations,
)
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6f-structural-inference-matrix-manifest-2026-08-29.json"
DEFAULT_BASELINE = LAB_DIR / "results/r6e-bp-marginal-gate.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6f-structural-inference-matrix.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6f-structural-inference-matrix.md"


def clustered_identity_error(raw, clustered, edge_count: int) -> float:
    raw_by_name = {factor.name: factor for factor in raw.factors}
    maximum = 0.0
    for edge in range(edge_count):
        merged = next(
            factor for factor in clustered.factors if factor.name == f"edge-superfactor-e{edge}"
        )
        blue = raw_by_name[f"pin-c0-e{edge}"].table
        green = raw_by_name[f"pin-c1-e{edge}"].table
        expected = np.zeros((2, 2, 2), dtype=float)
        for selected, blue_flow, green_flow in product((0, 1), repeat=3):
            expected[selected, blue_flow, green_flow] = (
                blue[selected, blue_flow] * green[selected, green_flow]
            )
        maximum = max(maximum, float(np.max(np.abs(merged.table - expected))))

    vertex_count = sum(factor.name.startswith("observation-v") for factor in raw.factors)
    for vertex in range(vertex_count):
        merged = next(
            factor
            for factor in clustered.factors
            if factor.name == f"vertex-superfactor-v{vertex}"
        )
        observation = raw_by_name[f"observation-v{vertex}"]
        blue = raw_by_name[f"flow-c0-v{vertex}"]
        green = raw_by_name[f"flow-c1-v{vertex}"]
        arity = len(observation.variables)
        expected = np.zeros_like(merged.table)
        for bits in product((0, 1), repeat=3 * arity):
            expected[bits] = (
                observation.table[bits[:arity]]
                * blue.table[bits[: 2 * arity]]
                * green.table[bits[:arity] + bits[2 * arity :]]
            )
        maximum = max(maximum, float(np.max(np.abs(merged.table - expected))))
    return maximum


def global_identity_error(lattice, observation, error_rate, terminal_screened) -> float:
    graph = build_exact_physical_factor_graph(
        lattice,
        observation,
        error_rate=error_rate,
        terminal_screened=terminal_screened,
    )
    table = graph.factors[0].table
    maximum = 0.0
    for bits in product((0, 1), repeat=lattice.edge_count):
        selected = np.asarray(bits, dtype=bool)
        from d4_belief_factorization import local_edge_flow_factor_weight

        expected = local_edge_flow_factor_weight(
            lattice,
            selected,
            observation,
            terminal_winding=terminal_screened,
        ).probability
        maximum = max(maximum, abs(float(table[bits]) - expected))
    return maximum


def safe_bp_row(graph, exact, physical_edge_count, base_row, damping):
    try:
        bp = run_sum_product(
            graph,
            old_message_weight=damping,
            max_iterations=MAX_ITERATIONS,
            tolerance=MESSAGE_TOLERANCE,
        )
    except ValueError as error:
        return {
            **base_row,
            "converged": False,
            "iterations": None,
            "final_maximum_message_delta": None,
            "maximum_absolute_error": None,
            "mean_absolute_error": None,
            "failure_reason": str(error),
        }
    return {
        **base_row,
        "converged": bp.converged,
        "iterations": bp.iterations,
        "final_maximum_message_delta": bp.max_message_delta,
        "failure_reason": None,
        **error_summary(bp.marginals[:physical_edge_count, 1], exact),
    }


def summarize_rows(rows):
    summary = {}
    for representation in sorted({row["representation"] for row in rows}):
        selected = [row for row in rows if row["representation"] == representation]
        converged = [row for row in selected if row["converged"]]
        exact = [
            row
            for row in converged
            if row["maximum_absolute_error"] is not None
            and row["maximum_absolute_error"] <= 1e-8
        ]
        failures = [row for row in selected if row.get("failure_reason")]
        summary[representation] = {
            "row_count": len(selected),
            "converged_count": len(converged),
            "exact_within_1e_8_count": len(exact),
            "hard_message_failure_count": len(failures),
            "maximum_error_among_converged": (
                max(row["maximum_absolute_error"] for row in converged) if converged else None
            ),
            "median_error_among_converged": (
                float(np.median([row["maximum_absolute_error"] for row in converged]))
                if converged
                else None
            ),
        }
    return summary


def run(baseline_path: Path) -> dict:
    baseline_payload = json.loads(baseline_path.read_text())
    baseline_rows = [
        {**row, "representation": "r6e_unclustered"}
        for row in baseline_payload["primitive_d4"]["rows"]
    ]
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    controls = selected_observations(catalog)

    identity_rows = []
    experiment_rows = []
    for observation_label, candidate_count, observation in controls:
        for error_rate in ERROR_RATES:
            for terminal_screened in (False, True):
                raw = build_r6d_factor_graph(
                    lattice,
                    observation,
                    error_rate=error_rate,
                    terminal_screened=terminal_screened,
                )
                clustered = build_r6d_superfactor_graph(
                    lattice,
                    observation,
                    error_rate=error_rate,
                    terminal_screened=terminal_screened,
                )
                global_graph = build_exact_physical_factor_graph(
                    lattice,
                    observation,
                    error_rate=error_rate,
                    terminal_screened=terminal_screened,
                )
                cluster_error = clustered_identity_error(raw, clustered, lattice.edge_count)
                global_error = global_identity_error(
                    lattice, observation, error_rate, terminal_screened
                )
                identity_rows.append({
                    "observation": observation_label,
                    "p": error_rate,
                    "graph_mode": "terminal_screened" if terminal_screened else "local_only",
                    "bounded_superfactor_maximum_local_product_error": cluster_error,
                    "global_physical_maximum_likelihood_error": global_error,
                })
                if cluster_error != 0.0 or global_error != 0.0:
                    raise AssertionError("R6F exact-preserving identity gate failed")

                exact, evidence, terminal_prior_weight = exact_d4_marginals(
                    lattice, observation, error_rate, terminal_screened
                )
                for representation, graph in (
                    ("bounded_superfactor", clustered),
                    ("global_physical_ceiling", global_graph),
                ):
                    for schedule, damping in SCHEDULES:
                        base = {
                            "observation": observation_label,
                            "registered_nonwinding_candidate_count": candidate_count,
                            "p": error_rate,
                            "graph_mode": (
                                "terminal_screened" if terminal_screened else "local_only"
                            ),
                            "representation": representation,
                            "schedule": schedule,
                            "old_message_weight": damping,
                            "exact_evidence": evidence,
                            "terminal_mask_unconditioned_prior_weight": terminal_prior_weight,
                        }
                        experiment_rows.append(
                            safe_bp_row(graph, exact, lattice.edge_count, base, damping)
                        )

    all_rows = baseline_rows + experiment_rows
    summary = summarize_rows(all_rows)
    if summary["global_physical_ceiling"]["exact_within_1e_8_count"] != 32:
        raise AssertionError("R6F global physical ceiling failed its exact marginal gate")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "exact_preserving_matrix_analyzed",
        "identity_gate": {
            "rows": identity_rows,
            "maximum_bounded_superfactor_local_product_error": max(
                row["bounded_superfactor_maximum_local_product_error"] for row in identity_rows
            ),
            "maximum_global_physical_likelihood_error": max(
                row["global_physical_maximum_likelihood_error"] for row in identity_rows
            ),
        },
        "matrix": {
            "rows": all_rows,
            "new_row_count": len(experiment_rows),
            "reused_r6e_row_count": len(baseline_rows),
            "summary_by_representation": summary,
        },
        "representation_complexity": {
            "r6e_unclustered": {"variable_count": 36, "factor_count_local_only": 36, "maximum_factor_arity": 6},
            "bounded_superfactor": {"variable_count": 36, "factor_count_local_only": 20, "maximum_factor_arity": 9, "scaling": "O(E+V) factors with constant local arity on trivalent lattices"},
            "global_physical_ceiling": {"variable_count": 12, "factor_count": 1, "maximum_factor_arity": 12, "table_entries": 4096, "scaling": "exponential in physical-edge count"},
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Exact primitive structural discrimination only. No correction, LER, threshold, scalable convergence, runtime scaling, or fault-tolerance claim.",
    }


def render(payload: dict) -> str:
    summary = payload["matrix"]["summary_by_representation"]
    lines = [
        "# R6F exact-preserving structural inference matrix",
        "",
        "## Registered question",
        "",
        "R6E verified exact factor messages but rejected ordinary loopy BP on the unclustered R6D graph as an exact posterior solver. R6F asks whether exact-preserving local clustering removes that pathology. It compares the frozen R6E baseline, a bounded nonnegative superfactor graph, and a deliberately non-scalable exact physical-factor ceiling on the same primitive controls.",
        "",
        "## Identity gate",
        "",
        f"The maximum local product-table error for the bounded clustering is `{payload['identity_gate']['maximum_bounded_superfactor_local_product_error']:.3e}`. The maximum entrywise error of the exact global physical likelihood table is `{payload['identity_gate']['maximum_global_physical_likelihood_error']:.3e}`. Thus both representations preserve the registered R6D finite likelihood exactly before BP is compared.",
        "",
        "## Matched marginal result",
        "",
        "| representation | converged | exact within 1e-8 | hard-message failures | median error (converged) | maximum error (converged) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for representation in ("r6e_unclustered", "bounded_superfactor", "global_physical_ceiling"):
        row = summary[representation]
        median = "n/a" if row["median_error_among_converged"] is None else f"{row['median_error_among_converged']:.6g}"
        maximum = "n/a" if row["maximum_error_among_converged"] is None else f"{row['maximum_error_among_converged']:.6g}"
        lines.append(
            f"| {representation} | {row['converged_count']}/{row['row_count']} | {row['exact_within_1e_8_count']}/{row['row_count']} | {row['hard_message_failure_count']} | {median} | {maximum} |"
        )
    cluster = summary["bounded_superfactor"]
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The global physical factor is a tree ceiling: exact agreement there confirms that the R6D likelihood and sum-product engine can recover the primitive posterior when all auxiliary-flow loops are removed. The bounded superfactor result is the discriminating arm. Any improvement is evidence that redundant local factor splitting mattered; residual bias or nonconvergence still rejects this particular bounded representation as an exact posterior solver.",
        "",
        f"The bounded graph uses 36 binary variables, 20 local factors, and maximum local arity nine. It converges on {cluster['converged_count']}/32 rows and is exact within 1e-8 on {cluster['exact_within_1e_8_count']}/32. These finite controls do not authorize correction or logical-error sampling.",
        "",
        "## Claim boundary",
        "",
        payload["claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["status"] != "registered before implementation":
        raise ValueError("R6F manifest was not in its registered pre-run state")
    payload = run(args.baseline)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
