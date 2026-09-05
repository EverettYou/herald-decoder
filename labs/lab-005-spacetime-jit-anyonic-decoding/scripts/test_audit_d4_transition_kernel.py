from __future__ import annotations

import json

import numpy as np

from audit_d4_transition_kernel import build_transition_kernel_audit


def _audit() -> dict:
    return build_transition_kernel_audit()


def test_k1_k4_factor_matrix_is_complete_and_explicitly_incomplete() -> None:
    audit = _audit()
    factors = {factor["factor"]: factor for factor in audit["factors"]}
    assert set(factors) == {
        "K1-physical-state-evolution",
        "K2-public-measurement-kernel",
        "K3-action-conditioned-postflux-kernel",
        "K4-private-logical-scorer",
    }
    assert factors["K1-physical-state-evolution"]["status"] == "missing"
    assert factors["K2-public-measurement-kernel"]["status"] == "localized_only"
    assert factors["K3-action-conditioned-postflux-kernel"]["status"] == "missing"
    assert factors["K4-private-logical-scorer"]["status"] == "partial"


def test_available_report_laws_are_exactly_normalized() -> None:
    normalization = _audit()["normalization"]
    assert all(
        np.isclose(value, 1.0)
        for value in normalization["e1_local_report_row_sums"].values()
    )
    assert np.allclose(normalization["generic_categorical_row_sums"], 1.0)


def test_static_spatial_sampler_does_not_claim_cross_round_state() -> None:
    parameters = _audit()["interface_signatures"]["static_spatial_observation"]
    assert parameters == ["lattice", "error_edges", "seed", "logical_sector"]
    assert "previous" not in parameters
    assert "action" not in parameters


def test_e2_keeps_physical_postflux_generation_external() -> None:
    parameters = _audit()["interface_signatures"]["e2_completion_runner"]
    assert "postflux_provider" in parameters
    factor = next(
        value
        for value in _audit()["factors"]
        if value["factor"] == "K3-action-conditioned-postflux-kernel"
    )
    assert factor["status"] == "missing"


def test_private_scorers_do_not_invent_repeated_history_truth() -> None:
    signatures = _audit()["interface_signatures"]
    assert signatures["single_flux_truth_scorer"] == [
        "lattice",
        "physical_error",
        "edge_weights",
    ]
    assert "logical_failure_truth" in signatures["frozen_transition_scorer"]


def test_audit_is_json_safe_and_contains_no_samples() -> None:
    audit = _audit()
    assert audit["sampling"] == 0
    assert audit["bounded_checks_can_discriminate_models"] is False
    assert audit["earliest_missing_dependency"] == "K1-physical-state-evolution"
    assert json.loads(json.dumps(audit, sort_keys=True)) == audit
