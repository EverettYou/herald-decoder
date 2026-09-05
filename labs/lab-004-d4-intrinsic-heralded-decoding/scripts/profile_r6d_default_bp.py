#!/usr/bin/env python3
"""Profile the frozen R6N default R6D BP recurrence by implementation layer."""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_factor_graph, run_sum_product
from d4_recovery import decode_and_score_flux_recovery


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6p-default-bp-runtime-profile-manifest-2026-08-29.json"
DEFAULT_INPUT = LAB_DIR / "results/r6n-default-flux-policy-comparison-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6p-default-bp-runtime-profile-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6p-default-bp-runtime-profile-2026-08-29.md"
BP = "R6D_local_BP_posterior_LLR_MWPM"


def selected_chain(edge_count: int, selected: list[int]) -> np.ndarray:
    chain = np.zeros(edge_count, dtype=np.uint8)
    chain[np.asarray(selected, dtype=int)] = 1
    return chain


def llr_weights(marginals: np.ndarray) -> np.ndarray:
    probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1.0 - 1.0e-12)
    return np.log((1.0 - probabilities) / probabilities)


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
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6P":
        raise ValueError("manifest is not an active R6P registration")
    source = json.loads(input_path.read_text(encoding="utf-8"))
    scope = source["scope"]
    config = scope["bp_defaults"]
    count = int(manifest["scope"]["records"].split()[1])
    frozen_rows = [row for row in source["rows"] if row["status"] == "nonterminal"][:count]
    if len(frozen_rows) != count:
        raise ValueError("frozen R6N input does not contain the registered record count")
    lattice = paper_periodic_honeycomb(int(scope["size"]))
    graph_times: list[float] = []
    bp_times: list[float] = []
    matching_times: list[float] = []
    profile = cProfile.Profile()
    replay_failures: list[int] = []
    iterations: list[int] = []
    for frozen in frozen_rows:
        public = frozen["public_observation"]
        physical = selected_chain(lattice.edge_count, frozen["physical_error_edges"])
        observation = PublicD4Observation(
            tuple(int(value) for value in public["flux_syndrome"]),
            tuple(int(value) for value in public["charge_outcomes"]),
        )
        start = time.perf_counter()
        graph = build_r6d_factor_graph(
            lattice, observation, error_rate=float(scope["physical_error_rate"]),
            terminal_screened=bool(config["terminal_screened"]),
        )
        graph_times.append(time.perf_counter() - start)
        start = time.perf_counter()
        profile.enable()
        bp = run_sum_product(
            graph, old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
        )
        profile.disable()
        bp_times.append(time.perf_counter() - start)
        iterations.append(int(bp.iterations))
        start = time.perf_counter()
        recovery = decode_and_score_flux_recovery(lattice, physical, llr_weights(bp.marginals[: lattice.edge_count, 1]))
        matching_times.append(time.perf_counter() - start)
        frozen_correction = selected_chain(lattice.edge_count, frozen["policies"][BP]["correction_edges"])
        if not np.array_equal(recovery.correction, frozen_correction):
            replay_failures.append(int(frozen["trajectory_index"]))
    if replay_failures:
        raise AssertionError(f"BP correction replay mismatch at {replay_failures}")
    output = io.StringIO()
    stats = pstats.Stats(profile, stream=output).strip_dirs().sort_stats("cumulative")
    stats.print_stats(20)
    total = sum(graph_times) + sum(bp_times) + sum(matching_times)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_replay_consistent_runtime_profile",
        "manifest": manifest_path.name,
        "source": input_path.name,
        "profiled_trajectory_indices": [int(row["trajectory_index"]) for row in frozen_rows],
        "replay_failure_count": 0,
        "timing": {
            "factor_graph_build": summary(graph_times),
            "BP_recurrence": summary(bp_times),
            "posterior_LLR_MWPM_and_scoring": summary(matching_times),
            "BP_share_of_profiled_pipeline": float(sum(bp_times) / total) if total else None,
            "mean_BP_iterations": float(np.mean(iterations)),
        },
        "cprofile_top_cumulative": output.getvalue(),
        "claim_boundary": manifest["claim_boundary"],
    }


def render(payload: dict) -> str:
    timing = payload["timing"]
    lines = [
        "# R6P default R6D BP runtime profile",
        "",
        f"Profiled {len(payload['profiled_trajectory_indices'])} fixed, replay-verified R6N trajectories.",
        "",
        "| layer | mean time | median time |",
        "| --- | ---: | ---: |",
    ]
    for label, key in (
        ("factor graph build", "factor_graph_build"),
        ("BP recurrence", "BP_recurrence"),
        ("posterior-LLR MWPM + scoring", "posterior_LLR_MWPM_and_scoring"),
    ):
        item = timing[key]
        lines.append(f"| {label} | {1000 * item['mean_seconds']:.2f} ms | {1000 * item['median_seconds']:.2f} ms |")
    lines.extend([
        "",
        f"The recurrence accounts for {100 * timing['BP_share_of_profiled_pipeline']:.1f}% of this Python-table pipeline; mean BP iterations are {timing['mean_BP_iterations']:.2f}.",
        "",
        "## cProfile cumulative-time excerpt",
        "",
        "```text",
        payload["cprofile_top_cumulative"].rstrip(),
        "```",
        "",
        "This profile identifies prototype implementation cost only. It does not extrapolate the measured Python ratio to an optimized dense, Numba, JAX, or GPU recurrence.",
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
    print(json.dumps({"output": str(args.output), "report": str(args.report), "timing": payload["timing"]}, indent=2))


if __name__ == "__main__":
    main()
