import numpy as np

from run_r6af_two_stage_public_charge_pilot import (
    exact_discordance_p_value,
    paired_bootstrap_interval,
    structural_gates,
    trajectory_keys,
    trajectory_row,
    wilson_interval,
)


def test_registered_key_streams_are_deterministic_and_distinct():
    first = trajectory_keys(68615, 3, 0.19, 7)
    assert first == trajectory_keys(68615, 3, 0.19, 7)
    assert len(set(first)) == 3
    assert first != trajectory_keys(68615, 3, 0.19, 8)


def test_zero_and_small_history_gates_are_replayable():
    assert all(structural_gates().values())
    first = trajectory_row(size=3, error_rate=0.19, index=0, salt=68615)
    assert first == trajectory_row(size=3, error_rate=0.19, index=0, salt=68615)
    assert first["arms"]["O0"]["public_transcript"]["first_record"] == first[
        "arms"
    ]["O2"]["public_transcript"]["first_record"]


def test_registered_interval_helpers_cover_limiting_cases():
    assert wilson_interval(0, 10)[0] == 0.0
    assert wilson_interval(10, 10)[1] == 1.0
    assert exact_discordance_p_value(0, 0) == 1.0
    assert exact_discordance_p_value(5, 0) == 0.0625
    values = np.asarray([-1, -1, 0, 0, 0], dtype=np.int8)
    interval = paired_bootstrap_interval(
        values, size=3, error_rate=0.19, salt=68616, replicates=1000
    )
    assert interval[0] <= float(np.mean(values)) <= interval[1]
