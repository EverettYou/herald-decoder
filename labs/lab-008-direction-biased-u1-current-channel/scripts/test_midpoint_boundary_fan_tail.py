"""Tests for the boundary-fan tail matrix."""

from audit_midpoint_boundary_fan_tail import diamond_chain_control, exact_tail_control


def test_exact_tail_identity_and_witness_injection() -> None:
    l3, l4 = exact_tail_control(3), exact_tail_control(4)
    assert l3["tail_sum_exact"] == l3["kappa_exact"] == "11/9"
    assert l4["tail_sum_exact"] == l4["kappa_exact"] == "3113/1605"
    assert l3["two_environment_witness"]["ordered_alternate_preimages"] == 28
    assert l4["two_environment_witness"]["ordered_alternate_preimages"] == 129688
    assert l3["two_environment_witness"]["signature_multiplicity_histogram"] == {1: 28}
    assert l4["two_environment_witness"]["signature_multiplicity_histogram"] == {1: 129688}
    assert l3["two_environment_witness"]["injective_on_exact_control"] is True
    assert l4["two_environment_witness"]["injective_on_exact_control"] is True


def test_l4_size_biased_tail() -> None:
    tail = exact_tail_control(4)["tail_under_size_biased_majority_domain"]
    assert tail["1"]["probability_exact"] == "1"
    assert tail["4"]["preimage_states"] == 7528
    assert tail["8"]["preimage_states"] == 64


def test_bounded_diamond_chain_matrix() -> None:
    controls = [diamond_chain_control(diamonds) for diamonds in range(1, 5)]
    assert [control["edges"] for control in controls] == [4, 8, 12, 16]
    assert [control["rough_to_rough_paths"] for control in controls] == [2, 4, 8, 16]
    assert [control["maximum_multiplicity"] for control in controls] == [1, 2, 4, 8]
    assert [control["maximum_multiplicity_targets"] for control in controls] == [12, 22, 32, 42]
