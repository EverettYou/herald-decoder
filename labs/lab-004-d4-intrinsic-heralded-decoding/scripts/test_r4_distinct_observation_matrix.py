from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_r4_distinct_observation_matrix import (  # noqa: E402
    analyze_catalog,
    build_primitive_observation_catalog,
)


CATALOG = build_primitive_observation_catalog()
PAYLOAD = analyze_catalog(CATALOG, (0.1, 0.3, 0.5, 0.6))


def test_r42_complete_mask_accounting_and_terminal_winding_gate() -> None:
    assert CATALOG.nonwinding_mask_count + len(CATALOG.terminal_winding_masks) == 4096
    assert len(CATALOG.terminal_winding_masks) == 123
    assert CATALOG.candidate_observation_pair_count <= 1_000_000
    assert CATALOG.maximum_per_error_normalization_error <= 1e-12


def test_r42_global_evidence_and_sector_posteriors_normalize() -> None:
    assert PAYLOAD["maximum_global_normalization_error"] <= 1e-12
    assert (
        PAYLOAD["posterior_validation"][
            "maximum_sector_posterior_normalization_error"
        ]
        <= 1e-12
    )
    for summary in PAYLOAD["prior_summaries"]:
        assert 0.0 <= summary["mean_nonterminal_bayes_risk"] <= 1.0
        assert 0.0 <= summary["combined_ground_state_relative_bayes_failure_probability"] <= 1.0


def test_r42_reproduces_r40_and_r41_fixtures() -> None:
    checks = PAYLOAD["fixture_checks"]
    assert max(checks["r4_0_maximum_probability_errors"].values()) <= 1e-12
    assert checks["r4_1_candidate_masks_equal_98_140"]
    assert checks["r4_1_one_sector_at_every_prior"]


def test_r42_independent_subset_matches_existing_exact_posterior() -> None:
    for row in PAYLOAD["fixture_checks"]["independent_subset"]:
        assert row["maximum_sector_probability_error"] <= 1e-12
        assert row["bayes_risk_error"] <= 1e-12


def test_r42_reports_set_valued_map_comparison_and_zero_sampling() -> None:
    allowed = {
        "exact_singleton_agreement",
        "overlapping_or_tied_ambiguity",
        "forced_disjoint_disagreement",
    }
    assert set(PAYLOAD["posterior_validation"]["agreement_classes_present"]) <= allowed
    assert PAYLOAD["observation_matrix_digest_sha256"]
    assert PAYLOAD["new_stochastic_samples"] == 0
