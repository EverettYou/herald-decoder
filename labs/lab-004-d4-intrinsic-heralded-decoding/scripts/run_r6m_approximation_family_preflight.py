#!/usr/bin/env python3
"""Run the R6M join-graph and compressed-tensor construction preflight."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_elimination_width import exact_bucket_partition, greedy_elimination_audit
from d4_local_bp import BinaryFactor, BinaryFactorGraph
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog
from run_r6e_bp_marginal_gate import selected_observations
from run_r6j_multi_observation_mini_bucket_validation import representations


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6m-approximation-family-construction-preflight-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6m-approximation-family-construction-preflight.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6m-approximation-family-construction-preflight.md"
ORDERS = ("global_min_fill", "auxiliary_first_min_fill")
I_BOUNDS = (10, 14)
MAX_BONDS = (2, 4, 8)


def aligned_table(factor, union_scope):
    positions = [union_scope.index(variable) for variable in factor.variables]
    permutation = np.argsort(positions)
    ordered_positions = [positions[index] for index in permutation]
    table = factor.table.transpose(tuple(int(index) for index in permutation))
    shape = [1] * len(union_scope)
    for position in ordered_positions:
        shape[position] = 2
    return table.reshape(shape)


def build_join_graph_decomposition(graph, order, i_bound):
    """Construct the arc-labeled mini-cluster join graph underlying IJGP."""

    entries = []
    original_ids = []
    for index, factor in enumerate(graph.factors):
        original_id = f"factor:{index}:{factor.name}"
        original_ids.append(original_id)
        entries.append({"factor": factor, "source": None, "original": original_id})
    for variable in range(graph.variable_count):
        factor = BinaryFactor(
            f"prior-v{variable}", (variable,), graph.priors[variable]
        )
        original_id = f"prior:{variable}"
        original_ids.append(original_id)
        entries.append({"factor": factor, "source": None, "original": original_id})

    nodes = []
    edges = []
    assigned = []
    scalar = 1.0
    seen = set()
    for variable in order:
        if variable in seen:
            raise ValueError("duplicate variable in order")
        seen.add(variable)
        bucket = [entry for entry in entries if variable in entry["factor"].variables]
        entries = [entry for entry in entries if variable not in entry["factor"].variables]
        if not bucket:
            continue
        bucket.sort(key=lambda entry: (
            -len(entry["factor"].variables),
            entry["factor"].variables,
            entry["factor"].name,
        ))
        groups = []
        scopes = []
        for entry in bucket:
            candidates = [
                (len(scope.union(entry["factor"].variables)), index)
                for index, scope in enumerate(scopes)
                if len(scope.union(entry["factor"].variables)) <= i_bound
            ]
            if candidates:
                _size, index = min(candidates)
                groups[index].append(entry)
                scopes[index].update(entry["factor"].variables)
            else:
                groups.append([entry])
                scopes.append(set(entry["factor"].variables))

        bucket_nodes = []
        for group, scope in zip(groups, scopes):
            node_id = len(nodes)
            bucket_nodes.append(node_id)
            original = [entry["original"] for entry in group if entry["original"]]
            assigned.extend(original)
            nodes.append({
                "id": node_id,
                "eliminated_variable": variable,
                "scope": sorted(scope),
                "original_factor_ids": original,
            })
            for entry in group:
                if entry["source"] is not None:
                    edges.append({
                        "left": entry["source"],
                        "right": node_id,
                        "separator": list(entry["factor"].variables),
                        "kind": "generated_message",
                    })
        for left, right in zip(bucket_nodes, bucket_nodes[1:]):
            edges.append({
                "left": left,
                "right": right,
                "separator": [variable],
                "kind": "within_bucket",
            })

        for node_id, group, scope in zip(bucket_nodes, groups, scopes):
            union_scope = tuple(sorted(scope))
            table = np.ones((2,) * len(union_scope), dtype=float)
            for entry in group:
                table *= aligned_table(entry["factor"], union_scope)
            axis = union_scope.index(variable)
            reduced = table.sum(axis=axis)
            reduced_scope = tuple(item for item in union_scope if item != variable)
            if reduced_scope:
                entries.append({
                    "factor": BinaryFactor(
                        f"join-message-v{variable}-n{node_id}",
                        reduced_scope,
                        reduced,
                    ),
                    "source": node_id,
                    "original": None,
                })
            else:
                scalar *= float(reduced)
    if seen != set(range(graph.variable_count)) or entries:
        raise AssertionError("join-graph trace did not eliminate every variable")

    assigned_counts = Counter(assigned)
    factor_assignment_valid = (
        set(assigned_counts) == set(original_ids)
        and all(count == 1 for count in assigned_counts.values())
    )
    scope_cap_valid = all(len(node["scope"]) <= i_bound for node in nodes)
    arc_labels_valid = all(
        edge["separator"]
        and set(edge["separator"]).issubset(
            set(nodes[edge["left"]]["scope"]).intersection(nodes[edge["right"]]["scope"])
        )
        for edge in edges
    )
    running_intersection_failures = []
    for variable in range(graph.variable_count):
        carriers = {node["id"] for node in nodes if variable in node["scope"]}
        if len(carriers) <= 1:
            continue
        adjacency = defaultdict(set)
        for edge in edges:
            if variable in edge["separator"]:
                adjacency[edge["left"]].add(edge["right"])
                adjacency[edge["right"]].add(edge["left"])
        reached = set()
        queue = deque([next(iter(carriers))])
        while queue:
            node = queue.popleft()
            if node in reached:
                continue
            reached.add(node)
            queue.extend(adjacency[node].difference(reached))
        if not carriers.issubset(reached):
            running_intersection_failures.append(variable)
    running_intersection_valid = not running_intersection_failures
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "cycle_rank": len(edges) - len(nodes) + 1 if nodes else 0,
        "maximum_cluster_variables": max(map(lambda node: len(node["scope"]), nodes), default=0),
        "maximum_separator_variables": max(map(lambda edge: len(edge["separator"]), edges), default=0),
        "factor_assignment_valid": factor_assignment_valid,
        "scope_cap_valid": scope_cap_valid,
        "arc_labels_valid": arc_labels_valid,
        "running_intersection_valid": running_intersection_valid,
        "running_intersection_failure_variables": running_intersection_failures,
        "partition_function_from_forward_pass": scalar,
        "valid": factor_assignment_valid and scope_cap_valid and arc_labels_valid and running_intersection_valid,
    }


def copy_tensor_network(graph):
    """Convert a factor graph hypernetwork into a standard COPY tensor network."""

    import quimb.tensor as qtn

    occurrences = defaultdict(list)
    tensors = []
    factors = list(graph.factors) + [
        BinaryFactor(f"prior-v{variable}", (variable,), graph.priors[variable])
        for variable in range(graph.variable_count)
    ]
    for factor_index, factor in enumerate(factors):
        inds = []
        for variable in factor.variables:
            ind = f"v{variable}-occ{len(occurrences[variable])}"
            occurrences[variable].append(ind)
            inds.append(ind)
        tensors.append(qtn.Tensor(
            data=np.asarray(factor.table, dtype=float),
            inds=inds,
            tags={f"FACTOR{factor_index}"},
        ))
    for variable in range(graph.variable_count):
        inds = occurrences[variable]
        copy = np.zeros((2,) * len(inds), dtype=float)
        copy[(0,) * len(inds)] = 1.0
        copy[(1,) * len(inds)] = 1.0
        tensors.append(qtn.Tensor(copy, inds=inds, tags={f"COPY{variable}"}))
    tn = qtn.TensorNetwork(tensors)
    index_counts = Counter(ind for tensor in tn for ind in tensor.inds)
    return tn, {
        "tensor_count": len(tensors),
        "bond_count": len(index_counts),
        "standard_network_valid": bool(index_counts) and set(index_counts.values()) == {2},
        "outer_index_count": sum(count == 1 for count in index_counts.values()),
    }


def scalar_value(value):
    array = np.asarray(value)
    if array.size != 1:
        raise AssertionError("tensor contraction did not return a scalar")
    return float(array.reshape(()))


def run_tensor_branch(graph, representation, physical_variable_count):
    import cotengra
    import opt_einsum
    import quimb

    tn, audit = copy_tensor_network(graph)
    if not audit["standard_network_valid"] or audit["outer_index_count"]:
        raise AssertionError("COPY tensor standardization failed")
    reference_audit = greedy_elimination_audit(
        graph,
        physical_variable_count=physical_variable_count,
        strategy="global_min_fill",
    )
    reference_result = exact_bucket_partition(
        graph,
        reference_audit.order,
        maximum_cluster_cap=20,
    )
    if reference_result.status != "computed" or reference_result.evidence is None:
        raise AssertionError("registered exact bucket reference was censored")
    reference = reference_result.evidence
    started = time.perf_counter()
    exact = scalar_value(tn.contract(all, optimize="greedy"))
    exact_runtime = time.perf_counter() - started
    exact_relative_error = abs(exact - reference) / max(abs(reference), 1e-300)
    rows = []
    for max_bond in MAX_BONDS:
        values = []
        runtimes = []
        errors = []
        for _replay in range(2):
            started = time.perf_counter()
            try:
                value = scalar_value(tn.contract_compressed(
                    "greedy",
                    max_bond=max_bond,
                    cutoff=0.0,
                    equalize_norms=True,
                ))
            except (ArithmeticError, ValueError) as exc:
                values.append(None)
                errors.append(f"{type(exc).__name__}: {exc}")
            else:
                values.append(value)
                errors.append(None)
            finally:
                runtimes.append(time.perf_counter() - started)
        finite = values[0] is not None and math.isfinite(values[0])
        deterministic = values[0] is not None and values[0] == values[1]
        rows.append({
            "representation": representation,
            "max_bond": max_bond,
            "value": values[0],
            "relative_error": (
                abs(values[0] - reference) / max(abs(reference), 1e-300)
                if finite else None
            ),
            "finite": finite,
            "deterministic_replay": deterministic,
            "replay_absolute_difference": (
                abs(values[0] - values[1]) if deterministic else None
            ),
            "errors": errors,
            "runtime_seconds": runtimes[0],
            "replay_runtime_seconds": runtimes[1],
        })
    return {
        "representation": representation,
        **audit,
        "reference_partition_function": reference,
        "reference_method": "exact_bucket_partition_global_min_fill",
        "reference_maximum_cluster_variables": (
            reference_result.maximum_cluster_variables
        ),
        "exact_tensor_value": exact,
        "exact_relative_error": exact_relative_error,
        "exact_runtime_seconds": exact_runtime,
        "compressed_rows": rows,
        "runtime_versions": {
            "quimb": quimb.__version__,
            "cotengra": cotengra.__version__,
            "opt_einsum": opt_einsum.__version__,
            "numpy": np.__version__,
        },
    }


def run():
    started = time.perf_counter()
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    label, candidate_count, observation = selected_observations(catalog)[-1]
    p = 0.10
    graphs = representations(lattice, observation, p)
    region_rows = []
    for representation, graph in graphs.items():
        for strategy in ORDERS:
            audit = greedy_elimination_audit(
                graph, physical_variable_count=lattice.edge_count, strategy=strategy
            )
            for i_bound in I_BOUNDS:
                result = build_join_graph_decomposition(graph, audit.order, i_bound)
                result.update({
                    "representation": representation,
                    "strategy": strategy,
                    "i_bound": i_bound,
                })
                region_rows.append(result)
    tensor_rows = [
        run_tensor_branch(graph, representation, lattice.edge_count)
        for representation, graph in graphs.items()
    ]
    region_pass = all(row["valid"] for row in region_rows)
    tensor_pass = all(
        row["standard_network_valid"]
        and row["exact_relative_error"] <= 1e-10
        and all(item["finite"] and item["deterministic_replay"] for item in row["compressed_rows"])
        for row in tensor_rows
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "approximation_family_construction_preflight_analyzed",
        "observation": label,
        "registered_nonwinding_candidate_count": candidate_count,
        "p": p,
        "region_rows": region_rows,
        "tensor_rows": tensor_rows,
        "diagnostics": {
            "region_row_count": len(region_rows),
            "region_valid_count": sum(row["valid"] for row in region_rows),
            "tensor_representation_count": len(tensor_rows),
            "tensor_exact_valid_count": sum(row["exact_relative_error"] <= 1e-10 for row in tensor_rows),
            "compressed_row_count": sum(len(row["compressed_rows"]) for row in tensor_rows),
            "compressed_finite_count": sum(item["finite"] for row in tensor_rows for item in row["compressed_rows"]),
            "compressed_deterministic_count": sum(item["deterministic_replay"] for row in tensor_rows for item in row["compressed_rows"]),
            "compressed_error_count": sum(
                any(error is not None for error in item["errors"])
                for row in tensor_rows for item in row["compressed_rows"]
            ),
            "total_runtime_seconds": time.perf_counter() - started,
        },
        "hypothesis_outcomes": {
            "H1": "supported" if region_pass else "rejected",
            "H2": "supported" if tensor_pass else "rejected",
            "H3": "supported" if region_pass and tensor_pass else "rejected",
        },
        "next_gate": (
            "register a matched exact-reference physical-marginal accuracy matrix for IJGP-style region messages and compressed tensor contraction"
            if region_pass and tensor_pass
            else "remediate the failed construction before any approximation-family selection"
        ),
        "new_decoder_samples": 0,
        "claim_boundary": "Construction feasibility on one primitive partition-function target only; compressed scalar error does not select a decoder and no posterior-accuracy, correction, paper-L2, LER, threshold, scaling, or fault-tolerance claim is made.",
    }


def render(payload):
    diag = payload["diagnostics"]
    lines = [
        "# R6M approximation-family construction preflight", "",
        "## Purpose", "",
        "R6M checks the earliest common gate for two independent bounded-inference families. It does not compare decoder quality. The region branch constructs the arc-labeled bounded join graph required before IJGP-style iteration; the tensor branch removes hyperedges with explicit COPY tensors, verifies exact contraction, and checks deterministic finite compressed contractions.", "",
        "## Region/join-graph construction", "",
        "| representation | order | i | nodes | arcs | cycle rank | max cluster | max separator | assignment | cap | labels | running intersection |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in payload["region_rows"]:
        lines.append(
            f"| {row['representation']} | {row['strategy']} | {row['i_bound']} | {row['node_count']} | {row['edge_count']} | {row['cycle_rank']} | {row['maximum_cluster_variables']} | {row['maximum_separator_variables']} | {row['factor_assignment_valid']} | {row['scope_cap_valid']} | {row['arc_labels_valid']} | {row['running_intersection_valid']} |"
        )
    lines.extend(["", "## COPY-tensor contraction smoke", "",
        "| representation | tensors | bonds | exact relative error | max bond | compressed relative error | finite | deterministic | seconds |",
        "|---|---:|---:|---:|---:|---:|---|---|---:|",
    ])
    for row in payload["tensor_rows"]:
        for item in row["compressed_rows"]:
            relative_error = (
                f"{item['relative_error']:.3e}"
                if item["relative_error"] is not None else "failed"
            )
            lines.append(
                f"| {row['representation']} | {row['tensor_count']} | {row['bond_count']} | {row['exact_relative_error']:.3e} | {item['max_bond']} | {relative_error} | {item['finite']} | {item['deterministic_replay']} | {item['runtime_seconds']:.3f} |"
            )
    errors = sorted({
        error
        for row in payload["tensor_rows"]
        for item in row["compressed_rows"]
        for error in item["errors"]
        if error is not None
    })
    if errors:
        lines.extend(["", "Compressed-contraction failures were retained as results:"])
        lines.extend(f"- `{error}`" for error in errors)
    lines.extend(["", "## Gate decision", "",
        f"Region validity: `{diag['region_valid_count']}/{diag['region_row_count']}`. Tensor exact ceilings: `{diag['tensor_exact_valid_count']}/{diag['tensor_representation_count']}`. Compressed finite and deterministic rows: `{diag['compressed_finite_count']}/{diag['compressed_row_count']}` and `{diag['compressed_deterministic_count']}/{diag['compressed_row_count']}`. Total runtime: `{diag['total_runtime_seconds']:.2f}` seconds.", "",
        f"H1 {payload['hypothesis_outcomes']['H1']}; H2 {payload['hypothesis_outcomes']['H2']}; H3 {payload['hypothesis_outcomes']['H3']}.", "",
        f"Next gate: {payload['next_gate']}.", "",
        "## Claim boundary", "", payload["claim_boundary"], "",
        "## Primary sources", "",
        "- Mateescu, Kask, Gogate, and Dechter, [Join-Graph Propagation Algorithms](https://doi.org/10.1613/jair.2842), JAIR 37 (2010).",
        "- Yedidia, Freeman, and Weiss, [Constructing Free Energy Approximations and Generalized Belief Propagation Algorithms](https://www.merl.com/publications/TR2002-35).",
        "- Bravyi, Suchara, and Vargo, [Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code](https://doi.org/10.1103/PhysRevA.90.032326), PRA 90 (2014).",
        "- Gray and Chan, [Hyperoptimized Approximate Contraction of Tensor Networks with Arbitrary Geometry](https://doi.org/10.1103/PhysRevX.14.011009), PRX 14 (2024).", "",
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
        raise ValueError("R6M manifest was not in its registered pre-run state")
    payload = run()
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render(payload))


if __name__ == "__main__":
    main()
