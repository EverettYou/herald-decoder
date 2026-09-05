#!/usr/bin/env python3
"""Matched legacy-damping versus memory-assisted BP benchmark for Lab 002."""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter
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


def bootstrap_mean_ci(values: list[float], rng: np.random.Generator) -> list[float]:
    values_array = np.asarray(values, dtype=float)
    sample_indices = rng.integers(0, len(values_array), size=(5000, len(values_array)))
    means = np.mean(values_array[sample_indices], axis=1)
    return [float(value) for value in np.quantile(means, [0.025, 0.975])]


def summarise_arm(records: list[dict]) -> dict:
    shots = len(records)
    failures = sum(record["failed"] for record in records)
    runtimes = np.asarray([record["decode_ms"] for record in records])
    return {
        "shots": shots,
        "logical_errors": failures,
        "logical_error_rate": failures / shots,
        "logical_error_ci95": wilson_interval(failures, shots),
        "mean_edge_log_loss": float(np.mean([record["log_loss"] for record in records])),
        "mean_edge_brier": float(np.mean([record["brier"] for record in records])),
        "bp_convergence_rate": float(np.mean([record["converged"] for record in records])),
        "mean_bp_iterations": float(np.mean([record["iterations"] for record in records])),
        "mean_max_message_delta": float(np.mean([record["max_message_delta"] for record in records])),
        "mean_decode_ms": float(np.mean(runtimes)),
        "median_decode_ms": float(np.median(runtimes)),
    }


def summarise_pair(records: dict[str, list[dict]], *, bootstrap_seed: int) -> dict:
    old = records["legacy_damped"]
    new = records["memory_assisted"]
    rescued = sum(a["failed"] and not b["failed"] for a, b in zip(old, new, strict=True))
    harmed = sum(b["failed"] and not a["failed"] for a, b in zip(old, new, strict=True))
    log_delta = [b["log_loss"] - a["log_loss"] for a, b in zip(old, new, strict=True)]
    brier_delta = [b["brier"] - a["brier"] for a, b in zip(old, new, strict=True)]
    rng = np.random.default_rng(bootstrap_seed)
    return {
        "reference": "legacy_damped",
        "candidate": "memory_assisted",
        "rescued_failures": rescued,
        "introduced_failures": harmed,
        "discordant_shots": rescued + harmed,
        "logical_error_rate_delta": (harmed - rescued) / len(old),
        "mcnemar_exact_p_value": mcnemar_exact(rescued, harmed),
        "mean_edge_log_loss_delta": float(np.mean(log_delta)),
        "edge_log_loss_delta_bootstrap_ci95": bootstrap_mean_ci(log_delta, rng),
        "mean_edge_brier_delta": float(np.mean(brier_delta)),
        "edge_brier_delta_bootstrap_ci95": bootstrap_mean_ci(brier_delta, rng),
        "mean_runtime_ratio": float(
            np.mean([record["decode_ms"] for record in new])
            / np.mean([record["decode_ms"] for record in old])
        ),
    }


def run_seed(
    graph,
    *,
    p: float,
    q: float,
    p_m: float,
    p_h: float,
    shots: int,
    seed: int,
) -> tuple[dict[str, list[dict]], Counter]:
    rng = np.random.default_rng(seed)
    old_decoder = LegacyDampedBpMatchingDecoder(
        graph,
        p=p,
        q=q,
        p_m=p_m,
        p_h=p_h,
        max_iterations=40,
        damping=0.25,
        tolerance=1e-8,
    )
    new_decoder = HeraldBeliefMatchingDecoder(
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
    )
    records: dict[str, list[dict]] = {name: [] for name in ARM_NAMES}
    selected_candidates: Counter = Counter()
    for _ in range(shots):
        observation = sample_observation(graph, rng, p=p, q=q, p_m=p_m, p_h=p_h)
        for arm, decoder in (
            ("legacy_damped", old_decoder),
            ("memory_assisted", new_decoder),
        ):
            start = perf_counter()
            result = decoder.decode(observation.syndrome, observation.herald)
            elapsed_ms = 1000 * (perf_counter() - start)
            if np.any(graph.true_syndrome(result.correction) != observation.syndrome):
                raise RuntimeError(f"{arm} correction is not syndrome faithful")
            failed = bool(graph.logical_parity(observation.error ^ result.correction))
            log_loss, brier = proper_scores(result.bp.edge_marginals, observation.error)
            records[arm].append(
                {
                    "failed": failed,
                    "log_loss": log_loss,
                    "brier": brier,
                    "converged": bool(result.bp.converged),
                    "iterations": int(result.bp.iterations),
                    "max_message_delta": float(result.bp.max_message_delta),
                    "decode_ms": elapsed_ms,
                }
            )
            if arm == "memory_assisted":
                selected_candidates[int(result.bp.selected_leg)] += 1
    return records, selected_candidates


