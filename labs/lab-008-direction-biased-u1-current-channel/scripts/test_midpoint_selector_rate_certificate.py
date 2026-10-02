from audit_midpoint_selector_rate_certificate import (
    charge_frontier_counterexample,
    path_count_tail_audit,
    zero_background_family,
)


def test_local_charge_frontier_key_is_not_selector_congruent():
    witness = charge_frontier_counterexample()
    assert witness["left"]["full_state"] == 79
    assert witness["right"]["full_state"] == 106
    assert witness["left"]["full_charge"] == witness["right"]["full_charge"]
    assert witness["left"]["selected_path_index"] == 0
    assert witness["right"]["selected_path_index"] == 2


def test_zero_background_path_family_fails_physical_weight_gate():
    rows = zero_background_family()
    assert [row["simple_path_configurations"] for row in rows] == [9, 29, 95]
    assert [row["physical_majority_states_mapping_to_zero"] for row in rows] == [0, 0, 0]


def test_path_count_cutoff_has_unbounded_width_scale():
    rows = path_count_tail_audit()
    assert [row["simple_paths"] for row in rows[:4]] == [9, 29, 95, 313]
    assert all(row["simple_paths"] >= row["explicit_x_monotone_paths"] for row in rows)
