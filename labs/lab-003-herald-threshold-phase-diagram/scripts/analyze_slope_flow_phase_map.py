#!/usr/bin/env python3
"""Historical exploratory logit-versus-log-size projection for Lab 003.

Methodology correction (2026-08-28): ``logit(P_L) = alpha + beta log(L)``
assumes power-law logical-error odds.  That assumption was not derived for the
code/noise/decoder and the sign of beta must not be used as a phase label.
The code remains only to reproduce the historical projection and bootstrap;
its generated red/green/gray map is not an accepted phase diagram.  See
``../METHODOLOGY.md``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


LAB_DIR = Path(__file__).resolve().parents[1]
SLOPE_ZERO_TOLERANCE = 1e-8
DEFAULT_MANIFEST = LAB_DIR / "phase2-residual80-q-skeleton-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase2-residual80-honeycomb-slope-flow-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase2-residual80-honeycomb-slope-flow-phase-map-2026-08-28.png"


def load_validator():
    path = Path(__file__).with_name("analyze_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase2_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def fit_logit_slopes(successes: np.ndarray, totals: np.ndarray, log_sizes: np.ndarray) -> np.ndarray:
    """Return binomial-logit slopes for rows of size-indexed counts.

    Jeffreys half-count regularization keeps zero-event cells finite while
    leaving their slope at zero when every distance has the same zero rate.
    """
    successes = np.asarray(successes, dtype=np.float64)
    totals = np.asarray(totals, dtype=np.float64)
    log_sizes = np.asarray(log_sizes, dtype=np.float64)
    if successes.shape != totals.shape or successes.ndim != 2:
        raise ValueError("successes and totals must be equal two-dimensional arrays")
    if successes.shape[1] != log_sizes.size or log_sizes.size < 2:
        raise ValueError("at least two distances are required")
    if np.any(totals <= 0) or np.any(successes < 0) or np.any(successes > totals):
        raise ValueError("invalid binomial counts")

    y = successes + 0.5
    n = totals + 1.0
    empirical = np.clip(y / n, 1e-8, 1 - 1e-8)
    logits = np.log(empirical / (1 - empirical))
    centered = log_sizes - log_sizes.mean()
    slope = (logits * centered).sum(axis=1) / np.square(centered).sum()
    intercept = logits.mean(axis=1) - slope * log_sizes.mean()

    for _ in range(30):
        eta = np.clip(intercept[:, None] + slope[:, None] * log_sizes, -30, 30)
        probability = 1.0 / (1.0 + np.exp(-eta))
        residual = y - n * probability
        weight = n * probability * (1 - probability)
        score_0 = residual.sum(axis=1)
        score_1 = (residual * log_sizes).sum(axis=1)
        h00 = weight.sum(axis=1) + 1e-10
        h01 = (weight * log_sizes).sum(axis=1)
        h11 = (weight * np.square(log_sizes)).sum(axis=1) + 1e-10
        determinant = np.maximum(h00 * h11 - h01 * h01, 1e-18)
        delta_0 = (h11 * score_0 - h01 * score_1) / determinant
        delta_1 = (-h01 * score_0 + h00 * score_1) / determinant
        intercept += np.clip(delta_0, -5, 5)
        slope += np.clip(delta_1, -5, 5)
        if max(float(np.max(np.abs(delta_0))), float(np.max(np.abs(delta_1)))) < 1e-10:
            break
    return slope


def seed_arrays(payload: dict, sizes: list[int], p_values: list[float], seeds: list[int]):
    seed_index = {seed: offset for offset, seed in enumerate(seeds)}
    size_index = {size: offset for offset, size in enumerate(sizes)}
    p_index = {round(p, 12): offset for offset, p in enumerate(p_values)}
    counts = np.zeros((len(seeds), len(sizes), len(p_values)), dtype=np.float64)
    shots = np.zeros_like(counts)
    seen = set()
    for row in payload["per_seed"]:
        key = (int(row["seed"]), int(row["L"]), round(float(row["p"]), 12))
        if key in seen:
            raise ValueError(f"duplicate per-seed cell {key}")
        seen.add(key)
        coordinate = (seed_index[key[0]], size_index[key[1]], p_index[key[2]])
        counts[coordinate] = int(row["logical_errors"])
        shots[coordinate] = int(row["shots"])
    if len(seen) != counts.size or np.any(shots <= 0):
        raise ValueError("incomplete per-seed trajectory cube")
    return counts, shots


def analyze_q(payload: dict, manifest: dict, replicates: int, bootstrap_seed: int) -> dict:
    sizes = [int(value) for value in manifest["sizes"]]
    p_values = [float(value) for value in manifest["p_grid"][payload["lattice"]]]
    seeds = [int(value) for value in manifest["seeds"]]
    counts, shots = seed_arrays(payload, sizes, p_values, seeds)
    log_sizes = np.log(np.asarray(sizes, dtype=np.float64))

    observed_successes = counts.sum(axis=0).T
    observed_totals = shots.sum(axis=0).T
    observed_beta = fit_logit_slopes(observed_successes, observed_totals, log_sizes)

    rng = np.random.default_rng(np.random.SeedSequence([bootstrap_seed, int(round(float(payload["q"]) * 100))]))
    boot_successes = np.empty((replicates, len(p_values), len(sizes)), dtype=np.float64)
    boot_totals = np.empty_like(boot_successes)
    for size_offset in range(len(sizes)):
        draws = rng.integers(0, len(seeds), size=(replicates, len(seeds)))
        boot_successes[:, :, size_offset] = counts[:, size_offset, :][draws].sum(axis=1)
        boot_totals[:, :, size_offset] = shots[:, size_offset, :][draws].sum(axis=1)
    beta_samples = fit_logit_slopes(
        boot_successes.reshape(-1, len(sizes)),
        boot_totals.reshape(-1, len(sizes)),
        log_sizes,
    ).reshape(replicates, len(p_values))

    cells = []
    for offset, p in enumerate(p_values):
        interval = np.quantile(beta_samples[:, offset], [0.05, 0.95])
        probability_decodable = float(np.mean(beta_samples[:, offset] < -SLOPE_ZERO_TOLERANCE))
        probability_undecodable = float(np.mean(beta_samples[:, offset] > SLOPE_ZERO_TOLERANCE))
        if interval[1] < -SLOPE_ZERO_TOLERANCE and probability_decodable >= 0.95:
            classification = "decodable"
        elif interval[0] > SLOPE_ZERO_TOLERANCE and probability_undecodable >= 0.95:
            classification = "undecodable"
        else:
            classification = "unresolved"
        pair_slopes = []
        for left in range(len(sizes)):
            retained = [index for index in range(len(sizes)) if index != left]
            pair_slopes.append(
                float(
                    fit_logit_slopes(
                        observed_successes[:, retained],
                        observed_totals[:, retained],
                        log_sizes[retained],
                    )[offset]
                )
            )
        beta_sign = int(np.sign(observed_beta[offset]))
        loo_stable = beta_sign != 0 and all(int(np.sign(value)) == beta_sign for value in pair_slopes)
        cells.append(
            {
                "p": p,
                "beta": float(observed_beta[offset]),
                "beta_interval90": [float(interval[0]), float(interval[1])],
                "probability_decodable": probability_decodable,
                "probability_undecodable": probability_undecodable,
                "classification": classification,
                "leave_one_distance_out_slopes": pair_slopes,
                "leave_one_distance_out_sign_stable": loo_stable,
            }
        )
    return {"q": float(payload["q"]), "cells": cells}


def cell_edges(values: list[float], lower: float | None = None, upper: float | None = None) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    midpoints = (values[:-1] + values[1:]) / 2
    first = values[0] - (midpoints[0] - values[0])
    last = values[-1] + (values[-1] - midpoints[-1])
    edges = np.concatenate([[first], midpoints, [last]])
    if lower is not None:
        edges[0] = lower
    if upper is not None:
        edges[-1] = upper
    return edges


def plot_phase_map(
    analyses: list[dict],
    p_values: list[float],
    destination: Path,
    *,
    title: str | None = None,
) -> None:
    q_values = [row["q"] for row in analyses]
    code = {"undecodable": 0, "unresolved": 1, "decodable": 2}
    matrix = np.asarray([[code[cell["classification"]] for cell in row["cells"]] for row in analyses])
    cmap = ListedColormap(["#D9584A", "#D9DDE2", "#3A9D5D"])
    figure, axis = plt.subplots(figsize=(9.8, 7.7), constrained_layout=True)
    axis.pcolormesh(
        cell_edges(p_values),
        cell_edges(q_values, 0.0, 1.0),
        matrix,
        cmap=cmap,
        vmin=-0.5,
        vmax=2.5,
        shading="flat",
        edgecolors="white",
        linewidth=0.45,
    )
    # Draw only observed green/red adjacencies whose all-distance slope sign is
    # resolved and leave-one-distance-out stable on both sides. This is a
    # beta-sign boundary, not a curve crossing.
    for q_offset, q in enumerate(q_values):
        classes = [cell["classification"] for cell in analyses[q_offset]["cells"]]
        for p_offset in range(len(p_values) - 1):
            left = analyses[q_offset]["cells"][p_offset]
            right = analyses[q_offset]["cells"][p_offset + 1]
            if (
                {classes[p_offset], classes[p_offset + 1]} == {"decodable", "undecodable"}
                and left["leave_one_distance_out_sign_stable"]
                and right["leave_one_distance_out_sign_stable"]
            ):
                axis.plot(
                    [(p_values[p_offset] + p_values[p_offset + 1]) / 2] * 2,
                    [cell_edges(q_values, 0.0, 1.0)[q_offset], cell_edges(q_values, 0.0, 1.0)[q_offset + 1]],
                    color="#20252B",
                    linewidth=2.0,
                )
    axis.set(
        title=title or "Honeycomb operational phase map from all-distance LER scaling flow\n"
        "beta from logit(LER) = alpha + beta log(L), L = 7, 9, 11; no crossing statistic",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(cell_edges(p_values)[0], cell_edges(p_values)[-1]),
        ylim=(0, 1),
    )
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0, 1.01, 0.1))
    axis.legend(
        handles=[
            Patch(facecolor="#3A9D5D", label="decodable: beta < 0 (90% resolved)"),
            Patch(facecolor="#D9584A", label="undecodable: beta > 0 (90% resolved)"),
            Patch(facecolor="#D9DDE2", label="unresolved: beta interval includes 0"),
        ],
        loc="upper left",
        frameon=True,
        fontsize=9,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    parser.add_argument("--bootstrap-replicates", type=int)
    args = parser.parse_args()

    validator = load_validator()
    manifest = validator.load_manifest(args.manifest)
    if manifest["lattices"] != ["honeycomb"] or manifest["sizes"] != [7, 9, 11]:
        raise SystemExit("slope-flow primary requires the honeycomb L=7,9,11 full skeleton")
    replicates = args.bootstrap_replicates or int(manifest["inference"]["bootstrap_replicates"])
    paths = validator.discover_shards(LAB_DIR / "results", manifest)
    current_sources = {name: validator.sha256(path) for name, path in validator.SOURCE_FILES.items()}
    runtime = sources = None
    analyses = []
    validated = []
    for key, path in sorted(paths.items()):
        payload = validator.validate_shard(
            path,
            manifest,
            lab_dir=LAB_DIR,
            expected_runtime=runtime,
            expected_sources=sources,
            current_sources=current_sources,
            validate_raw=False,
        )
        runtime = payload["runtime"] if runtime is None else runtime
        sources = payload["source_hashes"] if sources is None else sources
        analyses.append(analyze_q(payload, manifest, replicates, int(manifest["inference"]["bootstrap_seed"])))
        validated.append(str(path))
    p_values = [float(value) for value in manifest["p_grid"]["honeycomb"]]
    plot_phase_map(analyses, p_values, args.figure)
    counts = {
        label: sum(cell["classification"] == label for row in analyses for cell in row["cells"])
        for label in ("decodable", "undecodable", "unresolved")
    }
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "campaign": manifest["campaign"],
        "primary_statistic": "beta in logit(P_logical) = alpha + beta log(L)",
        "sizes": manifest["sizes"],
        "q_values": manifest["q_values"],
        "p_values": p_values,
        "bootstrap": {
            "replicates": replicates,
            "confidence_level": 0.90,
            "unit": "complete nested-p seed trajectory, independently resampled by distance",
        },
        "classification_rule": {
            "decodable": "beta interval90 upper < 0 and Pr(beta<0) >= 0.95",
            "undecodable": "beta interval90 lower > 0 and Pr(beta>0) >= 0.95",
            "unresolved": "otherwise",
        },
        "cell_counts": counts,
        "lattice": "honeycomb",
        "analyses": analyses,
        "figure": str(args.figure),
        "validated_summaries": validated,
        "runtime": runtime,
        "source_hashes": sources,
        "crossing_statistic_used": False,
        "evidence_boundary": "Decoder-specific finite-size scaling flow on measured L=7,9,11 cells. Gray cells remain unresolved; no unmeasured region is colored or interpolated.",
    }
    validator.atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "figure": str(args.figure), "cell_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
