#!/usr/bin/env python3
"""Tests for the midpoint collision-to-physical comparison audit."""

from audit_midpoint_charge_collision_comparison import exact_control


def test_exact_collision_controls_and_log_concavity() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["maximum_record_count"] == 14
    assert l4["maximum_record_count"] == 135
    assert l3["collision_to_maximum_record_probability_exact"] == "29/56"
    assert l4["collision_to_maximum_record_probability_exact"] == "653081/4423680"
    assert l3["collision_conditioned_opposite_sector_probability_exact"] == "57/116"
    assert l4["collision_conditioned_opposite_sector_probability_exact"] == "313452/653081"
    assert l3["coordinate_line_log_concavity"] == {
        "tested_neighbor_triples": 88,
        "violations": 0,
        "first_violation": [],
    }
    assert l4["coordinate_line_log_concavity"] == {
        "tested_neighbor_triples": 125616,
        "violations": 0,
        "first_violation": [],
    }


def test_dimension_and_complement_action() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["measured_charge_dimension"] == 3
    assert l4["measured_charge_dimension"] == 8
    assert l3["bitwise_complement_sector_action"] == "swaps_logical_sector"
    assert l4["bitwise_complement_sector_action"] == "preserves_logical_sector"
    assert l3["Gaussian_density_benchmark_2_to_minus_d_over_2"] > l4[
        "Gaussian_density_benchmark_2_to_minus_d_over_2"
    ]
