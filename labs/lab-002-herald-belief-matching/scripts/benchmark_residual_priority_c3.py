#!/usr/bin/env python3
"""Verify and time the compiled Lab 002 residual-priority BP recurrence."""

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

from benchmark_residual_priority_c2 import SEEDS, bootstrap


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "residual-priority-c3.json"
FIGURE = LAB / "figures" / "residual-priority-c3.png"


def make_decoder(schedule: str, use_numba: bool) -> LegacyDampedBpMatchingDecoder:
    return LegacyDampedBpMatchingDecoder(
        square_graph(9), p=0.20, q=1.0, max_iterations=80, damping=0.25,
        tolerance=1e-8, update_schedule=schedule, use_numba=use_numba,
    )


def decode(decoder: LegacyDampedBpMatchingDecoder, observation) -> tuple[object, float]:
    started = perf_counter()
    result = decoder.decode(observation.syndrome, observation.herald)
    elapsed = 1000 * (perf_counter() - started)
    if not np.array_equal(decoder.graph.true_syndrome(result.correction), observation.syndrome):
        raise RuntimeError("compiled residual-priority correction is not syndrome faithful")
    return result, elapsed


def main() -> None:
    graph = square_graph(9)
    observations = [sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0) for seed in SEEDS]
    arms = {
        "synchronous_numba": make_decoder("synchronous", True),
        "residual_priority_python": make_decoder("residual_priority", False),
        "residual_priority_numba": make_decoder("residual_priority", True),
    }
    # Warm all three paths before recording timings or equivalence rows.
    for decoder in arms.values():
        for _ in range(2):
            decoder.decode(observations[0].syndrome, observations[0].herald)
    records = {name: [] for name in arms}
    equivalence = []
    names = tuple(arms)
    for index, (seed, observation) in enumerate(zip(SEEDS, observations)):
        results = {}
        for offset in range(len(names)):
            name = names[(index + offset) % len(names)]
            result, runtime_ms = decode(arms[name], observation)
            results[name] = result
            records[name].append({
                "seed": seed,
                "runtime_ms": runtime_ms,
                "converged": bool(result.bp.converged),
                "iterations": int(result.bp.iterations),
                "max_message_delta": float(result.bp.max_message_delta),
                "logical_failure": bool(graph.logical_parity(observation.error ^ result.correction)),
            })
        python = results["residual_priority_python"]
        compiled = results["residual_priority_numba"]
        exact = (
            np.array_equal(python.bp.edge_marginals, compiled.bp.edge_marginals)
            and np.array_equal(python.edge_weights, compiled.edge_weights)
            and np.array_equal(python.correction, compiled.correction)
            and python.bp.iterations == compiled.bp.iterations
            and python.bp.converged == compiled.bp.converged
            and python.bp.max_message_delta == compiled.bp.max_message_delta
        )
        if not exact:
            raise RuntimeError(f"Python/Numba residual-priority mismatch on seed {seed}")
        equivalence.append({"seed": seed, "bit_identical": True})
    summaries = {
        name: {
            "mean_runtime_ms": float(np.mean([row["runtime_ms"] for row in rows])),
            "convergence_rate": float(np.mean([row["converged"] for row in rows])),
            "mean_iterations": float(np.mean([row["iterations"] for row in rows])),
            "logical_errors": int(sum(row["logical_failure"] for row in rows)),
        }
        for name, rows in records.items()
    }
    runtime_delta = np.asarray([
        new["runtime_ms"] - old["runtime_ms"]
        for old, new in zip(records["synchronous_numba"], records["residual_priority_numba"])
    ])
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C3 compiled residual-priority equivalence and timing validation",
        "sample_design": {"lattice": "square", "L": 9, "p": 0.20, "q": 1.0, "seeds": list(SEEDS), "shots": len(SEEDS)},
        "timing_protocol": "Two warm-ups per arm; three arm orders rotate by matched observation.",
        "equivalence": {"python_numba_bit_identical_all_observations": True, "rows": equivalence},
        "summaries": summaries,
        "paired_compiled_vs_synchronous": {
            "runtime_ms_delta": {"mean": float(np.mean(runtime_delta)), "bootstrap_ci95": bootstrap(runtime_delta, 5301)},
        },
        "per_observation": records,
        "evidence_boundary": "Compiled recurrence and timing validation only; no new powered logical-error comparison.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    figure, axis = plt.subplots(figsize=(7.4, 4.3), constrained_layout=True)
    labels = ["sync Numba", "residual Python", "residual Numba"]
    values = [summaries[key]["mean_runtime_ms"] for key in ("synchronous_numba", "residual_priority_python", "residual_priority_numba")]
    axis.bar(labels, values, color=["#0072B2", "#D55E00", "#009E73"])
    axis.set(title="Lab 002 C3 matched decode time", ylabel="mean ms / observation")
    axis.grid(axis="y", alpha=0.22)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)
    print(json.dumps({"result": str(RESULT), "figure": str(FIGURE), "summaries": summaries, "paired": payload["paired_compiled_vs_synchronous"]}, indent=2))


if __name__ == "__main__":
    main()
