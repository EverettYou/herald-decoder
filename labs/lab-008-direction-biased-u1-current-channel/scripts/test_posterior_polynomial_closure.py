import check_posterior_polynomial_closure as subject


def test_l4_transfer_closes_as_recurrence_obstruction():
    result = subject.analyze()
    assert result["status"] == "complete_recurrence_obstruction"
    assert result["new_physical_record_samples"] == 0
    assert result["exhaustive_current_states"] == 262144
    assert result["fixed_charge_records"] == 44494
    assert result["transfer_validation"]["matches_independent_exhaustive_table"] is True
    assert result["transfer_validation"]["actual_two_summand_pairs_tested"] == 34721
    assert result["transfer_validation"]["actual_pair_interlacing_failures"] == 0
    assert result["transfer_validation"]["final_real_nonpositive_root_failures"] == 0
    assert result["common_family_interlacing_counterexample"]["first_polynomial"] == "t"
    assert result["common_family_interlacing_counterexample"]["second_polynomial"] == "1+5t+t^2"
    assert result["L4_posterior_control"]["Bayes_LER_exact"] == "11849/32768"
    assert result["decision"]["outcome"] == "recurrence_obstruction_without_real_root_counterexample"
