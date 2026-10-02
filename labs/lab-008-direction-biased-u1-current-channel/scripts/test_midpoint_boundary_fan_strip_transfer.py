"""Tests for exact width-three strip embedding and transfer controls."""

from audit_midpoint_boundary_fan_strip_transfer import (
    charge_transfer,
    direct_control,
    selector_transfer_profile,
    width_three_strip,
)


def test_embedded_graph_and_direct_controls() -> None:
    strip = width_three_strip(4)
    assert len(strip.vertices) == 12
    assert len(strip.edges) == 13
    assert len(strip.detector_vertices) == 6
    assert len(strip.logical_edges) == 3
    w3, w4 = direct_control(3), direct_control(4)
    assert w3["kappa_exact"] == "11/9"
    assert w4["physical_majority_domain_states"] == 3926
    assert w4["selector_second_moment"] == 7968
    assert w4["kappa_exact"] == "3984/1963"
    assert w4["maximum_multiplicity"] == 5


def test_charge_transfer_replays_and_fails_closed() -> None:
    transfer = charge_transfer()
    widths = {row["width_columns"]: row for row in transfer["completed_widths"]}
    assert widths[3]["physical_majority_domain_states"] == 126
    assert widths[4]["physical_majority_domain_states"] == 3926
    assert widths[5]["frontier_charge_prefix_states"] == 144464
    assert widths[5]["charge_fibers"] == 80182
    assert widths[5]["physical_majority_domain_states"] == 108978
    assert widths[5]["exact_Bayes_numerator"] == 55496
    assert transfer["cap_hit"] == {
        "width_columns": 6,
        "interior_columns": 4,
        "states_observed_before_fail_closed": 2000001,
        "registered_state_cap": 2000000,
    }


def test_selector_pair_channel_profile() -> None:
    rows = {row["width_columns"]: row for row in selector_transfer_profile(8)}
    assert [rows[width]["simple_paths"] for width in range(3, 9)] == [9, 29, 95, 313, 1033, 3411]
    assert rows[7]["pair_channels_exceed_registered_cap"] is False
    assert rows[8]["pair_channels_exceed_registered_cap"] is True
