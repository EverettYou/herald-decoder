#!/usr/bin/env python3
"""Run Lab 002 Phase C2 end-to-end validation of residual-priority BP."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from math import comb, sqrt
from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder.lattice_model import sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "residual-priority-c2.json"
FIGURE = LAB / "figures" / "residual-priority-c2.png"
SEEDS = (12, *range(8201, 8264))


def wilson(errors: int, shots: int) -> list[float]:
    z = 1.959963984540054
    rate = errors / shots
    denom = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denom
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denom
    return [center - radius, center + radius]


def mcnemar(rescued: int, harmed: int) -> float:
    disagreements = rescued + harmed
    if disagreements == 0:
        return 1.0
    smaller = min(rescued, harmed)
    return min(1.0, 2 * sum(comb(disagreements, index) for index in range(smaller + 1)) / (2**disagreements))


def scores(probabilities: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    p = np.clip(probabilities, 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    return (
        float(-np.mean(truth * np.log(p) + (1 - truth) * np.log(1 - p))),
        float(np.mean((p - truth) ** 2)),
    )


def bootstrap(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(5000, len(values)))
    means = np.mean(values[indices], axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def make_decoder(schedule: str) -> LegacyDampedBpMatchingDecoder:
    graph = square_graph(9)
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
        use_numba=False,
    )


def decode_one(decoder: LegacyDampedBpMatchingDecoder, schedule: str, seed: int, observation) -> dict:
    graph = decoder.graph
    started = perf_counter()
    decoded = decoder.decode(observation.syndrome, observation.herald)
    runtime_ms = 1000 * (perf_counter() - started)
    syndrome_faithful = bool(np.array_equal(graph.true_syndrome(decoded.correction), observation.syndrome))
    if not syndrome_faithful:
        raise RuntimeError(f"{schedule} correction fails syndrome faithfulness on seed {seed}")
    log_loss, brier = scores(decoded.bp.edge_marginals, observation.error)
    return {
        "seed": seed,
        "converged": bool(decoded.bp.converged),
        "iterations": int(decoded.bp.iterations),
        "max_message_delta": float(decoded.bp.max_message_delta),
        "edge_log_loss": log_loss,
        "edge_brier": brier,
        "runtime_ms": runtime_ms,
        "logical_failure": bool(graph.logical_parity(observation.error ^ decoded.correction)),
        "syndrome_faithful": syndrome_faithful,
        "edge_weight_min": float(np.min(decoded.edge_weights)),
        "edge_weight_max": float(np.max(decoded.edge_weights)),
    }


def run_matched(observations) -> tuple[list[dict], list[dict]]:
    synchronous_decoder = make_decoder("synchronous")
    residual_decoder = make_decoder("residual_priority")
    # Compile/import/cache effects must not enter the timed scientific rows.
    for _ in range(2):
        synchronous_decoder.decode(observations[0].syndrome, observations[0].herald)
        residual_decoder.decode(observations[0].syndrome, observations[0].herald)
    records = {"synchronous": [], "residual_priority": []}
    for index, (seed, observation) in enumerate(zip(SEEDS, observations)):
        order = ("synchronous", "residual_priority") if index % 2 == 0 else ("residual_priority", "synchronous")
        for schedule in order:
            decoder = synchronous_decoder if schedule == "synchronous" else residual_decoder
            records[schedule].append(decode_one(decoder, schedule, seed, observation))
    return records["synchronous"], records["residual_priority"]


def summary(records: list[dict]) -> dict:
    count = len(records)
    failures = sum(row["logical_failure"] for row in records)
    return {
        "shots": count,
        "logical_errors": failures,
        "logical_error_rate": failures / count,
        "logical_error_ci95": wilson(failures, count),
        "converged": sum(row["converged"] for row in records),
        "convergence_rate": float(np.mean([row["converged"] for row in records])),
        "all_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in records)),
        "mean_iterations": float(np.mean([row["iterations"] for row in records])),
        "mean_log_loss": float(np.mean([row["edge_log_loss"] for row in records])),
        "mean_brier": float(np.mean([row["edge_brier"] for row in records])),
        "mean_runtime_ms": float(np.mean([row["runtime_ms"] for row in records])),
    }


def render(payload: dict) -> None:
    labels = ["synchronous", "residual-priority"]
    left = payload["summaries"]["synchronous"]
    right = payload["summaries"]["residual_priority"]
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), constrained_layout=True)
    axes[0].bar(labels, [left["convergence_rate"], right["convergence_rate"]], color=["#0072B2", "#009E73"])
    axes[0].set(title="Fixed-point convergence", ylabel="fraction", ylim=(0, 1))
    axes[1].bar(labels, [left["logical_error_rate"], right["logical_error_rate"]], color=["#0072B2", "#009E73"])
    axes[1].set(title="Corrected-LLR logical failure", ylabel="rate", ylim=(0, 1))
    axes[2].bar(labels, [left["mean_runtime_ms"], right["mean_runtime_ms"]], color=["#0072B2", "#009E73"])
    axes[2].set(title="Python decode time", ylabel="mean ms / observation")
    for axis in axes:
        axis.grid(axis="y", alpha=0.22)
    figure.suptitle("Lab 002 C2: synchronous versus residual-priority posterior-LLR decoding")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    graph = square_graph(9)
    observations = [
        sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0, p_m=0.0, p_h=0.0)
        for seed in SEEDS
    ]
    synchronous, residual = run_matched(observations)
    rescued = sum(old["logical_failure"] and not new["logical_failure"] for old, new in zip(synchronous, residual))
    harmed = sum(new["logical_failure"] and not old["logical_failure"] for old, new in zip(synchronous, residual))
    paired = {}
    for index, field in enumerate(("converged", "edge_log_loss", "edge_brier", "runtime_ms", "iterations")):
        values = np.asarray([float(new[field]) - float(old[field]) for old, new in zip(synchronous, residual)])
        paired[field] = {"mean_delta": float(np.mean(values)), "bootstrap_ci95": bootstrap(values, 4200 + index)}
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C2 residual-priority end-to-end posterior-LLR validation",
        "sample_design": {
            "lattice": "square", "L": 9, "p": 0.20, "q": 1.0, "p_m": 0.0, "p_h": 0.0,
            "seeds": list(SEEDS), "shots": len(SEEDS), "max_iterations": 80, "tolerance": 1e-8,
            "matching_projection": "posterior_llr",
        },
        "arms": {
            "synchronous": {"update_schedule": "synchronous", "use_numba": False},
            "residual_priority": {"update_schedule": "residual_priority", "use_numba": False},
        },
        "timing_protocol": "Two untimed warm-up decodes per arm, then alternating arm order by matched observation.",
        "summaries": {"synchronous": summary(synchronous), "residual_priority": summary(residual)},
        "paired": {
            "rescued_failures": rescued,
            "introduced_failures": harmed,
            "logical_error_rate_delta": (harmed - rescued) / len(SEEDS),
            "mcnemar_exact_p_value": mcnemar(rescued, harmed),
            "metrics": paired,
        },
        "per_observation": {"synchronous": synchronous, "residual_priority": residual},
        "evidence_boundary": "End-to-end correction-interface validation on the C1 mechanism sample. Logical outcomes are descriptive, not a powered LER claim or a production-performance benchmark.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    render(payload)
    print(json.dumps({"result": str(RESULT), "figure": str(FIGURE), "summaries": payload["summaries"], "paired": payload["paired"]}, indent=2))


if __name__ == "__main__":
    main()
