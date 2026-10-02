#!/usr/bin/env python3
"""Tests for the exact midpoint averaged-balance audit."""

from fractions import Fraction

from audit_midpoint_averaged_charge_balance import abstract_countermodels, count_fibers


def test_exact_controls_and_overlap_identities() -> None:
    l3, l4 = count_fibers(3), count_fibers(4)
    assert l3["exact_Bayes_risk"] == "7/16"
    assert l4["exact_Bayes_risk"] == "11849/32768"
    assert l3["same_charge_collision_probability_exact"] == "29/1024"
    assert l4["same_charge_collision_probability_exact"] == "653081/8589934592"
    assert l3["opposite_sector_same_charge_overlap_exact"] == "57/4096"
    assert l4["opposite_sector_same_charge_overlap_exact"] == "78363/2147483648"
    assert l3["collision_conditioned_opposite_sector_probability_exact"] == "57/116"
    assert l4["collision_conditioned_opposite_sector_probability_exact"] == "313452/653081"
    assert l3["collision_to_maximum_record_probability_exact"] == "29/56"
    assert l4["collision_to_maximum_record_probability_exact"] == "653081/4423680"
    assert l3["overlap_lower_bound_on_risk_exact"] == "57/448"
    assert l4["overlap_lower_bound_on_risk_exact"] == "8707/245760"
    assert l4["physical_mass_with_minority_ratio_at_least"]["1/8"] == "116411/131072"


def test_abstract_overlap_countermodels() -> None:
    models = abstract_countermodels()
    assert "1/(2N) -> 0" in models["unnormalized_overlap_can_vanish_at_maximal_risk"]["opposite_sector_same_charge_overlap"]
    assert models["normalized_overlap_can_stay_positive_while_risk_vanishes"]["collision_conditioned_opposite_probability_limit"] == "1/2"
    for n in (4, 8, 32):
        epsilon = Fraction(1, n)
        risk = epsilon / 2
        overlap = epsilon * epsilon / 2
        collision = epsilon * epsilon + (1 - epsilon) ** 2 / n**3
        assert risk > 0 and overlap / collision > Fraction(2, 5)
    assert Fraction(1, 2) > Fraction(0)
