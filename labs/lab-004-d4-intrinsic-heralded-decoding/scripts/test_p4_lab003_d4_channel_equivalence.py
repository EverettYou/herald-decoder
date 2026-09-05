from audit_p4_lab003_d4_channel_equivalence import build_audit


def test_p4_audit_rejects_cross_lab_numerical_comparison():
    audit = build_audit()
    assert audit["comparison_allowed"] is False
    assert audit["verdict"] == "non_equivalent_cross_lab_numerical_comparison_prohibited"
    assert all(audit["acceptance"].values())
    assert audit["closed_hexagon_support"] == {
        "lab_003_conditional_independent_binary_support": 64,
        "d4_colour_parity_constrained_support": 16,
    }


def test_p4_audit_covers_every_registered_dimension():
    audit = build_audit()
    dimensions = {row["dimension"] for row in audit["equivalence_matrix"]}
    assert dimensions == {
        "latent physical event",
        "herald conditioning",
        "correlation structure",
        "geometry and boundary",
        "error parameter",
        "decoder-visible record",
        "decoder",
        "logical-loss convention",
    }
    assert audit["size_5_geometry"]["lab_003"]["boundary_vertices"] > 0
    assert audit["size_5_geometry"]["d4"]["boundary_vertices"] == 0
