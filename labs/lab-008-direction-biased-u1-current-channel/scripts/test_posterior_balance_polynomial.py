import check_posterior_balance_polynomial as subject


def test_existing_l3_polynomial_control_closes_as_obstruction():
    result = subject.analyze()
    assert result["status"] == "complete_obstruction"
    assert result["new_physical_record_samples"] == 0
    assert result["identity_failures"] == 0
    assert result["Bayes_LER_exact"] == "7/16"
    assert result["conditional_posterior_balance_exact"] == "8/17"
    assert result["L3_root_control"]["all_records_real_nonpositive"] is True
    assert result["L3_variance_control"]["minimum_ambiguous_variance_exact"] == "1/4"
    assert result["L3_variance_control"]["variance_bound_failures"] == 0
    assert result["decision"]["outcome"] == "obstruction"
