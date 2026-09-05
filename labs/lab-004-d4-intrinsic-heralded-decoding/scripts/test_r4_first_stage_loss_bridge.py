from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_r4_distinct_observation_matrix import (  # noqa: E402
    build_primitive_observation_catalog,
)
from run_r4_first_stage_loss_bridge import (  # noqa: E402
    LAB_DIR,
    analyze_first_stage_loss_bridge,
)


CATALOG = build_primitive_observation_catalog()
R43 = json.loads(
    (LAB_DIR / "results/r4-nonwinding-information-hierarchy-audit.json").read_text()
)
PAYLOAD = analyze_first_stage_loss_bridge(
    CATALOG,
    (0.1, 0.3, 0.5, 0.6),
    R43,
    candidate_action_guard=2_000_000,
)


def test_r44_complete_action_and_observation_matrix() -> None:
    matrix = PAYLOAD["matrix"]
    assert matrix["o0_observation_count"] == 128
    assert matrix["o2_observation_count"] == 16230
    assert matrix["action_counts_per_syndrome"] == [32]
    assert matrix["candidate_action_evaluations"] <= 2_000_000


def test_r44_actions_are_faithful_and_public_decisions_are_members() -> None:
    checks = PAYLOAD["validation"]
    assert checks["maximum_action_boundary_error"] == 0
    assert checks["syndrome_only_action_membership_failures"] == 0
    assert checks["heralded_action_membership_failures"] == 0
    assert checks["production_decoder_truth_inputs"] == []


def test_r44_evidence_normalizes_and_recovers_r43_sector_risks() -> None:
    checks = PAYLOAD["validation"]
    assert checks["maximum_o0_vs_marginalized_o2_flux_evidence_error"] <= 1e-12
    assert checks["maximum_global_normalization_error"] <= 1e-12
    assert checks["maximum_r4_3_xor_sector_risk_recovery_error"] <= 1e-12


def test_r44_exact_union_loss_is_a_lower_bound_on_matched_production() -> None:
    assert PAYLOAD["validation"]["maximum_exact_lower_bound_violation"] <= 1e-12
    for row in PAYLOAD["prior_summaries"]:
        assert row["o0_flux_only"]["algorithmic_excess_risk"] >= -1e-12
        assert row["o2_flux_and_charge"]["algorithmic_excess_risk"] >= -1e-12


def test_r44_explicitly_tests_xor_sector_sufficiency_and_excludes_second_round() -> None:
    matrix = PAYLOAD["matrix"]
    assert "o0_xor_sector_loss_insufficient_observation_count" in matrix
    assert "o2_xor_sector_loss_insufficient_observation_count" in matrix
    assert not PAYLOAD["validation"]["postflux_second_measurement_used"]
    assert PAYLOAD["new_stochastic_samples"] == 0
