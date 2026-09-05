from __future__ import annotations

import inspect

import pytest

from d4_projector_instrument import (
    CHARGE,
    FLUX,
    VACUUM,
    TranslationRequired,
    jing_five_star_false_negative_example,
    perfect_report,
    project_post_action_charge_state,
    project_hidden_state,
    quasi_stabilizer_likelihoods,
    report_distribution,
    report_from_hidden,
    restricted_record_to_commit_request,
    typed_record_to_commit_request,
    typed_postflux_record_to_observation,
)
from d4_spatial_policy import (
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    canonical_digest,
    decode_charge_action,
    decode_flux_action,
)


PREFIX = "a" * 64
ACTION = "b" * 64


def _hidden(labels: dict[int, str] | None = None, *, action: str | None = None):
    return project_hidden_state(
        trial_id="e1-fixture",
        round=0,
        true_labels=labels or {0: FLUX, 1: FLUX, 2: CHARGE, 3: VACUUM},
        bound_action_digest=action,
    )


def test_e1a_projector_partition_rejects_unknown_true_label() -> None:
    with pytest.raises(ValueError, match="true projector label"):
        _hidden({0: "blue_green_confusion"})


def test_e1a_physical_event_changes_private_state_update_digest() -> None:
    first = _hidden({0: VACUUM, 1: VACUUM})
    no_event = project_hidden_state(
        trial_id=first.trial_id,
        round=1,
        true_labels={0: VACUUM, 1: VACUUM},
        previous=first,
    )
    physical_event = project_hidden_state(
        trial_id=first.trial_id,
        round=1,
        true_labels={0: FLUX, 1: FLUX},
        previous=first,
    )
    assert no_event.state_update_digest != physical_event.state_update_digest


def test_e1a_action_binding_changes_update_and_requires_sha_shape() -> None:
    unbound = _hidden({0: VACUUM})
    bound = _hidden({0: VACUUM}, action=ACTION)
    assert unbound.state_update_digest != bound.state_update_digest
    with pytest.raises(ValueError, match="SHA-256"):
        _hidden({0: VACUUM}, action="short")


def test_e1a_post_action_charge_projection_requires_bound_flux_action() -> None:
    with pytest.raises(ValueError, match="requires bound flux action"):
        project_post_action_charge_state(
            trial_id="post-action",
            round=0,
            charge_labels={2: CHARGE, 3: VACUUM},
            bound_action_digest=None,
        )
    projected = project_post_action_charge_state(
        trial_id="post-action",
        round=0,
        charge_labels={2: CHARGE, 3: VACUUM},
        bound_action_digest=ACTION,
    )
    assert projected.bound_action_digest == ACTION


@pytest.mark.parametrize("mode", ["syndrome_only", "heralded"])
def test_e1a_perfect_limit_runs_through_both_public_e0_modes(mode: str) -> None:
    record = perfect_report(_hidden())
    request = restricted_record_to_commit_request(
        record,
        request_id=f"perfect-{mode}",
        size=2,
        mode=mode,
        causal_prefix_digest=PREFIX,
    )
    action = decode_flux_action(request)
    assert request.flux_syndrome_vertices == (0, 1)
    assert action.status == "action"
    assert action.request_id == f"perfect-{mode}"
    if mode == "syndrome_only":
        assert request.initial_charge_measurements == ()
    else:
        assert request.initial_charge_measurements == ((2, 1), (3, 0))


def test_e1b_readout_only_fault_changes_public_report_not_hidden_update() -> None:
    hidden = _hidden()
    perfect = perfect_report(hidden)
    false_negative = report_from_hidden(
        hidden,
        {0: (), 1: (FLUX,), 2: (CHARGE,), 3: ()},
    )
    assert perfect.report_digest != false_negative.report_digest
    assert hidden.state_update_digest == hidden.private_dict()["state_update_digest"]
    assert "true_labels" not in false_negative.public_dict()
    assert "state_update_digest" not in false_negative.public_dict()


