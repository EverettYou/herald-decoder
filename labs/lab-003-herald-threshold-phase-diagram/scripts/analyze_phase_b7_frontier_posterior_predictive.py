#!/usr/bin/env python3
"""Recompute the Phase B7 frontier and compare bounded follow-up designs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b7-honeycomb-frontier-posterior-predictive-design-2026-08-28.json"
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.65, 0.28)}


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_by_key(phase_map: dict, q: float, p: float) -> dict[str, Any]:
    for row in phase_map["analyses"]:
        for cell in row["cells"]:
            if abs(float(row["q"]) - q) < 1e-12 and abs(float(cell["p"]) - p) < 1e-12:
                result = dict(cell)
                result["q"] = q
                if "sizes" not in result:
                    if len(result["shots"]) != 3:
                        raise ValueError("cannot infer source distance window")
                    result["sizes"] = [7, 9, 11]
                return result
    raise ValueError(f"missing Phase B7 cell: {(q, p)}")


def additions(cell: dict[str, Any], design: str) -> np.ndarray:
    shots = np.asarray(cell["shots"], dtype=int)
    if design == "raise_minimum_by_1000":
        return np.where(shots == shots.min(), 1000, 0)
    if design == "all_sizes_1000":
        return np.full(shots.shape, 1000, dtype=int)
    if design == "balance_to_3000":
        return np.maximum(3000 - shots, 0)
    raise ValueError(f"unknown design: {design}")


def analyze(
    map_path: Path,
    *,
    outer_draws: int = 1024,
    inner_draws: int = 4096,
    seed: int = 8282726,
) -> dict[str, Any]:
    phase_map = json.loads(map_path.read_text())
    frontier_module = load("select_phase_b3_frontier_reuse.py", "phase_b7_frontier")
    predictive = load("analyze_phase_b6_posterior_predictive_design.py", "phase_b7_predictive")
    frontier = frontier_module.frontier_candidates(phase_map)
    keys = {(float(row["q"]), float(row["p"])) for row in frontier}
    if keys != EXPECTED:
        raise ValueError(f"Phase B7 frontier drift: {sorted(keys)}")
    cells = [cell_by_key(phase_map, q, p) for q, p in sorted(EXPECTED)]

    design_names = ["raise_minimum_by_1000", "all_sizes_1000", "balance_to_3000"]
    designs = []
    for design_index, name in enumerate(design_names):
        results = []
        for cell_index, cell in enumerate(cells):
            results.append(
                predictive.simulate_cell(
                    cell,
                    additions(cell, name),
                    outer_draws=outer_draws,
                    inner_draws=inner_draws,
                    seed=seed + 1000 * design_index + cell_index,
                )
            )
        cost = sum(row["additional_decodes"] for row in results)
        resolved = sum(row["posterior_predictive_probability_resolved"] for row in results)
        false_resolved = sum(
            row["posterior_predictive_probability_false_direction_resolution"]
            for row in results
        )
        designs.append(
            {
                "name": name,
                "total_additional_decodes": cost,
                "expected_resolved_cells": resolved,
                "expected_false_direction_resolutions": false_resolved,
                "expected_resolved_cells_per_1000_decodes": 1000.0 * resolved / cost,
                "mean_expected_sign_entropy_reduction_nats": float(
                    np.mean([row["expected_sign_entropy_reduction_nats"] for row in results])
                ),
                "cells": results,
            }
        )
    ranking = [
        row["name"]
        for row in sorted(
            designs,
            key=lambda row: (-row["expected_resolved_cells_per_1000_decodes"], row["total_additional_decodes"]),
        )
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_design_diagnostic_no_data_registered_or_launched",
        "source_map": {"path": str(map_path), "sha256": sha256(map_path)},
        "frontier_rule": "All unresolved four-neighbor cells adjacent to both a decodable and an undecodable cell.",
        "frontier_candidates": frontier,
        "frontier_count": len(frontier),
        "posterior_model": {
            "likelihood": "independent binomial logical-error counts by distance",
            "prior": "independent Beta(0.5, 0.5) Jeffreys priors",
            "trend_functional": "OLS projection slope of latent LER on linear distance",
            "classification_threshold": 0.9,
            "outer_draws": outer_draws,
            "inner_draws_per_outer_draw": inner_draws,
            "seed": seed,
        },
        "designs": designs,
        "efficiency_ranking_descriptive_only": ranking,
        "registration_decision": "not_made_by_this_diagnostic",
        "evidence_boundary": "Conditional finite-window posterior-predictive design comparison for the exact Phase B7 frontier; no data registration, launch, crossing statistic, interpolation, or asymptotic phase claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--outer-draws", type=int, default=1024)
    parser.add_argument("--inner-draws", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=8282726)
    args = parser.parse_args()
    output = analyze(args.phase_map, outer_draws=args.outer_draws, inner_draws=args.inner_draws, seed=args.seed)
    load("analyze_phase_b6_posterior_predictive_design.py", "phase_b7_writer").atomic_json(args.output, output)
    print(json.dumps({"frontier_count": output["frontier_count"], "efficiency_ranking": output["efficiency_ranking_descriptive_only"]}, indent=2))


if __name__ == "__main__":
    main()
