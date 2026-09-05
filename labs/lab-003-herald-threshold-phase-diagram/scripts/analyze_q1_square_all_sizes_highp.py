#!/usr/bin/env python3
"""Merge and analyze the q=1 square L=3..13 high-p refinements."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
SOURCE_STEMS = (
    "q1-square-l3-l9-highp-refined-5000-2026-08-27",
    "q1-square-l11-l13-highp-refined-5000-2026-08-27",
)
OUTPUT_STEM = "q1-square-l3-l13-highp-refined-5000-2026-08-27"
SIZES = (3, 5, 7, 9, 11, 13)
PAIRS = tuple(zip(SIZES, SIZES[1:]))
BOOTSTRAP_REPLICATES = 20_000


def directed_crossings(p_values: list[float], lower: np.ndarray, upper: np.ndarray) -> list[float]:
    """Return physically directed positive-to-negative LER-difference crossings."""
    delta = lower - upper
    estimates: list[float] = []
    for index, (left, right) in enumerate(zip(delta, delta[1:])):
        if left > 0 and right < 0:
            fraction = left / (left - right)
            estimates.append(p_values[index] + fraction * (p_values[index + 1] - p_values[index]))
        elif left == 0 and right < 0:
            estimates.append(p_values[index])
    return estimates


def load_sources() -> tuple[list[dict], list[dict], dict]:
    payloads = [json.loads((LAB_DIR / "results" / f"{stem}.json").read_text()) for stem in SOURCE_STEMS]
    reference = payloads[0]
    for payload in payloads:
        if payload["lattice"] != "square" or payload["q"] != 1.0:
            raise SystemExit("source is not the registered q=1 square scan")
        for field in ("p_grid", "seeds", "shots_per_seed", "total_shots_per_cell"):
            if payload[field] != reference[field]:
                raise SystemExit(f"source design mismatch: {field}")
    sizes = sorted(size for payload in payloads for size in payload["sizes"])
    if sizes != list(SIZES):
        raise SystemExit(f"unexpected merged sizes: {sizes}")
    summaries = [row for payload in payloads for row in payload["summaries"]]
    per_seed = [row for payload in payloads for row in payload["per_seed"]]
    expected_summary_cells = {(size, float(p)) for size in SIZES for p in reference["p_grid"]}
    observed_summary_cells = {(int(row["L"]), float(row["p"])) for row in summaries}
    if observed_summary_cells != expected_summary_cells or len(summaries) != len(expected_summary_cells):
        raise SystemExit("merged summary cells are incomplete or duplicated")
    return summaries, per_seed, reference


def crossing_analysis(summaries: list[dict], per_seed: list[dict], reference: dict) -> dict:
    p_values = [float(value) for value in reference["p_grid"]]
    rates = {
        size: np.asarray([
            next(row["logical_error_rate"] for row in summaries if row["L"] == size and row["p"] == p)
            for p in p_values
        ])
        for size in SIZES
    }
    point = {
        f"L{lower}_L{upper}": directed_crossings(p_values, rates[lower], rates[upper])
        for lower, upper in PAIRS
    }
    seed_counts = {
        (int(row["seed"]), int(row["L"]), float(row["p"])): (int(row["logical_errors"]), int(row["shots"]))
        for row in per_seed
    }
    seeds = [int(seed) for seed in reference["seeds"]]
    expected_seed_cells = {(seed, size, p) for seed in seeds for size in SIZES for p in p_values}
    if set(seed_counts) != expected_seed_cells:
        raise SystemExit("merged seed cells are incomplete or duplicated")

    bootstrap = {
        f"L{lower}_L{upper}": {"single": [], "none": 0, "multiple": 0}
        for lower, upper in PAIRS
    }
    rng = np.random.default_rng(630001)
    for _ in range(BOOTSTRAP_REPLICATES):
        # RNG streams are nested across p within a size, but independent across
        # sizes because the registered SeedSequence includes L.  Resample the
        # seed trajectories independently within each size stratum.
        sampled_by_size = {
            size: rng.choice(seeds, size=len(seeds), replace=True)
            for size in SIZES
        }
        sampled_rates: dict[int, np.ndarray] = {}
        for size in SIZES:
            values = []
            for p in p_values:
                errors = sum(seed_counts[(int(seed), size, p)][0] for seed in sampled_by_size[size])
                shots = sum(seed_counts[(int(seed), size, p)][1] for seed in sampled_by_size[size])
                values.append(errors / shots)
            sampled_rates[size] = np.asarray(values)
        for lower, upper in PAIRS:
            key = f"L{lower}_L{upper}"
            estimates = directed_crossings(p_values, sampled_rates[lower], sampled_rates[upper])
            if len(estimates) == 1:
                bootstrap[key]["single"].append(estimates[0])
            elif estimates:
                bootstrap[key]["multiple"] += 1
            else:
                bootstrap[key]["none"] += 1

    output = {}
    for lower, upper in PAIRS:
        key = f"L{lower}_L{upper}"
        single = bootstrap[key]["single"]
        quantiles = np.quantile(single, [0.025, 0.5, 0.975]).tolist() if single else [None, None, None]
        output[key] = {
            "sizes": [lower, upper],
            "point_directed_crossings": point[key],
            "point_status": "single" if len(point[key]) == 1 else "multiple" if point[key] else "not_bracketed",
            "bootstrap": {
                "method": "size-stratified seed-cluster bootstrap; p trajectories stay nested within size and size streams resample independently",
                "seed": 630001,
                "replicates": BOOTSTRAP_REPLICATES,
                "single_crossing_replicates": len(single),
                "no_crossing_replicates": bootstrap[key]["none"],
                "multiple_crossing_replicates": bootstrap[key]["multiple"],
                "single_crossing_fraction": len(single) / BOOTSTRAP_REPLICATES,
                "conditional_quantiles": {"q025": quantiles[0], "median": quantiles[1], "q975": quantiles[2]},
            },
        }
    return output


def plot(summaries: list[dict], reference: dict, crossings: dict, destination: Path) -> None:
    figure, (axis, convergence_axis) = plt.subplots(
        2, 1, figsize=(9.0, 7.5), gridspec_kw={"height_ratios": [3.3, 1]}, sharex=True, constrained_layout=True
    )
    colors = {
        3: "#0072B2", 5: "#56B4E9", 7: "#009E73",
        9: "#E69F00", 11: "#CC79A7", 13: "#D55E00",
    }
    for size in SIZES:
        rows = sorted((row for row in summaries if row["L"] == size), key=lambda row: row["p"])
        x = [row["p"] for row in rows]
        y = [row["logical_error_rate"] for row in rows]
        low = [rate - row["logical_error_ci95"][0] for rate, row in zip(y, rows)]
        high = [row["logical_error_ci95"][1] - rate for rate, row in zip(y, rows)]
        axis.errorbar(x, y, yerr=[low, high], marker="o", markersize=3.4, linewidth=1.5, capsize=1.8, color=colors[size], label=f"L={size}")
        convergence_axis.plot(x, [row["bp_convergence_rate"] for row in rows], marker="o", markersize=2.8, linewidth=1.2, color=colors[size], label=f"L={size}")

    labels = []
    for key, item in crossings.items():
        estimates = item["point_directed_crossings"]
        if len(estimates) == 1:
            labels.append(f"{key.replace('_', '/')}: {estimates[0]:.4f}")
        elif estimates:
            labels.append(f"{key.replace('_', '/')}: {len(estimates)} crossings")
        else:
            labels.append(f"{key.replace('_', '/')}: none")
    axis.text(
        0.012, 0.975, "\n".join(labels), transform=axis.transAxes, ha="left", va="top", fontsize=8.1,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9},
    )
    axis.set_title(f"Square q=1 unified high-p scan, L=3–13 — {reference['total_shots_per_cell']} shots/cell")
    axis.set_ylabel("logical error rate (LER)")
    axis.grid(alpha=0.22)
    axis.legend(title="code size", ncol=3, loc="lower right")
    convergence_axis.set(xlabel="physical edge-error rate p", ylabel="BP converged", ylim=(-0.005, 1.02))
    convergence_axis.grid(alpha=0.22)
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    summaries, per_seed, reference = load_sources()
    crossings = crossing_analysis(summaries, per_seed, reference)
    analysis = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_shards": [f"results/{stem}.json" for stem in SOURCE_STEMS],
        "design": {
            "lattice": "square", "q": 1.0, "sizes": list(SIZES),
            "p_grid": reference["p_grid"], "seeds": reference["seeds"],
            "shots_per_seed": reference["shots_per_seed"], "shots_per_cell": reference["total_shots_per_cell"],
            "total_decoder_observations": len(SIZES) * len(reference["p_grid"]) * reference["total_shots_per_cell"],
        },
        "summaries": sorted(summaries, key=lambda row: (row["L"], row["p"])),
        "adjacent_size_crossings": crossings,
        "convergence": {
            f"L{size}": {
                "minimum_rate": min(row["bp_convergence_rate"] for row in summaries if row["L"] == size),
                "maximum_rate": max(row["bp_convergence_rate"] for row in summaries if row["L"] == size),
            }
            for size in SIZES
        },
        "evidence_boundary": "Unified finite-size high-p diagnostic for the fixed 40-iteration decoder; crossing multiplicity and convergence must be resolved before threshold promotion.",
    }
    result = LAB_DIR / "results" / f"{OUTPUT_STEM}-analysis.json"
    result.write_text(json.dumps(analysis, indent=2) + "\n")
    figure = LAB_DIR / "figures" / f"{OUTPUT_STEM}-ler-vs-p.png"
    plot(summaries, reference, crossings, figure)
    print(json.dumps({"analysis": str(result), "figure": str(figure), "crossings": crossings}, indent=2))


if __name__ == "__main__":
    main()