@pytest.mark.parametrize("true_label", [VACUUM, FLUX, CHARGE])
def test_e1b_report_distribution_is_normalized_and_has_correct_perfect_limit(
    true_label: str,
) -> None:
    perfect = report_distribution(
        true_label,
        false_negative=0.0,
        false_positive={FLUX: 0.0, CHARGE: 0.0},
    )
    expected = () if true_label == VACUUM else (true_label,)
    assert perfect == {expected: 1.0}

    noisy = report_distribution(
        true_label,
        false_negative=0.2,
        false_positive={FLUX: 0.1, CHARGE: 0.3},
    )
    assert sum(noisy.values()) == pytest.approx(1.0)
    assert all(value >= 0.0 for value in noisy.values())


def test_e1b_multilabel_report_is_retained_but_not_binary_coerced() -> None:
    hidden = _hidden({0: FLUX, 1: FLUX})
    record = report_from_hidden(hidden, {0: (FLUX, CHARGE), 1: (FLUX,)})
    assert record.reported_labels[0] == (0, (CHARGE, FLUX))
    with pytest.raises(TranslationRequired, match="multi-label"):
        restricted_record_to_commit_request(
            record,
            request_id="multi",
            size=2,
            mode="heralded",
            causal_prefix_digest=PREFIX,
        )


def test_e1b_deterministic_replay() -> None:
    first_hidden = _hidden()
    second_hidden = _hidden()
    assert first_hidden == second_hidden
    assert perfect_report(first_hidden) == perfect_report(second_hidden)


def test_e1c_reproduces_source_five_star_false_negative_table() -> None:
    example = jing_five_star_false_negative_example()
    rows = dict(example.rounds)
    assert example.localized_fixture_only
    assert example.semantic == "quasi_stabilizer_time_like_herald"
    assert rows[0] == (FLUX, VACUUM, CHARGE, VACUUM, FLUX)
    assert rows[2] == (FLUX, VACUUM, CHARGE, CHARGE, VACUUM)
    assert rows[3] == (FLUX, VACUUM, CHARGE, CHARGE, FLUX)
    assert rows[4] == rows[3]


def test_e1c_source_likelihood_ordering_is_explicit() -> None:
    result = quasi_stabilizer_likelihoods(
        measurement_error=0.05,
        flux_pair_error=0.05,
        charge_pair_error=0.05,
    )
    assert result == {
        "single_false_negative": 0.05,
        "three_flux_pair_errors": pytest.approx(0.000125),
        "two_flux_plus_charge_pair_errors": pytest.approx(0.000125),
        "single_is_strictly_most_likely": True,
    }


def _multilabel_record():
    hidden = _hidden({0: FLUX, 1: FLUX, 2: VACUUM, 3: VACUUM})
    return report_from_hidden(
        hidden,
        {0: (FLUX, CHARGE), 1: (FLUX,), 2: (CHARGE,), 3: ()},
    )


def test_t1a_syndrome_only_projects_charge_but_preserves_provenance() -> None:
    first_record = _multilabel_record()
    second_record = report_from_hidden(
        _hidden({0: FLUX, 1: FLUX, 2: VACUUM, 3: VACUUM}),
        {0: (FLUX,), 1: (FLUX, CHARGE), 2: (), 3: (CHARGE,)},
    )
    first = typed_record_to_commit_request(
        first_record,
        request_id="t1a",
        size=2,
        mode="syndrome_only",
        scheduler_prefix_digest=PREFIX,
    )
    second = typed_record_to_commit_request(
        second_record,
        request_id="t1a",
        size=2,
        mode="syndrome_only",
        scheduler_prefix_digest=PREFIX,
    )
    assert first.flux_syndrome_vertices == second.flux_syndrome_vertices == (0, 1)
    assert first.initial_charge_measurements == second.initial_charge_measurements == ()
    assert first.causal_prefix_digest != second.causal_prefix_digest
    assert decode_flux_action(first) == decode_flux_action(second)


