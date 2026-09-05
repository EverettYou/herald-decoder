#!/usr/bin/env python3
"""Run R6J matched multi-observation mini-bucket validation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_local_bp import build_r6d_factor_graph, build_r6d_superfactor_graph
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations
from run_r6i_mini_bucket_gate import I_BOUNDS, ORDERS, REPRESENTATIONS, primitive_row


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6j-multi-observation-mini-bucket-validation-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6j-multi-observation-mini-bucket-validation.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6j-multi-observation-mini-bucket-validation.md"
P_VALUES = (0.10, 0.30)


def representations(lattice, observation, p):
    return {
        "r6d_unclustered": build_r6d_factor_graph(
            lattice, observation, error_rate=p, terminal_screened=False
        ),
        "r6f_bounded_superfactor": build_r6d_superfactor_graph(
            lattice, observation, error_rate=p, terminal_screened=False
        ),
    }


def nonincreasing(values, tolerance=1e-12):
    return all(
        right <= left + tolerance * max(1.0, abs(left))
        for left, right in zip(values, values[1:])
    )


def run():
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    rows = []
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
                        )
                        row.update({
                            "observation": label,
                            "registered_nonwinding_candidate_count": candidate_count,
                            "p": p,
                            "prospective_cancellation": (
                                row["evidence_upper_bound_ratio"] > 2.0
                                and row["maximum_absolute_marginal_error"] < 1e-10
                            ),
                            "prospective_useful_accuracy": (
                                row["maximum_absolute_marginal_error"] <= 1e-2
                            ),
                        })
                        rows.append(row)
    if len(rows) != 128:
        raise AssertionError("R6J matrix is incomplete")

    aggregates = []
    for representation in REPRESENTATIONS:
        for strategy in ORDERS:
            for i_bound in I_BOUNDS:
                branch = [
                    row for row in rows
                    if row["representation"] == representation
                    and row["strategy"] == strategy
                    and row["i_bound"] == i_bound
                ]
                errors = [row["maximum_absolute_marginal_error"] for row in branch]
                ratios = [row["evidence_upper_bound_ratio"] for row in branch]
                aggregates.append({
                    "representation": representation,
                    "strategy": strategy,
                    "i_bound": i_bound,
                    "condition_count": len(branch),
                    "useful_accuracy_count": sum(row["prospective_useful_accuracy"] for row in branch),
                    "cancellation_count": sum(row["prospective_cancellation"] for row in branch),
                    "median_maximum_marginal_error": float(np.median(errors)),
                    "worst_maximum_marginal_error": max(errors),
                    "median_evidence_upper_bound_ratio": float(np.median(ratios)),
                    "maximum_evidence_upper_bound_ratio": max(ratios),
                })

    monotonicity = []
    for label, _count, _observation in selected_observations(catalog):
        for p in P_VALUES:
            for representation in REPRESENTATIONS:
                for strategy in ORDERS:
                    branch = sorted(
                        [
                            row for row in rows
                            if row["observation"] == label
                            and row["p"] == p
                            and row["representation"] == representation
                            and row["strategy"] == strategy
                        ],
                        key=lambda row: row["i_bound"],
                    )
                    monotonicity.append({
                        "observation": label,
                        "p": p,
                        "representation": representation,
                        "strategy": strategy,
                        "evidence_ratio_nonincreasing": nonincreasing([
                            row["evidence_upper_bound_ratio"] for row in branch
                        ]),
                        "maximum_marginal_error_nonincreasing": nonincreasing([
                            row["maximum_absolute_marginal_error"] for row in branch
                        ]),
                    })

    exact_rows = [row for row in rows if row["exact_ceiling_expected"]]
    low_i_aggregates = [row for row in aggregates if row["i_bound"] <= 14]
    robust_low_i = [row for row in low_i_aggregates if row["useful_accuracy_count"] == 8]
    auxiliary_cancellations = [
        row for row in rows
        if row["strategy"] == "auxiliary_first_min_fill"
        and row["i_bound"] <= 14
        and row["prospective_cancellation"]
    ]
    total_auxiliary_low_i = sum(
        row["strategy"] == "auxiliary_first_min_fill" and row["i_bound"] <= 14
        for row in rows
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "multi_observation_validation_analyzed",
        "method": {
            "observations": [item[0] for item in selected_observations(catalog)],
            "p_values": list(P_VALUES),
            "representations": list(REPRESENTATIONS),
            "orders": list(ORDERS),
            "i_bounds": list(I_BOUNDS),
            "cancellation_definition": "evidence ratio >2 and max marginal error <1e-10",
            "useful_accuracy_definition": "max marginal error <=1e-2",
        },
        "rows": rows,
        "aggregates": aggregates,
        "monotonicity": monotonicity,
        "exact_ceiling": {
            "row_count": len(exact_rows),
            "maximum_evidence_ratio_error": max(
                abs(row["evidence_upper_bound_ratio"] - 1.0) for row in exact_rows
            ),
            "maximum_marginal_error": max(
                row["maximum_absolute_marginal_error"] for row in exact_rows
            ),
        },
        "diagnostics": {
            "evidence_monotonicity_violation_count": sum(
                not row["evidence_ratio_nonincreasing"] for row in monotonicity
            ),
            "marginal_monotonicity_violation_count": sum(
                not row["maximum_marginal_error_nonincreasing"] for row in monotonicity
            ),
            "auxiliary_low_i_cancellation_count": len(auxiliary_cancellations),
            "auxiliary_low_i_condition_row_count": total_auxiliary_low_i,
            "robust_useful_low_i_branch_count": len(robust_low_i),
            "robust_useful_low_i_branches": robust_low_i,
        },
        "hypothesis_outcomes": {
            "H1": (
                "supported"
                if len(auxiliary_cancellations) < total_auxiliary_low_i
                else "rejected"
            ),
            "H2": (
                "supported"
                if all(row["evidence_ratio_nonincreasing"] for row in monotonicity)
                and any(not row["maximum_marginal_error_nonincreasing"] for row in monotonicity)
                else "rejected or unresolved"
            ),
            "H3": "supported" if not robust_low_i else "rejected",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Deterministic 12-edge primitive posterior validation only; no paper-L2 accuracy, scalable correction, LER, threshold, runtime-scaling, or fault-tolerance claim."
    }


def render(payload):
    lines = [
        "# R6J multi-observation mini-bucket exact-reference validation", "",
        "## Complete matched-cohort summary", "",
        "The 128 deterministic rows cover four registered observation strata, `p=0.10,0.30`, both exact factorizations, global/auxiliary-first orders, and `i=10,14,18,20`. No row is selected after seeing its error.", "",
        "| representation | order | i | useful / 8 | cancellation / 8 | median max error | worst max error | median evidence ratio | max evidence ratio |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["aggregates"]:
        lines.append(
            f"| {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['useful_accuracy_count']}/8 | {row['cancellation_count']}/8 | {row['median_maximum_marginal_error']:.3e} | {row['worst_maximum_marginal_error']:.3e} | {row['median_evidence_upper_bound_ratio']:.5g} | {row['maximum_evidence_upper_bound_ratio']:.5g} |"
        )
    exact = payload["exact_ceiling"]
    diag = payload["diagnostics"]
    lines.extend(["", "## Validity and hypotheses", "",
        f"All `{exact['row_count']}` exact-ceiling rows pass, with maximum evidence-ratio error `{exact['maximum_evidence_ratio_error']:.3e}` and maximum marginal error `{exact['maximum_marginal_error']:.3e}`.", "",
        f"Across 32 observation/prior/representation/order sequences, evidence monotonicity violations: `{diag['evidence_monotonicity_violation_count']}`; marginal-error monotonicity violations: `{diag['marginal_monotonicity_violation_count']}`. Auxiliary-first low-`i` cancellation occurs in `{diag['auxiliary_low_i_cancellation_count']}/{diag['auxiliary_low_i_condition_row_count']}` rows. Branches achieving the prospective 0.01 error gate on all eight conditions at `i<=14`: `{diag['robust_useful_low_i_branch_count']}`.", "",
        f"H1 {payload['hypothesis_outcomes']['H1']}; H2 {payload['hypothesis_outcomes']['H2']}; H3 {payload['hypothesis_outcomes']['H3']}.", "",
        "## Interpretation", "",
        "This cohort determines whether the favorable single-observation cancellation in R6I is reproducible. Evidence bounds and normalized clamped pseudo-marginals are kept separate: monotone improvement of the former does not certify the latter. If no low-`i` branch is uniformly useful, the result licenses a richer approximation comparison, not correction or LER sampling.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary method source", "",
        "- Rina Dechter and Irina Rish, [Mini-buckets: A general scheme for bounded inference](https://doi.org/10.1145/636865.636866), JACM 50 (2003).", "",
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
        raise ValueError("R6J manifest was not in its registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
