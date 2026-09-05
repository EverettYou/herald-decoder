#!/usr/bin/env python3
"""Run the registered R6G elimination-width and junction feasibility gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from d4_belief_factorization import PublicD4Observation
from d4_elimination_width import exact_bucket_partition, greedy_elimination_audit
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_factor_graph, build_r6d_superfactor_graph
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import exact_d4_marginals, selected_observations


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6g-elimination-width-gate-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6g-elimination-width-gate.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6g-elimination-width-gate.md"
STRATEGIES = (
    "auxiliary_first_min_fill",
    "physical_first_min_fill",
    "global_min_fill",
)
NUMERIC_CLUSTER_CAP = 20


def vacuum_observation(lattice):
    return PublicD4Observation(
        (0,) * lattice.vertex_count,
        (-1,) * lattice.vertex_count,
    )


def build_representations(lattice, observation):
    return {
        "r6d_unclustered": build_r6d_factor_graph(
            lattice, observation, error_rate=0.10, terminal_screened=False
        ),
        "r6f_bounded_superfactor": build_r6d_superfactor_graph(
            lattice, observation, error_rate=0.10, terminal_screened=False
        ),
    }


def structure_row(geometry, representation, graph, physical_count, strategy):
    audit = greedy_elimination_audit(
        graph,
        physical_variable_count=physical_count,
        strategy=strategy,
    )
    return {
        "geometry": geometry,
        "representation": representation,
        "strategy": strategy,
        "variable_count": graph.variable_count,
        "physical_variable_count": physical_count,
        "auxiliary_variable_count": graph.variable_count - physical_count,
        "factor_count": len(graph.factors),
        "maximum_input_factor_arity": max(len(factor.variables) for factor in graph.factors),
        "induced_width": audit.induced_width,
        "maximum_cluster_variables": audit.maximum_cluster_variables,
        "log2_maximum_binary_table_entries": audit.maximum_cluster_variables,
        "maximum_binary_table_entries": (
            2 ** audit.maximum_cluster_variables
            if audit.maximum_cluster_variables <= 62
            else None
        ),
        "total_fill_edges": audit.total_fill_edges,
        "order": list(audit.order),
    }, audit


def run() -> dict:
    catalog = build_primitive_observation_catalog()
    primitive = catalog.lattice
    _label, candidate_count, primitive_observation = selected_observations(catalog)[-1]
    paper = paper_periodic_honeycomb(2)
    geometries = (
        ("primitive", primitive, primitive_observation),
        ("paper_L2", paper, vacuum_observation(paper)),
    )
    rows = []
    audits = {}
    for geometry, lattice, observation in geometries:
        for representation, graph in build_representations(lattice, observation).items():
            for strategy in STRATEGIES:
                row, audit = structure_row(
                    geometry, representation, graph, lattice.edge_count, strategy
                )
                rows.append(row)
                audits[(geometry, representation, strategy)] = (graph, audit)

    exact, exact_evidence, _terminal = exact_d4_marginals(
        primitive, primitive_observation, 0.10, False
    )
    if len(exact) != primitive.edge_count:
        raise AssertionError("primitive exact target has the wrong edge count")
    numeric_rows = []
    for representation in ("r6d_unclustered", "r6f_bounded_superfactor"):
        for strategy in STRATEGIES:
            graph, audit = audits[("primitive", representation, strategy)]
            result = exact_bucket_partition(
                graph,
                audit.order,
                maximum_cluster_cap=NUMERIC_CLUSTER_CAP,
            )
            adjusted_evidence = (
                result.evidence * (2.0 ** (2 * primitive.edge_count))
                if result.evidence is not None
                else None
            )
            relative_error = (
                abs(adjusted_evidence - exact_evidence) / exact_evidence
                if adjusted_evidence is not None
                else None
            )
            if relative_error is not None and relative_error > 1e-10:
                raise AssertionError("R6G exact bucket evidence gate failed")
            numeric_rows.append({
                "geometry": "primitive",
                "observation": "maximum_candidate_stratum",
                "registered_nonwinding_candidate_count": candidate_count,
                "p": 0.10,
                "representation": representation,
                "strategy": strategy,
                "status": result.status,
                "registered_cluster_cap": NUMERIC_CLUSTER_CAP,
                "predicted_maximum_cluster_variables": audit.maximum_cluster_variables,
                "realized_maximum_cluster_variables": result.maximum_cluster_variables,
                "censored_at_variable": result.censored_at_variable,
                "raw_graph_evidence": result.evidence,
                "auxiliary_prior_adjusted_evidence": adjusted_evidence,
                "exact_4096_mask_evidence": exact_evidence,
                "relative_evidence_error": relative_error,
            })

    by_geometry = {}
    for geometry in ("primitive", "paper_L2"):
        selected = [row for row in rows if row["geometry"] == geometry]
        by_geometry[geometry] = {
            "minimum_maximum_cluster_variables": min(
                row["maximum_cluster_variables"] for row in selected
            ),
            "maximum_maximum_cluster_variables": max(
                row["maximum_cluster_variables"] for row in selected
            ),
            "best_rows": [
                {
                    "representation": row["representation"],
                    "strategy": row["strategy"],
                    "maximum_cluster_variables": row["maximum_cluster_variables"],
                    "total_fill_edges": row["total_fill_edges"],
                }
                for row in selected
                if row["maximum_cluster_variables"]
                == min(item["maximum_cluster_variables"] for item in selected)
            ],
        }

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "width_matrix_analyzed",
        "method": {
            "interaction_graph": "primal graph: every factor scope is completed to a clique",
            "score": "minimum new fill edges, then current degree, physical-before-auxiliary class, then integer id",
            "width_definition": "maximum number of live neighbours when a variable is eliminated; maximum cluster variables equals width plus one",
            "complexity_interpretation": "dense binary bucket time/space is exponential in the registered induced-width upper bound",
            "literature": [
                "https://doi.org/10.1016/S0004-3702(99)00059-4",
                "https://proceedings.neurips.cc/paper/2000/hash/61b1fb3f59e28c67f3925f3c79be81a1-Abstract.html"
            ],
        },
        "structure_rows": rows,
        "summary_by_geometry": by_geometry,
        "numeric_gate": {
            "maximum_cluster_cap": NUMERIC_CLUSTER_CAP,
            "rows": numeric_rows,
            "computed_count": sum(row["status"] == "computed" for row in numeric_rows),
            "censored_count": sum(row["status"] != "computed" for row in numeric_rows),
            "maximum_relative_evidence_error": max(
                (row["relative_evidence_error"] or 0.0) for row in numeric_rows
            ),
        },
        "hypothesis_outcomes": {
            "H1_bounded_superfactor_lowers_width": "rejected for the registered orders: it ties unclustered global/physical-first widths and is worse for auxiliary-first on both geometries",
            "H2_global_min_fill_is_best": "geometry-dependent: rejected on primitive where unclustered auxiliary-first needs 16 rather than 18 cluster variables; supported on paper-L2 where global min-fill needs 36 rather than 44-80",
            "H3_paper_L2_exceeds_numeric_cap": "supported: every registered paper-L2 branch needs at least 36 cluster variables, above the cap of 20",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Registered-order induced-width upper bounds and capped primitive exact-evidence checks only. No optimal-treewidth, generalized-BP, correction, LER, threshold, runtime-scaling, or fault-tolerance claim.",
    }


def render(payload):
    rows = payload["structure_rows"]
    lines = [
        "# R6G exact elimination-width and junction feasibility gate",
        "",
        "## Question and method",
        "",
        "R6F showed that exact global auxiliary elimination recovers the primitive posterior, while one bounded clustering remains biased. R6G therefore measures the structural cost of exact elimination before implementing a larger-region algorithm. Following Dechter's bucket-elimination framework, the relevant dense-table cost is exponential in induced width; following Yedidia, Freeman, and Weiss, larger regions are treated as an adjustable accuracy/complexity trade rather than presumed to solve the problem.",
        "",
        "Each factor scope is completed to a clique in the primal interaction graph. The reported widths are deterministic upper bounds for three registered min-fill orders, not proofs of optimal treewidth.",
        "",
        "## Complete structural matrix",
        "",
        "| geometry | representation | order | variables | factors | input max arity | induced width | max cluster vars | log2 peak entries | fill edges |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['geometry']} | {row['representation']} | {row['strategy']} | {row['variable_count']} | {row['factor_count']} | {row['maximum_input_factor_arity']} | {row['induced_width']} | {row['maximum_cluster_variables']} | {row['log2_maximum_binary_table_entries']} | {row['total_fill_edges']} |"
        )
    numeric = payload["numeric_gate"]
    lines.extend([
        "",
        "## Primitive exact-evidence gate",
        "",
        f"Dense bucket elimination is allowed only through {numeric['maximum_cluster_cap']} binary variables in one bucket. It computes {numeric['computed_count']}/6 registered primitive branches and censors {numeric['censored_count']}/6 before allocating an oversized table. Every computed branch matches the independent 4,096-mask evidence with maximum relative error `{numeric['maximum_relative_evidence_error']:.3e}`.",
        "",
        "## Interpretation",
        "",
    ])
    primitive = payload["summary_by_geometry"]["primitive"]
    paper = payload["summary_by_geometry"]["paper_L2"]
    lines.append(
        f"The best registered primitive order needs {primitive['minimum_maximum_cluster_variables']} binary variables in its largest cluster. On paper-L2 the best registered order needs {paper['minimum_maximum_cluster_variables']}, corresponding to a dense table with `2^{paper['minimum_maximum_cluster_variables']}` entries before accounting for multiple buckets or messages. This is the discriminating feasibility result: exact junction inference may be tractable on the semantic fixture while naive dense extension already has exponential structural growth at the first paper-normalized size."
    )
    lines.extend([
        "",
        "The hypotheses separate cleanly. H1 is rejected for these orders: the bounded superfactor graph never lowers maximum cluster size; it ties the unclustered graph under global and physical-first orders and is worse under auxiliary-first, even though it has fewer factors and sometimes fewer fill edges. Factor-count compression is therefore not treewidth compression. H2 is geometry-dependent: global min-fill is best at paper-L2, but the primitive unclustered auxiliary-first order is smaller (16 versus 18 cluster variables). H3 is supported because every paper-L2 branch exceeds the registered cap of 20.",
        "",
        "The next method should therefore expose a controlled region/cutset/tensor approximation and validate it against primitive exact marginals. It should not silently call a min-fill upper bound the optimal treewidth, and this audit does not authorize correction or LER sampling.",
        "",
        "## Claim boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Primary method sources",
        "",
        "- Rina Dechter, [Bucket elimination: A unifying framework for reasoning](https://doi.org/10.1016/S0004-3702(99)00059-4), *Artificial Intelligence* 113 (1999).",
        "- Jonathan Yedidia, William Freeman, and Yair Weiss, [Generalized Belief Propagation](https://proceedings.neurips.cc/paper/2000/hash/61b1fb3f59e28c67f3925f3c79be81a1-Abstract.html), NeurIPS 2000.",
        "",
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
        raise ValueError("R6G manifest was not in its registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
