#!/usr/bin/env python3
"""Run Lab 002 C8 cached-product numerical-equivalence gate."""

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
RESULT = LAB / "results" / "residual-priority-c8.json"
FIGURE = LAB / "figures" / "residual-priority-c8.png"
MARGINAL_TOLERANCE = 1e-12
LLR_TOLERANCE = 1e-10
REPEATS = 5
CONFIGS = (
    ("square", square_graph, 9, tuple(range(11601, 11665))),
    ("honeycomb", honeycomb_graph, 5, tuple(range(11701, 11765))),
)


def make_decoder(graph, cached: bool) -> LegacyDampedBpMatchingDecoder:
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
        residual_priority_cached_products=cached,
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
    reference = make_decoder(graph, False)
    candidate = make_decoder(graph, True)
    gate_rows = []
    for seed, observation in zip(seeds, observations):
        old = reference.decode(observation.syndrome, observation.herald)
        new = candidate.decode(observation.syndrome, observation.herald)
        marginal_error = float(np.max(np.abs(new.bp.edge_marginals - old.bp.edge_marginals)))
        llr_error = float(np.max(np.abs(new.edge_weights - old.edge_weights)))
        correction_equal = bool(np.array_equal(new.correction, old.correction))
        convergence_equal = bool(new.bp.converged == old.bp.converged)
        iterations_equal = bool(new.bp.iterations == old.bp.iterations)
        syndrome_faithful = bool(
            np.array_equal(graph.true_syndrome(new.correction), observation.syndrome)
            and np.array_equal(graph.true_syndrome(old.correction), observation.syndrome)
        )
        passed = bool(
            marginal_error <= MARGINAL_TOLERANCE
            and llr_error <= LLR_TOLERANCE
            and correction_equal
            and convergence_equal
            and iterations_equal
            and syndrome_faithful
        )
        gate_rows.append(
            {
                "seed": seed,
                "max_marginal_abs_error": marginal_error,
                "max_llr_abs_error": llr_error,
                "correction_equal": correction_equal,
                "convergence_equal": convergence_equal,
                "iterations_equal": iterations_equal,
                "syndrome_faithful": syndrome_faithful,
                "passed": passed,
            }
        )

    gate_passed = bool(all(row["passed"] for row in gate_rows))
    timing = None
    if gate_passed:
        for decoder in (reference, candidate):
            for _ in range(3):
                decoder.decode(observations[0].syndrome, observations[0].herald)
        timing_rows = []
        for index, (seed, observation) in enumerate(zip(seeds, observations)):
            elapsed = {"reference": [], "cached_product": []}
            arms = {"reference": reference, "cached_product": candidate}
            for repeat in range(REPEATS):
                order = (
                    ("reference", "cached_product")
                    if (index + repeat) % 2 == 0
                    else ("cached_product", "reference")
                )
                for label in order:
                    started = perf_counter()
                    arms[label].decode(observation.syndrome, observation.herald)
                    elapsed[label].append(1000 * (perf_counter() - started))
            old_ms = float(np.median(elapsed["reference"]))
            new_ms = float(np.median(elapsed["cached_product"]))
            timing_rows.append(
                {
                    "seed": seed,
                    "reference_decode_ms": old_ms,
                    "cached_product_decode_ms": new_ms,
                    "runtime_delta_ms": new_ms - old_ms,
                }
            )
        old_times = np.asarray([row["reference_decode_ms"] for row in timing_rows])
        new_times = np.asarray([row["cached_product_decode_ms"] for row in timing_rows])
        delta = new_times - old_times
        timing = {
            "reference_mean_decode_ms": float(np.mean(old_times)),
            "cached_product_mean_decode_ms": float(np.mean(new_times)),
            "cached_product_minus_reference_ms": {
                "mean": float(np.mean(delta)),
                "bootstrap_ci95": bootstrap(delta, 9400 + size),
            },
            "relative_runtime": float(np.mean(new_times) / np.mean(old_times)),
            "per_observation": timing_rows,
        }

    return {
        "lattice": name,
        "L": size,
        "seeds": list(seeds),
        "max_detector_factors_per_edge": int(max(len(factors) for factors in reference.edge_factors)),
        "gate": {
            "passed": gate_passed,
            "passed_observations": int(sum(row["passed"] for row in gate_rows)),
            "observations": len(gate_rows),
            "maximum_marginal_abs_error": float(
                max(row["max_marginal_abs_error"] for row in gate_rows)
            ),
            "maximum_llr_abs_error": float(max(row["max_llr_abs_error"] for row in gate_rows)),
            "correction_disagreements": int(sum(not row["correction_equal"] for row in gate_rows)),
            "convergence_disagreements": int(
                sum(not row["convergence_equal"] for row in gate_rows)
            ),
            "iteration_disagreements": int(sum(not row["iterations_equal"] for row in gate_rows)),
            "all_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in gate_rows)),
        },
        "timing": timing,
        "per_observation_gate": gate_rows,
    }


def render(results: list[dict]) -> None:
    labels = [item["lattice"] for item in results]
    figure, axis = plt.subplots(figsize=(7.8, 4.5), constrained_layout=True)
    if all(item["gate"]["passed"] for item in results):
        x = np.arange(len(labels))
        width = 0.35
        axis.bar(
            x - width / 2,
            [item["timing"]["reference_mean_decode_ms"] for item in results],
            width,
            label="validated stable sort",
            color="#0072B2",
        )
        axis.bar(
            x + width / 2,
            [item["timing"]["cached_product_mean_decode_ms"] for item in results],
            width,
            label="cached product",
            color="#009E73",
        )
        axis.set(ylabel="mean end-to-end decode ms / observation", xticks=x, xticklabels=labels)
        axis.legend()
    else:
        x = np.arange(len(labels))
        axis.bar(
            x,
            [item["gate"]["passed_observations"] / item["gate"]["observations"] for item in results],
            color="#D55E00",
        )
        axis.set(ylabel="fraction passing all gates", xticks=x, xticklabels=labels, ylim=(0, 1))
    axis.set_title("Cached-product numerical-equivalence gate")
    axis.grid(axis="y", alpha=0.22)
    figure.suptitle("Lab 002 C8")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    results = [run_geometry(*config) for config in CONFIGS]
    passed = bool(all(item["gate"]["passed"] for item in results))
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C8 cached-product bounded numerical-equivalence test",
        "gate_thresholds": {
            "maximum_marginal_abs_error": MARGINAL_TOLERANCE,
            "maximum_llr_abs_error": LLR_TOLERANCE,
            "identical_corrections": True,
            "identical_convergence_flags": True,
            "identical_iteration_counts": True,
            "syndrome_faithful": True,
        },
        "gate_passed": passed,
        "timing_protocol": (
            "Timing runs only if every gate passes; then three warm-ups and five alternating-order "
            "end-to-end decodes per arm and observation, with paired medians."
        ),
        "geometries": results,
        "evidence_boundary": "Implementation-only cached-product gate on the fixed C6 streams; no decoder-model, logical-performance, threshold, or default change.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    render(results)
    print(
        json.dumps(
            {
                "result": str(RESULT),
                "figure": str(FIGURE),
                "gate_passed": passed,
                "geometries": [
                    {"lattice": item["lattice"], "gate": item["gate"], "timing": item["timing"]}
                    for item in results
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
