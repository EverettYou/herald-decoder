from audit_midpoint_selector_automaton_feasibility import (
    exact_selector_table,
    reduce_selector_mtbdd,
)


def test_exact_controls_replay_registered_W3_W4_values():
    expected = {3: (126, 154, "11/9", 2), 4: (3926, 7968, "3984/1963", 5)}
    for width, values in expected.items():
        control, _ = exact_selector_table(width)
        assert (
            control["physical_majority_domain_states"],
            control["selector_second_moment"],
            control["kappa_exact"],
            control["maximum_multiplicity"],
        ) == values


def test_reduced_selector_map_has_no_semantic_merges():
    control, outputs = exact_selector_table(4)
    reduced = reduce_selector_mtbdd(outputs, control["edges"])
    assert reduced["truth_table_replay_mismatches"] == 0
    assert reduced["anti_merge_gate_passed"]
    assert reduced["total_states"] == 7842


def test_pair_identity_is_exact():
    control, _ = exact_selector_table(4)
    assert control["selector_second_moment"] == (
        control["physical_majority_domain_states"] + control["ordered_alternate_pairs"]
    )