def test_t1b_heralded_factorizes_multilabel_record_losslessly() -> None:
    record = _multilabel_record()
    request = typed_record_to_commit_request(
        record,
        request_id="t1b",
        size=2,
        mode="heralded",
        scheduler_prefix_digest=PREFIX,
    )
    expected_digest = canonical_digest(
        {
            "schema_version": 1,
            "scheduler_prefix_digest": PREFIX,
            "e1_report_digest": record.report_digest,
            "mode": "heralded",
        }
    )
    manual = D4SpatialCommitRequestV1.from_dict(
        {
            "schema_version": 1,
            "request_id": "t1b",
            "model_id": "paper_periodic_coloured_honeycomb_d4",
            "size": 2,
            "mode": "heralded",
            "decision_round": 0,
            "committed_through_round": 0,
            "flux_syndrome_vertices": [0, 1],
            "initial_charge_measurements": [
                {"vertex": 0, "outcome": 1},
                {"vertex": 1, "outcome": 0},
                {"vertex": 2, "outcome": 1},
                {"vertex": 3, "outcome": 0},
            ],
            "causal_prefix_digest": expected_digest,
        }
    )
    assert request == manual
    assert decode_flux_action(request) == decode_flux_action(manual)


@pytest.mark.parametrize("mode", ["syndrome_only", "heralded"])
def test_t1_perfect_limit_matches_restricted_adapter_action(mode: str) -> None:
    record = perfect_report(_hidden())
    typed = typed_record_to_commit_request(
        record,
        request_id=f"perfect-translation-{mode}",
        size=2,
        mode=mode,
        scheduler_prefix_digest=PREFIX,
    )
    restricted = restricted_record_to_commit_request(
        record,
        request_id=f"perfect-translation-{mode}",
        size=2,
        mode=mode,
        causal_prefix_digest=PREFIX,
    )
    assert decode_flux_action(typed) == decode_flux_action(restricted)


def test_t1c_provenance_replay_and_truth_free_signature() -> None:
    record = _multilabel_record()
    first = typed_record_to_commit_request(
        record,
        request_id="t1c",
        size=2,
        mode="heralded",
        scheduler_prefix_digest=PREFIX,
    )
    replay = typed_record_to_commit_request(
        record,
        request_id="t1c",
        size=2,
        mode="heralded",
        scheduler_prefix_digest=PREFIX,
    )
    changed_prefix = typed_record_to_commit_request(
        record,
        request_id="t1c",
        size=2,
        mode="heralded",
        scheduler_prefix_digest=ACTION,
    )
    assert first == replay
    assert first.causal_prefix_digest != changed_prefix.causal_prefix_digest
    assert set(inspect.signature(typed_record_to_commit_request).parameters) == {
        "record",
        "request_id",
        "size",
        "mode",
        "scheduler_prefix_digest",
    }
    serialized = first.to_dict()
    assert not ({"true_labels", "state_update_digest", "logical_error"} & set(serialized))


def test_t1c_old_rejection_is_adapter_restriction_not_schema_gap() -> None:
    record = _multilabel_record()
    with pytest.raises(TranslationRequired, match="multi-label"):
        restricted_record_to_commit_request(
            record,
            request_id="old-reject",
            size=2,
            mode="heralded",
            causal_prefix_digest=PREFIX,
        )
    translated = typed_record_to_commit_request(
        record,
        request_id="new-accept",
        size=2,
        mode="heralded",
        scheduler_prefix_digest=PREFIX,
    )
    assert translated.flux_syndrome_vertices == (0, 1)
    assert translated.initial_charge_measurements[0] == (0, 1)
    assert decode_flux_action(translated).status == "action"


def _e2a_stage1(mode: str = "heralded"):
    record = perfect_report(_hidden())
    request = typed_record_to_commit_request(
        record,
        request_id=f"e2a-{mode}",
        size=2,
        mode=mode,
        scheduler_prefix_digest=PREFIX,
    )
    return request, decode_flux_action(request)


