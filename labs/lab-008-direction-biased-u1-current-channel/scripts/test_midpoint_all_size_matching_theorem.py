from audit_midpoint_all_size_matching_theorem import analyze


def test_theorem_applicability_and_counterexample_matrix():
    result = analyze()
    assert result["status"] == "complete_missing_restricted_orientation_NMP_theorem"
    assert result["new_physical_record_samples"] == 0
    assert result["decoder_runs"] == 0
    by_size = {row["L"]: row for row in result["canonical_size_audits"]}

    assert by_size[3]["orientation_embedding"]["alpha_orientation_embedding"]
    assert by_size[4]["orientation_embedding"]["alpha_orientation_embedding"]
    assert by_size[3]["normalized_transport"]["transport_target"] == 456
    assert by_size[4]["normalized_transport"]["transport_target"] == 1_253_808
    assert by_size[3]["normalized_transport"]["deficit"] == 0
    assert by_size[4]["normalized_transport"]["deficit"] == 0
    assert by_size[4]["restricted_graph_fragmentation"][
        "ambiguous_records_split_into_multiple_switching_components"
    ] == 578
    assert by_size[4]["internal_directed_plaquette_states"] == 86_528

    matrix = result["counterexample_matrix"]
    assert matrix["single_edge_deletions_tested"] == 18
    assert matrix["double_edge_deletions_tested"] == 153
    assert matrix["first_Hall_gap"] is None
    assert matrix["minimum_matching_fraction_of_bayes_numerator_exact"] == "1"
    assert len(result["primary_source_applicability"]) == 4
    assert result["decision"]["threshold_claim"] == (
        "No square midpoint noncorrectability or decoding-threshold claim is promoted."
    )
