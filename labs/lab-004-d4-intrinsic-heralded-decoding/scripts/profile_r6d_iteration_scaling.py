#!/usr/bin/env python3
"""Measure warm R6D dense-kernel cost per forced BP iteration."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import (
    _run_sum_product_dense_numba,
    build_r6d_factor_graph,
    dense_factor_graph_arrays,
    run_sum_product_dense_numba,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6r-iteration-runtime-scaling-manifest-2026-08-29.json"
DEFAULT_INPUT = LAB_DIR / "results/r6n-default-flux-policy-comparison-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6r-iteration-runtime-scaling-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6r-iteration-runtime-scaling-2026-08-29.md"


def summary(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(len(array)),
        "mean_seconds": float(array.mean()),
        "median_seconds": float(np.median(array)),
        "minimum_seconds": float(array.min()),
        "maximum_seconds": float(array.max()),
    }


def run(manifest_path: Path, input_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6R":
        raise ValueError("manifest is not an active R6R registration")
    source = json.loads(input_path.read_text(encoding="utf-8"))
    source_scope = source["scope"]
    config = source_scope["bp_defaults"]
    count = int(manifest["scope"]["records"].split()[1])
    rows = [row for row in source["rows"] if row["status"] == "nonterminal"][:count]
    if len(rows) != count:
        raise ValueError("input has fewer nonterminal rows than registered")
    lattice = paper_periodic_honeycomb(int(source_scope["size"]))
    packed = []
    graph_times: list[float] = []
    pack_times: list[float] = []
    for row in rows:
        public = row["public_observation"]
        observation = PublicD4Observation(
            tuple(int(value) for value in public["flux_syndrome"]),
            tuple(int(value) for value in public["charge_outcomes"]),
        )
        start = time.perf_counter()
        graph = build_r6d_factor_graph(
            lattice, observation, error_rate=float(source_scope["physical_error_rate"]),
            terminal_screened=bool(config["terminal_screened"]),
        )
        graph_times.append(time.perf_counter() - start)
        start = time.perf_counter()
        arrays = dense_factor_graph_arrays(graph)
        pack_times.append(time.perf_counter() - start)
        packed.append((graph, arrays))

    # Compile and verify the direct prepacked-kernel call once; do not time it.
    graph, arrays = packed[0]
    direct = _run_sum_product_dense_numba(
        graph.priors, *arrays, float(config["old_message_weight"]),
        int(config["max_iterations"]), float(config["tolerance"]),
    )
    wrapped = run_sum_product_dense_numba(
        graph, old_message_weight=float(config["old_message_weight"]),
        max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
    )
    direct_marginals, direct_converged, direct_iterations, direct_delta, direct_valid = direct
    if (
        not direct_valid
        or not np.array_equal(direct_marginals, wrapped.marginals)
        or bool(direct_converged) != wrapped.converged
        or int(direct_iterations) != wrapped.iterations
        or float(direct_delta) != wrapped.max_message_delta
    ):
        raise AssertionError("prepacked dense kernel differs from public dense wrapper")

    caps = [int(value) for value in manifest["scope"]["iteration_caps"]]
    timing_repetitions = int(manifest["scope"]["timing_repetitions_per_record"])
    if timing_repetitions < 1:
        raise ValueError("timing_repetitions_per_record must be positive")
    forced = {}
    for cap in caps:
        timings: list[float] = []
        iterations: list[int] = []
        for graph, arrays in packed:
            start = time.perf_counter()
            for _ in range(timing_repetitions):
                _marginals, _converged, performed, _delta, valid = _run_sum_product_dense_numba(
                    graph.priors, *arrays, float(config["old_message_weight"]), cap,
                    float(manifest["scope"]["forced_full_cap_tolerance"]),
                )
                if not valid or int(performed) != cap:
                    raise AssertionError(f"forced cap {cap} did not complete")
            timings.append((time.perf_counter() - start) / timing_repetitions)
            iterations.append(int(performed))
        aggregate = summary(timings)
        forced[str(cap)] = {
            **aggregate,
            "mean_microseconds_per_iteration": float(1e6 * aggregate["mean_seconds"] / cap),
            "median_microseconds_per_iteration": float(1e6 * aggregate["median_seconds"] / cap),
        }
    default_times: list[float] = []
    default_iterations: list[int] = []
    for graph, arrays in packed:
        start = time.perf_counter()
        for _ in range(timing_repetitions):
            _marginals, _converged, performed, _delta, valid = _run_sum_product_dense_numba(
                graph.priors, *arrays, float(config["old_message_weight"]),
                int(config["max_iterations"]), float(config["tolerance"]),
            )
            if not valid:
                raise AssertionError("default dense recurrence became invalid")
        default_times.append((time.perf_counter() - start) / timing_repetitions)
        default_iterations.append(int(performed))
    default_summary = summary(default_times)
    default_summary["mean_iterations"] = float(np.mean(default_iterations))
    default_summary["mean_microseconds_per_performed_iteration"] = float(
        1e6 * sum(default_times) / sum(default_iterations)
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_prepacked_iteration_scaling_audit",
        "manifest": manifest_path.name,
        "source": input_path.name,
        "records": len(rows),
        "timing_repetitions_per_record": timing_repetitions,
        "topology": {
            "physical_edges": lattice.edge_count,
            "R6D_binary_variables": packed[0][0].variable_count,
            "R6D_factor_count": len(packed[0][0].factors),
            "directed_messages": int(packed[0][1][4].shape[0]),
            "maximum_factor_arity": int(packed[0][1][0].shape[1]),
        },
        "fixed_overhead": {
            "factor_graph_build": summary(graph_times),
            "dense_pack": summary(pack_times),
        },
        "forced_full_cap": forced,
        "default_early_stopping": default_summary,
        "claim_boundary": manifest["claim_boundary"],
    }


def render(payload: dict) -> str:
    topology = payload["topology"]
    lines = [
        "# R6R dense R6D iteration-runtime scaling audit",
        "",
        f"Profiled {payload['records']} frozen paper-L2 records: {topology['physical_edges']} physical edges, {topology['R6D_binary_variables']} binary variables, {topology['R6D_factor_count']} factors, and {topology['directed_messages']} directed messages.",
        "",
        "| forced cap | mean kernel time | mean per iteration |",
        "| ---: | ---: | ---: |",
    ]
    for cap, item in payload["forced_full_cap"].items():
        lines.append(f"| {cap} | {1000 * item['mean_seconds']:.3f} ms | {item['mean_microseconds_per_iteration']:.2f} µs |")
    graph = payload["fixed_overhead"]["factor_graph_build"]
    pack = payload["fixed_overhead"]["dense_pack"]
    default = payload["default_early_stopping"]
    lines.extend([
        "",
        f"Fixed per-record overhead: factor-graph build {1000 * graph['mean_seconds']:.3f} ms; dense packing {1000 * pack['mean_seconds']:.3f} ms.",
        f"At the default tolerance, mean performed iterations are {default['mean_iterations']:.2f} and pure prepacked-kernel cost is {default['mean_microseconds_per_performed_iteration']:.2f} µs per performed iteration.",
        "",
        "Forced caps test the recurrence with early stopping disabled, so near-proportional cap scaling is the relevant check. This remains a CPU microbenchmark; a small single L2 instance will not predict GPU latency without batching.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run(args.manifest, args.input)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "report": str(args.report), "default": payload["default_early_stopping"], "forced": payload["forced_full_cap"]}, indent=2))


if __name__ == "__main__":
    main()