def _e2a_postflux_record(action_digest: str, labels=None, *, round: int = 0):
    hidden = project_post_action_charge_state(
        trial_id="e2a-postflux",
        round=round,
        charge_labels={0: VACUUM, 2: VACUUM},
        bound_action_digest=action_digest,
    )
    return (
        perfect_report(hidden)
        if labels is None
        else report_from_hidden(hidden, labels)
    )


def test_e2a_action_bound_postflux_adapter_matches_manual_e0_observation() -> None:
    request, flux = _e2a_stage1()
    record = _e2a_postflux_record(flux.action_digest)
    adapted = typed_postflux_record_to_observation(
        record,
        request=request,
        flux_action=flux,
        active_vertices=(0, 2),
        entanglement_pairs=((0, 2),),
    )
    unsigned = {
        "request_id": request.request_id,
        "action_digest": flux.action_digest,
        "observation_round": record.round,
        "measurement_layout": {
            "active_vertices": [0, 2],
            "entanglement_pairs": [[0, 2]],
        },
        "charge_measurements": [
            {"vertex": 0, "outcome": 0},
            {"vertex": 2, "outcome": 0},
        ],
    }
    manual = D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=24,
    )
    assert adapted == manual
    assert decode_charge_action(request, flux, adapted).status == "action"


def test_e2a_rejects_wrong_action_binding_and_noncharge_reports() -> None:
    request, flux = _e2a_stage1()
    wrong_bound = _e2a_postflux_record(ACTION)
    with pytest.raises(ValueError, match="exact flux action"):
        typed_postflux_record_to_observation(
            wrong_bound,
            request=request,
            flux_action=flux,
            active_vertices=(0, 2),
            entanglement_pairs=((0, 2),),
        )

    flux_report = _e2a_postflux_record(
        flux.action_digest,
        {0: (FLUX,), 2: ()},
    )
    with pytest.raises(ValueError, match="charge/vacuum"):
        typed_postflux_record_to_observation(
            flux_report,
            request=request,
            flux_action=flux,
            active_vertices=(0, 2),
            entanglement_pairs=((0, 2),),
        )

    multi_report = _e2a_postflux_record(
        flux.action_digest,
        {0: (CHARGE, FLUX), 2: ()},
    )
    with pytest.raises(ValueError, match="charge/vacuum"):
        typed_postflux_record_to_observation(
            multi_report,
            request=request,
            flux_action=flux,
            active_vertices=(0, 2),
            entanglement_pairs=((0, 2),),
        )


def test_e2a_rejects_mismatched_layout_and_predating_report() -> None:
    request, flux = _e2a_stage1()
    record = _e2a_postflux_record(flux.action_digest)
    with pytest.raises(ValueError, match="exactly the active"):
        typed_postflux_record_to_observation(
            record,
            request=request,
            flux_action=flux,
            active_vertices=(0,),
            entanglement_pairs=(),
        )

    later_request_payload = request.to_dict()
    later_request_payload["decision_round"] = 1
    later_request_payload["committed_through_round"] = 1
    later_request = D4SpatialCommitRequestV1.from_dict(later_request_payload)
    later_flux = decode_flux_action(later_request)
    predating = _e2a_postflux_record(later_flux.action_digest, round=0)
    with pytest.raises(ValueError, match="predates"):
        typed_postflux_record_to_observation(
            predating,
            request=later_request,
            flux_action=later_flux,
            active_vertices=(0, 2),
            entanglement_pairs=((0, 2),),
        )


def test_e2a_public_adapter_signature_excludes_truth_and_hidden_state() -> None:
    assert set(inspect.signature(typed_postflux_record_to_observation).parameters) == {
        "record",
        "request",
        "flux_action",
        "active_vertices",
        "entanglement_pairs",
    }
