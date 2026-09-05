#!/usr/bin/env python3
"""Compare bounded follow-up designs for the four unresolved Phase B6 cells.

This is a nested posterior-predictive calculation, not a data-producing run.
For each outer draw, latent LERs are sampled from the current independent
Jeffreys-Beta posterior, future binomial counts are simulated, and the updated
posterior probability of the finite-window linear-projection slope sign is
estimated with inner draws.  The MWPM decoder is never invoked by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    LAB_DIR
    / "results"
    / "phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json"
)
DEFAULT_OUTPUT = (
    LAB_DIR
    / "results"
    / "phase-b6-honeycomb-posterior-predictive-design-2026-08-28.json"
)
CLASSIFICATION_THRESHOLD = 0.90


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def slope_weights(sizes: np.ndarray) -> np.ndarray:
    centered = sizes.astype(float) - float(np.mean(sizes))
    return centered / float(np.dot(centered, centered))


def binary_entropy(probability: float) -> float:
    p = float(np.clip(probability, 1e-15, 1.0 - 1e-15))
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))


def planned_additions(cell: dict[str, Any], design: str) -> np.ndarray:
    shots = np.asarray(cell["shots"], dtype=int)
    sizes = np.asarray(cell["sizes"], dtype=int)
    if design == "endpoints_1000":
        return np.where(np.isin(sizes, [int(sizes.min()), int(sizes.max())]), 1000, 0)
    if design == "all_sizes_1000":
        return np.full(shots.shape, 1000, dtype=int)
    if design == "balance_to_3000":
        return np.maximum(3000 - shots, 0)
    raise ValueError(f"unknown design: {design}")


def monte_carlo_se(probability: float, replicates: int) -> float:
    return math.sqrt(max(probability * (1.0 - probability), 0.0) / replicates)


def simulate_cell(
    cell: dict[str, Any],
    additions: np.ndarray,
    *,
    outer_draws: int,
    inner_draws: int,
    seed: int,
) -> dict[str, Any]:
    errors = np.asarray(cell["logical_errors"], dtype=int)
    shots = np.asarray(cell["shots"], dtype=int)
    sizes = np.asarray(cell["sizes"], dtype=float)
    additions = np.asarray(additions, dtype=int)
    if errors.shape != shots.shape or errors.shape != sizes.shape or errors.shape != additions.shape:
        raise ValueError("errors, shots, sizes, and additions must have equal shape")
    if np.any(errors < 0) or np.any(errors > shots) or np.any(additions < 0):
        raise ValueError("invalid binomial counts or additions")
    if outer_draws <= 0 or inner_draws <= 0:
        raise ValueError("draw counts must be positive")

    rng = np.random.default_rng(seed)
    alpha = errors.astype(float) + 0.5
    beta = shots.astype(float) - errors.astype(float) + 0.5
    weights = slope_weights(sizes)

    resolved_up = np.zeros(outer_draws, dtype=bool)
    resolved_down = np.zeros(outer_draws, dtype=bool)
    false_resolution = np.zeros(outer_draws, dtype=bool)
    posterior_up = np.empty(outer_draws, dtype=float)
    entropy = np.empty(outer_draws, dtype=float)

    for replicate in range(outer_draws):
        latent = rng.beta(alpha, beta)
        future_errors = rng.binomial(additions, latent)
        updated_alpha = alpha + future_errors
        updated_beta = beta + additions - future_errors
        inner = rng.beta(updated_alpha, updated_beta, size=(inner_draws, len(alpha)))
        p_up = float(np.mean((inner @ weights) > 0.0))
        posterior_up[replicate] = p_up
        entropy[replicate] = binary_entropy(p_up)
        resolved_up[replicate] = p_up >= CLASSIFICATION_THRESHOLD
        resolved_down[replicate] = (1.0 - p_up) >= CLASSIFICATION_THRESHOLD
        true_up = float(np.dot(latent, weights)) > 0.0
        false_resolution[replicate] = (
            (resolved_up[replicate] and not true_up)
            or (resolved_down[replicate] and true_up)
        )

    resolved = resolved_up | resolved_down
    p_resolved = float(np.mean(resolved))
    p_upward = float(np.mean(resolved_up))
    p_downward = float(np.mean(resolved_down))
    p_false = float(np.mean(false_resolution))
    current_up = float(cell["posterior_probability_upward_trend"])
    current_entropy = binary_entropy(current_up)
    expected_entropy = float(np.mean(entropy))

    return {
        "q": float(cell["q"]),
        "p": float(cell["p"]),
        "sizes": [int(value) for value in sizes],
        "current_logical_errors": errors.tolist(),
        "current_shots": shots.tolist(),
        "additional_shots": additions.tolist(),
        "additional_decodes": int(np.sum(additions)),
        "current_posterior_probability_upward": current_up,
        "current_sign_entropy_nats": current_entropy,
        "posterior_predictive_probability_resolved": p_resolved,
        "posterior_predictive_probability_resolved_upward": p_upward,
        "posterior_predictive_probability_resolved_downward": p_downward,
        "posterior_predictive_probability_unresolved": 1.0 - p_resolved,
        "posterior_predictive_probability_false_direction_resolution": p_false,
        "expected_updated_posterior_probability_upward": float(np.mean(posterior_up)),
        "expected_updated_sign_entropy_nats": expected_entropy,
        "expected_sign_entropy_reduction_nats": current_entropy - expected_entropy,
        "monte_carlo_standard_errors": {
            "resolved": monte_carlo_se(p_resolved, outer_draws),
            "resolved_upward": monte_carlo_se(p_upward, outer_draws),
            "resolved_downward": monte_carlo_se(p_downward, outer_draws),
            "false_direction_resolution": monte_carlo_se(p_false, outer_draws),
            "mean_updated_entropy": float(np.std(entropy, ddof=1) / math.sqrt(outer_draws))
            if outer_draws > 1
            else 0.0,
        },
    }


def analyze(
    source_path: Path,
    *,
    outer_draws: int = 1024,
    inner_draws: int = 4096,
    seed: int = 8282026,
) -> dict[str, Any]:
    source = json.loads(source_path.read_text())
    cells = source["analyses"]
    if len(cells) != 4 or any(cell["classification"] != "unresolved" for cell in cells):
        raise ValueError("expected exactly four unresolved Phase B6 cells")

    design_names = ["endpoints_1000", "all_sizes_1000", "balance_to_3000"]
    designs: list[dict[str, Any]] = []
    for design_index, design_name in enumerate(design_names):
        cell_results = []
        for cell_index, cell in enumerate(cells):
            cell_results.append(
                simulate_cell(
                    cell,
                    planned_additions(cell, design_name),
                    outer_draws=outer_draws,
                    inner_draws=inner_draws,
                    seed=seed + 1000 * design_index + cell_index,
                )
            )
        total_decodes = sum(item["additional_decodes"] for item in cell_results)
        expected_resolved = sum(
            item["posterior_predictive_probability_resolved"] for item in cell_results
        )
        expected_false = sum(
            item["posterior_predictive_probability_false_direction_resolution"]
            for item in cell_results
        )
        designs.append(
            {
                "name": design_name,
                "total_additional_decodes": total_decodes,
                "expected_resolved_cells": expected_resolved,
                "expected_false_direction_resolutions": expected_false,
                "expected_resolved_cells_per_1000_decodes": (
                    1000.0 * expected_resolved / total_decodes if total_decodes else 0.0
                ),
                "mean_expected_sign_entropy_reduction_nats": float(
                    np.mean(
                        [item["expected_sign_entropy_reduction_nats"] for item in cell_results]
                    )
                ),
                "cells": cell_results,
            }
        )

    efficiency_ranking = [
        item["name"]
        for item in sorted(
            designs,
            key=lambda item: (
                -item["expected_resolved_cells_per_1000_decodes"],
                item["total_additional_decodes"],
            ),
        )
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_design_diagnostic_no_data_launched",
        "source": {"path": str(source_path), "sha256": sha256(source_path)},
        "posterior_model": {
            "likelihood": "independent binomial logical-error counts by distance",
            "prior": "independent Beta(0.5, 0.5) Jeffreys priors",
            "trend_functional": "OLS projection slope of latent LER on linear distance",
            "classification_threshold": CLASSIFICATION_THRESHOLD,
            "outer_draws": outer_draws,
            "inner_draws_per_outer_draw": inner_draws,
            "seed": seed,
        },
        "designs": designs,
        "efficiency_ranking_descriptive_only": efficiency_ranking,
        "registration_decision": "not_made_by_this_diagnostic",
        "evidence_boundary": (
            "Conditional on the current independent-Beta finite-window model. "
            "This estimates how often specified bounded measurements would cross the 0.90 "
            "posterior sign gate; it does not guarantee resolution, establish an asymptotic "
            "phase, choose a scientific loss function, or launch decoder jobs."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--outer-draws", type=int, default=1024)
    parser.add_argument("--inner-draws", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=8282026)
    args = parser.parse_args()
    result = analyze(
        args.source,
        outer_draws=args.outer_draws,
        inner_draws=args.inner_draws,
        seed=args.seed,
    )
    atomic_json(args.output, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(args.output),
                "efficiency_ranking": result["efficiency_ranking_descriptive_only"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
