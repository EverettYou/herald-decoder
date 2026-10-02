#!/usr/bin/env python3
"""Tests for the direct physical-risk reduction."""

from audit_midpoint_direct_risk_renormalization import exact_control


def test_average_congestion_certificates() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["lower_extremal_selector"]["effective_size_biased_multiplicity_exact"] == "110/63"
    assert l3["lower_extremal_selector"]["Cauchy_direct_risk_lower_bound_exact"] == "3969/14080"
    assert l4["lower_extremal_selector"]["effective_size_biased_multiplicity_exact"] == "76181/23005"
    assert l4["lower_extremal_selector"]["Cauchy_direct_risk_lower_bound_exact"] == "1587690075/9985196032"
    assert l4["upper_extremal_selector"]["effective_size_biased_multiplicity_exact"] == "76171/23005"
    assert l4["upper_extremal_selector"]["missing_selector_states"] == 0


def test_natural_reveal_profiles() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["natural_charge_reveal"]["Bayes_risk_exact"] == ["1/2", "1/2", "1/2", "7/16"]
    assert l4["natural_charge_reveal"]["Bayes_risk_exact"][:-1] == ["1/2"] * 8
    assert l4["natural_charge_reveal"]["Bayes_risk_exact"][-1] == "11849/32768"
    assert abs(l4["natural_charge_reveal"]["conditional_logical_entropy_bits"][-1] - 0.8514082240002261) < 1e-14
