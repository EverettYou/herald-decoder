#!/usr/bin/env python3
"""Infer a Bayesian fuzzy linear trend from Phase B1 LER posteriors."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import beta as beta_distribution
from scipy.stats import qmc


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-sentinels-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-bayesian-fuzzy-trend-2026-08-28.json"
POSTERIOR_THRESHOLD = 0.90


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def _censored_log_odds(p_up: float, p_down: float, resolution: float) -> tuple[float | None, dict]:
    if p_up > 0.0 and p_down > 0.0:
        value = float(np.log(p_up / p_down))
        return value, {"relation": "equal", "bound": value}
    if p_up == 0.0 and p_down > 0.0:
        return None, {"relation": "less_than", "bound": float(np.log(resolution / p_down))}
    if p_down == 0.0 and p_up > 0.0:
        return None, {"relation": "greater_than", "bound": float(np.log(p_up / resolution))}
    return None, {"relation": "indeterminate", "bound": None}


def _kendall_tau(draws: np.ndarray) -> np.ndarray:
    pairs = draws.shape[1] * (draws.shape[1] - 1) // 2
    concordance = np.zeros(draws.shape[0], dtype=np.int16)
    for left in range(draws.shape[1]):
        for right in range(left + 1, draws.shape[1]):
            concordance += np.where(draws[:, right] > draws[:, left], 1, -1)
    return concordance / pairs


def posterior_fuzzy_linear_trend(
    errors: np.ndarray,
    shots: np.ndarray,
    sizes: np.ndarray,
    *,
    prior_alpha: float = 0.5,
    prior_beta: float = 0.5,
    scramble_replicates: int = 8,
    base2_power: int = 13,
    seed: int = 880128,
    threshold: float = POSTERIOR_THRESHOLD,
) -> dict:
    """Project each latent-LER posterior draw onto a linear-in-distance slope.

    This defines beta(theta) as the ordinary least-squares projection

        beta = sum_i (L_i - Lbar) theta_i / sum_i (L_i - Lbar)^2.

    The binomial/Beta model is only for the unknown LER values theta_i.  The
    line is a descriptive functional of each posterior draw, not an assumption
    that the true LER curve is linear.
    """
    errors = np.asarray(errors, dtype=np.float64)
    shots = np.asarray(shots, dtype=np.float64)
    sizes = np.asarray(sizes, dtype=np.float64)
    if errors.shape != shots.shape or errors.shape != sizes.shape or errors.ndim != 1 or errors.size < 3:
        raise ValueError("matching one-dimensional counts and at least three sizes are required")
    if np.any(shots <= 0) or np.any(errors < 0) or np.any(errors > shots):
        raise ValueError("invalid binomial counts")
    if len(np.unique(sizes)) != sizes.size:
        raise ValueError("sizes must be unique")
    centered = sizes - sizes.mean()
    denominator = float(np.dot(centered, centered))
    alpha = errors + prior_alpha
    beta = shots - errors + prior_beta
    replicate_up = []
    replicate_down = []
    slopes = []
    endpoint_differences = []
    kendall_taus = []
    midpoint_residuals = []
    for replicate in range(scramble_replicates):
        uniforms = qmc.Sobol(errors.size, scramble=True, seed=seed + replicate).random_base2(base2_power)
        draws = beta_distribution.ppf(uniforms, alpha, beta)
        replicate_slopes = draws @ centered / denominator
        slopes.append(replicate_slopes)
        replicate_up.append(float(np.mean(replicate_slopes > 0.0)))
        replicate_down.append(float(np.mean(replicate_slopes < 0.0)))
        endpoint_differences.append(draws[:, -1] - draws[:, 0])
        kendall_taus.append(_kendall_tau(draws))
        middle = draws.shape[1] // 2
        fraction = (sizes[middle] - sizes[0]) / (sizes[-1] - sizes[0])
        endpoint_chord = (1.0 - fraction) * draws[:, 0] + fraction * draws[:, -1]
        midpoint_residuals.append(draws[:, middle] - endpoint_chord)
    all_slopes = np.concatenate(slopes)
    all_endpoint = np.concatenate(endpoint_differences)
    all_tau = np.concatenate(kendall_taus)
    all_midpoint_residual = np.concatenate(midpoint_residuals)
    p_up = float(np.mean(all_slopes > 0.0))
    p_down = float(np.mean(all_slopes < 0.0))
    resolution = 1.0 / all_slopes.size
    log_odds, censoring = _censored_log_odds(p_up, p_down, resolution)
    classification = "unresolved"
    if p_down >= threshold:
        classification = "decodable"
    elif p_up >= threshold:
        classification = "undecodable"
    return {
        "posterior_probability_upward_trend": p_up,
        "posterior_probability_downward_trend": p_down,
        "posterior_mean_slope_ler_per_distance": float(np.mean(all_slopes)),
        "posterior_slope_interval90": [float(value) for value in np.quantile(all_slopes, [0.05, 0.95])],
        "posterior_log_odds_upward_vs_downward": log_odds,
        "posterior_log_odds_censoring": censoring,
        "qmc_standard_error_upward_probability": None if p_up in {0.0, 1.0} else float(np.std(replicate_up, ddof=1) / np.sqrt(scramble_replicates)),
        "qmc_standard_error_downward_probability": None if p_down in {0.0, 1.0} else float(np.std(replicate_down, ddof=1) / np.sqrt(scramble_replicates)),
        "qmc_probability_resolution": resolution,
        "classification": classification,
        "classification_threshold": threshold,
        "sensitivity": {
            "posterior_probability_endpoint_upward": float(np.mean(all_endpoint > 0.0)),
            "posterior_probability_endpoint_downward": float(np.mean(all_endpoint < 0.0)),
            "posterior_probability_positive_kendall_tau": float(np.mean(all_tau > 0.0)),
            "posterior_probability_negative_kendall_tau": float(np.mean(all_tau < 0.0)),
            "posterior_probability_zero_kendall_tau": float(np.mean(all_tau == 0.0)),
            "posterior_mean_kendall_tau": float(np.mean(all_tau)),
            "posterior_probability_midpoint_above_endpoint_chord": float(np.mean(all_midpoint_residual > 0.0)),
            "posterior_probability_midpoint_below_endpoint_chord": float(np.mean(all_midpoint_residual < 0.0)),
            "posterior_mean_midpoint_chord_residual": float(np.mean(all_midpoint_residual)),
            "posterior_midpoint_chord_residual_interval90": [float(value) for value in np.quantile(all_midpoint_residual, [0.05, 0.95])],
        },
        "qmc_scramble_replicates": scramble_replicates,
        "qmc_draws_per_replicate": 2**base2_power,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = json.loads(args.source.read_text())
    rows = []
    for offset, cell in enumerate(source["analyses"]):
        errors = np.asarray(cell["logical_errors"])
        shots = np.asarray(cell["shots"])
        sizes = np.asarray(cell["sizes"])
        primary = posterior_fuzzy_linear_trend(errors, shots, sizes, seed=880128 + offset)
        uniform = posterior_fuzzy_linear_trend(
            errors,
            shots,
            sizes,
            prior_alpha=1.0,
            prior_beta=1.0,
            seed=890128 + offset,
        )
        rows.append(
            {
                "role": cell["role"],
                "q": cell["q"],
                "p": cell["p"],
                "sizes": cell["sizes"],
                "logical_errors": cell["logical_errors"],
                "shots": cell["shots"],
                **primary,
                "uniform_prior_sensitivity": uniform,
                "strict_order_classification": cell["classification"],
                "ordering_entropy_bits": cell["qmc_ordering_entropy_bits"],
                "effective_ordering_count": cell["qmc_effective_ordering_count"],
            }
        )
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "definition": {
            "latent_parameters": "theta_L is the unknown LER at each measured distance",
            "likelihood": "independent Binomial(n_L, theta_L) logical-error counts",
            "prior": "independent Jeffreys Beta(1/2,1/2); uniform Beta(1,1) sensitivity",
            "trend_functional": "beta(theta)=sum_L (L-Lbar) theta_L / sum_L (L-Lbar)^2, the OLS linear projection slope of each latent-LER draw",
            "H_up": "beta(theta) > 0",
            "H_down": "beta(theta) < 0",
            "classification": "undecodable if Pr(H_up|D)>=0.90; decodable if Pr(H_down|D)>=0.90; otherwise unresolved",
            "interpretation": "Bayesian finite-window fuzzy trend; the projection summarizes direction and does not assert that the true LER curve is linear",
            "shape_sensitivity": "endpoint direction and Kendall-tau sign probabilities are reported separately",
        },
        "provenance": {
            "five_distance_source": {"path": str(args.source), "sha256": sha256(args.source)},
            "analyzer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        },
        "analyses": rows,
        "crossing_statistic_used": False,
        "grid_expanded": False,
        "evidence_boundary": "Four Phase B1 sentinel cells only; validates the researcher-selected fuzzy linear-trend definition before full-grid use.",
    }
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "classifications": {row["role"]: row["classification"] for row in rows}}, indent=2))


if __name__ == "__main__":
    main()
