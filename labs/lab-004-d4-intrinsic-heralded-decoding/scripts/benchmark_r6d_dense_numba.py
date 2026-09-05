#!/usr/bin/env python3
"""Verify and benchmark dense Numba R6D BP against the frozen Python recurrence."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_factor_graph, run_sum_product, run_sum_product_dense_numba
from d4_recovery import decode_and_score_flux_recovery


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6q-dense-numba-equivalence-benchmark-manifest-2026-08-29.json"
DEFAULT_INPUT = LAB_DIR / "results/r6n-default-flux-policy-comparison-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6q-dense-numba-equivalence-benchmark-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6q-dense-numba-equivalence-benchmark-2026-08-29.md"
BP = "R6D_local_BP_posterior_LLR_MWPM"


def selected_chain(edge_count: int, selected: list[int]) -> np.ndarray:
    chain = np.zeros(edge_count, dtype=np.uint8)
    chain[np.asarray(selected, dtype=int)] = 1
    return chain


def llr_weights(marginals: np.ndarray) -> np.ndarray:
    probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1.0 - 1.0e-12)
    return np.log((1.0 - probabilities) / probabilities)


def timing_summary(values: list[float]) -> dict:
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
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6Q":
        raise ValueError("manifest is not an active R6Q registration")
    source = json.loads(input_path.read_text(encoding="utf-8"))
    scope = source["scope"]
    config = scope["bp_defaults"]
    lattice = paper_periodic_honeycomb(int(scope["size"]))
    rows = [row for row in source["rows"] if row["status"] == "nonterminal"]
    if len(rows) != 100:
        raise ValueError("R6Q expects the frozen 100-record R6N cohort")

    def graph_for(row):
        public = row["public_observation"]
        observation = PublicD4Observation(
            tuple(int(value) for value in public["flux_syndrome"]),
            tuple(int(value) for value in public["charge_outcomes"]),
        )
        return build_r6d_factor_graph(
            lattice, observation, error_rate=float(scope["physical_error_rate"]),
            terminal_screened=bool(config["terminal_screened"]),
        )

    # Compile once and keep it separate from warm recurrence timing.
    warm_graph = graph_for(rows[0])
    started = time.perf_counter()
    run_sum_product_dense_numba(
        warm_graph, old_message_weight=float(config["old_message_weight"]),
        max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
    )
    compilation_seconds = time.perf_counter() - started

    python_times: list[float] = []
    dense_times: list[float] = []
    maximum_marginal_error = 0.0
    mismatches: list[dict] = []
    for row in rows:
        graph = graph_for(row)
        physical = selected_chain(lattice.edge_count, row["physical_error_edges"])
        started = time.perf_counter()
        python = run_sum_product(
            graph, old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
        )
        python_times.append(time.perf_counter() - started)
        started = time.perf_counter()
        dense = run_sum_product_dense_numba(
            graph, old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
        )
        dense_times.append(time.perf_counter() - started)
        error = float(np.max(np.abs(python.marginals - dense.marginals)))
        maximum_marginal_error = max(maximum_marginal_error, error)
        python_recovery = decode_and_score_flux_recovery(lattice, physical, llr_weights(python.marginals[: lattice.edge_count, 1]))
        dense_recovery = decode_and_score_flux_recovery(lattice, physical, llr_weights(dense.marginals[: lattice.edge_count, 1]))
        frozen = selected_chain(lattice.edge_count, row["policies"][BP]["correction_edges"])
        if (
            error > 1e-12
            or python.converged != dense.converged
            or python.iterations != dense.iterations
            or abs(python.max_message_delta - dense.max_message_delta) > 1e-12
            or not np.array_equal(python_recovery.correction, dense_recovery.correction)
            or not np.array_equal(dense_recovery.correction, frozen)
        ):
            mismatches.append({
                "trajectory_index": int(row["trajectory_index"]),
                "maximum_marginal_error": error,
                "python": {"converged": bool(python.converged), "iterations": int(python.iterations), "delta": float(python.max_message_delta)},
                "dense": {"converged": bool(dense.converged), "iterations": int(dense.iterations), "delta": float(dense.max_message_delta)},
            })
    if mismatches:
        raise AssertionError(f"dense R6D equivalence failed: {mismatches[:3]}")
    python_summary = timing_summary(python_times)
    dense_summary = timing_summary(dense_times)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_exact_recurrence_equivalence_benchmark",
        "manifest": manifest_path.name,
        "source": input_path.name,
        "records": len(rows),
        "maximum_marginal_error": maximum_marginal_error,
        "mismatch_count": 0,
        "timing": {
            "numba_first_call_compilation_seconds": compilation_seconds,
            "python_recurrence": python_summary,
            "dense_numba_recurrence_and_packing": dense_summary,
            "mean_speedup": float(python_summary["mean_seconds"] / dense_summary["mean_seconds"]),
            "median_speedup": float(python_summary["median_seconds"] / dense_summary["median_seconds"]),
        },
        "claim_boundary": manifest["claim_boundary"],
    }


def render(payload: dict) -> str:
    timing = payload["timing"]
    python = timing["python_recurrence"]
    dense = timing["dense_numba_recurrence_and_packing"]
    return "\n".join([
        "# R6Q dense Numba R6D recurrence benchmark",
        "",
        f"All {payload['records']} frozen R6N records match exactly at the recorded default recurrence: maximum marginal difference {payload['maximum_marginal_error']:.3e}; no convergence, iteration, residual, or MWPM-correction mismatches.",
        "",
        "| implementation | mean recurrence time | median recurrence time |",
        "| --- | ---: | ---: |",
        f"| Python table recurrence | {1000 * python['mean_seconds']:.2f} ms | {1000 * python['median_seconds']:.2f} ms |",
        f"| Dense Numba recurrence + packing | {1000 * dense['mean_seconds']:.2f} ms | {1000 * dense['median_seconds']:.2f} ms |",
        "",
        f"Warm mean speedup: {timing['mean_speedup']:.2f}×; median speedup: {timing['median_speedup']:.2f}×. The excluded first-call JIT compilation cost is {timing['numba_first_call_compilation_seconds']:.2f} s.",
        "",
        "The comparison preserves the approximation exactly; it is a CPU Numba result, not a GPU benchmark or an exact-posterior claim.",
        "",
    ])


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
    print(json.dumps({"output": str(args.output), "report": str(args.report), "timing": payload["timing"]}, indent=2))


if __name__ == "__main__":
    main()
