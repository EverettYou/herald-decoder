"""Tests for the shortest-selector exchange/obstruction matrix."""

from audit_midpoint_shortest_selector_exchange import exact_control


def test_replays_registered_shortest_selector_controls() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["kappa_exact"] == "11/9"
    assert l4["kappa_exact"] == "3113/1605"
    assert l3["collision_pairs"] == 14
    assert l4["collision_pairs"] == 64844
    for control in (l3, l4):
        checks = control["integrity_checks"]
        for name in (
            "selector_replay",
            "target_replay",
            "charge_preservation",
            "logical_parity_flip",
        ):
            assert checks[name] == checks["preimages"]
        assert checks["virtual_divergence_reconnection"] == control["collision_pairs"]


def test_closed_geodesic_exchange_is_not_exhaustive() -> None:
    l3, l4 = exact_control(3), exact_control(4)
    assert l3["exchange_matrix"]["same_physical_endpoints_closed_cycle_pairs"]["count"] == 0
    assert l4["exchange_matrix"]["same_physical_endpoints_closed_cycle_pairs"]["count"] == 4170
    assert l4["exchange_matrix"]["equal_path_length_pairs"]["count"] == 7586
    assert l4["exchange_matrix"]["symmetric_difference_components"] == {1: 59326, 2: 5518}


def test_finite_collision_fan_control() -> None:
    l4 = exact_control(4)
    fan = l4["collision_fan_control"]
    assert fan["preimage_mass_at_multiplicity_at_least_4"]["count"] == 7528
    assert fan["second_moment_from_multiplicity_at_least_4"]["count"] == 33900
    assert fan["maximum_multiplicity"] == 8
    assert fan["maximum_multiplicity_targets"] == 8
    assert fan["maximum_target_common_core_edge_count"] == {1: 8}
