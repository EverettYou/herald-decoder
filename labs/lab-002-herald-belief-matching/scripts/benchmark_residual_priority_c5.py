#!/usr/bin/env python3
"""Profile equivalent compiled factor-order selectors for Lab 002 C5."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder.lattice_model import sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder

from benchmark_residual_priority_c2 import bootstrap


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "residual-priority-c5.json"
FIGURE = LAB / "figures" / "residual-priority-c5.png"
SEEDS = tuple(range(10401, 10465))
REPEATS = 5


def decoder(order: str) -> LegacyDampedBpMatchingDecoder:
    return LegacyDampedBpMatchingDecoder(
        square_graph(9),
        p=0.20,
        q=1.0,
        max_iterations=80,
        damping=0.25,
        tolerance=1e-8,
        update_schedule="residual_priority",
        residual_priority_order=order,
        use_numba=True,
    )


def timed_infer(decoder_: LegacyDampedBpMatchingDecoder, observation) -> tuple[object, float]:
    started = perf_counter()
    result = decoder_.infer(observation.syndrome, observation.herald)
    return result, 1000 * (perf_counter() - started)


def main() -> None:
    graph = square_graph(9)
    observations = [
        sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0)
        for seed in SEEDS
    ]
    arms = {"scan": decoder("scan"), "stable_sort": decoder("stable_sort")}
    for arm in arms.values():
        for _ in range(3):
            arm.decode(observations[0].syndrome, observations[0].herald)

    rows = []
    for index, (seed, observation) in enumerate(zip(SEEDS, observations)):
        timings = {name: [] for name in arms}
        terminal = {}
        for repeat in range(REPEATS):
            names = ("scan", "stable_sort") if (index + repeat) % 2 == 0 else ("stable_sort", "scan")
            for name in names:
                result, elapsed = timed_infer(arms[name], observation)
                timings[name].append(elapsed)
                terminal[name] = result

        reference = arms["scan"].decode(observation.syndrome, observation.herald)
        optimized = arms["stable_sort"].decode(observation.syndrome, observation.herald)
        exact = (
            np.array_equal(reference.bp.edge_marginals, optimized.bp.edge_marginals)
            and np.array_equal(reference.edge_weights, optimized.edge_weights)
            and np.array_equal(reference.correction, optimized.correction)
            and reference.bp.iterations == optimized.bp.iterations
            and reference.bp.converged == optimized.bp.converged
            and reference.bp.max_message_delta == optimized.bp.max_message_delta
            and np.array_equal(
                graph.true_syndrome(reference.correction),
                observation.syndrome,
            )
            and np.array_equal(
                graph.true_syndrome(optimized.correction),
                observation.syndrome,
            )
        )
        if not exact:
            raise RuntimeError(f"C5 ordering mismatch on seed {seed}")
        for name in arms:
            inferred = terminal[name]
            if not np.array_equal(inferred.edge_marginals, reference.bp.edge_marginals):
                raise RuntimeError(f"C5 timed inference mismatch for {name} on seed {seed}")

        scan_ms = float(np.median(timings["scan"]))
        sort_ms = float(np.median(timings["stable_sort"]))
        rows.append(
            {
                "seed": seed,
                "iterations": int(reference.bp.iterations),
                "converged": bool(reference.bp.converged),
                "scan_infer_ms": scan_ms,
                "stable_sort_infer_ms": sort_ms,
                "runtime_delta_ms": sort_ms - scan_ms,
                "scan_ms_per_iteration": scan_ms / reference.bp.iterations,
                "stable_sort_ms_per_iteration": sort_ms / reference.bp.iterations,
                "bit_identical": True,
                "syndrome_faithful": True,
            }
        )

    scan = np.asarray([row["scan_infer_ms"] for row in rows])
    stable = np.asarray([row["stable_sort_infer_ms"] for row in rows])
    delta = stable - scan
    scan_per_iteration = np.asarray([row["scan_ms_per_iteration"] for row in rows])
    stable_per_iteration = np.asarray([row["stable_sort_ms_per_iteration"] for row in rows])
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C5 compiled residual-priority scheduler-overhead profile",
        "sample_design": {
            "lattice": "square",
            "L": 9,
            "p": 0.20,
            "q": 1.0,
            "seeds": list(SEEDS),
            "observations": len(SEEDS),
            "timed_repeats_per_arm": REPEATS,
        },
        "timing_protocol": "Three untimed warm-ups per arm; five compiled infer timings per arm and observation with alternating arm order; per-observation median enters paired analysis.",
        "equivalence": {
            "all_observations_bit_identical": bool(all(row["bit_identical"] for row in rows)),
            "all_corrections_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in rows)),
            "equal_factor_update_order": True,
            "interpretation": "Because outputs, iteration counts, and factor order are identical, the paired infer-time difference isolates the ordering implementation overhead within measurement noise.",
        },
        "summary": {
            "scan_mean_infer_ms": float(np.mean(scan)),
            "stable_sort_mean_infer_ms": float(np.mean(stable)),
            "stable_sort_minus_scan_ms": {
                "mean": float(np.mean(delta)),
                "bootstrap_ci95": bootstrap(delta, 7501),
            },
            "scan_mean_ms_per_iteration": float(np.mean(scan_per_iteration)),
            "stable_sort_mean_ms_per_iteration": float(np.mean(stable_per_iteration)),
            "relative_runtime": float(np.mean(stable) / np.mean(scan)),
            "converged": int(sum(row["converged"] for row in rows)),
        },
        "per_observation": rows,
        "evidence_boundary": "Equivalent compiled scheduler profile on the fixed C4 square stream; no posterior, logical, threshold, or default-promotion change.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.3), constrained_layout=True)
    axes[0].bar(
        ["repeated scan", "stable sort"],
        [float(np.mean(scan)), float(np.mean(stable))],
        color=["#D55E00", "#009E73"],
    )
    axes[0].set(title="Compiled residual-priority inference", ylabel="mean ms / observation")
    axes[0].grid(axis="y", alpha=0.22)
    axes[1].scatter(scan, stable, s=24, alpha=0.72, color="#0072B2")
    limit = max(float(np.max(scan)), float(np.max(stable))) * 1.03
    axes[1].plot([0, limit], [0, limit], linestyle="--", color="#333333", linewidth=1)
    axes[1].set(
        title="Matched observation timings",
        xlabel="repeated scan ms",
        ylabel="stable sort ms",
        xlim=(0, limit),
        ylim=(0, limit),
    )
    figure.suptitle("Lab 002 C5 · equivalent factor-priority ordering")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)
    print(json.dumps({"result": str(RESULT), "figure": str(FIGURE), "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
