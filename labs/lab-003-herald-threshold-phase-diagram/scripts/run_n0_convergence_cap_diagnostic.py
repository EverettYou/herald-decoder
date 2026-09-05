#!/usr/bin/env python3
"""Run the bounded Lab 003 N0 high-p convergence-cap diagnostic."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import matplotlib
import numba
import numpy as np
import pymatching

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder import NUMBA_AVAILABLE, sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


LAB = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB.parents[1]
RESULT = LAB / "results" / "n0-square-q1-convergence-cap-2026-08-27.json"
FIGURE = LAB / "figures" / "n0-square-q1-convergence-cap-2026-08-27.png"
SIZES = (7, 9, 11, 13)
P_GRID = (0.30, 0.40, 0.49)
SEEDS = tuple(range(13001, 13065))
ARMS = ("synchronous_40", "synchronous_80", "residual_priority_80")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scores(probabilities: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    p = np.clip(probabilities, 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    return (
        float(-np.mean(truth * np.log(p) + (1 - truth) * np.log(1 - p))),
        float(np.mean((p - truth) ** 2)),
    )


def bootstrap(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(4000, len(values)))
    means = np.mean(values[indices], axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def make_decoder(graph, p: float, arm: str) -> LegacyDampedBpMatchingDecoder:
    residual = arm == "residual_priority_80"
    return LegacyDampedBpMatchingDecoder(
        graph,
        p=p,
        q=1.0,
        p_m=0.0,
        p_h=0.0,
        max_iterations=40 if arm == "synchronous_40" else 80,
        damping=0.25,
        tolerance=1e-8,
        update_schedule="residual_priority" if residual else "synchronous",
        residual_priority_order="stable_sort",
        use_numba=True,
    )


def summarize(rows: list[dict]) -> dict:
    return {
        "converged": int(sum(row["converged"] for row in rows)),
        "convergence_rate": float(np.mean([row["converged"] for row in rows])),
        "mean_iterations": float(np.mean([row["iterations"] for row in rows])),
        "mean_final_residual": float(np.mean([row["max_message_delta"] for row in rows])),
        "mean_log_loss": float(np.mean([row["edge_log_loss"] for row in rows])),
        "mean_brier": float(np.mean([row["edge_brier"] for row in rows])),
        "mean_runtime_ms": float(np.mean([row["runtime_ms"] for row in rows])),
        "logical_failures": int(sum(row["logical_failure"] for row in rows)),
        "all_syndrome_faithful": bool(all(row["syndrome_faithful"] for row in rows)),
    }


def run_cell(size: int, p: float) -> dict:
    graph = square_graph(size)
    observations = [
        sample_observation(graph, np.random.default_rng(seed), p=p, q=1.0, p_m=0.0, p_h=0.0)
        for seed in SEEDS
    ]
    decoders = {arm: make_decoder(graph, p, arm) for arm in ARMS}
    for decoder in decoders.values():
        for _ in range(2):
            decoder.decode(observations[0].syndrome, observations[0].herald)

    records = {arm: [] for arm in ARMS}
    corrections = {}
    for index, (seed, observation) in enumerate(zip(SEEDS, observations)):
        order = ARMS[index % 3 :] + ARMS[: index % 3]
        corrections[seed] = {}
        for arm in order:
            started = perf_counter()
            decoded = decoders[arm].decode(observation.syndrome, observation.herald)
            elapsed = 1000 * (perf_counter() - started)
            faithful = bool(
                np.array_equal(graph.true_syndrome(decoded.correction), observation.syndrome)
            )
            if not faithful:
                raise RuntimeError(f"N0 syndrome failure at L={size}, p={p}, seed={seed}, arm={arm}")
            log_loss, brier = scores(decoded.bp.edge_marginals, observation.error)
            logical_failure = bool(graph.logical_parity(observation.error ^ decoded.correction))
            records[arm].append(
                {
                    "seed": seed,
                    "converged": bool(decoded.bp.converged),
                    "iterations": int(decoded.bp.iterations),
                    "max_message_delta": float(decoded.bp.max_message_delta),
                    "edge_log_loss": log_loss,
                    "edge_brier": brier,
                    "runtime_ms": elapsed,
                    "logical_failure": logical_failure,
                    "syndrome_faithful": faithful,
                }
            )
            corrections[seed][arm] = decoded.correction

    summaries = {arm: summarize(rows) for arm, rows in records.items()}
    comparisons = {}
    for comparison_index, (old_arm, new_arm) in enumerate(
        (("synchronous_40", "synchronous_80"), ("synchronous_80", "residual_priority_80"))
    ):
        metrics = {}
        for metric_index, field in enumerate(
            ("converged", "iterations", "max_message_delta", "edge_log_loss", "edge_brier", "runtime_ms")
        ):
            values = np.asarray(
                [
                    float(new[field]) - float(old[field])
                    for old, new in zip(records[old_arm], records[new_arm])
                ]
            )
            metrics[field] = {
                "mean_delta": float(np.mean(values)),
                "bootstrap_ci95": bootstrap(
                    values, 15000 + 100 * size + 10 * comparison_index + metric_index
                ),
            }
        correction_disagreements = sum(
            not np.array_equal(corrections[seed][old_arm], corrections[seed][new_arm])
            for seed in SEEDS
        )
        rescued = sum(
            old["logical_failure"] and not new["logical_failure"]
            for old, new in zip(records[old_arm], records[new_arm])
        )
        harmed = sum(
            new["logical_failure"] and not old["logical_failure"]
            for old, new in zip(records[old_arm], records[new_arm])
        )
        comparisons[f"{new_arm}_minus_{old_arm}"] = {
            "metrics": metrics,
            "correction_disagreements": int(correction_disagreements),
            "rescued_failures": int(rescued),
            "introduced_failures": int(harmed),
        }

    cap_interval = comparisons["synchronous_80_minus_synchronous_40"]["metrics"]["converged"]["bootstrap_ci95"]
    schedule_interval = comparisons["residual_priority_80_minus_synchronous_80"]["metrics"]["converged"]["bootstrap_ci95"]
    if cap_interval[0] > 0 and schedule_interval[0] > 0:
        mechanism = "cap_and_schedule_sensitive"
    elif cap_interval[0] > 0:
        mechanism = "cap_sensitive"
    elif schedule_interval[0] > 0:
        mechanism = "schedule_sensitive"
    else:
        mechanism = "no_resolved_convergence_gain"
    return {
        "L": size,
        "p": p,
        "q": 1.0,
        "seeds": list(SEEDS),
        "summaries": summaries,
        "comparisons": comparisons,
        "mechanism_classification": mechanism,
        "per_observation": records,
    }


def render(cells: list[dict]) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True, sharey=True)
    colors = {"synchronous_40": "#0072B2", "synchronous_80": "#E69F00", "residual_priority_80": "#009E73"}
    for axis, p in zip(axes, P_GRID):
        rows = [cell for cell in cells if cell["p"] == p]
        x = np.arange(len(SIZES))
        width = 0.24
        for arm_index, arm in enumerate(ARMS):
            axis.bar(
                x + (arm_index - 1) * width,
                [cell["summaries"][arm]["convergence_rate"] for cell in rows],
                width,
                label=arm.replace("_", " "),
                color=colors[arm],
            )
        axis.set(title=f"p={p:.2f}", xlabel="L", xticks=x, xticklabels=SIZES, ylim=(0, 1))
        axis.grid(axis="y", alpha=0.22)
    axes[0].set_ylabel("fixed-point convergence fraction")
    axes[0].legend(fontsize=8)
    figure.suptitle("Lab 003 N0 · square q=1 convergence-cap diagnostic")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    if not NUMBA_AVAILABLE:
        raise SystemExit("accelerated runtime required")
    cells = [run_cell(size, p) for p in P_GRID for size in SIZES]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 003 Phase N0 bounded square q=1 convergence-cap diagnostic",
        "design": {
            "lattice": "square",
            "q": 1.0,
            "sizes": list(SIZES),
            "p_grid": list(P_GRID),
            "seeds": list(SEEDS),
            "observations_per_cell": len(SEEDS),
            "arms": {
                "synchronous_40": {"schedule": "synchronous", "max_iterations": 40},
                "synchronous_80": {"schedule": "synchronous", "max_iterations": 80},
                "residual_priority_80": {
                    "schedule": "residual_priority",
                    "priority_order": "stable_sort",
                    "max_iterations": 80,
                },
            },
            "matching_projection": "posterior_llr",
        },
        "timing_protocol": "Two untimed warm-ups per arm and cell; one end-to-end timed decode per matched observation with three-arm order rotated by observation index.",
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "numba_version": numba.__version__,
            "pymatching_version": pymatching.__version__,
            "numba_available": bool(NUMBA_AVAILABLE),
        },
        "source_hashes": {
            "runner": sha256(Path(__file__)),
            "lattice_model": sha256(PROJECT_ROOT / "src/herald_decoder/lattice_model.py"),
            "decoder": sha256(PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py"),
            "damping_decoder": sha256(
                PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py"
            ),
            "numba_kernels": sha256(PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py"),
        },
        "cells": cells,
        "evidence_boundary": "Small matched mechanism diagnostic for the fixed decoder; logical counts are descriptive and cannot update a threshold or phase boundary.",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    render(cells)
    print(
        json.dumps(
            {
                "result": str(RESULT),
                "figure": str(FIGURE),
                "cells": [
                    {
                        "L": cell["L"],
                        "p": cell["p"],
                        "mechanism": cell["mechanism_classification"],
                        "converged": {
                            arm: cell["summaries"][arm]["converged"] for arm in ARMS
                        },
                    }
                    for cell in cells
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
