#!/usr/bin/env python3
"""Compare independent greedy mini-buckets with a monotone valid-bound envelope."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from run_r6i_mini_bucket_gate import I_BOUNDS, ORDERS, REPRESENTATIONS
from run_r6j_multi_observation_mini_bucket_validation import P_VALUES, run as run_r6j


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6k-monotone-bound-envelope-gate-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6k-monotone-bound-envelope-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6k-monotone-bound-envelope-gate.md"


def nonincreasing(values, tolerance=1e-12):
    return all(
        right <= left + tolerance * max(1.0, abs(left))
        for left, right in zip(values, values[1:])
    )


def run():
    source = run_r6j()
    greedy_rows = source["rows"]
    output_rows = []
    observations = source["method"]["observations"]
    for observation in observations:
        for p in P_VALUES:
            for representation in REPRESENTATIONS:
                for strategy in ORDERS:
                    sequence = sorted(
                        [
                            row for row in greedy_rows
                            if row["observation"] == observation
                            and row["p"] == p
                            and row["representation"] == representation
                            and row["strategy"] == strategy
                        ],
                        key=lambda row: row["i_bound"],
                    )
                    if [row["i_bound"] for row in sequence] != list(I_BOUNDS):
                        raise AssertionError("incomplete R6K source sequence")
                    exact_row = sequence[-1]
                    if not exact_row["exact_ceiling_expected"]:
                        raise AssertionError("R6K lacks an exact i=20 ceiling")
                    exact_marginals = np.asarray(exact_row["physical_pseudo_marginals"])
                    exact_clamped = np.asarray(
                        exact_row["adjusted_clamped_evidence_upper_bounds"]
                    )
                    envelope_evidence = float("inf")
                    envelope_clamped = np.full_like(exact_clamped, np.inf)
                    for greedy in sequence:
                        greedy_clamped = np.asarray(
                            greedy["adjusted_clamped_evidence_upper_bounds"]
                        )
                        envelope_evidence = min(
                            envelope_evidence, greedy["adjusted_evidence_upper_bound"]
                        )
                        envelope_clamped = np.minimum(envelope_clamped, greedy_clamped)
                        if envelope_evidence > greedy["adjusted_evidence_upper_bound"] + 1e-14:
                            raise AssertionError("envelope exceeds greedy evidence bound")
                        if envelope_evidence < greedy["exact_evidence"] - 1e-10 * greedy["exact_evidence"]:
                            raise AssertionError("envelope fell below exact evidence")
                        if np.any(envelope_clamped < exact_clamped - 1e-10 * greedy["exact_evidence"]):
                            raise AssertionError("clamped envelope fell below exact evidence")
                        envelope_pseudo = envelope_clamped[:, 1] / envelope_clamped.sum(axis=1)
                        envelope_errors = np.abs(envelope_pseudo - exact_marginals)
                        shared = {
                            "observation": observation,
                            "p": p,
                            "representation": representation,
                            "strategy": strategy,
                            "i_bound": greedy["i_bound"],
                        }
                        output_rows.append({
                            **shared,
                            "branch": "independent_greedy",
                            "evidence_upper_bound_ratio": greedy["evidence_upper_bound_ratio"],
                            "maximum_absolute_marginal_error": greedy["maximum_absolute_marginal_error"],
                            "mean_absolute_marginal_error": greedy["mean_absolute_marginal_error"],
                            "prospective_useful_accuracy": greedy["prospective_useful_accuracy"],
                        })
                        output_rows.append({
                            **shared,
                            "branch": "cumulative_valid_bound_envelope",
                            "evidence_upper_bound_ratio": envelope_evidence / greedy["exact_evidence"],
                            "maximum_absolute_marginal_error": float(envelope_errors.max()),
                            "mean_absolute_marginal_error": float(envelope_errors.mean()),
                            "prospective_useful_accuracy": float(envelope_errors.max()) <= 1e-2,
                            "maximum_error_change_vs_greedy": float(
                                envelope_errors.max() - greedy["maximum_absolute_marginal_error"]
                            ),
                        })
    if len(output_rows) != 256:
        raise AssertionError("R6K matrix is incomplete")

    aggregates = []
    for branch in ("independent_greedy", "cumulative_valid_bound_envelope"):
        for representation in REPRESENTATIONS:
            for strategy in ORDERS:
                for i_bound in I_BOUNDS:
                    rows = [
                        row for row in output_rows
                        if row["branch"] == branch
                        and row["representation"] == representation
                        and row["strategy"] == strategy
                        and row["i_bound"] == i_bound
                    ]
                    aggregates.append({
                        "branch": branch,
                        "representation": representation,
                        "strategy": strategy,
                        "i_bound": i_bound,
                        "condition_count": len(rows),
                        "useful_accuracy_count": sum(row["prospective_useful_accuracy"] for row in rows),
                        "median_maximum_marginal_error": float(np.median([
                            row["maximum_absolute_marginal_error"] for row in rows
                        ])),
                        "worst_maximum_marginal_error": max(
                            row["maximum_absolute_marginal_error"] for row in rows
                        ),
                    })

    monotonicity = []
    for branch in ("independent_greedy", "cumulative_valid_bound_envelope"):
        for observation in observations:
            for p in P_VALUES:
                for representation in REPRESENTATIONS:
                    for strategy in ORDERS:
                        rows = sorted(
                            [
                                row for row in output_rows
                                if row["branch"] == branch
                                and row["observation"] == observation
                                and row["p"] == p
                                and row["representation"] == representation
                                and row["strategy"] == strategy
                            ],
                            key=lambda row: row["i_bound"],
                        )
                        monotonicity.append({
                            "branch": branch,
                            "observation": observation,
                            "p": p,
                            "representation": representation,
                            "strategy": strategy,
                            "evidence_nonincreasing": nonincreasing([
                                row["evidence_upper_bound_ratio"] for row in rows
                            ]),
                            "marginal_error_nonincreasing": nonincreasing([
                                row["maximum_absolute_marginal_error"] for row in rows
                            ]),
                        })

    diagnostics = {}
    for branch in ("independent_greedy", "cumulative_valid_bound_envelope"):
        branch_monotonicity = [row for row in monotonicity if row["branch"] == branch]
        low_i = [
            row for row in aggregates if row["branch"] == branch and row["i_bound"] <= 14
        ]
        diagnostics[branch] = {
            "evidence_monotonicity_violation_count": sum(
                not row["evidence_nonincreasing"] for row in branch_monotonicity
            ),
            "marginal_monotonicity_violation_count": sum(
                not row["marginal_error_nonincreasing"] for row in branch_monotonicity
            ),
            "uniformly_useful_low_i_branch_count": sum(
                row["useful_accuracy_count"] == 8 for row in low_i
            ),
            "total_useful_low_i_rows": sum(row["useful_accuracy_count"] for row in low_i),
        }
    changes = [
        row["maximum_error_change_vs_greedy"]
        for row in output_rows
        if row["branch"] == "cumulative_valid_bound_envelope"
    ]
    diagnostics["matched_error_change"] = {
        "improved_row_count": sum(value < -1e-12 for value in changes),
        "unchanged_row_count": sum(abs(value) <= 1e-12 for value in changes),
        "worsened_row_count": sum(value > 1e-12 for value in changes),
        "median_change": float(np.median(changes)),
        "maximum_improvement": -min(changes),
        "maximum_regression": max(changes),
    }
    envelope_diag = diagnostics["cumulative_valid_bound_envelope"]
    greedy_diag = diagnostics["independent_greedy"]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "monotone_envelope_analyzed",
        "method": {
            "source_cohort": "R6J matched exact cohort recomputed with query-level clamped bound provenance",
            "branches": ["independent_greedy", "cumulative_valid_bound_envelope"],
            "envelope": "query-wise minimum valid upper bound over all registered i values not exceeding the current i",
            "boundary": "valid evidence envelope, not a nested partition algorithm and not a posterior bound",
            "literature": "https://doi.org/10.1609/aaai.v24i1.7761",
        },
        "rows": output_rows,
        "aggregates": aggregates,
        "monotonicity": monotonicity,
        "diagnostics": diagnostics,
        "hypothesis_outcomes": {
            "H1": "supported" if envelope_diag["evidence_monotonicity_violation_count"] == 0 else "rejected",
            "H2": (
                "supported"
                if envelope_diag["marginal_monotonicity_violation_count"] < greedy_diag["marginal_monotonicity_violation_count"]
                and envelope_diag["total_useful_low_i_rows"] > greedy_diag["total_useful_low_i_rows"]
                else "mixed or rejected"
            ),
            "H3": "supported" if envelope_diag["uniformly_useful_low_i_branch_count"] == 0 else "rejected",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Primitive valid-bound selection diagnostic only; the envelope is not a nested partition algorithm or posterior bound, and no paper-L2 accuracy, correction, LER, threshold, scaling, or fault-tolerance claim is made."
    }


def render(payload):
    diag = payload["diagnostics"]
    lines = [
        "# R6K monotone mini-bucket bound-envelope gate", "",
        "## Question and construction", "",
        "R6J's independent greedy partitions are not nested across `i`. R6K isolates that failure without introducing a new partition heuristic: for every total or clamped evidence query, the envelope at `i_j` is the minimum valid mini-bucket upper bound observed at any registered `i<=i_j`. This guarantees monotone evidence bounds. The two clamped envelopes are normalized only as a pseudo-marginal diagnostic.", "",
        "## Matched aggregate comparison", "",
        "| branch | representation | order | i | useful / 8 | median max error | worst max error |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["aggregates"]:
        lines.append(
            f"| {row['branch']} | {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['useful_accuracy_count']}/8 | {row['median_maximum_marginal_error']:.3e} | {row['worst_maximum_marginal_error']:.3e} |"
        )
    greedy = diag["independent_greedy"]
    envelope = diag["cumulative_valid_bound_envelope"]
    change = diag["matched_error_change"]
    lines.extend(["", "## Analysis", "",
        f"Evidence monotonicity violations fall from `{greedy['evidence_monotonicity_violation_count']}` to `{envelope['evidence_monotonicity_violation_count']}`. Marginal-error monotonicity violations change from `{greedy['marginal_monotonicity_violation_count']}` to `{envelope['marginal_monotonicity_violation_count']}`. Total useful low-`i` rows change from `{greedy['total_useful_low_i_rows']}` to `{envelope['total_useful_low_i_rows']}`, while uniformly useful low-`i` branches change from `{greedy['uniformly_useful_low_i_branch_count']}` to `{envelope['uniformly_useful_low_i_branch_count']}`.", "",
        f"On 128 matched envelope rows, error improves in `{change['improved_row_count']}`, is unchanged in `{change['unchanged_row_count']}`, and worsens in `{change['worsened_row_count']}`. Maximum improvement is `{change['maximum_improvement']:.3e}` and maximum regression `{change['maximum_regression']:.3e}`.", "",
        f"H1 {payload['hypothesis_outcomes']['H1']}; H2 {payload['hypothesis_outcomes']['H2']}; H3 {payload['hypothesis_outcomes']['H3']}.", "",
        "A monotone valid-bound envelope fixes bound ordering but need not improve normalized clamped pseudo-marginals, because tightening the two state bounds by different factors can move their ratio either way. If uniform low-`i` accuracy remains absent, the next method must change factor content/region coupling rather than merely select among existing bounds.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary source", "",
        "- Emma Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://doi.org/10.1609/aaai.v24i1.7761), AAAI 2010.", "",
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
        raise ValueError("R6K manifest was not in registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
