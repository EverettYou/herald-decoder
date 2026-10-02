"""Small independent controls for the symbolic periodic operator audit."""

from run_j6m_periodic_operator_ground_orbit import (
    flip_basis_and_relations,
    parity,
    phase_difference,
    qphase,
    reduced,
    row_basis,
    run,
)


def test_cz_phase_difference_matches_direct_three_qubit_truth_table() -> None:
    pairs = [(0, 1), (1, 2)]
    for flip in range(8):
        linear, constant = phase_difference(pairs, flip)
        for state in range(8):
            assert qphase(pairs, state ^ flip) ^ qphase(pairs, state) == (
                parity(linear & state) ^ constant
            )


def test_gf2_row_span_and_dependent_flip_relation() -> None:
    basis = row_basis([0b011, 0b110, 0b101])
    assert len(basis) == 2
    assert reduced(0b101, basis) == 0
    assert reduced(0b001, basis) != 0
    rank, relations = flip_basis_and_relations([0b001, 0b010, 0b011])
    assert rank == 2
    assert relations == [0b111]


def test_periodic_symbolic_audit_passes_registered_bound() -> None:
    result = run()
    assert result["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    counts = result["operator_counts"]
    assert (counts["qubits"], counts["stars"], counts["triangles"]) == (108, 36, 72)
    assert counts["star_pair_cases_per_model"] == 630
    assert counts["source_nonzero_adjacent_commutators"] == 108
    assert result["checks"]["all_adjacent_commutators_match_two_local_triangle_products"]
    assert counts["cz_deleted_null_nonzero_commutators"] == 0
    assert counts["outer_x_flip_rank"] == 33
    assert counts["outer_x_flip_relation_count"] == 3
