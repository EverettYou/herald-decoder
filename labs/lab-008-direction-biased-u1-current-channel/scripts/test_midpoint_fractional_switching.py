from check_midpoint_fractional_switching import analyze


def test_exact_fractional_switching_saturates_finite_bayes_numerator():
    result = analyze()
    assert result["status"] == "complete_finite_saturation_missing_uniform_theorem"
    assert result["new_physical_record_samples"] == 0
    assert result["decoder_runs"] == 0
    by_size = {row["L"]: row for row in result["size_audits"]}

    assert by_size[3]["unique_switching_edges"] == 352
    assert by_size[3]["maximum_integral_matching_pairs"] == 112
    assert by_size[3]["finite_Bayes_LER_exact"] == "7/16"
    assert by_size[3]["additional_pairs_over_selector"] == 26

    assert by_size[4]["unique_switching_edges"] == 580608
    assert by_size[4]["maximum_integral_matching_pairs"] == 94792
    assert by_size[4]["finite_Bayes_LER_exact"] == "11849/32768"
    assert by_size[4]["additional_pairs_over_selector"] == 38086

    for row in by_size.values():
        assert row["switching_edge_charge_failures"] == 0
        assert row["switching_edge_parity_failures"] == 0
        assert row["record_saturation_failures"] == 0
        assert row["matching_fraction_of_bayes_numerator_exact"] == "1"
        assert row["fractional_certificate"][
            "fractional_optimum_equals_integral_optimum"
        ]
        assert row["dual_vertex_cover"]["uncovered_switching_edges"] == 0
        assert row["dual_vertex_cover"]["equals_matching_size"]
        assert (
            row["component_audit"]["component_decomposition_gap_to_bayes_numerator"]
            == 0
        )

    assert result["decision"]["threshold_claim"] == (
        "No square midpoint noncorrectability or decoding-threshold claim is promoted."
    )