def markdown_report(payload: dict) -> str:
    lines = [
        "# Matched BP-update A/B",
        "",
        (
            f"Generated `{payload['generated_at']}` with {payload['shots_per_seed']} matched shots per seed "
            f"and seeds `{payload['seeds']}`. Both arms use posterior-LLR weights and the same PyMatching backend."
        ),
        "",
        "| Lattice | Scope | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Converged | Iterations | Mean ms |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in payload["cases"]:
        scopes = [("pooled", case["pooled"])] + [
            (f"seed {row['seed']}", row) for row in case["per_seed"]
        ]
        for scope, summary in scopes:
            for arm in ARM_NAMES:
                metrics = summary["arms"][arm]
                low, high = metrics["logical_error_ci95"]
                lines.append(
                    f"| {case['lattice']} | {scope} | {arm} | {metrics['logical_errors']}/{metrics['shots']} | "
                    f"{metrics['logical_error_rate']:.4f} [{low:.4f}, {high:.4f}] | "
                    f"{metrics['mean_edge_log_loss']:.4f} | {metrics['mean_edge_brier']:.4f} | "
                    f"{metrics['bp_convergence_rate']:.1%} | {metrics['mean_bp_iterations']:.2f} | "
                    f"{metrics['mean_decode_ms']:.2f} |"
                )
        pair = case["pooled"]["paired"]
        lines.extend(
            [
                "",
                (
                    f"- **{case['lattice']} pooled:** memory-assisted rescued {pair['rescued_failures']} "
                    f"legacy failures and introduced {pair['introduced_failures']}; LER delta "
                    f"{pair['logical_error_rate_delta']:+.4f}; exact McNemar "
                    f"p={pair['mcnemar_exact_p_value']:.4g}."
                ),
                (
                    f"  Paired soft deltas (new minus old): log loss {pair['mean_edge_log_loss_delta']:+.5f} "
                    f"(bootstrap 95% CI {pair['edge_log_loss_delta_bootstrap_ci95']}), Brier "
                    f"{pair['mean_edge_brier_delta']:+.5f} "
                    f"(bootstrap 95% CI {pair['edge_brier_delta_bootstrap_ci95']})."
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Evidence boundary",
            "",
            "This is a finite-size, two-cell implementation A/B, not a threshold estimate. The selected memory-search candidate is ranked only from the observed factor model; simulator truth is used only after decoding for evaluation. Runtime includes BP, per-shot matching-graph construction, and PyMatching decode.",
            "",
        ]
    )
    return "\n".join(lines)


def plot_summary(payload: dict, output: Path) -> None:
    """Render the matched corrected-LLR comparison next to its support metrics."""
    figure, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), constrained_layout=True)
    colors = {"legacy_damped": "#0072B2", "memory_assisted": "#D55E00"}
    labels = {"legacy_damped": "Damping", "memory_assisted": "Relay-memory"}
    for column, case in enumerate(payload["cases"]):
        arms = case["pooled"]["arms"]
        pair = case["pooled"]["paired"]
        names = list(ARM_NAMES)
        x = np.arange(len(names))

        ler_axis = axes[0, column]
        rates = [arms[name]["logical_error_rate"] for name in names]
        errors = [
            [
                arms[name]["logical_error_rate"] - arms[name]["logical_error_ci95"][0]
                for name in names
            ],
            [
                arms[name]["logical_error_ci95"][1] - arms[name]["logical_error_rate"]
                for name in names
            ],
        ]
        ler_axis.bar(x, rates, color=[colors[name] for name in names], width=0.62)
        ler_axis.errorbar(x, rates, yerr=errors, fmt="none", color="#1f2937", capsize=4)
        for index, name in enumerate(names):
            arm = arms[name]
            ler_axis.text(
                index,
                rates[index] + max(errors[1][index], 0.005) + 0.006,
                f"{arm['logical_errors']}/{arm['shots']}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        ler_axis.set(
            title=f"{case['lattice'].title()} LER — corrected posterior LLR",
            ylabel="logical error rate",
            xticks=x,
            xticklabels=[labels[name] for name in names],
            ylim=(0, max(max(rates) + max(errors[1]) + 0.08, 0.18)),
        )
        ler_axis.grid(axis="y", alpha=0.25)
        ler_axis.text(
            0.5,
            0.96,
            f"Matched: rescued {pair['rescued_failures']}, introduced {pair['introduced_failures']}\n"
            f"ΔLER={pair['logical_error_rate_delta']:+.3f}; McNemar p={pair['mcnemar_exact_p_value']:.3g}",
            transform=ler_axis.transAxes,
            ha="center",
            va="top",
            fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#9ca3af"},
        )

        support_axis = axes[1, column]
        convergence = [arms[name]["bp_convergence_rate"] for name in names]
        runtime_ratio = [1.0, pair["mean_runtime_ratio"]]
        width = 0.34
        support_axis.bar(x - width / 2, convergence, width, color="#009E73", label="BP convergence")
        support_axis.set(
            title=f"{case['lattice'].title()} reliability and cost",
            ylabel="converged shots fraction",
            xticks=x,
            xticklabels=[labels[name] for name in names],
            ylim=(0, 1.05),
        )
        support_axis.grid(axis="y", alpha=0.25)
        runtime_axis = support_axis.twinx()
        runtime_axis.bar(x + width / 2, runtime_ratio, width, color="#CC79A7", label="runtime / damping")
        runtime_axis.set_ylabel("mean runtime ratio")
        runtime_axis.set_yscale("log")
        runtime_axis.set_ylim(0.5, max(2.0, max(runtime_ratio) * 2))
        handles, labels_left = support_axis.get_legend_handles_labels()
        right_handles, labels_right = runtime_axis.get_legend_handles_labels()
        support_axis.legend(handles + right_handles, labels_left + labels_right, loc="upper left", fontsize=8)

    figure.suptitle(
        "Lab 002 matched damping vs Relay-memory rerun — 300 shots/lattice, posterior-LLR MWPM",
        fontsize=12,
    )
    figure.savefig(output, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots-per-seed", type=int, default=200)
    parser.add_argument("--seeds", type=int, nargs="+", default=[281001, 281002, 281003])
    parser.add_argument("--p", type=float, default=0.10)
    parser.add_argument("--q", type=float, default=0.75)
    parser.add_argument("--p-m", type=float, default=0.0)
    parser.add_argument("--p-h", type=float, default=0.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parents[1] / "results" / "memory-vs-damping-ab.json",
    )
    parser.add_argument(
        "--refresh-plot",
        action="store_true",
        help="render the summary figure from an existing JSON result without rerunning simulations",
    )
    args = parser.parse_args()
    if args.shots_per_seed < 1 or not args.seeds:
        parser.error("shots and seeds must be non-empty and positive")
    if args.refresh_plot:
        payload = json.loads(args.output.read_text())
        plot_summary(payload, args.output.with_suffix(".png"))
        print(f"wrote {args.output.with_suffix('.png')}", flush=True)
        return

    cases = []
    for case_index, (lattice, builder) in enumerate(
        (("square", square_graph), ("honeycomb", honeycomb_graph))
    ):
        graph = builder(5)
        pooled_records: dict[str, list[dict]] = {name: [] for name in ARM_NAMES}
        pooled_candidates: Counter = Counter()
        per_seed = []
        for seed_index, seed in enumerate(args.seeds):
            records, selected = run_seed(
                graph,
                p=args.p,
                q=args.q,
                p_m=args.p_m,
                p_h=args.p_h,
                shots=args.shots_per_seed,
                seed=seed,
            )
            for arm in ARM_NAMES:
                pooled_records[arm].extend(records[arm])
            pooled_candidates.update(selected)
            summary = {
                "seed": seed,
                "arms": {arm: summarise_arm(records[arm]) for arm in ARM_NAMES},
                "paired": summarise_pair(
                    records,
                    bootstrap_seed=900_000 + case_index * 100 + seed_index,
                ),
                "memory_selected_candidate_counts_zero_based": {
                    str(key): value for key, value in sorted(selected.items())
                },
            }
            per_seed.append(summary)
            pair = summary["paired"]
            print(
                f"finished {lattice} seed={seed}: rescued={pair['rescued_failures']} "
                f"harmed={pair['introduced_failures']}",
                flush=True,
            )
        pooled = {
            "arms": {arm: summarise_arm(pooled_records[arm]) for arm in ARM_NAMES},
            "paired": summarise_pair(
                pooled_records,
                bootstrap_seed=990_000 + case_index,
            ),
            "memory_selected_candidate_counts_zero_based": {
                str(key): value for key, value in sorted(pooled_candidates.items())
            },
        }
        cases.append(
            {
                "lattice": lattice,
                "L": 5,
                "edges": len(graph.edges),
                "detectors": len(graph.detector_vertices),
                "p": args.p,
                "q": args.q,
                "p_m": args.p_m,
                "p_h": args.p_h,
                "per_seed": per_seed,
                "pooled": pooled,
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "comparison": "legacy_probability_damping_vs_memory_assisted_bp",
        "paired_design": True,
        "shots_per_seed": args.shots_per_seed,
        "seeds": args.seeds,
        "matching_projection": "posterior_llr",
        "common_downstream": {
            "backend": "pymatching.Matching.from_check_matrix",
            "use_virtual_boundary_node": True,
        },
        "arms": {
            "legacy_damped": {
                "implementation": "scripts/legacy_damped_bp_decoder.py",
                "frozen_regression_test": "test_frozen_legacy_damping_ablation_matches_archived_result",
                "max_iterations": 40,
                "damping": 0.25,
                "tolerance": 1e-8,
            },
            "memory_assisted": {
                "max_iterations": 40,
                "tolerance": 1e-8,
                "initial_memory": 0.15,
                "additional_candidates": 6,
                "candidate_iterations": 20,
                "memory_interval": [-0.24, 0.66],
                "memory_seed": 0,
                "selection": "Bethe score minus local pseudomarginal inconsistency",
            },
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pymatching": pymatching.__version__,
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(markdown_report(payload))
    plot_summary(payload, args.output.with_suffix(".png"))
    print(f"wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
