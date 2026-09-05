#!/usr/bin/env python3
"""Run the registered Lab 002 Phase C1 convergence ablations.

This intentionally owns an experimental recurrence implementation rather than
changing the frozen Lab 002 damping decoder.  It measures whether damping,
update ordering, or deterministic local initialization changes convergence on
matched observations.  It does not decode or make a logical-error claim.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder.lattice_model import sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


LAB = Path(__file__).resolve().parents[1]
RESULT = LAB / "results" / "convergence-ablations-c1.json"
FIGURE = LAB / "figures" / "convergence-ablations-c1.png"
SEEDS = (12, *range(8201, 8264))
TOLERANCE = 1e-8
MAX_ITERATIONS = 80


@dataclass(frozen=True)
class Condition:
    id: str
    family: str
    label: str
    damping: float = 0.25
    schedule: str = "synchronous"
    initialization: str = "prior"


CONDITIONS = (
    Condition("baseline", "reference", "frozen synchronous, damping 0.25"),
    Condition("damping_0", "damping", "damping 0.00", damping=0.0),
    Condition("damping_010", "damping", "damping 0.10", damping=0.10),
    Condition("damping_050", "damping", "damping 0.50", damping=0.50),
    Condition(
        "residual_priority",
        "schedule",
        "residual-priority Gauss-Seidel",
        schedule="residual_priority",
    ),
    Condition(
        "local_bootstrap",
        "initialization",
        "local-observation bootstrap",
        initialization="local_bootstrap",
    ),
)


def normalise(values: np.ndarray) -> np.ndarray:
    total = float(values[0] + values[1])
    if not np.isfinite(total) or total <= 0:
        raise ValueError("zero-probability BP message")
    return values / total


def max_delta(current: np.ndarray, previous: np.ndarray) -> float:
    return float(np.max(np.abs(current - previous)))


def factor_message(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
    variable_to_factor: dict[tuple[int, int], np.ndarray],
    factor: int,
    target_position: int,
) -> np.ndarray:
    incident = decoder.factor_edges[factor]
    assignments = decoder.assignments[len(incident)]
    potential = decoder.factor_potentials[(len(incident), int(syndrome[factor]), int(herald[factor]))]
    values = potential.copy()
    for position, edge in enumerate(incident):
        if position != target_position:
            values *= variable_to_factor[(edge, factor)][assignments[:, position]]
    return normalise(
        np.bincount(assignments[:, target_position], weights=values, minlength=2).astype(float)
    )


def variable_message(
    decoder: LegacyDampedBpMatchingDecoder,
    factor_to_variable: dict[tuple[int, int], np.ndarray],
    edge: int,
    target_factor: int,
) -> np.ndarray:
    values = decoder.prior.copy()
    for factor in decoder.edge_factors[edge]:
        if factor != target_factor:
            values *= factor_to_variable[(edge, factor)]
    return normalise(values)


def initialise(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
    mode: str,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray]]:
    variable_to_factor = {
        (edge, factor): decoder.prior.copy()
        for edge, factors in enumerate(decoder.edge_factors)
        for factor in factors
    }
    factor_to_variable = {key: np.full(2, 0.5) for key in variable_to_factor}
    if mode == "prior":
        return variable_to_factor, factor_to_variable
    if mode != "local_bootstrap":
        raise ValueError(f"unknown initialization mode: {mode}")
    # This single local pass uses no neighboring BP evidence beyond the prior.
    for factor, incident in enumerate(decoder.factor_edges):
        for position, edge in enumerate(incident):
            factor_to_variable[(edge, factor)] = factor_message(
                decoder, syndrome, herald, variable_to_factor, factor, position
            )
    for edge, factors in enumerate(decoder.edge_factors):
        for target_factor in factors:
            variable_to_factor[(edge, target_factor)] = variable_message(
                decoder, factor_to_variable, edge, target_factor
            )
    return variable_to_factor, factor_to_variable


def marginals(
    decoder: LegacyDampedBpMatchingDecoder,
    factor_to_variable: dict[tuple[int, int], np.ndarray],
) -> np.ndarray:
    result = np.zeros(len(decoder.graph.edges), dtype=float)
    for edge, factors in enumerate(decoder.edge_factors):
        belief = decoder.prior.copy()
        for factor in factors:
            belief *= factor_to_variable[(edge, factor)]
        result[edge] = normalise(belief)[1]
    return result


def synchronous_step(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
    variable_to_factor: dict[tuple[int, int], np.ndarray],
    factor_to_variable: dict[tuple[int, int], np.ndarray],
    damping: float,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray], np.ndarray]:
    updated_factor: dict[tuple[int, int], np.ndarray] = {}
    for factor, incident in enumerate(decoder.factor_edges):
        for position, edge in enumerate(incident):
            raw = factor_message(decoder, syndrome, herald, variable_to_factor, factor, position)
            updated_factor[(edge, factor)] = normalise(
                damping * factor_to_variable[(edge, factor)] + (1 - damping) * raw
            )
    updated_variable = {
        (edge, target): variable_message(decoder, updated_factor, edge, target)
        for edge, factors in enumerate(decoder.edge_factors)
        for target in factors
    }
    deltas = np.asarray(
        [max_delta(updated_factor[key], factor_to_variable[key]) for key in updated_factor]
        + [max_delta(updated_variable[key], variable_to_factor[key]) for key in updated_variable],
        dtype=float,
    )
    return updated_variable, updated_factor, deltas


def residual_priority_step(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
    variable_to_factor: dict[tuple[int, int], np.ndarray],
    factor_to_variable: dict[tuple[int, int], np.ndarray],
    damping: float,
    previous_factor_residuals: np.ndarray | None,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray], np.ndarray, np.ndarray]:
    variable = {key: value.copy() for key, value in variable_to_factor.items()}
    factor_messages = {key: value.copy() for key, value in factor_to_variable.items()}
    if previous_factor_residuals is None:
        order = range(len(decoder.factor_edges))
    else:
        order = np.argsort(-previous_factor_residuals, kind="stable")
    factor_residuals = np.zeros(len(decoder.factor_edges), dtype=float)
    deltas: list[float] = []
    for factor in order:
        incident = decoder.factor_edges[int(factor)]
        for position, edge in enumerate(incident):
            key = (edge, int(factor))
            raw = factor_message(decoder, syndrome, herald, variable, int(factor), position)
            updated = normalise(damping * factor_messages[key] + (1 - damping) * raw)
            delta = max_delta(updated, factor_messages[key])
            deltas.append(delta)
            factor_residuals[int(factor)] = max(factor_residuals[int(factor)], delta)
            factor_messages[key] = updated
            # Propagate this factor update immediately to the other endpoint.
            for target_factor in decoder.edge_factors[edge]:
                if target_factor == factor:
                    continue
                variable_key = (edge, target_factor)
                refreshed = variable_message(decoder, factor_messages, edge, target_factor)
                variable_delta = max_delta(refreshed, variable[variable_key])
                deltas.append(variable_delta)
                factor_residuals[target_factor] = max(factor_residuals[target_factor], variable_delta)
                variable[variable_key] = refreshed
    return variable, factor_messages, np.asarray(deltas, dtype=float), factor_residuals


def proper_scores(probabilities: np.ndarray, error: np.ndarray) -> tuple[float, float]:
    clipped = np.clip(probabilities, 1e-12, 1 - 1e-12)
    truth = np.asarray(error, dtype=float)
    return (
        float(-np.mean(truth * np.log(clipped) + (1 - truth) * np.log(1 - clipped))),
        float(np.mean((clipped - truth) ** 2)),
    )


def run_condition(condition: Condition, observation) -> dict:
    graph = square_graph(9)
    decoder = LegacyDampedBpMatchingDecoder(
        graph, p=0.20, q=1.0, p_m=0.0, p_h=0.0, max_iterations=MAX_ITERATIONS,
        damping=condition.damping, tolerance=TOLERANCE, use_numba=False,
    )
    variable, factor = initialise(decoder, observation.syndrome, observation.herald, condition.initialization)
    prior_factor_residuals = None
    started = perf_counter()
    for iteration in range(1, MAX_ITERATIONS + 1):
        if condition.schedule == "synchronous":
            variable, factor, deltas = synchronous_step(
                decoder, observation.syndrome, observation.herald, variable, factor, condition.damping
            )
        elif condition.schedule == "residual_priority":
            variable, factor, deltas, prior_factor_residuals = residual_priority_step(
                decoder, observation.syndrome, observation.herald, variable, factor, condition.damping,
                prior_factor_residuals,
            )
        else:
            raise ValueError(f"unknown schedule: {condition.schedule}")
        final_delta = float(np.max(deltas))
        if final_delta < TOLERANCE:
            break
    elapsed_ms = 1000 * (perf_counter() - started)
    edge_marginals = marginals(decoder, factor)
    log_loss, brier = proper_scores(edge_marginals, observation.error)
    return {
        "iterations": iteration,
        "converged": final_delta < TOLERANCE,
        "final_max_message_delta": final_delta,
        "edge_log_loss": log_loss,
        "edge_brier": brier,
        "runtime_ms": elapsed_ms,
        "marginals": edge_marginals,
    }


def paired_interval(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    sample_count = len(values)
    indices = rng.integers(0, sample_count, size=(5000, sample_count))
    means = np.mean(values[indices], axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def summarise(condition: Condition, records: list[dict], baseline: list[dict]) -> dict:
    fields = ("iterations", "final_max_message_delta", "edge_log_loss", "edge_brier", "runtime_ms")
    summary = {
        "id": condition.id,
        "family": condition.family,
        "label": condition.label,
        "controls": {
            "damping": condition.damping,
            "schedule": condition.schedule,
            "initialization": condition.initialization,
        },
        "converged": int(sum(record["converged"] for record in records)),
        "convergence_rate": float(np.mean([record["converged"] for record in records])),
        "means": {field: float(np.mean([record[field] for record in records])) for field in fields},
    }
    if condition.id != "baseline":
        paired = {}
        for offset, field in enumerate(("edge_log_loss", "edge_brier", "runtime_ms")):
            difference = np.asarray([row[field] - ref[field] for row, ref in zip(records, baseline)], dtype=float)
            paired[field] = {"mean_delta": float(np.mean(difference)), "bootstrap_ci95": paired_interval(difference, 2300 + offset)}
        convergence_delta = np.asarray(
            [float(row["converged"]) - float(ref["converged"]) for row, ref in zip(records, baseline)]
        )
        paired["convergence_rate"] = {"mean_delta": float(np.mean(convergence_delta)), "bootstrap_ci95": paired_interval(convergence_delta, 2400)}
        summary["paired_vs_baseline"] = paired
    return summary


def render(payload: dict) -> None:
    summaries = payload["summaries"]
    labels = [summary["label"] for summary in summaries]
    x = np.arange(len(summaries))
    baseline = summaries[0]
    convergence = [summary["convergence_rate"] for summary in summaries]
    log_loss_delta = [summary["means"]["edge_log_loss"] - baseline["means"]["edge_log_loss"] for summary in summaries]
    runtime_ratio = [summary["means"]["runtime_ms"] / baseline["means"]["runtime_ms"] for summary in summaries]
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    colors = ["#0072B2" if item["id"] == "baseline" else "#009E73" for item in summaries]
    axes[0].bar(x, convergence, color=colors)
    axes[0].set(title="Fixed-point convergence", ylabel="fraction of 64 observations", ylim=(0, 1))
    axes[1].bar(x, log_loss_delta, color=colors)
    axes[1].axhline(0, color="#222222", linewidth=0.8)
    axes[1].set(title="Mean edge log-loss versus frozen baseline", ylabel="delta (positive is worse)")
    axes[2].bar(x, runtime_ratio, color=colors)
    axes[2].axhline(1, color="#222222", linewidth=0.8)
    axes[2].set(title="Python recurrence runtime", ylabel="ratio to frozen baseline")
    for axis in axes:
        axis.set_xticks(x, labels, rotation=31, ha="right", fontsize=8)
        axis.grid(axis="y", alpha=0.2)
    figure.suptitle("Lab 002 Phase C1 matched BP convergence ablation · square L=9, p=0.20, q=1")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--observation-count",
        type=int,
        default=len(SEEDS),
        help="run a deterministic prefix of the registered seed list; default is the full 64-observation matrix",
    )
    args = parser.parse_args()
    if not 1 <= args.observation_count <= len(SEEDS):
        raise SystemExit(f"observation-count must lie in [1, {len(SEEDS)}]")
    graph = square_graph(9)
    active_seeds = SEEDS[: args.observation_count]
    observations = [
        sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0, p_m=0.0, p_h=0.0)
        for seed in active_seeds
    ]
    all_records: dict[str, list[dict]] = {}
    for condition in CONDITIONS:
        all_records[condition.id] = [run_condition(condition, observation) for observation in observations]
    # C0 remains a frozen-reference check, not merely a repeated observation.
    reference = LegacyDampedBpMatchingDecoder(
        graph, p=0.20, q=1.0, max_iterations=MAX_ITERATIONS, damping=0.25,
        tolerance=TOLERANCE, use_numba=False,
    ).infer(observations[0].syndrome, observations[0].herald)
    if not np.array_equal(reference.edge_marginals, all_records["baseline"][0]["marginals"]):
        raise RuntimeError("C1 frozen baseline does not reproduce the production seed-12 marginals")
    if reference.max_message_delta != all_records["baseline"][0]["final_max_message_delta"]:
        raise RuntimeError("C1 frozen baseline does not reproduce the production seed-12 residual")
    summaries = [summarise(condition, all_records[condition.id], all_records["baseline"]) for condition in CONDITIONS]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C1 complete matched BP convergence ablation",
        "sample_design": {
            "lattice": "square", "L": 9, "p": 0.20, "q": 1.0, "p_m": 0.0, "p_h": 0.0,
            "seeds": list(active_seeds), "observations": len(observations), "includes_c0_seed": 12 in active_seeds,
            "tolerance": TOLERANCE, "max_iterations": MAX_ITERATIONS,
        },
        "reference_validation": {
            "seed12_marginals_bit_identical_to_frozen_production": True,
            "seed12_final_residual_identical_to_frozen_production": True,
        },
        "conditions": [condition.__dict__ for condition in CONDITIONS],
        "summaries": summaries,
        "per_observation": {
            condition.id: [
                {key: value for key, value in record.items() if key != "marginals"}
                for record in all_records[condition.id]
            ]
            for condition in CONDITIONS
        },
        "evidence_boundary": "Matched recurrence diagnostics only. No decoding, LER, or promotion inference is made.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    render(payload)
    print(json.dumps({"result": str(RESULT), "figure": str(FIGURE), "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
