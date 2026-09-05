#!/usr/bin/env python3
"""Pilot and systematic matched A/B for the two Lab 002 BP front ends."""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from math import comb, sqrt
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pymatching

from herald_bp_decoder import HeraldBeliefMatchingDecoder
from lattice_model import honeycomb_graph, sample_observation, square_graph
from legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


ARM_NAMES = ("legacy_damped", "memory_assisted")


def graph_for(lattice: str, size: int = 5):
    return square_graph(size) if lattice == "square" else honeycomb_graph(size)


def wilson_interval(errors: int, shots: int) -> list[float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return [center - radius, center + radius]


def mcnemar_exact(rescued: int, harmed: int) -> float:
    discordant = rescued + harmed
    if discordant == 0:
        return 1.0
    tail = sum(comb(discordant, index) for index in range(min(rescued, harmed) + 1))
    return min(1.0, 2 * tail / (2**discordant))


def proper_scores(probabilities: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    probabilities = np.clip(np.asarray(probabilities, dtype=float), 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    log_loss = -np.mean(truth * np.log(probabilities) + (1 - truth) * np.log(1 - probabilities))
    brier = np.mean((probabilities - truth) ** 2)
    return float(log_loss), float(brier)


def bootstrap_mean_ci(values: list[float], seed: int) -> list[float]:
    values_array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means: list[np.ndarray] = []
    remaining = 5000
    while remaining:
        batch = min(250, remaining)
        indices = rng.integers(0, len(values_array), size=(batch, len(values_array)))
        means.append(np.mean(values_array[indices], axis=1))
        remaining -= batch
    return [float(value) for value in np.quantile(np.concatenate(means), [0.025, 0.975])]


def make_decoders(graph, *, p: float, q: float, p_m: float, p_h: float):
    return {
        "legacy_damped": LegacyDampedBpMatchingDecoder(
            graph,
            p=p,
            q=q,
            p_m=p_m,
            p_h=p_h,
            max_iterations=40,
            damping=0.25,
            tolerance=1e-8,
        ),
        "memory_assisted": HeraldBeliefMatchingDecoder(
            graph,
            p=p,
            q=q,
            p_m=p_m,
            p_h=p_h,
            recurrence_mode="memory",
            max_iterations=40,
            tolerance=1e-8,
            gamma0=0.15,
            relay_legs=6,
            relay_leg_iterations=20,
            gamma_interval=(-0.24, 0.66),
            relay_seed=0,
        ),
    }


def record_from_result(graph, observation, result, *, decode_ms: float, cache_hit: bool) -> dict:
    failed = bool(graph.logical_parity(observation.error ^ result.correction))
    log_loss, brier = proper_scores(result.bp.edge_marginals, observation.error)
    return {
        "failed": failed,
        "log_loss": log_loss,
        "brier": brier,
        "converged": bool(result.bp.converged),
        "iterations": int(result.bp.iterations),
        "max_message_delta": float(result.bp.max_message_delta),
        "decode_ms": decode_ms,
        "cache_hit": cache_hit,
        "selected_candidate": getattr(result.bp, "selected_leg", None),
        "candidate_score": getattr(result.bp, "score", None),
    }


def summarise_arm(records: list[dict]) -> dict:
    shots = len(records)
    failures = sum(record["failed"] for record in records)
    miss_times = [record["decode_ms"] for record in records if not record["cache_hit"]]
    result = {
        "shots": shots,
        "logical_errors": failures,
        "logical_error_rate": failures / shots,
        "logical_error_ci95": wilson_interval(failures, shots),
        "mean_edge_log_loss": float(np.mean([record["log_loss"] for record in records])),
        "mean_edge_brier": float(np.mean([record["brier"] for record in records])),
        "selected_candidate_convergence_rate": float(
            np.mean([record["converged"] for record in records])
        ),
        "mean_bp_iterations": float(np.mean([record["iterations"] for record in records])),
        "mean_max_message_delta": float(
            np.mean([record["max_message_delta"] for record in records])
        ),
        "cache_hit_rate": float(np.mean([record["cache_hit"] for record in records])),
        "unique_observations_decoded": len(miss_times),
        "mean_uncached_decode_ms": float(np.mean(miss_times)),
        "amortized_decode_compute_ms": float(np.sum(miss_times) / shots),
    }
    selected = [record["selected_candidate"] for record in records if record["selected_candidate"] is not None]
    if selected:
        result["selected_candidate_counts_zero_based"] = {
            str(key): value for key, value in sorted(Counter(selected).items())
        }
        result["mean_candidate_score"] = float(
            np.mean([record["candidate_score"] for record in records])
        )
    else:
        result["selected_candidate_counts_zero_based"] = None
        result["mean_candidate_score"] = None
    return result


def summarise_pair(records: dict[str, list[dict]], seed: int) -> dict:
    old = records["legacy_damped"]
    new = records["memory_assisted"]
    rescued = sum(a["failed"] and not b["failed"] for a, b in zip(old, new, strict=True))
    harmed = sum(b["failed"] and not a["failed"] for a, b in zip(old, new, strict=True))
    log_delta = [b["log_loss"] - a["log_loss"] for a, b in zip(old, new, strict=True)]
    brier_delta = [b["brier"] - a["brier"] for a, b in zip(old, new, strict=True)]
    return {
        "rescued_failures": rescued,
        "introduced_failures": harmed,
        "discordant_shots": rescued + harmed,
        "logical_error_rate_delta": (harmed - rescued) / len(old),
        "mcnemar_exact_p_value": mcnemar_exact(rescued, harmed),
        "mean_edge_log_loss_delta": float(np.mean(log_delta)),
        "edge_log_loss_delta_bootstrap_ci95": bootstrap_mean_ci(log_delta, seed),
        "mean_edge_brier_delta": float(np.mean(brier_delta)),
        "edge_brier_delta_bootstrap_ci95": bootstrap_mean_ci(brier_delta, seed + 1),
    }


def run_final_cell(task: dict) -> dict:
    lattice = task["lattice"]
    p = task["p"]
    graph = graph_for(lattice)
    decoders = make_decoders(
        graph,
        p=p,
        q=task["q"],
        p_m=task["p_m"],
        p_h=task["p_h"],
    )
    caches = {arm: {} for arm in ARM_NAMES}
    pooled = {arm: [] for arm in ARM_NAMES}
    per_seed = []
    cell_start = perf_counter()
    for seed_index, seed in enumerate(task["seeds"]):
        rng = np.random.default_rng(seed)
        seed_records = {arm: [] for arm in ARM_NAMES}
        for _ in range(task["shots_per_seed"]):
            observation = sample_observation(
                graph,
                rng,
                p=p,
                q=task["q"],
                p_m=task["p_m"],
                p_h=task["p_h"],
            )
            key = (observation.syndrome.tobytes(), observation.herald.tobytes())
            for arm, decoder in decoders.items():
                cache_hit = key in caches[arm]
                if cache_hit:
                    result = caches[arm][key]
                    decode_ms = 0.0
                else:
                    start = perf_counter()
                    result = decoder.decode(observation.syndrome, observation.herald)
                    decode_ms = 1000 * (perf_counter() - start)
                    if np.any(graph.true_syndrome(result.correction) != observation.syndrome):
                        raise RuntimeError(f"{arm} correction is not syndrome faithful")
                    caches[arm][key] = result
                record = record_from_result(
                    graph,
                    observation,
                    result,
                    decode_ms=decode_ms,
                    cache_hit=cache_hit,
                )
                seed_records[arm].append(record)
                pooled[arm].append(record)
        per_seed.append(
            {
                "seed": seed,
                "arms": {arm: summarise_arm(seed_records[arm]) for arm in ARM_NAMES},
                "paired": summarise_pair(
                    seed_records,
                    task["bootstrap_seed"] + seed_index * 10,
                ),
            }
        )
    return {
        "lattice": lattice,
        "L": 5,
        "edges": len(graph.edges),
        "detectors": len(graph.detector_vertices),
        "p": p,
        "q": task["q"],
        "p_m": task["p_m"],
        "p_h": task["p_h"],
        "shots": len(task["seeds"]) * task["shots_per_seed"],
        "per_seed": per_seed,
        "pooled": {
            "arms": {arm: summarise_arm(pooled[arm]) for arm in ARM_NAMES},
            "paired": summarise_pair(pooled, task["bootstrap_seed"] + 999),
        },
        "cell_wall_seconds": perf_counter() - cell_start,
    }


def run_pilot_cell(task: dict) -> dict:
    graph = graph_for(task["lattice"])
    decoder = make_decoders(
        graph,
        p=task["p"],
        q=task["q"],
        p_m=task["p_m"],
        p_h=task["p_h"],
    )["legacy_damped"]
    cache = {}
    records = []
    start_cell = perf_counter()
    for seed in task["seeds"]:
        rng = np.random.default_rng(seed)
        for _ in range(task["shots_per_seed"]):
            observation = sample_observation(
                graph,
                rng,
                p=task["p"],
                q=task["q"],
                p_m=task["p_m"],
                p_h=task["p_h"],
            )
            key = (observation.syndrome.tobytes(), observation.herald.tobytes())
            cache_hit = key in cache
            if cache_hit:
                result = cache[key]
                decode_ms = 0.0
            else:
                start = perf_counter()
                result = decoder.decode(observation.syndrome, observation.herald)
                decode_ms = 1000 * (perf_counter() - start)
                cache[key] = result
            records.append(
                record_from_result(
                    graph,
                    observation,
                    result,
                    decode_ms=decode_ms,
                    cache_hit=cache_hit,
                )
            )
    return {
        "lattice": task["lattice"],
        "L": 5,
        "p": task["p"],
        "shots": len(records),
        "legacy_damped": summarise_arm(records),
        "cell_wall_seconds": perf_counter() - start_cell,
    }


def run_tasks(tasks: list[dict], function, workers: int) -> tuple[list[dict], float]:
    started = perf_counter()
    rows = []
    if workers == 1:
        # Some constrained hosts prohibit process semaphores.  Keep the
        # registered samples and deterministic cell order intact by falling
        # back to serial execution rather than failing or changing the study.
        for task in tasks:
            row = function(task)
            rows.append(row)
            print(
                f"finished {row['lattice']} p={row['p']:.3f} shots={row['shots']}",
                flush=True,
            )
        return rows, perf_counter() - started
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(function, task): task for task in tasks}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(
                f"finished {row['lattice']} p={row['p']:.3f} shots={row['shots']}",
                flush=True,
            )
    rows.sort(key=lambda row: ((0 if row["lattice"] == "square" else 1), row["p"]))
    return rows, perf_counter() - started


def aggregate_logical_cases(cases: list[dict]) -> dict:
    shots = sum(case["shots"] for case in cases)
    arms = {}
    for arm in ARM_NAMES:
        errors = sum(case["pooled"]["arms"][arm]["logical_errors"] for case in cases)
        arms[arm] = {
            "shots": shots,
            "logical_errors": errors,
            "logical_error_rate": errors / shots,
            "logical_error_ci95": wilson_interval(errors, shots),
        }
    rescued = sum(case["pooled"]["paired"]["rescued_failures"] for case in cases)
    harmed = sum(case["pooled"]["paired"]["introduced_failures"] for case in cases)
    return {
        "cells": len(cases),
        "arms": arms,
        "paired": {
            "rescued_failures": rescued,
            "introduced_failures": harmed,
            "discordant_shots": rescued + harmed,
            "logical_error_rate_delta": (harmed - rescued) / shots,
            "mcnemar_exact_p_value": mcnemar_exact(rescued, harmed),
        },
        "scope_note": "Descriptive pooling across distinct physical-error rates; cell-level estimates are primary.",
    }


def common_payload(args, *, mode: str, rows: list[dict], wall_seconds: float) -> dict:
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "L": 5,
        "q": args.q,
        "p_m": args.p_m,
        "p_h": args.p_h,
        "seeds": args.seeds,
        "shots_per_seed": args.shots_per_seed,
        "workers": args.workers,
        "parallel_wall_seconds": wall_seconds,
        "matching_projection": "posterior_llr",
        "observation_cache": "exact (syndrome bytes, herald bytes), per lattice-p cell",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pymatching": pymatching.__version__,
        },
        "rows" if mode == "pilot" else "cases": rows,
    }
    if mode == "final":
        payload["pooled_by_lattice"] = {
            lattice: aggregate_logical_cases(
                [case for case in rows if case["lattice"] == lattice]
            )
            for lattice in ("square", "honeycomb")
        }
        payload["pooled_all_cells"] = aggregate_logical_cases(rows)
    return payload


