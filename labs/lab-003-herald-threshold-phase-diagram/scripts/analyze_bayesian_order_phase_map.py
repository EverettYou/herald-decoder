#!/usr/bin/env python3
"""Infer posterior probabilities of increasing/decreasing finite-size LER.

For one measured (p, q) cell, let theta_7, theta_9, theta_11 be the unknown
logical-error probabilities.  Independent Jeffreys priors and binomial
likelihoods give independent Beta posteriors.  This script integrates the
posterior mass of the two order-constrained hypotheses

    H_down: theta_7 > theta_9 > theta_11
    H_up:   theta_7 < theta_9 < theta_11

exactly up to numerical quadrature.  The remaining posterior mass belongs to
the four nonmonotone orderings.  No scaling-law fit or curve crossing enters
the inference.  The hypotheses concern only the measured L=7,9,11 window.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from scipy.special import betainc, roots_jacobi
from scipy.stats import beta as beta_distribution


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase2-residual80-q-skeleton-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase2-residual80-honeycomb-bayesian-order-phase-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase2-residual80-honeycomb-bayesian-order-phase-2026-08-28.png"
POSTERIOR_THRESHOLD = 0.90
QUADRATURE_ORDER = 256


def load_validator():
    path = Path(__file__).with_name("analyze_phase2_scout.py")
    spec = importlib.util.spec_from_file_location("phase2_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def posterior_order_probabilities(
    logical_errors: np.ndarray,
    shots: np.ndarray,
    *,
    prior_alpha: float = 0.5,
    prior_beta: float = 0.5,
) -> dict:
    """Return posterior mass for strict decrease, increase, and other orders.

    For three independent posterior variables X0, X1, X2,

      Pr(X0 > X1 > X2) = integral f1(y) [1-F0(y)] F2(y) dy,
      Pr(X0 < X1 < X2) = integral f1(y) F0(y) [1-F2(y)] dy.

    Ties have zero posterior probability under continuous Beta priors, so the
    remaining mass is exactly the union of the four nonmonotone permutations.
    """
    logical_errors = np.asarray(logical_errors, dtype=np.float64)
    shots = np.asarray(shots, dtype=np.float64)
    if logical_errors.shape != (3,) or shots.shape != (3,):
        raise ValueError("exactly three measured distances are required")
    if np.any(shots <= 0) or np.any(logical_errors < 0) or np.any(logical_errors > shots):
        raise ValueError("invalid binomial counts")
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("Beta prior parameters must be positive")

    alpha = logical_errors + prior_alpha
    beta = shots - logical_errors + prior_beta

    # Gauss-Jacobi quadrature absorbs the middle Beta density into its weight,
    # avoiding endpoint underflow and adaptive-integration warnings for cells
    # with zero or near-certain logical-error counts.
    nodes, weights = roots_jacobi(
        QUADRATURE_ORDER,
        beta[1] - 1.0,
        alpha[1] - 1.0,
    )
    middle_values = (nodes + 1.0) / 2.0
    normalized_weights = weights / weights.sum()
    cdf_0 = betainc(alpha[0], beta[0], middle_values)
    cdf_2 = betainc(alpha[2], beta[2], middle_values)
    probability_decreasing = float(np.sum(normalized_weights * (1.0 - cdf_0) * cdf_2))
    probability_increasing = float(np.sum(normalized_weights * cdf_0 * (1.0 - cdf_2)))
    probability_other = float(max(0.0, 1.0 - probability_decreasing - probability_increasing))
    log_odds = float(
        np.log(max(probability_increasing, 1e-300))
        - np.log(max(probability_decreasing, 1e-300))
    )
    posterior_mean = alpha / (alpha + beta)
    credible = np.asarray(
        [
            beta_distribution.ppf([0.05, 0.95], alpha[index], beta[index])
            for index in range(3)
        ]
    )
    return {
        "posterior_probability_decreasing": probability_decreasing,
        "posterior_probability_increasing": probability_increasing,
        "posterior_probability_other_order": probability_other,
        "posterior_direction_score": probability_increasing - probability_decreasing,
        "posterior_log_odds_increasing_vs_decreasing": log_odds,
        "posterior_mean_ler": [float(value) for value in posterior_mean],
        "posterior_ler_intervals90": [[float(lo), float(hi)] for lo, hi in credible],
    }


def classify(probabilities: dict, threshold: float = POSTERIOR_THRESHOLD) -> str:
    if probabilities["posterior_probability_decreasing"] >= threshold:
        return "decodable"
    if probabilities["posterior_probability_increasing"] >= threshold:
        return "undecodable"
    return "unresolved"


def cell_edges(values: list[float], lower: float | None = None, upper: float | None = None) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    midpoints = (array[:-1] + array[1:]) / 2
    edges = np.concatenate(
        [[array[0] - (midpoints[0] - array[0])], midpoints, [array[-1] + (array[-1] - midpoints[-1])]]
    )
    if lower is not None:
        edges[0] = lower
    if upper is not None:
        edges[-1] = upper
    return edges


def analyze_q(payload: dict, manifest: dict) -> dict:
    sizes = [int(value) for value in manifest["sizes"]]
    if sizes != [7, 9, 11]:
        raise ValueError("Bayesian order analysis currently requires L=7,9,11")
    summaries = {(int(row["L"]), round(float(row["p"]), 12)): row for row in payload["summaries"]}
    cells = []
    for p in [float(value) for value in manifest["p_grid"][payload["lattice"]]]:
        rows = [summaries[(size, round(p, 12))] for size in sizes]
        errors = np.asarray([int(row["logical_errors"]) for row in rows])
        shots = np.asarray([int(row["shots"]) for row in rows])
        posterior = posterior_order_probabilities(errors, shots)
        uniform_sensitivity = posterior_order_probabilities(
            errors, shots, prior_alpha=1.0, prior_beta=1.0
        )
        posterior.update(
            {
                "p": p,
                "logical_errors": [int(value) for value in errors],
                "shots": [int(value) for value in shots],
                "classification": classify(posterior),
                "uniform_prior_sensitivity": {
                    "posterior_probability_decreasing": uniform_sensitivity[
                        "posterior_probability_decreasing"
                    ],
                    "posterior_probability_increasing": uniform_sensitivity[
                        "posterior_probability_increasing"
                    ],
                    "posterior_probability_other_order": uniform_sensitivity[
                        "posterior_probability_other_order"
                    ],
                    "classification": classify(uniform_sensitivity),
                },
            }
        )
        cells.append(posterior)
    return {"q": float(payload["q"]), "cells": cells}


def plot_posterior_map(analyses: list[dict], p_values: list[float], destination: Path) -> None:
    q_values = [row["q"] for row in analyses]
    log_odds = np.asarray(
        [
            [cell["posterior_log_odds_increasing_vs_decreasing"] for cell in row["cells"]]
            for row in analyses
        ]
    )
    cmap = LinearSegmentedColormap.from_list(
        "decrease_other_increase", ["#16834A", "#ECEFF1", "#C63F32"]
    )
    figure, axis = plt.subplots(figsize=(9.8, 7.7), constrained_layout=True)
    mesh = axis.pcolormesh(
        cell_edges(p_values),
        cell_edges(q_values, 0.0, 1.0),
        np.clip(log_odds, -10.0, 10.0),
        cmap=cmap,
        norm=TwoSlopeNorm(vmin=-10.0, vcenter=0.0, vmax=10.0),
        shading="flat",
        edgecolors="white",
        linewidth=0.45,
    )
    counts = {
        label: sum(cell["classification"] == label for row in analyses for cell in row["cells"])
        for label in ("decodable", "undecodable", "unresolved")
    }
    axis.set(
        title="Honeycomb Bayesian finite-size direction map\n"
        "color = log[Pr(increasing | data) / Pr(decreasing | data)], L = 7, 9, 11",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(cell_edges(p_values)[0], cell_edges(p_values)[-1]),
        ylim=(0, 1),
    )
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0, 1.01, 0.1))
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.02)
    colorbar.set_label("log posterior odds  (green: decreasing, red: increasing; clipped at +/-10)")
    axis.text(
        0.995,
        0.015,
        f"90% posterior classification: {counts['decodable']} green, "
        f"{counts['undecodable']} red, {counts['unresolved']} unresolved",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="#30353B",
        bbox={"facecolor": "white", "edgecolor": "#C8CDD2", "alpha": 0.90, "pad": 4},
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()

    validator = load_validator()
    manifest = validator.load_manifest(args.manifest)
    if manifest["lattices"] != ["honeycomb"] or manifest["sizes"] != [7, 9, 11]:
        raise SystemExit("Bayesian order map requires the honeycomb L=7,9,11 full skeleton")
    paths = validator.discover_shards(LAB_DIR / "results", manifest)
    current_sources = {name: validator.sha256(path) for name, path in validator.SOURCE_FILES.items()}
    runtime = sources = None
    analyses = []
    validated = []
    for _, path in sorted(paths.items()):
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
        analyses.append(analyze_q(payload, manifest))
        validated.append(str(path))

    p_values = [float(value) for value in manifest["p_grid"]["honeycomb"]]
    plot_posterior_map(analyses, p_values, args.figure)
    counts = {
        label: sum(cell["classification"] == label for row in analyses for cell in row["cells"])
        for label in ("decodable", "undecodable", "unresolved")
    }
    prior_sensitive = sum(
        cell["classification"] != cell["uniform_prior_sensitivity"]["classification"]
        for row in analyses
        for cell in row["cells"]
    )
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "campaign": manifest["campaign"],
        "hypotheses": {
            "decreasing": "theta_7 > theta_9 > theta_11",
            "increasing": "theta_7 < theta_9 < theta_11",
            "other_order": "union of the four remaining strict orderings",
        },
        "likelihood": "independent binomial logical-error counts at each distance",
        "primary_prior": "independent Jeffreys Beta(1/2,1/2) priors for theta_7, theta_9, theta_11",
        "prior_hypothesis_mass": {
            "decreasing": 1 / 6,
            "increasing": 1 / 6,
            "other_order": 4 / 6,
        },
        "posterior_computation": "one-dimensional order-probability integrals evaluated by 256-point Gauss-Jacobi quadrature",
        "map_score": "log[Pr(H_increasing|data)/Pr(H_decreasing|data)], clipped to [-10,10] for color only",
        "classification_threshold": POSTERIOR_THRESHOLD,
        "classification_rule": {
            "decodable": "Pr(H_decreasing | data) >= 0.90",
            "undecodable": "Pr(H_increasing | data) >= 0.90",
            "unresolved": "otherwise",
        },
        "sizes": manifest["sizes"],
        "q_values": manifest["q_values"],
        "p_values": p_values,
        "cell_counts": counts,
        "uniform_prior_classification_changes": prior_sensitive,
        "lattice": "honeycomb",
        "analyses": analyses,
        "figure": str(args.figure),
        "validated_summaries": validated,
        "runtime": runtime,
        "source_hashes": sources,
        "crossing_statistic_used": False,
        "functional_scaling_form_assumed": None,
        "evidence_boundary": "Posterior evidence for monotone ordering only on measured L=7,9,11. This operational finite-window result is not an asymptotic phase proof.",
    }
    validator.atomic_json(args.output, output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "figure": str(args.figure),
                "cell_counts": counts,
                "uniform_prior_classification_changes": prior_sensitive,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
