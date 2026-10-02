#!/usr/bin/env python3
"""Tests for selector second-moment collision classification."""

from audit_midpoint_selector_second_moment import exact_control


def test_extremal_replay_and_paired_identity() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["order_matrix"]["lexicographic_lower"]["kappa_exact"] == "110/63"
    assert l4["order_matrix"]["lexicographic_lower"]["kappa_exact"] == "76181/23005"
    assert l4["order_matrix"]["lexicographic_upper"]["kappa_exact"] == "76171/23005"
    for control in (l3, l4):
        for order in control["order_matrix"].values():
            assert order["paired_identity"]["replayed"] is True
            assert order["collision_geometry"]["same_path_off_diagonal_pairs"] == 0
            assert order["collision_geometry"]["interior_odd_degree_failures"] == 0


def test_common_domains_and_registered_order_matrix() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["common_physical_majority_domain_states"] == 126
    assert l4["common_physical_majority_domain_states"] == 138030
    expected = {
        "lexicographic_lower",
        "lexicographic_upper",
        "shortest_then_lexicographic",
        "longest_then_lexicographic",
    }
    assert set(l3["order_matrix"]) == expected
    assert set(l4["order_matrix"]) == expected
