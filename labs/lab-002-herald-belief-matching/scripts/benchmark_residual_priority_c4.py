#!/usr/bin/env python3
"""Fresh multi-geometry C4 replication for compiled residual-priority BP."""

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

from benchmark_residual_priority_c2 import bootstrap, scores


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "residual-priority-c4.json"
FIGURE = LAB / "figures" / "residual-priority-c4.png"
CONFIGS = (
    ("square", square_graph, 9, tuple(range(10401, 10465))),
    ("honeycomb", honeycomb_graph, 5, tuple(range(10501, 10565))),
)


def decoder(graph, schedule: str) -> LegacyDampedBpMatchingDecoder:
    return LegacyDampedBpMatchingDecoder(
        graph, p=0.20, q=1.0, max_iterations=80, damping=0.25,
        tolerance=1e-8, update_schedule=schedule, use_numba=True,
    )


def run_geometry(name, make_graph, size, seeds) -> dict:
    graph = make_graph(size)
    observations = [sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0) for seed in seeds]
    arms = {"synchronous": decoder(graph, "synchronous"), "residual_priority": decoder(graph, "residual_priority")}
    for arm in arms.values():
        for _ in range(2):
            arm.decode(observations[0].syndrome, observations[0].herald)
    records = {name: [] for name in arms}
    for index, (seed, observation) in enumerate(zip(seeds, observations)):
        order = ("synchronous", "residual_priority") if index % 2 == 0 else ("residual_priority", "synchronous")
        for label in order:
            started = perf_counter()
            decoded = arms[label].decode(observation.syndrome, observation.herald)
            elapsed = 1000 * (perf_counter() - started)
            if not np.array_equal(graph.true_syndrome(decoded.correction), observation.syndrome):
                raise RuntimeError(f"{name} {label} correction is not syndrome faithful on seed {seed}")
            log_loss, brier = scores(decoded.bp.edge_marginals, observation.error)
            records[label].append({
                "seed": seed, "runtime_ms": elapsed, "converged": bool(decoded.bp.converged),
                "iterations": int(decoded.bp.iterations), "edge_log_loss": log_loss, "edge_brier": brier,
                "syndrome_faithful": True,
            })
    summaries = {
        label: {
            "convergence_rate": float(np.mean([row["converged"] for row in rows])),
            "mean_iterations": float(np.mean([row["iterations"] for row in rows])),
            "mean_log_loss": float(np.mean([row["edge_log_loss"] for row in rows])),
            "mean_brier": float(np.mean([row["edge_brier"] for row in rows])),
            "mean_runtime_ms": float(np.mean([row["runtime_ms"] for row in rows])),
            "all_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in rows)),
        }
        for label, rows in records.items()
    }
    paired = {}
    for offset, field in enumerate(("converged", "iterations", "edge_log_loss", "edge_brier", "runtime_ms")):
        values = np.asarray([float(new[field]) - float(old[field]) for old, new in zip(records["synchronous"], records["residual_priority"])])
        paired[field] = {"mean_delta": float(np.mean(values)), "bootstrap_ci95": bootstrap(values, 6100 + offset)}
    return {"lattice": name, "L": size, "p": 0.20, "q": 1.0, "seeds": list(seeds), "summaries": summaries, "paired": paired, "per_observation": records}


def main() -> None:
    results = [run_geometry(*config) for config in CONFIGS]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C4 independent compiled residual-priority multi-geometry replication",
        "timing_protocol": "Two untimed warm-ups per arm, followed by alternating arm order on each matched observation.",
        "geometries": results,
        "evidence_boundary": "Independent convergence, posterior-score, syndrome-faithfulness, and timing replication; geometry-specific results are not pooled into a threshold or cross-geometry LER claim.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), constrained_layout=True)
    labels = [item["lattice"] for item in results]
    x = np.arange(len(labels))
    width = 0.35
    axes[0].bar(x - width / 2, [item["summaries"]["synchronous"]["convergence_rate"] for item in results], width, label="synchronous", color="#0072B2")
    axes[0].bar(x + width / 2, [item["summaries"]["residual_priority"]["convergence_rate"] for item in results], width, label="residual priority", color="#009E73")
    axes[0].set(title="Fixed-point convergence", ylabel="fraction", xticks=x, xticklabels=labels, ylim=(0, 1))
    axes[0].legend()
    axes[1].bar(x - width / 2, [item["summaries"]["synchronous"]["mean_runtime_ms"] for item in results], width, label="synchronous", color="#0072B2")
    axes[1].bar(x + width / 2, [item["summaries"]["residual_priority"]["mean_runtime_ms"] for item in results], width, label="residual priority", color="#009E73")
    axes[1].set(title="Compiled decode time", ylabel="mean ms / observation", xticks=x, xticklabels=labels)
    for axis in axes:
        axis.grid(axis="y", alpha=0.22)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)
    print(json.dumps({"result": str(RESULT), "figure": str(FIGURE), "geometries": [{"lattice": item["lattice"], "summaries": item["summaries"], "paired": item["paired"]} for item in results]}, indent=2))


if __name__ == "__main__":
    main()
