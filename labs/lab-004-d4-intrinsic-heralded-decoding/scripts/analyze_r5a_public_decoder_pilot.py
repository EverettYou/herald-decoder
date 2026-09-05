#!/usr/bin/env python3
"""Analyze the registered R5a matched public-decoder pilot.

The analysis deliberately reports finite-size risks and paired differences.
It does not fit crossings, thresholds, phase labels, or extrapolations.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
from typing import Iterable

import numpy as np


def wilson_interval(failures: int, total: int, confidence: float = 0.90) -> tuple[float, float]:
    if total <= 0 or failures < 0 or failures > total:
        raise ValueError("invalid binomial counts")
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    estimate = failures / total
    denominator = 1.0 + z * z / total
    center = (estimate + z * z / (2.0 * total)) / denominator
    radius = z * math.sqrt(
        estimate * (1.0 - estimate) / total + z * z / (4.0 * total * total)
    ) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def paired_bootstrap_interval(
    differences: np.ndarray,
    *,
    confidence: float = 0.90,
    replicates: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    values = np.asarray(differences, dtype=np.float64)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("paired differences must be a nonempty vector")
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=np.float64)
    chunk = 500
    written = 0
    while written < replicates:
        count = min(chunk, replicates - written)
        indices = rng.integers(0, len(values), size=(count, len(values)))
        means[written : written + count] = np.mean(values[indices], axis=1)
        written += count
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(means, (tail, 1.0 - tail))
    return float(low), float(high)


def independent_difference_bootstrap_interval(
    left: np.ndarray,
    right: np.ndarray,
    *,
    confidence: float = 0.90,
    replicates: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """Bootstrap ``mean(right)-mean(left)`` for independent size cohorts."""

    left_values = np.asarray(left, dtype=np.float64)
    right_values = np.asarray(right, dtype=np.float64)
    if left_values.ndim != 1 or right_values.ndim != 1:
        raise ValueError("independent samples must be vectors")
    if len(left_values) == 0 or len(right_values) == 0:
        raise ValueError("independent samples must be nonempty")
    rng = np.random.default_rng(seed)
    differences = np.empty(replicates, dtype=np.float64)
    chunk = 500
    written = 0
    while written < replicates:
        count = min(chunk, replicates - written)
        left_indices = rng.integers(0, len(left_values), size=(count, len(left_values)))
        right_indices = rng.integers(0, len(right_values), size=(count, len(right_values)))
        differences[written : written + count] = (
            np.mean(right_values[right_indices], axis=1)
            - np.mean(left_values[left_indices], axis=1)
        )
        written += count
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(differences, (tail, 1.0 - tail))
    return float(low), float(high)


def read_records(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def analyze_records(records: Iterable[dict], *, bootstrap_seed: int) -> dict:
    rows = list(records)
    grouped: dict[tuple[int, float, str], list[dict]] = defaultdict(list)
    paired: dict[tuple[int, float], dict[int, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for row in rows:
        key = (int(row["size"]), float(row["error_rate"]), str(row["mode"]))
        grouped[key].append(row)
        paired[(key[0], key[1])][int(row["seed_index"])][key[2]] = row

    cell_results = []
    for (size, error_rate, mode), cell in sorted(grouped.items()):
        failures = sum(bool(row["logical_error"]) for row in cell)
        low, high = wilson_interval(failures, len(cell))
        stages: dict[str, int] = defaultdict(int)
        for row in cell:
            stages[str(row["stage_outcome"])] += 1
        cell_results.append(
            {
                "size": size,
                "error_rate": error_rate,
                "mode": mode,
                "histories": len(cell),
                "logical_failures": failures,
                "logical_risk": failures / len(cell),
                "wilson_90": [low, high],
                "stage_counts": dict(sorted(stages.items())),
            }
        )

    paired_results = []
    for pair_index, ((size, error_rate), by_seed) in enumerate(sorted(paired.items())):
        differences = []
        decoder_contingent_differences = []
        terminal_histories = 0
        for seed_index, modes in sorted(by_seed.items()):
            if set(modes) != {"syndrome_only", "heralded"}:
                raise ValueError(f"incomplete policy pair at {(size, error_rate, seed_index)}")
            difference = (
                int(bool(modes["heralded"]["logical_error"]))
                - int(bool(modes["syndrome_only"]["logical_error"]))
            )
            differences.append(difference)
            terminal_flags = {
                str(modes[mode]["stage_outcome"]) == "terminal_physical_winding"
                for mode in ("syndrome_only", "heralded")
            }
            if len(terminal_flags) != 1:
                raise ValueError(
                    f"terminal status differs across paired policies at {(size, error_rate, seed_index)}"
                )
            if True in terminal_flags:
                terminal_histories += 1
            else:
                decoder_contingent_differences.append(difference)
        values = np.asarray(differences, dtype=np.float64)
        low, high = paired_bootstrap_interval(
            values, seed=bootstrap_seed + pair_index
        )
        direction = "unresolved"
        if high < 0.0:
            direction = "heralded_lower_risk"
        elif low > 0.0:
            direction = "heralded_higher_risk"
        result = {
                "size": size,
                "error_rate": error_rate,
                "paired_histories": len(values),
                "heralded_minus_syndrome_risk": float(np.mean(values)),
                "seed_cluster_bootstrap_90": [low, high],
                "direction": direction,
                "terminal_physical_winding_histories": terminal_histories,
            }
        if decoder_contingent_differences:
            contingent = np.asarray(decoder_contingent_differences, dtype=np.float64)
            contingent_low, contingent_high = paired_bootstrap_interval(
                contingent, seed=bootstrap_seed + 10_000 + pair_index
            )
            result["decoder_contingent_sensitivity"] = {
                "histories": len(contingent),
                "heralded_minus_syndrome_risk": float(np.mean(contingent)),
                "seed_cluster_bootstrap_90": [contingent_low, contingent_high],
            }
        paired_results.append(result)

    size_results = []
    rates = sorted({float(row["error_rate"]) for row in rows})
    modes = sorted({str(row["mode"]) for row in rows})
    for size_index, (error_rate, mode) in enumerate(
        (pair for pair in ((p, m) for p in rates for m in modes))
    ):
        lower = grouped.get((2, error_rate, mode), [])
        upper = grouped.get((3, error_rate, mode), [])
        if not lower or not upper:
            continue
        lower_values = np.asarray(
            [int(bool(row["logical_error"])) for row in lower], dtype=np.float64
        )
        upper_values = np.asarray(
            [int(bool(row["logical_error"])) for row in upper], dtype=np.float64
        )
        low, high = independent_difference_bootstrap_interval(
            lower_values,
            upper_values,
            seed=bootstrap_seed + 20_000 + size_index,
        )
        direction = "unresolved"
        if high < 0.0:
            direction = "risk_decreases_with_size"
        elif low > 0.0:
            direction = "risk_increases_with_size"
        size_results.append(
            {
                "error_rate": error_rate,
                "mode": mode,
                "lower_size": 2,
                "upper_size": 3,
                "histories_per_size": [len(lower_values), len(upper_values)],
                "upper_minus_lower_risk": float(
                    np.mean(upper_values) - np.mean(lower_values)
                ),
                "independent_seed_cluster_bootstrap_90": [low, high],
                "direction": direction,
            }
        )

    return {
        "status": "finite_size_public_decoder_analysis",
        "cells": cell_results,
        "paired_policy_differences": paired_results,
        "independent_size_differences": size_results,
        "claim_boundary": "Finite-size public-policy risks and paired differences only; no crossing, threshold, phase, exact larger-lattice optimum, noisy-measurement, or fault-tolerance claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--bootstrap-seed", type=int, default=5_004_005)
    args = parser.parse_args()
    result = analyze_records(read_records(args.records), bootstrap_seed=args.bootstrap_seed)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
