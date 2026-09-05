from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_spatial_policy import (  # noqa: E402
    MODEL_ID,
    D4FluxActionV1,
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    canonical_digest,
    causal_prefix_digest,
    decode_charge_action,
    decode_flux_action,
)
from d4_matching import edge_chain_boundary  # noqa: E402
from d4_honeycomb import BLUE, paper_periodic_honeycomb  # noqa: E402
from d4_charge import (  # noqa: E402
    build_charge_lattice,
    charge_chain_boundary,
    effective_error_from_relations,
)
from spacetime_record import build_record_from_fault_masks  # noqa: E402


def _prefix_digest() -> str:
    truth = np.zeros((3, 2), dtype=bool)
    herald = np.zeros((3, 1), dtype=bool)
    record = build_record_from_fault_masks(truth, truth, herald, herald)
    return causal_prefix_digest(record.causal_prefix(1))


def _request(mode: str = "syndrome_only") -> D4SpatialCommitRequestV1:
    payload = {
        "schema_version": 1,
        "request_id": "tiny-commit-1",
        "model_id": MODEL_ID,
        "size": 2,
        "mode": mode,
        "decision_round": 1,
        "committed_through_round": 1,
        "flux_syndrome_vertices": [0, 1],
        "initial_charge_measurements": (
            [] if mode == "syndrome_only" else [{"vertex": 0, "outcome": 1}]
        ),
        "causal_prefix_digest": _prefix_digest(),
    }
    return D4SpatialCommitRequestV1.from_dict(payload)


def _empty_post(request, flux_action, *, action_digest: str | None = None):
    unsigned = {
        "request_id": request.request_id,
        "action_digest": action_digest or flux_action.action_digest,
        "observation_round": request.decision_round,
        "measurement_layout": {"active_vertices": [], "entanglement_pairs": []},
        "charge_measurements": [],
    }
    return D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=paper_periodic_honeycomb(request.size).vertex_count,
    )


def test_stage_one_is_observation_only_syndrome_faithful_and_deterministic() -> None:
    request = _request()
    first = decode_flux_action(request)
    second = decode_flux_action(request)
    assert first == second
    lattice = paper_periodic_honeycomb(request.size)
    correction = np.zeros(lattice.edge_count, dtype=np.uint8)
    correction[list(first.correction_edges)] = 1
    assert tuple(np.flatnonzero(edge_chain_boundary(lattice, correction))) == (
        request.flux_syndrome_vertices
    )
    assert set(first.to_dict()) == {
        "request_id",
        "status",
        "correction_edges",
        "objective_weight",
        "policy_source_digest",
        "action_digest",
    }
    assert D4FluxActionV1.from_dict(first.to_dict()) == first


def test_causal_prefix_digest_ignores_different_future_rounds() -> None:
    truth_a = np.zeros((4, 2), dtype=bool)
    truth_b = truth_a.copy()
    truth_b[2:, 0] = True
    herald = np.zeros((4, 1), dtype=bool)
    record_a = build_record_from_fault_masks(truth_a, np.zeros_like(truth_a), herald, herald)
    record_b = build_record_from_fault_masks(truth_b, np.zeros_like(truth_b), herald, herald)
    assert causal_prefix_digest(record_a.causal_prefix(1)) == causal_prefix_digest(
        record_b.causal_prefix(1)
    )


def test_forbidden_or_future_fields_are_rejected() -> None:
    payload = _request().to_dict()
    payload["physical_error_edges"] = [0]
    with pytest.raises(ValueError, match="extra"):
        D4SpatialCommitRequestV1.from_dict(payload)
    payload = _request().to_dict()
    payload["committed_through_round"] = 2
    with pytest.raises(ValueError, match="committed causal round"):
        D4SpatialCommitRequestV1.from_dict(payload)


def test_heralded_request_uses_sparse_binary_measurements_without_sentinel() -> None:
    request = _request("heralded")
    assert request.initial_charge_measurements == ((0, 1),)
    assert all(
        item["outcome"] in (0, 1)
        for item in request.to_dict()["initial_charge_measurements"]
    )
    assert decode_flux_action(request).status == "action"


def test_post_action_digest_binding_and_empty_supported_charge_action() -> None:
    request = _request()
    flux = decode_flux_action(request)
    post = _empty_post(request, flux)
    first = decode_charge_action(request, flux, post)
    second = decode_charge_action(request, flux, post)
    assert first == second
    assert first.blue_correction_edges == ()
    assert first.green_correction_edges == ()
    with pytest.raises(ValueError, match="not bound"):
        bad = _empty_post(request, flux, action_digest="0" * 64)
        decode_charge_action(request, flux, bad)


def test_post_action_support_rejects_odd_component_parity() -> None:
    request = _request()
    flux = decode_flux_action(request)
    unsigned = {
        "request_id": request.request_id,
        "action_digest": flux.action_digest,
        "observation_round": request.decision_round,
        "measurement_layout": {"active_vertices": [0], "entanglement_pairs": []},
        "charge_measurements": [{"vertex": 0, "outcome": 1}],
    }
    post = D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=paper_periodic_honeycomb(request.size).vertex_count,
    )
    with pytest.raises(ValueError, match="parity support"):
        decode_charge_action(request, flux, post)


def test_nonempty_post_action_charge_correction_is_syndrome_faithful() -> None:
    request = _request()
    flux = decode_flux_action(request)
    lattice = paper_periodic_honeycomb(request.size)
    blue = build_charge_lattice(lattice, BLUE)
    left, right = (int(value) for value in blue.edge_global_vertices[0])
    pair = [min(left, right), max(left, right)]
    unsigned = {
        "request_id": request.request_id,
        "action_digest": flux.action_digest,
        "observation_round": request.decision_round,
        "measurement_layout": {
            "active_vertices": pair,
            "entanglement_pairs": [pair],
        },
        "charge_measurements": [
            {"vertex": pair[0], "outcome": 1},
            {"vertex": pair[1], "outcome": 1},
        ],
    }
    post = D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=lattice.vertex_count,
    )
    action = decode_charge_action(request, flux, post)
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[pair] = 1
    effective = effective_error_from_relations(
        blue, (tuple(pair),), charge, tuple(pair)
    )
    correction = np.zeros(blue.edge_count, dtype=np.uint8)
    correction[list(action.blue_correction_edges)] = 1
    assert np.array_equal(
        charge_chain_boundary(blue, correction),
        charge_chain_boundary(blue, effective),
    )


def test_public_entry_points_have_no_truth_argument() -> None:
    assert tuple(inspect.signature(decode_flux_action).parameters) == ("request",)
    assert tuple(inspect.signature(decode_charge_action).parameters) == (
        "request",
        "flux_action",
        "observation",
    )
