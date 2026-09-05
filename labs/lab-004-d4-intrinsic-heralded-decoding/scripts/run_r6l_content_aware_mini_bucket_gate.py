#!/usr/bin/env python3
"""Run the registered R6L factor-content-aware mini-bucket gate."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_elimination_width import mini_bucket_partition_content
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations
from run_r6i_mini_bucket_gate import I_BOUNDS, ORDERS, REPRESENTATIONS, primitive_row
from run_r6j_multi_observation_mini_bucket_validation import P_VALUES, representations


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6l-content-aware-mini-bucket-gate-manifest-2026-08-29.json"
DEFAULT_BASELINE = LAB_DIR / "results/r6j-multi-observation-mini-bucket-validation.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6l-content-aware-mini-bucket-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6l-content-aware-mini-bucket-gate.md"
KEYS = ("observation", "p", "representation", "strategy", "i_bound")


def key(row):
    return tuple(row[item] for item in KEYS)


def useful(row):
    return row["maximum_absolute_marginal_error"] <= 1e-2


def run(baseline_path=DEFAULT_BASELINE):
    baseline_payload = json.loads(Path(baseline_path).read_text())
    baseline_rows = {key(row): row for row in baseline_payload["rows"]}
    if len(baseline_rows) != 128:
        raise AssertionError("R6J baseline cohort is incomplete")

    started = time.perf_counter()
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    content_rows = []
    for label, candidate_count, observation in selected_observations(catalog):
        for p in P_VALUES:
            exact_marginals, exact_evidence, _terminal = exact_d4_marginals(
                lattice, observation, p, False
            )
            for representation, graph in representations(lattice, observation, p).items():
                for strategy in ORDERS:
                    for i_bound in I_BOUNDS:
                        row = primitive_row(
                            representation,
                            strategy,
                            graph,
                            lattice.edge_count,
                            i_bound,
                            exact_marginals,
                            exact_evidence,
                            partitioner=mini_bucket_partition_content,
                        )
                        row.update({
                            "observation": label,
                            "registered_nonwinding_candidate_count": candidate_count,
                            "p": p,
                            "prospective_useful_accuracy": useful(row),
                        })
                        content_rows.append(row)
    runtime = time.perf_counter() - started
    if len(content_rows) != 128 or set(map(key, content_rows)) != set(baseline_rows):
        raise AssertionError("R6L candidate cohort does not match R6J")

    comparisons = []
    tolerance = 1e-12
    for content in content_rows:
        baseline = baseline_rows[key(content)]
        delta = (
            content["maximum_absolute_marginal_error"]
            - baseline["maximum_absolute_marginal_error"]
        )
        evidence_delta = (
            content["evidence_upper_bound_ratio"]
            - baseline["evidence_upper_bound_ratio"]
        )
        comparisons.append({
            **{item: content[item] for item in KEYS},
            "scope_maximum_marginal_error": baseline["maximum_absolute_marginal_error"],
            "content_maximum_marginal_error": content["maximum_absolute_marginal_error"],
            "content_minus_scope_maximum_marginal_error": delta,
            "scope_evidence_upper_bound_ratio": baseline["evidence_upper_bound_ratio"],
            "content_evidence_upper_bound_ratio": content["evidence_upper_bound_ratio"],
            "content_minus_scope_evidence_ratio": evidence_delta,
            "scope_useful": useful(baseline),
            "content_useful": useful(content),
            "marginal_outcome": (
                "improved" if delta < -tolerance
                else "worsened" if delta > tolerance
                else "tied"
            ),
            "evidence_outcome": (
                "tighter" if evidence_delta < -tolerance
                else "looser" if evidence_delta > tolerance
                else "tied"
            ),
        })

    low = [row for row in comparisons if row["i_bound"] <= 14]
    aggregates = []
    for representation in REPRESENTATIONS:
        for strategy in ORDERS:
            for i_bound in I_BOUNDS:
                branch = [
                    row for row in comparisons
                    if row["representation"] == representation
                    and row["strategy"] == strategy
                    and row["i_bound"] == i_bound
                ]
                aggregates.append({
                    "representation": representation,
                    "strategy": strategy,
                    "i_bound": i_bound,
                    "condition_count": len(branch),
                    "scope_useful_count": sum(row["scope_useful"] for row in branch),
                    "content_useful_count": sum(row["content_useful"] for row in branch),
                    "content_improved_count": sum(row["marginal_outcome"] == "improved" for row in branch),
                    "content_worsened_count": sum(row["marginal_outcome"] == "worsened" for row in branch),
                    "median_scope_error": float(np.median([row["scope_maximum_marginal_error"] for row in branch])),
                    "median_content_error": float(np.median([row["content_maximum_marginal_error"] for row in branch])),
                    "worst_content_error": max(row["content_maximum_marginal_error"] for row in branch),
                })

    content_exact = [row for row in content_rows if row["exact_ceiling_expected"]]
    content_uniform_low = [
        row for row in aggregates
        if row["i_bound"] <= 14 and row["content_useful_count"] == 8
    ]
    scope_uniform_low = [
        row for row in aggregates
        if row["i_bound"] <= 14 and row["scope_useful_count"] == 8
    ]
    changed = [
        row for row in comparisons
        if row["marginal_outcome"] != "tied" or row["evidence_outcome"] != "tied"
    ]
    low_improved = sum(row["marginal_outcome"] == "improved" for row in low)
    low_worsened = sum(row["marginal_outcome"] == "worsened" for row in low)
    scope_low_useful = sum(row["scope_useful"] for row in low)
    content_low_useful = sum(row["content_useful"] for row in low)
    h1 = bool(changed) and any(row["positive_content_merge_count"] for row in content_rows)
    h2 = low_improved > low_worsened and content_low_useful > scope_low_useful
    h3 = bool(content_uniform_low)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "content_aware_partition_gate_analyzed",
        "method": {
            "baseline": "R6J scope-first-fit mini-bucket",
            "candidate": "zero-safe content-local normalized absolute tightening",
            "literature": "https://doi.org/10.1609/aaai.v24i1.7761",
            "hard_zero_adaptation": "local normalized sum-product gap replaces log-relative error",
            "candidate_runtime_seconds": runtime,
        },
        "content_rows": content_rows,
        "matched_comparisons": comparisons,
        "aggregates": aggregates,
        "exact_ceiling": {
            "row_count": len(content_exact),
            "maximum_evidence_ratio_error": max(abs(row["evidence_upper_bound_ratio"] - 1.0) for row in content_exact),
            "maximum_marginal_error": max(row["maximum_absolute_marginal_error"] for row in content_exact),
        },
        "diagnostics": {
            "changed_matched_row_count": len(changed),
            "positive_content_merge_row_count": sum(bool(row["positive_content_merge_count"]) for row in content_rows),
            "low_i_content_improved_count": low_improved,
            "low_i_content_worsened_count": low_worsened,
            "low_i_content_tied_count": len(low) - low_improved - low_worsened,
            "scope_low_i_useful_count": scope_low_useful,
            "content_low_i_useful_count": content_low_useful,
            "scope_uniform_low_i_branch_count": len(scope_uniform_low),
            "content_uniform_low_i_branch_count": len(content_uniform_low),
            "low_i_evidence_tighter_count": sum(row["evidence_outcome"] == "tighter" for row in low),
            "low_i_evidence_looser_count": sum(row["evidence_outcome"] == "looser" for row in low),
        },
        "hypothesis_outcomes": {
            "H1": "supported" if h1 else "rejected",
            "H2": "supported" if h2 else "rejected or mixed",
            "H3": "supported" if h3 else "rejected",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Deterministic primitive posterior method comparison only; no paper-L2 accuracy, decoder correction, LER, threshold, runtime scaling, or fault-tolerance claim.",
    }


def render(payload):
    diag = payload["diagnostics"]
    exact = payload["exact_ceiling"]
    lines = [
        "# R6L factor-content-aware mini-bucket partition gate", "",
        "## Question and method", "",
        "R6L changes one variable in the R6J exact-reference cohort: scope-first-fit partitioning is replaced by a bottom-up factor-content-aware traversal. Each legal merge is scored by its normalized local absolute reduction between separately and jointly eliminated nonnegative factor products. This is a zero-safe project adaptation of Rollon and Dechter's content-based framework because the D4 factors contain exact zeros; it is not their logarithmic heuristic verbatim.", "",
        "## Matched aggregate comparison", "",
        "| representation | order | i | scope useful / 8 | content useful / 8 | improved | worsened | median scope error | median content error | worst content error |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["aggregates"]:
        lines.append(
            f"| {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['scope_useful_count']}/8 | {row['content_useful_count']}/8 | {row['content_improved_count']} | {row['content_worsened_count']} | {row['median_scope_error']:.3e} | {row['median_content_error']:.3e} | {row['worst_content_error']:.3e} |"
        )
    lines.extend([
        "", "## Validity and discrimination", "",
        f"All `{exact['row_count']}` content exact-ceiling rows pass, with maximum evidence-ratio error `{exact['maximum_evidence_ratio_error']:.3e}` and maximum marginal error `{exact['maximum_marginal_error']:.3e}`. Candidate runtime is `{payload['method']['candidate_runtime_seconds']:.2f}` seconds.", "",
        f"The content traversal changes `{diag['changed_matched_row_count']}` matched rows and selects at least one positive local-tightening merge in `{diag['positive_content_merge_row_count']}` candidate rows. At `i<=14`, it improves `{diag['low_i_content_improved_count']}` marginal rows, worsens `{diag['low_i_content_worsened_count']}`, and ties `{diag['low_i_content_tied_count']}`. Useful low-`i` rows change from `{diag['scope_low_i_useful_count']}` to `{diag['content_low_i_useful_count']}`; uniformly useful branches change from `{diag['scope_uniform_low_i_branch_count']}` to `{diag['content_uniform_low_i_branch_count']}`. Evidence bounds become tighter on `{diag['low_i_evidence_tighter_count']}` low-`i` rows and looser on `{diag['low_i_evidence_looser_count']}`.", "",
        f"H1 {payload['hypothesis_outcomes']['H1']}; H2 {payload['hypothesis_outcomes']['H2']}; H3 {payload['hypothesis_outcomes']['H3']}.", "",
        "## Interpretation rule", "",
        "If factor contents change bounds but do not improve uniform pseudo-marginal accuracy, further mini-bucket packing optimization stops: the next comparison must change the approximation family (explicit regions/join graph versus a bounded tensor contraction). Evidence-bound tightness alone never promotes a decoder.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary source", "",
        "- Emma Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://doi.org/10.1609/aaai.v24i1.7761), AAAI 2010.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["status"] != "registered before implementation":
        raise ValueError("R6L manifest was not in its registered pre-run state")
    payload = run(args.baseline)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
