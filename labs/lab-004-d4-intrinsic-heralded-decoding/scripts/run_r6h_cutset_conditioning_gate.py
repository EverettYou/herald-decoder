#!/usr/bin/env python3
"""Run the registered R6H exact cutset-conditioning time-space gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from d4_elimination_width import (
    exact_cutset_partition,
    greedy_elimination_audit,
    primal_adjacency,
)
from d4_honeycomb import paper_periodic_honeycomb
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations
from run_r6g_elimination_width_gate import build_representations, vacuum_observation


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6h-cutset-conditioning-gate-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6h-cutset-conditioning-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6h-cutset-conditioning-gate.md"
POLICIES = ("physical_only_core", "auxiliary_only_core", "unrestricted_core")
MEMORY_CAP = 20


def eligible_variables(graph, physical_count, policy, cutset):
    remaining = set(range(graph.variable_count)).difference(cutset)
    if policy == "physical_only_core":
        return {v for v in remaining if v < physical_count}
    if policy == "auxiliary_only_core":
        return {v for v in remaining if v >= physical_count}
    if policy == "unrestricted_core":
        return remaining
    raise ValueError("unknown cutset policy")


def cutset_frontier(graph, physical_count, policy, maximum_k):
    base = primal_adjacency(graph)
    cutset: list[int] = []
    rows = []
    for k in range(maximum_k + 1):
        audit = greedy_elimination_audit(
            graph,
            physical_variable_count=physical_count,
            strategy="global_min_fill",
            excluded_variables=cutset,
        )
        cluster = audit.maximum_cluster_variables
        rows.append({
            "k": k,
            "cutset": list(cutset),
            "physical_cutset_count": sum(v < physical_count for v in cutset),
            "auxiliary_cutset_count": sum(v >= physical_count for v in cutset),
            "residual_induced_width": audit.induced_width,
            "residual_maximum_cluster_variables": cluster,
            "branch_exponent": k,
            "coarse_work_exponent_k_plus_cluster": k + cluster,
            "memory_cap_reached": cluster <= MEMORY_CAP,
        })
        if k == maximum_k:
            break
        eligible = eligible_variables(graph, physical_count, policy, cutset)
        if not eligible:
            break
        ranks = {variable: rank for rank, variable in enumerate(audit.order)}
        peak = set(audit.peak_cluster)
        variable = max(
            eligible,
            key=lambda v: (
                int(v in peak),
                len(set(base[v]).difference(cutset)),
                ranks.get(v, -1),
                -v,
            ),
        )
        cutset.append(variable)
    return rows


def run():
    catalog = build_primitive_observation_catalog()
    primitive = catalog.lattice
    _label, candidate_count, primitive_observation = selected_observations(catalog)[-1]
    paper = paper_periodic_honeycomb(2)
    geometries = (
        ("primitive", primitive, primitive_observation, 8),
        ("paper_L2", paper, vacuum_observation(paper), 24),
    )
    structure_rows = []
    graphs = {}
    for geometry, lattice, observation, maximum_k in geometries:
        for representation, graph in build_representations(lattice, observation).items():
            graphs[(geometry, representation)] = graph
            for policy in POLICIES:
                for row in cutset_frontier(
                    graph, lattice.edge_count, policy, maximum_k
                ):
                    structure_rows.append({
                        "geometry": geometry,
                        "representation": representation,
                        "policy": policy,
                        **row,
                    })

    _marginals, exact_evidence, _terminal = exact_d4_marginals(
        primitive, primitive_observation, 0.10, False
    )
    numeric_rows = []
    for representation in ("r6d_unclustered", "r6f_bounded_superfactor"):
        graph = graphs[("primitive", representation)]
        for policy in POLICIES:
            frontier = [
                row for row in structure_rows
                if row["geometry"] == "primitive"
                and row["representation"] == representation
                and row["policy"] == policy
            ]
            for k in (0, 2, 4):
                cutset = frontier[k]["cutset"]
                audit = greedy_elimination_audit(
                    graph,
                    physical_variable_count=primitive.edge_count,
                    strategy="global_min_fill",
                    excluded_variables=cutset,
                )
                # The full order is used only to induce the residual order per branch.
                full_order = tuple(v for v in audit.order) + tuple(cutset)
                result = exact_cutset_partition(
                    graph, full_order, cutset, maximum_cluster_cap=MEMORY_CAP
                )
                adjusted = (
                    result.evidence * 2.0 ** (2 * primitive.edge_count)
                    if result.evidence is not None else None
                )
                relative_error = (
                    abs(adjusted - exact_evidence) / exact_evidence
                    if adjusted is not None else None
                )
                if relative_error is None or relative_error > 1e-10:
                    raise AssertionError("R6H primitive cutset reconstruction failed")
                numeric_rows.append({
                    "representation": representation,
                    "policy": policy,
                    "k": k,
                    "cutset": cutset,
                    "branch_count": result.branch_count,
                    "status": result.status,
                    "maximum_cluster_variables": result.maximum_cluster_variables,
                    "auxiliary_prior_adjusted_evidence": adjusted,
                    "exact_4096_mask_evidence": exact_evidence,
                    "relative_evidence_error": relative_error,
                })

    summaries = []
    for representation in ("r6d_unclustered", "r6f_bounded_superfactor"):
        for policy in POLICIES:
            rows = [
                row for row in structure_rows
                if row["geometry"] == "paper_L2"
                and row["representation"] == representation
                and row["policy"] == policy
            ]
            crossings = [row for row in rows if row["memory_cap_reached"]]
            best_work = min(rows, key=lambda row: row["coarse_work_exponent_k_plus_cluster"])
            summaries.append({
                "representation": representation,
                "policy": policy,
                "first_k_reaching_memory_cap": crossings[0]["k"] if crossings else None,
                "cluster_at_first_crossing": crossings[0]["residual_maximum_cluster_variables"] if crossings else None,
                "work_exponent_at_first_crossing": crossings[0]["coarse_work_exponent_k_plus_cluster"] if crossings else None,
                "minimum_coarse_work_exponent": best_work["coarse_work_exponent_k_plus_cluster"],
                "k_at_minimum_coarse_work_exponent": best_work["k"],
                "cluster_at_minimum_coarse_work_exponent": best_work["residual_maximum_cluster_variables"],
            })

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "cutset_frontier_analyzed",
        "method": {
            "conditioning": "enumerate 2^k binary assignments and exactly eliminate each residual graph",
            "selection": "registered peak-cluster core heuristic recomputed after every removal",
            "memory_exponent": "residual maximum cluster variables",
            "coarse_work_exponent": "k plus residual maximum cluster variables; structural proxy only",
            "literature": [
                "https://doi.org/10.1016/S0004-3702(99)00059-4",
                "https://arxiv.org/abs/1302.3573"
            ],
        },
        "registered_nonwinding_candidate_count": candidate_count,
        "memory_cap": MEMORY_CAP,
        "structure_rows": structure_rows,
        "paper_L2_summary": summaries,
        "primitive_numeric_gate": {
            "rows": numeric_rows,
            "maximum_relative_evidence_error": max(row["relative_evidence_error"] for row in numeric_rows),
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Exact registered-cutset resource frontier and primitive evidence reconstruction only; no optimal cutset/treewidth, approximation, correction, LER, threshold, runtime-scaling, or fault-tolerance claim.",
    }


def render(payload):
    summaries = payload["paper_L2_summary"]
    lines = [
        "# R6H cutset-conditioning exact time-space gate", "",
        "## Result", "",
        "R6G's paper-L2 dense-memory barrier is not treated as permission to guess a larger-region decoder. Following Dechter, R6H first measures the exact conditioning/elimination trade: conditioning `k` variables creates `2^k` residual branches but can reduce the largest dense table.", "",
        "| representation | cutset policy | first k with cluster <=20 | cluster | k+cluster at crossing | minimum k+cluster | location (k, cluster) |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        crossing = row["first_k_reaching_memory_cap"]
        lines.append(
            f"| {row['representation']} | {row['policy']} | {crossing if crossing is not None else 'not reached'} | {row['cluster_at_first_crossing'] if crossing is not None else '—'} | {row['work_exponent_at_first_crossing'] if crossing is not None else '—'} | {row['minimum_coarse_work_exponent']} | ({row['k_at_minimum_coarse_work_exponent']}, {row['cluster_at_minimum_coarse_work_exponent']}) |"
        )
    maximum_error = payload["primitive_numeric_gate"]["maximum_relative_evidence_error"]
    lines.extend([
        "", "## Validity gate", "",
        f"All 18 registered primitive reconstructions (two representations × three policies × `k=0,2,4`) enumerate every cutset assignment and recover the independent 4,096-mask evidence. Maximum relative error is `{maximum_error:.3e}`. The frontier is therefore an exact space/time decomposition, not an approximation.", "",
        "## Interpretation", "",
        "The color of the result is deliberately resource-theoretic: a lower residual cluster means lower peak dense memory, whereas `k+cluster` exposes whether that saving merely moves exponential cost into branching. Physical-only, auxiliary-only, and unrestricted policies are all shown, so the comparison diagnoses which variable class carries the core without elevating one heuristic into a scientific assumption.", "",
        "These are deterministic upper bounds for one registered cutset-selection and residual min-fill rule. They do not prove an optimal cutset or treewidth, and the exponent proxy is not measured runtime.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary sources", "",
        "- Rina Dechter, [Bucket elimination: A unifying framework for reasoning](https://doi.org/10.1016/S0004-3702(99)00059-4), *Artificial Intelligence* 113 (1999).",
        "- Rina Dechter and Yousri El Fattah, [Topological parameters for time-space tradeoff](https://arxiv.org/abs/1302.3573), *Artificial Intelligence* 125 (2001).", "",
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
        raise ValueError("R6H manifest was not in its registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
