#!/usr/bin/env python3
"""Render the honeycomb Bayesian fuzzy linear-trend phase map."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap, TwoSlopeNorm


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase2-residual80-q-skeleton-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.png"
CURVATURE_GATE = 0.95


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def cell_edges(values: list[float], lower: float | None = None, upper: float | None = None) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    midpoints = (array[:-1] + array[1:]) / 2.0
    edges = np.concatenate([[array[0] - (midpoints[0] - array[0])], midpoints, [array[-1] + (array[-1] - midpoints[-1])]])
    if lower is not None:
        edges[0] = lower
    if upper is not None:
        edges[-1] = upper
    return edges


def gray_measurement_route(trend: dict, *, curvature_gate: float = CURVATURE_GATE) -> str | None:
    """Route unresolved cells using a posterior shape diagnostic, not a phase label."""
    if trend["classification"] != "unresolved":
        return None
    sensitivity = trend["sensitivity"]
    curvature_probability = max(
        sensitivity["posterior_probability_midpoint_above_endpoint_chord"],
        sensitivity["posterior_probability_midpoint_below_endpoint_chord"],
    )
    if curvature_probability >= curvature_gate:
        return "add_L5_L13_distance_leverage"
    return "more_shots_existing_L7_L9_L11_first"


def analyze_cell(payload: dict, *, p: float, sizes: list[int], fuzzy, seed: int) -> dict:
    summaries = {(int(row["L"]), round(float(row["p"]), 12)): row for row in payload["summaries"]}
    rows = [summaries[(size, round(p, 12))] for size in sizes]
    errors = np.asarray([int(row["logical_errors"]) for row in rows])
    shots = np.asarray([int(row["shots"]) for row in rows])
    primary = fuzzy.posterior_fuzzy_linear_trend(errors, shots, np.asarray(sizes), seed=seed)
    uniform = fuzzy.posterior_fuzzy_linear_trend(
        errors,
        shots,
        np.asarray(sizes),
        prior_alpha=1.0,
        prior_beta=1.0,
        seed=seed + 1_000_000,
    )
    primary["p"] = p
    primary["logical_errors"] = errors.tolist()
    primary["shots"] = shots.tolist()
    primary["uniform_prior_sensitivity"] = uniform
    primary["jeffreys_classification"] = primary["classification"]
    primary["prior_sensitivity_status"] = "stable"
    if primary["classification"] != uniform["classification"]:
        primary["classification"] = "unresolved"
        primary["prior_sensitivity_status"] = "classification_changed_conservative_gray"
    primary["gray_measurement_route"] = gray_measurement_route(primary)
    return primary


def plot_map(analyses: list[dict], p_values: list[float], destination: Path) -> None:
    q_values = [row["q"] for row in analyses]
    cells = [[cell for cell in row["cells"]] for row in analyses]
    evidence = np.asarray(
        [
            [
                cell["posterior_log_odds_upward_vs_downward"]
                if cell["posterior_log_odds_upward_vs_downward"] is not None
                else cell["posterior_log_odds_censoring"]["bound"]
                for cell in row
            ]
            for row in cells
        ]
    )
    q_edges = cell_edges(q_values, 0.0, 1.0)
    p_edges = cell_edges(p_values)
    figure, axis = plt.subplots(figsize=(8.8, 7.2), constrained_layout=True)
    evidence_cmap = LinearSegmentedColormap.from_list("trend_evidence", ["#16834A", "#F1F3F4", "#C63F32"])
    mesh = axis.pcolormesh(p_edges, q_edges, np.clip(evidence, -8.0, 8.0), cmap=evidence_cmap, norm=TwoSlopeNorm(vmin=-8.0, vcenter=0.0, vmax=8.0), shading="flat", edgecolors="white", linewidth=0.45)
    axis.set(
        title=r"$\log\!\left[\Pr(\mathrm{upward}\mid\mathrm{data}) / \Pr(\mathrm{downward}\mid\mathrm{data})\right]$",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(p_edges[0], p_edges[-1]),
        ylim=(0.0, 1.0),
    )
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0.0, 1.01, 0.1))
    axis.tick_params(labelsize=12)
    axis.xaxis.label.set_size(14)
    axis.yaxis.label.set_size(14)
    axis.title.set_size(16)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.025)
    colorbar.set_label("log likelihood ratio  (clipped at +/-8)", fontsize=13)
    colorbar.ax.tick_params(labelsize=11)
    figure.suptitle("Honeycomb phase diagram · Bayesian fuzzy trend", fontsize=16)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    validator = load_module("analyze_phase2_scout.py", "phase2_validator_fuzzy")
    fuzzy = load_module("analyze_phase_b1_bayesian_fuzzy_trend.py", "phase_b1_fuzzy_map")
    manifest = validator.load_manifest(args.manifest)
    if manifest["lattices"] != ["honeycomb"] or manifest["sizes"] != [7, 9, 11]:
        raise SystemExit("fuzzy trend map requires the honeycomb L=7,9,11 skeleton")
    paths = validator.discover_shards(LAB_DIR / "results", manifest)
    current_sources = {name: validator.sha256(path) for name, path in validator.SOURCE_FILES.items()}
    runtime = sources = None
    analyses = []
    validated = []
    p_values = [float(value) for value in manifest["p_grid"]["honeycomb"]]
    for q_offset, (_, path) in enumerate(sorted(paths.items())):
        payload = validator.validate_shard(path, manifest, lab_dir=LAB_DIR, expected_runtime=runtime, expected_sources=sources, current_sources=current_sources, validate_raw=False)
        runtime = payload["runtime"] if runtime is None else runtime
        sources = payload["source_hashes"] if sources is None else sources
        cells = [analyze_cell(payload, p=p, sizes=[7, 9, 11], fuzzy=fuzzy, seed=881000 + q_offset * 100 + p_offset) for p_offset, p in enumerate(p_values)]
        analyses.append({"q": float(payload["q"]), "cells": cells})
        validated.append(str(path))
    plot_map(analyses, p_values, args.figure)
    counts = {label: sum(cell["classification"] == label for row in analyses for cell in row["cells"]) for label in ("decodable", "undecodable", "unresolved")}
    gray_routes = {
        route: sum(cell["gray_measurement_route"] == route for row in analyses for cell in row["cells"])
        for route in ("more_shots_existing_L7_L9_L11_first", "add_L5_L13_distance_leverage")
    }
    prior_sensitive = sum(cell["prior_sensitivity_status"] != "stable" for row in analyses for cell in row["cells"])
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "campaign": manifest["campaign"],
        "sizes": [7, 9, 11],
        "definition": "Bayesian posterior sign of the OLS linear projection slope of latent LER against code distance",
        "classification_threshold": 0.90,
        "prior_sensitivity_gate": "A Jeffreys-prior resolved cell is conservatively gray when the uniform-prior sensitivity classification differs.",
        "counts": counts,
        "gray_measurement_routes": gray_routes,
        "gray_routing_rule": "For unresolved cells, posterior midpoint curvature >=0.95 routes to L5/L13 distance leverage; otherwise collect more L7/L9/L11 shots first. This is a measurement diagnostic, not a phase label.",
        "prior_sensitive_classifications": prior_sensitive,
        "analyses": analyses,
        "validated_summaries": validated,
        "provenance": {
            "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
            "analyzer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
            "fuzzy_trend_core": {"path": str(Path(__file__).with_name("analyze_phase_b1_bayesian_fuzzy_trend.py")), "sha256": sha256(Path(__file__).with_name("analyze_phase_b1_bayesian_fuzzy_trend.py"))},
        },
        "figure": str(args.figure),
        "crossing_statistic_used": False,
        "evidence_boundary": "Finite-window L=7,9,11 decoder-specific trend map; no asymptotic phase boundary or critical exponent.",
    }
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "figure": str(args.figure), "counts": counts, "gray_measurement_routes": gray_routes, "prior_sensitive_classifications": prior_sensitive}, indent=2))


if __name__ == "__main__":
    main()
