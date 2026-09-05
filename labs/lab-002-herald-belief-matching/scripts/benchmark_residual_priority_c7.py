#!/usr/bin/env python3
"""Run Lab 002 C7 allocation-only exact-equivalence benchmark."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder.lattice_model import honeycomb_graph, sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder

from benchmark_residual_priority_c2 import bootstrap


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "residual-priority-c7.json"
FIGURE = LAB / "figures" / "residual-priority-c7.png"
REPEATS = 5
CONFIGS = (
    ("square", square_graph, 9, tuple(range(11601, 11665))),
    ("honeycomb", honeycomb_graph, 5, tuple(range(11701, 11765))),
)


def make_decoder(graph, reuse: bool) -> LegacyDampedBpMatchingDecoder:
    return LegacyDampedBpMatchingDecoder(
        graph,
        p=0.20,
        q=1.0,
        p_m=0.0,
        p_h=0.0,
        max_iterations=80,
        damping=0.25,
        tolerance=1e-8,
        update_schedule="residual_priority",
        residual_priority_order="stable_sort",
        residual_priority_buffer_reuse=reuse,
        use_numba=True,
    )


def run_geometry(name, make_graph, size, seeds) -> dict:
    graph = make_graph(size)
    observations = [
        sample_observation(
            graph, np.random.default_rng(seed), p=0.20, q=1.0, p_m=0.0, p_h=0.0
        )
        for seed in seeds
    ]
    arms = {"reference": make_decoder(graph, False), "buffer_reuse": make_decoder(graph, True)}
    for decoder in arms.values():
        for _ in range(3):
            decoder.decode(observations[0].syndrome, observations[0].herald)

    rows = []
    for index, (seed, observation) in enumerate(zip(seeds, observations)):
        timings = {label: [] for label in arms}
        terminal = {}
        for repeat in range(REPEATS):
            order = (
                ("reference", "buffer_reuse")
                if (index + repeat) % 2 == 0
                else ("buffer_reuse", "reference")
            )
            for label in order:
                started = perf_counter()
                terminal[label] = arms[label].decode(
                    observation.syndrome, observation.herald
                )
                timings[label].append(1000 * (perf_counter() - started))

        reference = terminal["reference"]
        optimized = terminal["buffer_reuse"]
        faithful = all(
            np.array_equal(graph.true_syndrome(result.correction), observation.syndrome)
            for result in terminal.values()
        )
        exact = (
            np.array_equal(reference.bp.edge_marginals, optimized.bp.edge_marginals)
            and np.array_equal(reference.edge_weights, optimized.edge_weights)
            and np.array_equal(reference.correction, optimized.correction)
            and reference.bp.iterations == optimized.bp.iterations
            and reference.bp.converged == optimized.bp.converged
            and reference.bp.max_message_delta == optimized.bp.max_message_delta
            and faithful
        )
        if not exact:
            raise RuntimeError(f"C7 exact-equivalence gate failed for {name} seed {seed}")
        reference_ms = float(np.median(timings["reference"]))
        reuse_ms = float(np.median(timings["buffer_reuse"]))
        rows.append(
            {
                "seed": seed,
                "iterations": int(reference.bp.iterations),
                "converged": bool(reference.bp.converged),
                "reference_decode_ms": reference_ms,
                "buffer_reuse_decode_ms": reuse_ms,
                "runtime_delta_ms": reuse_ms - reference_ms,
                "bit_identical": True,
                "syndrome_faithful": True,
            }
        )

    reference_times = np.asarray([row["reference_decode_ms"] for row in rows])
    reuse_times = np.asarray([row["buffer_reuse_decode_ms"] for row in rows])
    delta = reuse_times - reference_times
    return {
        "lattice": name,
        "L": size,
        "seeds": list(seeds),
        "equivalence": {
            "all_observations_bit_identical": bool(all(row["bit_identical"] for row in rows)),
            "all_corrections_syndrome_faithful": bool(
                all(row["syndrome_faithful"] for row in rows)
            ),
        },
        "summary": {
            "reference_mean_decode_ms": float(np.mean(reference_times)),
            "buffer_reuse_mean_decode_ms": float(np.mean(reuse_times)),
            "buffer_reuse_minus_reference_ms": {
                "mean": float(np.mean(delta)),
                "bootstrap_ci95": bootstrap(delta, 8300 + size),
            },
            "relative_runtime": float(np.mean(reuse_times) / np.mean(reference_times)),
            "converged": int(sum(row["converged"] for row in rows)),
        },
        "per_observation": rows,
    }


def render(results: list[dict]) -> None:
    labels = [item["lattice"] for item in results]
    x = np.arange(len(labels))
    width = 0.35
    figure, axis = plt.subplots(figsize=(7.8, 4.5), constrained_layout=True)
    axis.bar(
        x - width / 2,
        [item["summary"]["reference_mean_decode_ms"] for item in results],
        width,
        label="validated stable sort",
        color="#0072B2",
    )
    axis.bar(
        x + width / 2,
        [item["summary"]["buffer_reuse_mean_decode_ms"] for item in results],
        width,
        label="preallocated buffers",
        color="#009E73",
    )
    axis.set(
        title="Allocation-only residual-priority optimization",
        ylabel="mean end-to-end decode ms / observation",
        xticks=x,
        xticklabels=labels,
    )
    axis.grid(axis="y", alpha=0.22)
    axis.legend()
    figure.suptitle("Lab 002 C7 · exact-equivalence gate")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    results = [run_geometry(*config) for config in CONFIGS]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C7 allocation-only exact-equivalence optimization",
        "timing_protocol": "C6 streams; three untimed warm-ups per arm; five end-to-end decode timings per arm and observation with alternating arm order; per-observation medians enter paired analysis.",
        "implementation_change": "Preallocate and swap factor-message, variable-message, residual, priority-order, priority-scratch, and processed buffers without changing factor or floating-point operation order.",
        "geometries": results,
        "evidence_boundary": "Implementation-only exact-equivalence and timing test; no BP-model, logical-performance, threshold, or default change.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    render(results)
    print(
        json.dumps(
            {
                "result": str(RESULT),
                "figure": str(FIGURE),
                "geometries": [
                    {"lattice": item["lattice"], "summary": item["summary"]}
                    for item in results
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
