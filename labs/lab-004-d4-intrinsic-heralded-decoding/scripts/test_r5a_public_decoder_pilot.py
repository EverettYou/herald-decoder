from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_r5a_public_decoder_pilot import (  # noqa: E402
    analyze_records,
    independent_difference_bootstrap_interval,
    paired_bootstrap_interval,
    wilson_interval,
)
from run_r5a_public_decoder_preflight import trajectory_seeds  # noqa: E402


def test_wilson_interval_contains_empirical_risk() -> None:
    low, high = wilson_interval(30, 100)
    assert low < 0.30 < high


def test_paired_bootstrap_detects_strict_direction() -> None:
    low, high = paired_bootstrap_interval(
        -np.ones(40, dtype=np.float64), replicates=500, seed=9
    )
    assert low == -1.0
    assert high == -1.0


def test_independent_size_bootstrap_uses_upper_minus_lower_sign() -> None:
    low, high = independent_difference_bootstrap_interval(
        np.ones(30), np.zeros(30), replicates=500, seed=11
    )
    assert low == -1.0
    assert high == -1.0


def test_trajectory_seed_is_deterministic_and_cell_specific() -> None:
    first = trajectory_seeds(10, 2, 0.16, 3)
    assert first == trajectory_seeds(10, 2, 0.16, 3)
    assert first != trajectory_seeds(10, 3, 0.16, 3)
    assert first != trajectory_seeds(10, 2, 0.20, 3)


def test_analysis_requires_complete_pairs_and_uses_registered_sign() -> None:
    records = []
    for seed in range(20):
        records.extend(
            [
                {
                    "size": 2,
                    "error_rate": 0.16,
                    "seed_index": seed,
                    "mode": "syndrome_only",
                    "logical_error": True,
                    "stage_outcome": "first_stage_union_winding",
                },
                {
                    "size": 2,
                    "error_rate": 0.16,
                    "seed_index": seed,
                    "mode": "heralded",
                    "logical_error": False,
                    "stage_outcome": "decoded_success",
                },
            ]
        )
    result = analyze_records(records, bootstrap_seed=7)
    assert result["paired_policy_differences"][0]["direction"] == "heralded_lower_risk"
    assert result["paired_policy_differences"][0]["heralded_minus_syndrome_risk"] == -1.0
    assert result["paired_policy_differences"][0]["terminal_physical_winding_histories"] == 0
