#!/usr/bin/env python3
"""Run the registered R6I mini-bucket bounded-approximation gate."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_elimination_width import (
    condition_graph,
    greedy_elimination_audit,
    mini_bucket_partition,
)
from d4_honeycomb import paper_periodic_honeycomb
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations
from run_r6g_elimination_width_gate import build_representations, vacuum_observation


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6i-mini-bucket-approximation-gate-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6i-mini-bucket-approximation-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6i-mini-bucket-approximation-gate.md"
REPRESENTATIONS = ("r6d_unclustered", "r6f_bounded_superfactor")
ORDERS = ("global_min_fill", "auxiliary_first_min_fill")
I_BOUNDS = (10, 14, 18, 20)


def adjusted_evidence(value, edge_count):
    return value * 2.0 ** (2 * edge_count)


def clamped_bound(graph, order, variable, state, i_bound, partitioner=mini_bucket_partition):
    residual, scalar, remap = condition_graph(graph, {variable: state})
    residual_order = tuple(remap[item] for item in order if item in remap)
    result = partitioner(residual, residual_order, i_bound=i_bound)
    return scalar * result.evidence_upper_bound


def primitive_row(
    representation,
    strategy,
    graph,
    edge_count,
    i_bound,
    exact_marginals,
    exact_evidence,
    partitioner=mini_bucket_partition,
):
    audit = greedy_elimination_audit(
        graph, physical_variable_count=edge_count, strategy=strategy
    )
    partition = partitioner(graph, audit.order, i_bound=i_bound)
    adjusted = adjusted_evidence(partition.evidence_upper_bound, edge_count)
    ratio = adjusted / exact_evidence
    if ratio < 1.0 - 1e-10:
        raise AssertionError("mini-bucket violated the primitive evidence upper bound")
    pseudo = []
    adjusted_clamped_bounds = []
    clamped_ratios = []
    zero_exact_clamp_has_positive_bound = False
    for variable in range(edge_count):
        bounds = np.asarray([
            clamped_bound(graph, audit.order, variable, state, i_bound, partitioner)
            for state in (0, 1)
        ])
        pseudo.append(bounds[1] / bounds.sum())
        exact_clamped = np.asarray([
            exact_evidence * (1.0 - exact_marginals[variable]),
            exact_evidence * exact_marginals[variable],
        ])
        adjusted_bounds = bounds * 2.0 ** (2 * edge_count)
        adjusted_clamped_bounds.append(adjusted_bounds.tolist())
        if np.any(adjusted_bounds < exact_clamped - 1e-10 * exact_evidence):
            raise AssertionError("clamped mini-bucket violated an evidence upper bound")
        for approximate_value, exact_value in zip(adjusted_bounds, exact_clamped):
            if exact_value > 0:
                clamped_ratios.append(float(approximate_value / exact_value))
            elif approximate_value > 1e-14 * exact_evidence:
                zero_exact_clamp_has_positive_bound = True
    errors = np.abs(np.asarray(pseudo) - exact_marginals)
    exact_ceiling_expected = i_bound >= audit.maximum_cluster_variables
    if exact_ceiling_expected and (
        abs(ratio - 1.0) > 1e-10 or float(errors.max()) > 1e-10
    ):
        raise AssertionError("mini-bucket exact-ceiling control failed")
    return {
        "geometry": "primitive",
        "representation": representation,
        "strategy": strategy,
        "i_bound": i_bound,
        "exact_order_maximum_cluster_variables": audit.maximum_cluster_variables,
        "exact_ceiling_expected": exact_ceiling_expected,
        "realized_maximum_mini_bucket_scope": partition.maximum_cluster_variables,
        "split_bucket_count": partition.split_bucket_count,
        "mini_bucket_count": partition.mini_bucket_count,
        "partition_heuristic": partition.partition_heuristic,
        "positive_content_merge_count": partition.positive_content_merge_count,
        "content_candidate_evaluation_count": partition.content_candidate_evaluation_count,
        "adjusted_evidence_upper_bound": adjusted,
        "exact_evidence": exact_evidence,
        "evidence_upper_bound_ratio": ratio,
        "maximum_clamped_evidence_upper_bound_ratio": (
            None if zero_exact_clamp_has_positive_bound else max(clamped_ratios)
        ),
        "physical_pseudo_marginals": pseudo,
        "adjusted_clamped_evidence_upper_bounds": adjusted_clamped_bounds,
        "maximum_absolute_marginal_error": float(errors.max()),
        "mean_absolute_marginal_error": float(errors.mean()),
    }


def paper_row(representation, strategy, graph, edge_count, i_bound):
    audit = greedy_elimination_audit(
        graph, physical_variable_count=edge_count, strategy=strategy
    )
    partition = mini_bucket_partition(graph, audit.order, i_bound=i_bound)
    adjusted = adjusted_evidence(partition.evidence_upper_bound, edge_count)
    return {
        "geometry": "paper_L2",
        "representation": representation,
        "strategy": strategy,
        "i_bound": i_bound,
        "exact_order_maximum_cluster_variables": audit.maximum_cluster_variables,
        "realized_maximum_mini_bucket_scope": partition.maximum_cluster_variables,
        "split_bucket_count": partition.split_bucket_count,
        "mini_bucket_count": partition.mini_bucket_count,
        "adjusted_evidence_upper_bound": adjusted,
        "log10_adjusted_evidence_upper_bound": math.log10(adjusted),
    }


def monotonic(values, tolerance=1e-12):
    return all(right <= left + tolerance * max(1.0, abs(left)) for left, right in zip(values, values[1:]))


def run():
    catalog = build_primitive_observation_catalog()
    primitive = catalog.lattice
    label, candidate_count, observation = selected_observations(catalog)[-1]
    exact_marginals, exact_evidence, _terminal_evidence = exact_d4_marginals(
        primitive, observation, 0.10, False
    )
    if label != "maximum":
        raise AssertionError("wrong primitive validation observation")
    primitive_rows = []
    for representation, graph in build_representations(primitive, observation).items():
        for strategy in ORDERS:
            for i_bound in I_BOUNDS:
                primitive_rows.append(primitive_row(
                    representation,
                    strategy,
                    graph,
                    primitive.edge_count,
                    i_bound,
                    exact_marginals,
                    exact_evidence,
                ))

    paper = paper_periodic_honeycomb(2)
    paper_observation = vacuum_observation(paper)
    paper_rows = []
    for representation, graph in build_representations(paper, paper_observation).items():
        for strategy in ORDERS:
            for i_bound in I_BOUNDS:
                paper_rows.append(paper_row(
                    representation, strategy, graph, paper.edge_count, i_bound
                ))

    branch_summaries = []
    for representation in REPRESENTATIONS:
        for strategy in ORDERS:
            rows = [
                row for row in primitive_rows
                if row["representation"] == representation
                and row["strategy"] == strategy
            ]
            branch_summaries.append({
                "representation": representation,
                "strategy": strategy,
                "evidence_ratio_nonincreasing": monotonic([
                    row["evidence_upper_bound_ratio"] for row in rows
                ]),
                "maximum_marginal_error_nonincreasing": monotonic([
                    row["maximum_absolute_marginal_error"] for row in rows
                ]),
                "best_i_bound": min(
                    rows, key=lambda row: row["maximum_absolute_marginal_error"]
                )["i_bound"],
                "best_maximum_marginal_error": min(
                    row["maximum_absolute_marginal_error"] for row in rows
                ),
            })
    paper_spread = []
    for i_bound in I_BOUNDS:
        values = [
            row["log10_adjusted_evidence_upper_bound"]
            for row in paper_rows if row["i_bound"] == i_bound
        ]
        paper_spread.append({
            "i_bound": i_bound,
            "minimum_log10_adjusted_evidence_upper_bound": min(values),
            "maximum_log10_adjusted_evidence_upper_bound": max(values),
            "cross_branch_log10_spread": max(values) - min(values),
        })
    exact_rows = [row for row in primitive_rows if row["exact_ceiling_expected"]]
    h1_evidence = all(row["evidence_ratio_nonincreasing"] for row in branch_summaries)
    h1_marginal = all(row["maximum_marginal_error_nonincreasing"] for row in branch_summaries)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "mini_bucket_matrix_analyzed",
        "method": {
            "i_bounds": list(I_BOUNDS),
            "partition": "decreasing input scope; feasible mini-bucket with minimum resulting union scope, then stable group index",
            "evidence_semantics": "nonnegative mini-bucket upper bound",
            "pseudo_marginal_semantics": "normalized pair of separately clamped evidence upper bounds; not a posterior bound",
            "literature": [
                "https://doi.org/10.1145/636865.636866",
                "https://ojs.aaai.org/index.php/AAAI/article/view/7761"
            ],
        },
        "primitive_observation": {
            "label": label,
            "registered_nonwinding_candidate_count": candidate_count,
            "p": 0.10,
            "exact_evidence": exact_evidence,
            "exact_physical_marginals": exact_marginals.tolist(),
        },
        "primitive_rows": primitive_rows,
        "primitive_branch_summaries": branch_summaries,
        "paper_L2_rows": paper_rows,
        "paper_L2_cross_branch_spread": paper_spread,
        "exact_ceiling_row_count": len(exact_rows),
        "maximum_exact_ceiling_evidence_error": max(
            abs(row["evidence_upper_bound_ratio"] - 1.0) for row in exact_rows
        ),
        "maximum_exact_ceiling_marginal_error": max(
            row["maximum_absolute_marginal_error"] for row in exact_rows
        ),
        "hypothesis_outcomes": {
            "H1": (
                "supported for every branch and both evidence/marginal metrics"
                if h1_evidence and h1_marginal
                else f"mixed: evidence monotonic in every branch={h1_evidence}; maximum marginal error monotonic in every branch={h1_marginal}"
            ),
            "H2": f"supported on {len(exact_rows)} exact-ceiling rows",
            "H3": "evaluate from paper_L2_cross_branch_spread; nonzero spread is representation/order sensitivity, not an accuracy estimate",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Deterministic primitive approximation error and paper-L2 evidence-bound sensitivity only; normalized clamped bounds are not marginal bounds, paper-L2 has no exact accuracy reference, and no correction/LER/threshold/runtime-scaling/fault-tolerance claim is made."
    }


def render(payload):
    lines = [
        "# R6I mini-bucket bounded-approximation gate", "",
        "## Method", "",
        "Mini-bucket elimination is the lowest-cost controlled approximation implied by R6G/R6H: it retains the exact nonnegative factors and registered elimination orders, but partitions a bucket whenever its joint scope would exceed `i`. Its evidence output is an upper bound. The reported physical pseudo-marginal normalizes two separately clamped upper bounds and is therefore a diagnostic, not a marginal bound.", "",
        "## Primitive exact-reference matrix", "",
        "| representation | order | i | exact cluster | split buckets | evidence ratio | max marginal error | mean marginal error |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["primitive_rows"]:
        lines.append(
            f"| {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['exact_order_maximum_cluster_variables']} | {row['split_bucket_count']} | {row['evidence_upper_bound_ratio']:.6g} | {row['maximum_absolute_marginal_error']:.3e} | {row['mean_absolute_marginal_error']:.3e} |"
        )
    lines.extend(["", "## Paper-L2 bounded evidence diagnostic", "",
        "| representation | order | i | exact cluster | split buckets | log10 adjusted evidence upper bound |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in payload["paper_L2_rows"]:
        lines.append(
            f"| {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['exact_order_maximum_cluster_variables']} | {row['split_bucket_count']} | {row['log10_adjusted_evidence_upper_bound']:.6f} |"
        )
    lines.extend(["", "## Analysis", "",
        f"Exact-ceiling controls: `{payload['exact_ceiling_row_count']}` rows, maximum evidence-ratio error `{payload['maximum_exact_ceiling_evidence_error']:.3e}`, maximum physical-marginal error `{payload['maximum_exact_ceiling_marginal_error']:.3e}`.", "",
        f"H1: {payload['hypothesis_outcomes']['H1']}. H2: {payload['hypothesis_outcomes']['H2']}.", "",
    ])
    for spread in payload["paper_L2_cross_branch_spread"]:
        lines.append(
            f"- At `i={spread['i_bound']}`, the four paper-L2 branches span `{spread['cross_branch_log10_spread']:.3f}` decades in adjusted evidence upper bound."
        )
    lines.extend(["",
        "Paper-L2 branch spread is a sensitivity diagnostic only. Without an exact paper-L2 reference, a smaller upper bound is tighter but does not validate the normalized clamped pseudo-marginals. A richer GBP/tensor branch is warranted only where this baseline leaves material primitive error at the affordable `i` values.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary sources", "",
        "- Rina Dechter and Irina Rish, [Mini-buckets: A general scheme for bounded inference](https://doi.org/10.1145/636865.636866), JACM 50 (2003).",
        "- Eduardo Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://ojs.aaai.org/index.php/AAAI/article/view/7761), AAAI 2010.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["status"] != "registered before implementation":
        raise ValueError("R6I manifest was not in its registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
