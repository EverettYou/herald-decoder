from preflight_r6af_two_stage_public_charge import build_preflight


def test_r6af_localizes_public_charge_interface_before_sampling():
    result = build_preflight()
    assert result["new_production_trajectories"] == 0
    assert result["gates"]["first_record_signal_only"]
    assert result["gates"]["ambiguous_zero_present"]
    assert result["gates"]["first_actions_disagree_on_frozen_fixture"]
    assert result["gates"]["second_channel_is_action_conditioned"]
    assert result["gates"]["own_support_valid"]
    assert result["gates"]["zero_fixture_decodes_without_loss"]
    assert result["gates"]["full_binary_public_second_record"]
    assert result["gates"]["charge_action_excludes_hidden_relations"]
    assert result["gates"]["wrong_action_support_rejected"]
    assert result["gates"]["public_transcript_excludes_private_truth"]
    assert result["status"] == "passed"
    assert result["failed_gates"] == []
    assert result["pilot_registration_authorized"]
    assert not result["production_sampling_authorized"]


def test_r6af_uses_common_exogenous_key_without_forcing_equal_records():
    result = build_preflight()
    arms = result["fixture"]["arms"]
    assert result["gates"]["same_second_exogenous_key_used"]
    assert arms["O0"]["public_second_record"] != arms["O2"]["public_second_record"]
    assert arms["O0"]["active_vertices"] != arms["O2"]["active_vertices"]
