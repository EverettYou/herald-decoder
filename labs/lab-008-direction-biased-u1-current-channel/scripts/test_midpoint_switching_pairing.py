import check_midpoint_switching_pairing as subject


def test_exact_switching_matrix_closes_at_registered_bounds():
    result = subject.analyze()
    assert result["status"] == "complete_selector_obstruction"
    assert result["new_physical_record_samples"] == 0
    l3, l4 = result["size_audits"]
    assert l3["simple_rough_to_rough_paths"] == 9
    assert l4["simple_rough_to_rough_paths"] == 80
    assert l3["path_flip_charge_preservation_failures"] == 0
    assert l4["path_flip_logical_parity_failures"] == 0
    assert l3["lower_extremal_selector"]["finite_Bayes_LER_pairing_lower_bound_exact"] == "43/128"
    assert l4["lower_extremal_selector"]["finite_Bayes_LER_pairing_lower_bound_exact"] == "28353/131072"
    assert l4["lower_extremal_selector"]["all_eligible_map_maximum_multiplicity"] == 16
    assert l4["upper_extremal_selector"]["all_eligible_map_injective"] is False
    assert l4["local_plaquette"]["states_with_directed_plaquette"] == 86528
    assert l4["local_plaquette"]["logical_parity_flip_successes"] == 0
    assert result["decision"]["outcome"] == "natural_selector_obstruction_and_missing_event_theorem"
