"""Registered chain/star topology and first-conditioned public-law checks."""

from fractions import Fraction

from run_j6r_three_edge_topology_causal_law import run


def test_registered_eight_branch_matrix_and_censoring():
    result = run()
    assert result["status"] == "partially_censored_two_topology_exact_matrix"
    assert len(result["cases"]) == 8
    assert all(result["pinned_input_checks"].values())
    assert result["stochastic_histories"] == result["schedule_arm_evaluations"] == 0
    censored = [case for case in result["cases"]
                if case["status"] == "censored_support_exceeds_bound"]
    assert len(censored) == 1
    assert (censored[0]["topology"], censored[0]["action"]) == \
           ("connected_chain", "matched")
    assert censored[0]["public_law_rows"] == []
    assert censored[0]["second_random_counts_private"] == [4, 4, 4, 4]


def test_chain_one_edge_prefix_has_full_record_first_dependence():
    case = next(case for case in run()["cases"]
                if case["topology"] == "connected_chain" and
                case["action"] == "partial_one")
    assert case["first_random_sites_private"] == [1, 2]
    assert case["positive_first_record_count"] == 4
    assert case["first_dependence_full_public_law"] == "dependent_on_first_record"
    first_records = {tuple(row["first_public"]["charge"]) for row in case["public_law_rows"]}
    assert len(first_records) == 4
    for first in first_records:
        rows = [row for row in case["public_law_rows"]
                if tuple(row["first_public"]["charge"]) == first]
        assert len(rows) == 2
        assert {Fraction(row["second_conditional_probability"]) for row in rows} == \
               {Fraction(1, 2)}
        assert all(row["second_public"]["charge"][2] == first[2]
                   for row in rows)
        assert {row["second_public"]["charge"][0] for row in rows} == {0, 1}


def test_star_control_and_public_array_boundary():
    cases = run()["cases"]
    for case in cases:
        if case["topology"] == "three_arm_star":
            assert case["positive_first_record_count"] == 1
            assert case["first_random_sites_private"] == []
        if case["status"] != "exact_full_public_law":
            continue
        first_mass = {tuple(row["first_public"]["charge"]):
                      Fraction(row["first_probability"])
                      for row in case["public_law_rows"]}
        assert sum(first_mass.values()) == 1
        for first in first_mass:
            rows = [row for row in case["public_law_rows"]
                    if tuple(row["first_public"]["charge"]) == first]
            if case["action"] == "defer":
                assert all(row["second_public"] is None for row in rows)
            else:
                assert sum(Fraction(row["second_conditional_probability"])
                           for row in rows) == 1
            for row in rows:
                for key in ("first_public", "second_public"):
                    public = row[key]
                    if public is None:
                        continue
                    assert set(public) == {"flux", "charge", "vacuum"}
                    assert all(len(bits) == 24 and set(bits) <= {0, 1}
                               for bits in public.values())
                    assert public["vacuum"] == [1 - bit for bit in public["charge"]]
