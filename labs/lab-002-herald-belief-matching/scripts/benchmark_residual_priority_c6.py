#!/usr/bin/env python3
"""Run Lab 002 C6 fresh end-to-end stable-sort timing confirmation."""

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
RESULT = LAB / "results" / "residual-priority-c6.json"
FIGURE = LAB / "figures" / "residual-priority-c6.png"
REPEATS = 5
CONFIGS = (
    ("square", square_graph, 9, tuple(range(11601, 11665))),
    ("honeycomb", honeycomb_graph, 5, tuple(range(11701, 11765))),
)


def make_decoder(graph, arm: str) -> LegacyDampedBpMatchingDecoder:
    schedule = "synchronous" if arm == "synchronous" else "residual_priority"
    return LegacyDampedBpMatchingDecoder(
        graph,
        p=0.20,
        q=1.0,
        p_m=0.0,
        p_h=0.0,
        max_iterations=80,
        damping=0.25,
        tolerance=1e-8,
        update_schedule=schedule,
        residual_priority_order="stable_sort",
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
    arms = {label: make_decoder(graph, label) for label in ("synchronous", "stable_sort")}
    for decoder in arms.values():
        for _ in range(3):
            decoder.decode(observations[0].syndrome, observations[0].herald)

    records = {label: [] for label in arms}
    correction_agreement = []
    for index, (seed, observation) in enumerate(zip(seeds, observations)):
        timings = {label: [] for label in arms}
        terminal = {}
        for repeat in range(REPEATS):
            order = (
                ("synchronous", "stable_sort")
                if (index + repeat) % 2 == 0
                else ("stable_sort", "synchronous")
            )
            for label in order:
                started = perf_counter()
                decoded = arms[label].decode(observation.syndrome, observation.herald)
                timings[label].append(1000 * (perf_counter() - started))
                terminal[label] = decoded

        for label, decoded in terminal.items():
            faithful = bool(
                np.array_equal(graph.true_syndrome(decoded.correction), observation.syndrome)
            )
            if not faithful:
                raise RuntimeError(f"{name} {label} correction is not syndrome faithful on seed {seed}")
            log_loss, brier = scores(decoded.bp.edge_marginals, observation.error)
            records[label].append(
                {
                    "seed": seed,
                    "runtime_ms": float(np.median(timings[label])),
                    "converged": bool(decoded.bp.converged),
                    "iterations": int(decoded.bp.iterations),
                    "max_message_delta": float(decoded.bp.max_message_delta),
                    "edge_log_loss": log_loss,
                    "edge_brier": brier,
                    "logical_failure": bool(
                        graph.logical_parity(observation.error ^ decoded.correction)
                    ),
                    "syndrome_faithful": True,
                }
            )
        correction_agreement.append(
            bool(np.array_equal(terminal["synchronous"].correction, terminal["stable_sort"].correction))
        )

    summaries = {}
    for label, rows in records.items():
        summaries[label] = {
            "converged": int(sum(row["converged"] for row in rows)),
            "convergence_rate": float(np.mean([row["converged"] for row in rows])),
            "mean_iterations": float(np.mean([row["iterations"] for row in rows])),
            "mean_log_loss": float(np.mean([row["edge_log_loss"] for row in rows])),
            "mean_brier": float(np.mean([row["edge_brier"] for row in rows])),
            "mean_runtime_ms": float(np.mean([row["runtime_ms"] for row in rows])),
            "logical_failures": int(sum(row["logical_failure"] for row in rows)),
            "all_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in rows)),
        }

    paired = {}
    fields = ("converged", "iterations", "edge_log_loss", "edge_brier", "runtime_ms")
    for offset, field in enumerate(fields):
        values = np.asarray(
            [
                float(new[field]) - float(old[field])
                for old, new in zip(records["synchronous"], records["stable_sort"])
            ]
        )
        paired[field] = {
            "mean_delta": float(np.mean(values)),
            "bootstrap_ci95": bootstrap(values, 7200 + offset),
        }
    paired["correction_agreement"] = int(sum(correction_agreement))
    paired["correction_disagreement"] = int(len(correction_agreement) - sum(correction_agreement))
    paired["rescued_failures"] = int(
        sum(
            old["logical_failure"] and not new["logical_failure"]
            for old, new in zip(records["synchronous"], records["stable_sort"])
        )
    )
    paired["introduced_failures"] = int(
        sum(
            new["logical_failure"] and not old["logical_failure"]
            for old, new in zip(records["synchronous"], records["stable_sort"])
        )
    )
    return {
        "lattice": name,
        "L": size,
        "p": 0.20,
        "q": 1.0,
        "p_m": 0.0,
        "p_h": 0.0,
        "seeds": list(seeds),
        "summaries": summaries,
        "paired": paired,
        "per_observation": records,
    }


def render(results: list[dict]) -> None:
    labels = [item["lattice"] for item in results]
    x = np.arange(len(labels))
    width = 0.35
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.3), constrained_layout=True)
    for axis, metric, title, ylabel in (
        (axes[0], "convergence_rate", "Fixed-point convergence", "fraction"),
        (axes[1], "mean_runtime_ms", "Compiled end-to-end decode", "mean ms / observation"),
    ):
        axis.bar(
            x - width / 2,
            [item["summaries"]["synchronous"][metric] for item in results],
            width,
            label="synchronous",
            color="#0072B2",
        )
        axis.bar(
            x + width / 2,
            [item["summaries"]["stable_sort"][metric] for item in results],
            width,
            label="stable-sort residual priority",
            color="#009E73",
        )
        axis.set(title=title, ylabel=ylabel, xticks=x, xticklabels=labels)
        axis.grid(axis="y", alpha=0.22)
    axes[0].set_ylim(0, 1)
    axes[0].legend()
    figure.suptitle("Lab 002 C6 · fresh optimized residual-priority confirmation")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    results = [run_geometry(*config) for config in CONFIGS]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C6 fresh end-to-end optimized residual-priority confirmation",
        "timing_protocol": "Three untimed warm-ups per arm; five compiled end-to-end decode timings per arm and observation with alternating arm order; per-observation medians enter paired analysis.",
        "arms": {
            "synchronous": {"update_schedule": "synchronous", "use_numba": True},
            "stable_sort": {
                "update_schedule": "residual_priority",
                "residual_priority_order": "stable_sort",
                "use_numba": True,
            },
        },
        "geometries": results,
        "evidence_boundary": "Fresh geometry-separated convergence, proper-score, correction, syndrome-faithfulness, and end-to-end timing confirmation; logical counts are descriptive and no default or threshold claim follows automatically.",
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
                    {
                        "lattice": item["lattice"],
                        "summaries": item["summaries"],
                        "paired": item["paired"],
                    }
                    for item in results
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
