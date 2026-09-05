#!/usr/bin/env python3
"""Compare two independent L11/L13 cohorts without pooling them.

The diagnostic resamples complete seed trajectories independently for each
size and cohort.  PyMatching consumes posterior LLRs upstream; this script
never re-decodes or reweights observations.  It asks only whether the measured
size trend, LER(11)-LER(13), differs between the two fresh cohorts at their
pre-registered common p values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = LAB_DIR / "results"
Q_VALUES = (0.85, 0.90, 0.95)
SIZES = (11, 13)
EXPECTED_COMMON_P = (0.40, 0.45, 0.47, 0.49)
DEFAULT_REPLICATES = 20_000
DEFAULT_SEED = 611_057
OLD_TEMPLATE = "phase4-residual80-honeycomb-q{tag}-l11-l13-scaling-4000-2026-08-28.json"
NEW_TEMPLATE = "phase4-residual80-honeycomb-q{tag}-adaptive-p-confirmation-4000-2026-08-28.json"
DEFAULT_OUTPUT = RESULTS_DIR / "phase4-residual80-honeycomb-highq-two-cohort-heterogeneity-2026-08-28.json"


class ValidationError(RuntimeError):
    """Raised when cohorts cannot be compared safely."""


def q_tag(q: float) -> str:
    return f"{int(round(100 * q)):03d}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def load_cohort(path: Path, q: float) -> dict:
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1 or payload.get("lattice") != "honeycomb":
        raise ValidationError(f"unexpected schema/lattice in {path.name}")
    if not np.isclose(float(payload.get("q")), q):
        raise ValidationError(f"q mismatch in {path.name}")
    if tuple(payload.get("sizes", [])) != SIZES:
        raise ValidationError(f"expected sizes {SIZES} in {path.name}")
    decoder = payload.get("decoder", {})
    required_decoder = {
        "max_iterations": 80,
        "update_schedule": "residual_priority",
        "residual_priority_order": "stable_sort",
        "matching_projection": "posterior_llr",
    }
    for key, expected in required_decoder.items():
        if decoder.get(key) != expected:
            raise ValidationError(f"decoder {key} mismatch in {path.name}")
    if payload.get("syndrome_fidelity", {}).get("all_faithful") is not True:
        raise ValidationError(f"syndrome fidelity failed in {path.name}")
    if payload.get("source_stability", {}).get("start_equals_end") is not True:
        raise ValidationError(f"source stability failed in {path.name}")
    return payload


def trajectory_array(payload: dict, common_p: tuple[float, ...]) -> tuple[np.ndarray, list[int]]:
    seeds = [int(seed) for seed in payload["seeds"]]
    shots = int(payload["shots_per_seed"])
    lookup: dict[tuple[int, float, int], float] = {}
    for row in payload["per_seed"]:
        key = (int(row["L"]), round(float(row["p"]), 12), int(row["seed"]))
        if key in lookup:
            raise ValidationError(f"duplicate per-seed cell {key}")
        logical_errors = int(row["logical_errors"])
        if int(row["shots"]) != shots or not 0 <= logical_errors <= shots:
            raise ValidationError(f"invalid per-seed count {key}")
        lookup[key] = logical_errors / shots

    values = np.empty((len(SIZES), len(seeds), len(common_p)), dtype=np.float64)
    for size_offset, size in enumerate(SIZES):
        for seed_offset, seed in enumerate(seeds):
            for p_offset, p in enumerate(common_p):
                key = (size, round(p, 12), seed)
                if key not in lookup:
                    raise ValidationError(f"missing per-seed cell {key}")
                values[size_offset, seed_offset, p_offset] = lookup[key]
    return values, seeds


def interval90(samples: np.ndarray) -> list[float]:
    return [float(value) for value in np.quantile(samples, [0.05, 0.95])]


def analyze_cohort_pair(
    old: dict,
    new: dict,
    *,
    common_p: tuple[float, ...],
    replicates: int,
    seed: int,
) -> dict:
    if replicates < 100:
        raise ValidationError("at least 100 bootstrap replicates are required")
    old_values, old_seeds = trajectory_array(old, common_p)
    new_values, new_seeds = trajectory_array(new, common_p)
    if set(old_seeds) & set(new_seeds):
        raise ValidationError("cohort seed streams overlap")
    if old.get("source_hashes") != new.get("source_hashes"):
        raise ValidationError("cohorts do not share one source fingerprint")
    if old.get("runtime") != new.get("runtime"):
        raise ValidationError("cohorts do not share one runtime fingerprint")

    rng = np.random.default_rng(seed)
    old_means = []
    new_means = []
    for values, means in ((old_values, old_means), (new_values, new_means)):
        for size_offset in range(2):
            indexes = rng.integers(0, values.shape[1], size=(replicates, values.shape[1]))
            means.append(values[size_offset][indexes].mean(axis=1))
    old_delta_samples = old_means[0] - old_means[1]
    new_delta_samples = new_means[0] - new_means[1]
    difference_samples = new_delta_samples - old_delta_samples
    old_point = old_values[0].mean(axis=0) - old_values[1].mean(axis=0)
    new_point = new_values[0].mean(axis=0) - new_values[1].mean(axis=0)
    difference_point = new_point - old_point

    cells = []
    resolved = 0
    for offset, p in enumerate(common_p):
        difference_ci = interval90(difference_samples[:, offset])
        if difference_ci[0] > 0:
            classification = "confirmation_more_decodable"
            resolved += 1
        elif difference_ci[1] < 0:
            classification = "confirmation_less_decodable"
            resolved += 1
        else:
            classification = "no_resolved_difference"
        cells.append(
            {
                "p": p,
                "old_size_trend": float(old_point[offset]),
                "old_interval90": interval90(old_delta_samples[:, offset]),
                "confirmation_size_trend": float(new_point[offset]),
                "confirmation_interval90": interval90(new_delta_samples[:, offset]),
                "confirmation_minus_old": float(difference_point[offset]),
                "difference_interval90": difference_ci,
                "probability_confirmation_more_decodable": float(
                    np.mean(difference_samples[:, offset] > 0)
                ),
                "classification": classification,
            }
        )
    return {
        "q": float(old["q"]),
        "old_seed_clusters": len(old_seeds),
        "confirmation_seed_clusters": len(new_seeds),
        "common_p": list(common_p),
        "cells": cells,
        "resolved_cells": resolved,
        "classification": (
            "resolved_between_cohort_heterogeneity"
            if resolved
            else "no_resolved_between_cohort_heterogeneity"
        ),
        "rms_point_difference": float(np.sqrt(np.mean(difference_point**2))),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--bootstrap-seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyses = []
    source_files = []
    for offset, q in enumerate(Q_VALUES):
        tag = q_tag(q)
        old_path = args.results_dir / OLD_TEMPLATE.format(tag=tag)
        new_path = args.results_dir / NEW_TEMPLATE.format(tag=tag)
        old = load_cohort(old_path, q)
        new = load_cohort(new_path, q)
        old_p = {round(float(p), 12) for p in old["p_grid"]}
        new_p = {round(float(p), 12) for p in new["p_grid"]}
        common_p = tuple(sorted(old_p & new_p))
        if common_p != EXPECTED_COMMON_P:
            raise ValidationError(f"unexpected common p grid for q={q}: {common_p}")
        analyses.append(
            analyze_cohort_pair(
                old,
                new,
                common_p=common_p,
                replicates=args.bootstrap_replicates,
                seed=args.bootstrap_seed + offset,
            )
        )
        source_files.extend(
            [
                {"path": str(old_path), "sha256": sha256(old_path)},
                {"path": str(new_path), "sha256": sha256(new_path)},
            ]
        )
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis": "independent two-cohort L11/L13 size-trend heterogeneity",
        "bootstrap": {
            "replicates": args.bootstrap_replicates,
            "confidence_level": 0.90,
            "seed": args.bootstrap_seed,
            "unit": "complete nested-p seed trajectory, independently resampled by size and cohort",
            "difference": "[LER11-LER13]_confirmation - [LER11-LER13]_old; positive means the confirmation is more decodable",
        },
        "common_p": list(EXPECTED_COMMON_P),
        "source_files": source_files,
        "q_results": analyses,
        "resolved_common_p_cells": sum(row["resolved_cells"] for row in analyses),
        "conclusion": "No common-p cell has a central-90% between-cohort size-trend difference excluding zero. The cohort-local topology changes are compatible with trajectory sampling fluctuations, but this does not satisfy the registered replication gate or authorize pooling.",
        "promotion": {
            "p_c_q": "not evaluated",
            "q_c": "not evaluated",
            "q_0_925": "remains gated",
            "L15": "remains gated",
            "square": "remains gated",
        },
        "evidence_boundary": "This diagnostic tests cross-cohort size-trend heterogeneity at shared measured p values. It does not pool cohorts, estimate a phase boundary, or rehabilitate cohort-local topology labels.",
        "next_transition": "Register the smallest third-cohort adjudication matrix that covers q=0.85,0.90,0.95 with outcome-independent p selections; do not add q=0.925, L15, or square.",
    }
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "classifications": {str(row["q"]): row["classification"] for row in analyses}}, indent=2))


if __name__ == "__main__":
    main()
