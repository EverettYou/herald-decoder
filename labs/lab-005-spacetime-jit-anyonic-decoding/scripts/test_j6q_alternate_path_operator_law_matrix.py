"""Independent exact-law and claim-boundary checks for the J6Q matrix."""

from fractions import Fraction
import json

from run_j6n_sequential_local_projector_moments import sequential_probability
from run_j6q_alternate_path_operator_law_matrix import (
    INPUTS, projection_probability, run,
)
from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star


def test_general_sandwich_replays_old_one_first_projector_formula():
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    stars = {star["center"]: star for star in embedding["star_supports"]}
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    first = conjugated_star(stars["green:1"], mask([0, 4]))
    second = conjugated_star(stars["blue:0"], mask([4]))
    for first_outcome in (-1, 1):
        for second_outcome in (-1, 1):
            assert projection_probability([first], (first_outcome,), [second],
                                          (second_outcome,), flips) == \
                   sequential_probability(first, [second], first_outcome,
                                          (second_outcome,), flips)


def test_six_cells_have_exact_complete_public_laws():
    result = run()
    assert result["status"] == "passed_two_geometry_exact_matrix"
    assert len(result["cases"]) == 6
    assert result["stochastic_histories"] == result["schedule_arm_evaluations"] == 0
    for case in result["cases"]:
        assert case["status"] == "exact_full_public_law"
        rows = case["public_law_rows"]
        first_masses = {tuple(row["first_public"]["charge"]): Fraction(row["first_probability"])
                        for row in rows}
        assert sum(first_masses.values()) == 1
        for first_charge in first_masses:
            conditional = [row for row in rows
                           if tuple(row["first_public"]["charge"]) == first_charge]
            if case["action"] == "defer":
                assert all(row["second_public"] is None for row in conditional)
            else:
                assert sum(Fraction(row["second_conditional_probability"])
                           for row in conditional) == 1
            for row in conditional:
                for name in ("first_public", "second_public"):
                    record = row[name]
                    if record is None:
                        continue
                    assert set(record) == {"flux", "charge", "vacuum"}
                    assert all(len(bits) == 24 and set(bits) <= {0, 1}
                               for bits in record.values())
                    assert record["vacuum"] == [1 - bit for bit in record["charge"]]


def test_disjoint_pair_is_deterministic_and_shared_blue_transfers_color():
    result = run()
    by_case = {(row["geometry"], row["action"]): row for row in result["cases"]}
    assert all(len(by_case[("disjoint", action)]["public_law_rows"]) == 1
               for action in ("defer", "partial", "matched"))
    shared = by_case[("shared_blue", "matched")]
    assert shared["first_random_sites_private"] == [0]
    assert shared["second_random_counts_private"] == [2, 2]
    assert {tuple(i for i, bit in enumerate(row["second_public"]["charge"]) if bit)
            for row in shared["public_law_rows"]} == {(), (1, 17)}
