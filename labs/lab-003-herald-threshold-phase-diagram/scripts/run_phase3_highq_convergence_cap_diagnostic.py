#!/usr/bin/env python3
"""Run the bounded matched honeycomb high-q residual-BP cap diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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

from herald_decoder import NUMBA_AVAILABLE, honeycomb_graph, sample_observation
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


LAB = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB.parents[1]
RESULT = LAB / "results" / "phase3-honeycomb-highq-l11-convergence-cap-2026-08-28.json"
FIGURE = LAB / "figures" / "phase3-honeycomb-highq-l11-convergence-cap-2026-08-28.png"
Q_VALUES = (0.85, 0.90, 0.95)
P_GRID = (0.40, 0.45, 0.49)
SIZE = 11
SEEDS = tuple(range(59001, 59065))
ARMS = ("residual_priority_80", "residual_priority_160", "residual_priority_320")
CAPS = {"residual_priority_80": 80, "residual_priority_160": 160, "residual_priority_320": 320}
SOURCE_FILES = {
    "runner": Path(__file__),
    "lattice_model": PROJECT_ROOT / "src/herald_decoder/lattice_model.py",
    "decoder": PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py",
    "damping_decoder": PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py",
    "numba_kernels": PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    return {name: sha256(path) for name, path in SOURCE_FILES.items()}


def central_interval(values: np.ndarray, seed: int, confidence: float = 0.90) -> list[float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(4000, len(values)))
    means = np.mean(values[indices], axis=1)
    tail = (1.0 - confidence) / 2.0
    return [float(np.quantile(means, tail)), float(np.quantile(means, 1.0 - tail))]


def scores(probabilities: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    probabilities = np.clip(probabilities, 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    return (
        float(-np.mean(truth * np.log(probabilities) + (1 - truth) * np.log(1 - probabilities))),
        float(np.mean((probabilities - truth) ** 2)),
    )


def make_decoder(graph, p: float, q: float, arm: str) -> LegacyDampedBpMatchingDecoder:
    return LegacyDampedBpMatchingDecoder(
        graph,
        p=p,
        q=q,
        p_m=0.0,
        p_h=0.0,
        max_iterations=CAPS[arm],
        damping=0.25,
        tolerance=1e-8,
        update_schedule="residual_priority",
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


def run_cell(size: int, p: float, q: float) -> dict:
    graph = honeycomb_graph(size)
    observations = [
        sample_observation(graph, np.random.default_rng(seed), p=p, q=q, p_m=0.0, p_h=0.0)
        for seed in SEEDS
    ]
    decoders = {arm: make_decoder(graph, p, q, arm) for arm in ARMS}
    for decoder in decoders.values():
        decoder.decode(observations[0].syndrome, observations[0].herald)

    records = {arm: [] for arm in ARMS}
    corrections: dict[int, dict[str, np.ndarray]] = {}
    for index, (seed, observation) in enumerate(zip(SEEDS, observations)):
        order = ARMS[index % len(ARMS):] + ARMS[: index % len(ARMS)]
        corrections[seed] = {}
        for arm in order:
            started = perf_counter()
            decoded = decoders[arm].decode(observation.syndrome, observation.herald)
            elapsed = 1000.0 * (perf_counter() - started)
            faithful = bool(np.array_equal(graph.true_syndrome(decoded.correction), observation.syndrome))
            if not faithful:
                raise RuntimeError(f"syndrome failure at L={size}, p={p}, q={q}, seed={seed}, arm={arm}")
            log_loss, brier = scores(decoded.bp.edge_marginals, observation.error)
            records[arm].append({
                "seed": seed,
                "converged": bool(decoded.bp.converged),
                "iterations": int(decoded.bp.iterations),
                "max_message_delta": float(decoded.bp.max_message_delta),
                "edge_log_loss": log_loss,
                "edge_brier": brier,
                "runtime_ms": elapsed,
                "logical_failure": bool(graph.logical_parity(observation.error ^ decoded.correction)),
                "syndrome_faithful": faithful,
            })
            corrections[seed][arm] = decoded.correction

    summaries = {arm: summarize(rows) for arm, rows in records.items()}
    comparisons = {}
    for comparison_index, (old_arm, new_arm) in enumerate(zip(ARMS, ARMS[1:])):
        metrics = {}
        for metric_index, field in enumerate(
            ("converged", "iterations", "max_message_delta", "edge_log_loss", "edge_brier", "runtime_ms")
        ):
            values = np.asarray([
                float(new[field]) - float(old[field])
                for old, new in zip(records[old_arm], records[new_arm])
            ])
            metrics[field] = {
                "mean_delta": float(np.mean(values)),
                "bootstrap_interval90": central_interval(
                    values,
                    590000 + 1000 * comparison_index + 100 * int(round(q * 100)) + 10 * int(round(p * 100)) + metric_index,
                ),
            }
        comparisons[f"{new_arm}_minus_{old_arm}"] = {
            "metrics": metrics,
            "correction_disagreements": int(sum(
                not np.array_equal(corrections[seed][old_arm], corrections[seed][new_arm])
                for seed in SEEDS
            )),
            "rescued_failures": int(sum(
                old["logical_failure"] and not new["logical_failure"]
                for old, new in zip(records[old_arm], records[new_arm])
            )),
            "introduced_failures": int(sum(
                new["logical_failure"] and not old["logical_failure"]
                for old, new in zip(records[old_arm], records[new_arm])
            )),
        }
    gains = [
        comparisons[f"{new}_minus_{old}"]["metrics"]["converged"]["bootstrap_interval90"][0] > 0
        for old, new in zip(ARMS, ARMS[1:])
    ]
    mechanism = "cap_80_to_160_and_160_to_320_sensitive" if all(gains) else (
        "cap_80_to_160_sensitive" if gains[0] else ("cap_160_to_320_sensitive" if gains[1] else "no_resolved_cap_gain")
    )
    return {
        "L": size,
        "p": p,
        "q": q,
        "seeds": list(SEEDS),
        "summaries": summaries,
        "comparisons": comparisons,
        "mechanism_classification": mechanism,
        "per_observation": records,
    }


def default_artifact_paths(size: int) -> tuple[Path, Path]:
    if size == 11:
        return RESULT, FIGURE
    stem = f"phase4-honeycomb-highq-l{size}-convergence-cap-2026-08-28"
    return LAB / "results" / f"{stem}.json", LAB / "figures" / f"{stem}.png"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=SIZE)
    parser.add_argument("--seed-start", type=int)
    parser.add_argument("--seed-count", type=int, default=len(SEEDS))
    parser.add_argument("--result", type=Path)
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args(argv)
    if args.size < 2 or args.seed_count < 1:
        parser.error("size must be at least 2 and seed-count must be positive")
    if args.seed_start is None:
        args.seed_start = 59001 if args.size == 11 else 60001
    default_result, default_figure = default_artifact_paths(args.size)
    args.result = args.result or default_result
    args.figure = args.figure or default_figure
    return args


def render(cells: list[dict], *, size: int, figure_path: Path) -> None:
    figure, axes = plt.subplots(1, len(Q_VALUES), figsize=(15, 4.8), constrained_layout=True, sharey=True)
    colors = {"residual_priority_80": "#0072B2", "residual_priority_160": "#E69F00", "residual_priority_320": "#009E73"}
    x = np.arange(len(P_GRID))
    width = 0.24
    for axis, q in zip(axes, Q_VALUES):
        rows = [cell for cell in cells if cell["q"] == q]
        for arm_index, arm in enumerate(ARMS):
            axis.bar(
                x + (arm_index - 1) * width,
                [cell["summaries"][arm]["convergence_rate"] for cell in rows],
                width,
                label=arm.replace("residual_priority_", "cap "),
                color=colors[arm],
            )
        axis.set(title=f"q={q:.2f}", xlabel="physical error p", xticks=x, xticklabels=[f"{p:.2f}" for p in P_GRID], ylim=(0, 1))
        axis.grid(axis="y", alpha=0.22)
    axes[0].set_ylabel("fixed-point convergence fraction")
    axes[0].legend(fontsize=8)
    figure.suptitle(f"Lab 003 · honeycomb L={size} high-q residual-BP iteration-cap diagnostic")
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=180)
    plt.close(figure)


def main(argv: list[str] | None = None) -> None:
    global SEEDS
    args = parse_args(argv)
    SEEDS = tuple(range(args.seed_start, args.seed_start + args.seed_count))
    if not NUMBA_AVAILABLE:
        raise SystemExit("accelerated runtime required")
    start_hashes = source_hashes()
    cells = [run_cell(args.size, p, q) for q in Q_VALUES for p in P_GRID]
    render(cells, size=args.size, figure_path=args.figure)
    end_hashes = source_hashes()
    if start_hashes != end_hashes:
        args.figure.unlink(missing_ok=True)
        raise RuntimeError("source drift detected; result and figure were not published")
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": f"Lab 003 bounded honeycomb high-q L{args.size} residual-BP convergence-cap diagnostic",
        "design": {
            "lattice": "honeycomb",
            "q_values": list(Q_VALUES),
            "L": args.size,
            "p_grid": list(P_GRID),
            "seeds": list(SEEDS),
            "observations_per_cell": len(SEEDS),
            "arms": {arm: {"schedule": "residual_priority", "priority_order": "stable_sort", "max_iterations": CAPS[arm]} for arm in ARMS},
            "matching_projection": "posterior_llr",
            "confidence_level": 0.90,
        },
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "numba_version": numba.__version__,
            "pymatching_version": pymatching.__version__,
            "numba_available": bool(NUMBA_AVAILABLE),
        },
        "source_hashes": start_hashes,
        "source_stability": {"start_equals_end": True},
        "cells": cells,
        "evidence_boundary": "Matched mechanism diagnostic only. It can identify iteration-cap sensitivity but cannot update p_c(q), q_c, or promote a new primary cap without a later registered end-to-end confirmation.",
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.result.with_name(f".{args.result.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, args.result)
    print(json.dumps({
        "result": str(args.result),
        "figure": str(args.figure),
        "cells": [{
            "q": cell["q"],
            "p": cell["p"],
            "mechanism": cell["mechanism_classification"],
            "converged": {arm: cell["summaries"][arm]["converged"] for arm in ARMS},
        } for cell in cells],
    }, indent=2))


if __name__ == "__main__":
    main()
