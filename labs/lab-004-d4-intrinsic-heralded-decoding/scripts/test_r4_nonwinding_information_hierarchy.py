from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_r4_distinct_observation_matrix import (  # noqa: E402
    build_primitive_observation_catalog,
)
from run_r4_nonwinding_information_hierarchy import (  # noqa: E402
    LAB_DIR,
    analyze_information_hierarchy,
)


CATALOG = build_primitive_observation_catalog()
R42_AUDIT = json.loads(
    (LAB_DIR / "results/r4-distinct-observation-matrix-audit.json").read_text()
)
PAYLOAD = analyze_information_hierarchy(
    CATALOG, (0.1, 0.3, 0.5, 0.6), R42_AUDIT
)


def test_r43_o2_to_o0_mapping_is_total_and_coarse_grained() -> None:
    hierarchy = PAYLOAD["observation_hierarchy"]
    assert hierarchy["o2_distinct_flux_charge_observations"] == 16230
    assert 0 < hierarchy["o0_distinct_flux_observations"] < 16230
    assert hierarchy["o2_to_o0_mapping_is_total_and_single_valued"]
    assert not hierarchy["terminal_winding_status_is_decoder_visible"]


def test_r43_evidence_and_posteriors_are_conserved() -> None:
    checks = PAYLOAD["validation"]
    assert checks["maximum_o0_posterior_normalization_error"] <= 1e-12
    assert checks["maximum_o2_posterior_normalization_error"] <= 1e-12
    assert checks["maximum_per_flux_sector_evidence_conservation_error"] <= 1e-12
    assert checks["maximum_total_nonwinding_mass_conservation_error"] <= 1e-12


def test_r43_reproduces_r42_o2_aggregates() -> None:
    assert PAYLOAD["validation"]["maximum_r4_2_aggregate_recovery_error"] <= 1e-12


def test_r43_information_budget_is_monotone() -> None:
    checks = PAYLOAD["validation"]
    assert checks["all_bayes_risk_inequalities_pass"]
    assert checks["all_conditional_entropy_inequalities_pass"]
    for row in PAYLOAD["prior_summaries"]:
        assert row["fusion_charge_increment"]["bayes_risk_reduction"] >= -1e-12
        assert (
            row["fusion_charge_increment"]["conditional_mutual_information_bits"]
            >= -1e-12
        )


def test_r43_preserves_terminal_separation_and_zero_sampling() -> None:
    assert PAYLOAD["new_stochastic_samples"] == 0
    assert "nonwinding-conditioned" in PAYLOAD["claim_boundary"]
