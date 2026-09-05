#!/usr/bin/env python3
"""Analyze the q=1 square L=5..13 dense first-crossing refinement."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
STEM = "q1-square-l5-l13-crossing-refined-10000-2026-08-27"
SIZES = (5, 7, 9, 11, 13)
PAIRS = tuple(zip(SIZES, SIZES[1:]))
BOOTSTRAP_REPLICATES = 20_000


def directed_crossings(p_values: np.ndarray, delta: np.ndarray) -> list[float]:
    estimates: list[float] = []
    for index, (left, right) in enumerate(zip(delta, delta[1:])):
        if left > 0 and right < 0:
            fraction = left / (left - right)
            estimates.append(float(p_values[index] + fraction * (p_values[index + 1] - p_values[index])))
        elif left == 0 and right < 0:
            estimates.append(float(p_values[index]))
    return estimates


def reverse_crossings(p_values: np.ndarray, delta: np.ndarray) -> list[float]:
    return directed_crossings(p_values, -delta)


def resolved_bracket(p_values: np.ndarray, low: np.ndarray, high: np.ndarray) -> dict | None:
    """Bracket the first statistically resolved +delta to -delta transition."""
    positive = [index for index, value in enumerate(low) if value > 0]
    negative = [index for index, value in enumerate(high) if value < 0]
    later_negative = [right for right in negative if any(left < right for left in positive)]
    if not later_negative:
        return None
    right = min(later_negative)
    left = max(left for left in positive if left < right)
    return {
        "last_resolved_positive_p": float(p_values[left]),
        "first_later_resolved_negative_p": float(p_values[right]),
        "unresolved_grid_points_between": right - left - 1,
    }


def analyze(payload: dict) -> tuple[dict, dict[int, np.ndarray], dict[str, dict[str, np.ndarray]]]:
    p_values = np.asarray(payload["p_grid"], dtype=float)
    seeds = [int(seed) for seed in payload["seeds"]]
    summaries = payload["summaries"]
    observed_rates = {
        size: np.asarray([
            next(row["logical_error_rate"] for row in summaries if row["L"] == size and row["p"] == p)
            for p in p_values
        ])
        for size in SIZES
    }

    per_seed = {
        (int(row["L"]), int(row["seed"]), float(row["p"])): int(row["logical_errors"]) / int(row["shots"])
        for row in payload["per_seed"]
    }
    expected = {(size, seed, float(p)) for size in SIZES for seed in seeds for p in p_values}
    if set(per_seed) != expected:
        raise SystemExit("per-seed cells are incomplete or duplicated")
    seed_rates = {
        size: np.asarray([[per_seed[(size, seed, float(p))] for p in p_values] for seed in seeds])
        for size in SIZES
    }

    rng = np.random.default_rng(720001)
    bootstrap_rates = {}
    for size in SIZES:
        indices = rng.integers(0, len(seeds), size=(BOOTSTRAP_REPLICATES, len(seeds)))
        bootstrap_rates[size] = seed_rates[size][indices].mean(axis=1)

    pair_analysis = {}
    delta_plot = {}
    for lower_size, upper_size in PAIRS:
        key = f"L{lower_size}_L{upper_size}"
        observed_delta = observed_rates[lower_size] - observed_rates[upper_size]
        boot_delta = bootstrap_rates[lower_size] - bootstrap_rates[upper_size]
        low, median, high = np.quantile(boot_delta, [0.025, 0.5, 0.975], axis=0)
        first_crossings = []
        no_crossing = multiple_crossings = stable_topology = 0
        for replicate in boot_delta:
            directed = directed_crossings(p_values, replicate)
            reverse = reverse_crossings(p_values, replicate)
            if directed:
                first_crossings.append(directed[0])
                if len(directed) > 1:
                    multiple_crossings += 1
                if len(directed) == 1 and not reverse:
                    stable_topology += 1
            else:
                no_crossing += 1
        quantiles = np.quantile(first_crossings, [0.025, 0.5, 0.975]).tolist() if first_crossings else [None, None, None]
        point_directed = directed_crossings(p_values, observed_delta)
        point_reverse = reverse_crossings(p_values, observed_delta)
        pair_analysis[key] = {
            "sizes": [lower_size, upper_size],
            "delta_definition": f"LER_L{lower_size} - LER_L{upper_size}",
            "point_directed_crossings": point_directed,
            "point_reverse_crossings": point_reverse,
            "point_topology_stable": len(point_directed) == 1 and not point_reverse,
            "resolved_95pct_delta_bracket": resolved_bracket(p_values, low, high),
            "bootstrap": {
                "method": "size-stratified seed-cluster bootstrap preserving nested p trajectories",
                "seed": 720001,
                "replicates": BOOTSTRAP_REPLICATES,
                "any_directed_crossing_fraction": len(first_crossings) / BOOTSTRAP_REPLICATES,
                "no_directed_crossing_fraction": no_crossing / BOOTSTRAP_REPLICATES,
                "multiple_directed_crossing_fraction": multiple_crossings / BOOTSTRAP_REPLICATES,
                "stable_single_crossing_no_reverse_fraction": stable_topology / BOOTSTRAP_REPLICATES,
                "first_crossing_conditional_quantiles": {"q025": quantiles[0], "median": quantiles[1], "q975": quantiles[2]},
            },
            "delta_by_p": [
                {"p": float(p), "estimate": float(value), "bootstrap_median": float(mid), "ci95": [float(lo), float(hi)]}
                for p, value, mid, lo, hi in zip(p_values, observed_delta, median, low, high)
            ],
        }
        delta_plot[key] = {"estimate": observed_delta, "low": low, "high": high}

    analysis = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": f"results/{STEM}.json",
        "design": {
            "lattice": "square", "q": 1.0, "sizes": list(SIZES),
            "p_grid": payload["p_grid"], "seeds": payload["seeds"],
            "shots_per_seed": payload["shots_per_seed"], "shots_per_cell": payload["total_shots_per_cell"],
            "total_decoder_observations": len(SIZES) * len(p_values) * payload["total_shots_per_cell"],
        },
        "adjacent_size_delta_analysis": pair_analysis,
        "convergence": {
            f"L{size}": {
                "minimum_rate": min(row["bp_convergence_rate"] for row in summaries if row["L"] == size),
                "maximum_rate": max(row["bp_convergence_rate"] for row in summaries if row["L"] == size),
            }
            for size in SIZES
        },
        "evidence_boundary": "Dense finite-size first-crossing diagnostic for the fixed 40-iteration q=1 decoder; delta bands quantify visibility but do not cure BP non-convergence or establish an asymptotic threshold.",
    }
    return analysis, observed_rates, delta_plot


def plot(payload: dict, analysis: dict, observed_rates: dict[int, np.ndarray], delta_plot: dict, destination: Path) -> None:
    p_values = np.asarray(payload["p_grid"], dtype=float)
    colors = {5: "#56B4E9", 7: "#009E73", 9: "#E69F00", 11: "#CC79A7", 13: "#D55E00"}
    pair_colors = {"L5_L7": "#0072B2", "L7_L9": "#009E73", "L9_L11": "#E69F00", "L11_L13": "#D55E00"}
    figure, (ler_axis, delta_axis, convergence_axis) = plt.subplots(
        3, 1, figsize=(9.2, 9.2), gridspec_kw={"height_ratios": [3.0, 2.1, 1.0]}, sharex=True, constrained_layout=True
    )

    for size in SIZES:
        rows = sorted((row for row in payload["summaries"] if row["L"] == size), key=lambda row: row["p"])
        low = [row["logical_error_rate"] - row["logical_error_ci95"][0] for row in rows]
        high = [row["logical_error_ci95"][1] - row["logical_error_rate"] for row in rows]
        ler_axis.errorbar(p_values, observed_rates[size], yerr=[low, high], marker="o", markersize=3.1, linewidth=1.4, capsize=1.6, color=colors[size], label=f"L={size}")
        convergence_axis.plot(p_values, [row["bp_convergence_rate"] for row in rows], marker="o", markersize=2.5, linewidth=1.15, color=colors[size], label=f"L={size}")
    ler_axis.set_title(f"Square q=1 refined first-crossing scan, L=5–13 — {payload['total_shots_per_cell']} shots/cell")
    ler_axis.set_ylabel("logical error rate (LER)")
    ler_axis.grid(alpha=0.22)
    ler_axis.legend(title="code size", ncol=3)

    for key, values in delta_plot.items():
        label = key.replace("_", "/")
        color = pair_colors[key]
        delta_axis.fill_between(p_values, values["low"], values["high"], color=color, alpha=0.13)
        delta_axis.plot(p_values, values["estimate"], marker="o", markersize=3.0, linewidth=1.45, color=color, label=label)
    delta_axis.axhline(0, color="#444444", linewidth=1.0)
    delta_axis.set_ylabel("adjacent-size ΔLER")
    delta_axis.grid(alpha=0.22)
    delta_axis.legend(title="Δ = smaller − larger", ncol=2)

    convergence_axis.set(xlabel="physical edge-error rate p", ylabel="BP converged", ylim=(-0.005, 0.78))
    convergence_axis.grid(alpha=0.22)
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def plot_pairwise(payload: dict, analysis: dict, delta_plot: dict, destination: Path) -> None:
    p_values = np.asarray(payload["p_grid"], dtype=float)
    pair_colors = {"L5_L7": "#0072B2", "L7_L9": "#009E73", "L9_L11": "#E69F00", "L11_L13": "#D55E00"}
    figure, axes = plt.subplots(2, 2, figsize=(9.2, 7.3), sharex=True, sharey=True, constrained_layout=True)
    for axis, (key, values) in zip(axes.flat, delta_plot.items()):
        item = analysis["adjacent_size_delta_analysis"][key]
        color = pair_colors[key]
        axis.fill_between(p_values, values["low"], values["high"], color=color, alpha=0.18, label="seed-bootstrap 95% band")
        axis.plot(p_values, values["estimate"], marker="o", markersize=3.2, linewidth=1.55, color=color, label="observed ΔLER")
        axis.axhline(0, color="#444444", linewidth=1.0)
        for crossing in item["point_directed_crossings"]:
            axis.axvline(crossing, color=color, linestyle="--", linewidth=1.0, alpha=0.85)
        bracket = item["resolved_95pct_delta_bracket"]
        if bracket is not None:
            axis.axvspan(bracket["last_resolved_positive_p"], bracket["first_later_resolved_negative_p"], color="#777777", alpha=0.08)
        crossings = item["point_directed_crossings"]
        crossing_text = ", ".join(f"{value:.4f}" for value in crossings) if crossings else "none"
        stable = item["bootstrap"]["stable_single_crossing_no_reverse_fraction"]
        axis.set_title(f"{key.replace('_', '/')}  directed: {crossing_text}\nstable topology: {stable:.1%}", fontsize=10)
        axis.grid(alpha=0.22)
    axes[0, 0].set_ylabel("ΔLER (smaller − larger)")
    axes[1, 0].set_ylabel("ΔLER (smaller − larger)")
    axes[1, 0].set_xlabel("physical edge-error rate p")
    axes[1, 1].set_xlabel("physical edge-error rate p")
    axes[0, 0].legend(loc="upper right", fontsize=8)
    figure.suptitle(f"Square q=1 adjacent-size crossing diagnostics — {payload['total_shots_per_cell']} shots/cell", fontsize=15)
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    source = LAB_DIR / "results" / f"{STEM}.json"
    payload = json.loads(source.read_text())
    if payload["sizes"] != list(SIZES) or payload["total_shots_per_cell"] != 10_000:
        raise SystemExit("unexpected source design")
    analysis, observed_rates, delta_plot = analyze(payload)
    destination = LAB_DIR / "results" / f"{STEM}-analysis.json"
    destination.write_text(json.dumps(analysis, indent=2) + "\n")
    figure = LAB_DIR / "figures" / f"{STEM}-ler-delta-vs-p.png"
    plot(payload, analysis, observed_rates, delta_plot, figure)
    pairwise_figure = LAB_DIR / "figures" / f"{STEM}-pairwise-delta.png"
    plot_pairwise(payload, analysis, delta_plot, pairwise_figure)
    print(json.dumps({
        "analysis": str(destination), "figure": str(figure), "pairwise_figure": str(pairwise_figure),
        "pairs": {
            key: {
                "point_directed_crossings": value["point_directed_crossings"],
                "resolved_95pct_delta_bracket": value["resolved_95pct_delta_bracket"],
                "bootstrap": value["bootstrap"],
            }
            for key, value in analysis["adjacent_size_delta_analysis"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
