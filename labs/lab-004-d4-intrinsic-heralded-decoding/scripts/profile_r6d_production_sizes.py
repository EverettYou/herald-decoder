#!/usr/bin/env python3
"""Bounded production-size CPU baseline for the R6D dense BP recurrence."""

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
    build_r6d_dense_template,
    dense_factor_graph_arrays,
    run_r6d_dense_template,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6s-production-size-runtime-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6s-production-size-runtime-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6s-production-size-runtime-2026-08-29.md"


def measure(call, repetitions: int):
    started = time.perf_counter()
    value = None
    for _ in range(repetitions):
        value = call()
    return (time.perf_counter() - started) / repetitions, value


def run(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("phase") != "R6S":
        raise ValueError("manifest is not an active R6S registration")
    scope = manifest["scope"]
    sizes = [int(item) for item in scope["sizes"]]
    repetitions = int(scope["timing_repetitions_per_size"])
    cap = int(scope["forced_iterations"])
    if repetitions < 1 or cap < 1:
        raise ValueError("invalid timing scope")

    rows = []
    # Compile once; its latency is intentionally excluded from all measurements.
    warm_lattice = paper_periodic_honeycomb(sizes[0])
    warm_observation = PublicD4Observation(
        (0,) * warm_lattice.vertex_count, (-1,) * warm_lattice.vertex_count
    )
    warm_graph = build_r6d_factor_graph(
        warm_lattice, warm_observation, error_rate=float(scope["error_rate"]),
        terminal_screened=False,
    )
    warm_arrays = dense_factor_graph_arrays(warm_graph)
    _run_sum_product_dense_numba(
        warm_graph.priors, *warm_arrays, float(scope["old_message_weight"]), cap,
        float(scope["forced_full_cap_tolerance"]),
    )

    for size in sizes:
        lattice = paper_periodic_honeycomb(size)
        observation = PublicD4Observation(
            (0,) * lattice.vertex_count, (-1,) * lattice.vertex_count
        )

        graph_seconds, graph = measure(
            lambda: build_r6d_factor_graph(
                lattice, observation, error_rate=float(scope["error_rate"]),
                terminal_screened=False,
            ), 1,
        )
        pack_seconds, arrays = measure(lambda: dense_factor_graph_arrays(graph), 1)
        template_seconds, template = measure(
            lambda: build_r6d_dense_template(lattice, error_rate=float(scope["error_rate"])), 1
        )

        def recurrence():
            return _run_sum_product_dense_numba(
                graph.priors, *arrays, float(scope["old_message_weight"]), cap,
                float(scope["forced_full_cap_tolerance"]),
            )

        recurrence_seconds, result = measure(recurrence, 1)
        cached_seconds, cached = measure(
            lambda: run_r6d_dense_template(
                template, observation, old_message_weight=float(scope["old_message_weight"]),
                max_iterations=cap, tolerance=float(scope["forced_full_cap_tolerance"]),
            ), repetitions,
        )
        _marginals, _converged, iterations, _delta, valid = result
        if not valid or int(iterations) != cap:
            raise AssertionError(f"L={size} failed the forced recurrence gate")
        if not np.array_equal(result[0], cached.marginals) or int(result[2]) != cached.iterations:
            raise AssertionError(f"L={size} cached recurrence differs from rebuilt recurrence")
        if lattice.edge_count != 9 * size * size or graph.variable_count != 27 * size * size:
            raise AssertionError(f"L={size} has unexpected paper-normalized topology")
        rows.append({
            "size": size,
            "physical_edges": lattice.edge_count,
            "binary_variables": graph.variable_count,
            "factors": len(graph.factors),
            "directed_messages": int(arrays[4].shape[0]),
            "maximum_factor_arity": int(arrays[0].shape[1]),
            "graph_build_seconds": graph_seconds,
            "dense_pack_seconds": pack_seconds,
            "one_time_template_build_seconds": template_seconds,
            "prepacked_recurrence_seconds": recurrence_seconds,
            "prepacked_microseconds_per_iteration": 1e6 * recurrence_seconds / cap,
            "cached_refresh_and_recurrence_seconds": cached_seconds,
            "cached_end_to_end_speedup": (graph_seconds + pack_seconds + recurrence_seconds) / cached_seconds,
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_production_size_cpu_baseline",
        "manifest": manifest_path.name,
        "scope": scope,
        "rows": rows,
        "claim_boundary": manifest["claim_boundary"],
    }


def render(payload: dict) -> str:
    scope = payload["scope"]
    lines = [
        "# R6S production-size R6D BP CPU baseline",
        "",
        "This controlled benchmark uses one deterministic, finite observation per size and forces "
        f"{scope['forced_iterations']} iterations. Each timing is the mean of "
        f"{scope['timing_repetitions_per_size']} calls after one excluded compilation warm-up.",
        "",
        "| L | edges | build + pack + BP | cached refresh + BP | speedup |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['size']} | {row['physical_edges']} | "
            f"{1e3 * (row['graph_build_seconds'] + row['dense_pack_seconds'] + row['prepacked_recurrence_seconds']):.2f} ms | "
            f"{1e3 * row['cached_refresh_and_recurrence_seconds']:.2f} ms | "
            f"{row['cached_end_to_end_speedup']:.2f}x |"
        )
    lines.extend(["", payload["claim_boundary"], ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run(args.manifest)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "report": str(args.report), "rows": payload["rows"]}, indent=2))


if __name__ == "__main__":
    main()