def markdown_final(payload: dict) -> str:
    lines = [
        "# Systematic matched BP-update A/B",
        "",
        f"Five seeds × {payload['shots_per_seed']} shots give 1000 matched observations per cell. Parallel workers: {payload['workers']}.",
        "",
        "| Lattice | p | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Selected converged | Mean iterations | Cache hit | Uncached ms |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in payload["cases"]:
        for arm in ARM_NAMES:
            metrics = case["pooled"]["arms"][arm]
            low, high = metrics["logical_error_ci95"]
            lines.append(
                f"| {case['lattice']} | {case['p']:.3f} | {arm} | "
                f"{metrics['logical_errors']}/{metrics['shots']} | "
                f"{metrics['logical_error_rate']:.4f} [{low:.4f}, {high:.4f}] | "
                f"{metrics['mean_edge_log_loss']:.4f} | {metrics['mean_edge_brier']:.4f} | "
                f"{metrics['selected_candidate_convergence_rate']:.1%} | "
                f"{metrics['mean_bp_iterations']:.2f} | {metrics['cache_hit_rate']:.1%} | "
                f"{metrics['mean_uncached_decode_ms']:.2f} |"
            )
        pair = case["pooled"]["paired"]
        lines.append(
            f"- {case['lattice']} p={case['p']:.3f}: new rescued {pair['rescued_failures']}, "
            f"introduced {pair['introduced_failures']}, LER delta "
            f"{pair['logical_error_rate_delta']:+.4f}, exact McNemar "
            f"p={pair['mcnemar_exact_p_value']:.4g}; log-loss delta "
            f"{pair['mean_edge_log_loss_delta']:+.5f} "
            f"CI={pair['edge_log_loss_delta_bootstrap_ci95']}."
        )
    lines.extend(["", "## Descriptive pooled logical results", ""])
    for scope, aggregate in (
        ("square", payload["pooled_by_lattice"]["square"]),
        ("honeycomb", payload["pooled_by_lattice"]["honeycomb"]),
        ("all cells", payload["pooled_all_cells"]),
    ):
        old = aggregate["arms"]["legacy_damped"]
        new = aggregate["arms"]["memory_assisted"]
        pair = aggregate["paired"]
        lines.append(
            f"- {scope}: legacy {old['logical_errors']}/{old['shots']} "
            f"({old['logical_error_rate']:.4f}), memory {new['logical_errors']}/{new['shots']} "
            f"({new['logical_error_rate']:.4f}); rescued {pair['rescued_failures']}, "
            f"introduced {pair['introduced_failures']}, delta "
            f"{pair['logical_error_rate_delta']:+.4f}, McNemar "
            f"p={pair['mcnemar_exact_p_value']:.4g}."
        )
    lines.extend(
        [
            "",
            "This is systematic finite-size evidence at L=5, not threshold estimation. Grid selection used a legacy-only pilot and did not inspect the A/B effect.",
            "",
        ]
    )
    return "\n".join(lines)


def plot_final(payload: dict, output: Path) -> None:
    """Plot the registered multi-point LLR comparison without pooling lattices."""
    figure, axes = plt.subplots(2, 2, figsize=(11.5, 7.6), constrained_layout=True)
    colors = {"legacy_damped": "#0072B2", "memory_assisted": "#D55E00"}
    labels = {"legacy_damped": "Damping", "memory_assisted": "Relay-memory"}
    for column, lattice in enumerate(("square", "honeycomb")):
        cases = [case for case in payload["cases"] if case["lattice"] == lattice]
        cases.sort(key=lambda case: case["p"])
        p = np.asarray([case["p"] for case in cases])
        ler_axis = axes[0, column]
        support_axis = axes[1, column]
        for arm in ARM_NAMES:
            rates = np.asarray([case["pooled"]["arms"][arm]["logical_error_rate"] for case in cases])
            ci = np.asarray([case["pooled"]["arms"][arm]["logical_error_ci95"] for case in cases])
            ler_axis.errorbar(
                p,
                rates,
                yerr=[rates - ci[:, 0], ci[:, 1] - rates],
                marker="o",
                linewidth=1.8,
                capsize=3,
                color=colors[arm],
                label=labels[arm],
            )
            convergence = np.asarray(
                [case["pooled"]["arms"][arm]["selected_candidate_convergence_rate"] for case in cases]
            )
            runtime = np.asarray(
                [case["pooled"]["arms"][arm]["amortized_decode_compute_ms"] for case in cases]
            )
            support_axis.plot(p, convergence, marker="o", linewidth=1.8, color=colors[arm], label=labels[arm])
            support_axis.text(
                p[-1] + 0.002,
                convergence[-1],
                f"{labels[arm]} {runtime[-1]:.1f} ms",
                color=colors[arm],
                fontsize=8,
                va="center",
            )
        pair_lines = [
            f"p={case['p']:.2f}: ΔLER={case['pooled']['paired']['logical_error_rate_delta']:+.3f}, "
            f"p={case['pooled']['paired']['mcnemar_exact_p_value']:.3g}"
            for case in cases
        ]
        ler_axis.set(
            title=f"{lattice.title()} corrected-LLR LER",
            xlabel="physical error rate p",
            ylabel="logical error rate",
        )
        ler_axis.grid(alpha=0.25)
        ler_axis.legend(loc="upper left")
        ler_axis.text(
            0.98,
            0.04,
            "\n".join(pair_lines),
            transform=ler_axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#9ca3af"},
        )
        support_axis.set(
            title=f"{lattice.title()} BP convergence",
            xlabel="physical error rate p",
            ylabel="selected-candidate convergence fraction",
            ylim=(-0.03, 1.03),
        )
        support_axis.grid(alpha=0.25)
        support_axis.legend(loc="upper right")
    figure.suptitle(
        "Lab 002 systematic matched rerun — posterior-LLR MWPM, 1,000 shots/cell",
        fontsize=12,
    )
    figure.savefig(output, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pilot", "final"))
    parser.add_argument("--square-p", type=float, nargs="+", required=True)
    parser.add_argument("--honeycomb-p", type=float, nargs="+", required=True)
    parser.add_argument("--shots-per-seed", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--q", type=float, default=0.75)
    parser.add_argument("--p-m", type=float, default=0.0)
    parser.add_argument("--p-h", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--refresh-plot",
        action="store_true",
        help="render the final-mode plot from an existing result without rerunning simulations",
    )
    args = parser.parse_args()
    if args.shots_per_seed < 1 or args.workers < 1:
        parser.error("shots and workers must be positive")
    if args.refresh_plot:
        if args.mode != "final":
            parser.error("--refresh-plot is supported only for final results")
        payload = json.loads(args.output.read_text())
        plot_final(payload, args.output.with_suffix(".png"))
        print(f"wrote {args.output.with_suffix('.png')}", flush=True)
        return
    tasks = []
    for lattice, grid in (("square", args.square_p), ("honeycomb", args.honeycomb_p)):
        for index, p in enumerate(grid):
            tasks.append(
                {
                    "lattice": lattice,
                    "p": p,
                    "q": args.q,
                    "p_m": args.p_m,
                    "p_h": args.p_h,
                    "seeds": args.seeds,
                    "shots_per_seed": args.shots_per_seed,
                    "bootstrap_seed": 730_000 + index + (10_000 if lattice == "honeycomb" else 0),
                }
            )
    function = run_pilot_cell if args.mode == "pilot" else run_final_cell
    rows, wall_seconds = run_tasks(tasks, function, args.workers)
    payload = common_payload(args, mode=args.mode, rows=rows, wall_seconds=wall_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    if args.mode == "final":
        args.output.with_suffix(".md").write_text(markdown_final(payload))
        plot_final(payload, args.output.with_suffix(".png"))
    print(f"wrote {args.output} in {wall_seconds:.1f}s", flush=True)


if __name__ == "__main__":
    main()
