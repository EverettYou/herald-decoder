import json

import pytest

import audit_midpoint_charge_fiber_balance as audit


def test_midpoint_charge_fiber_balance(tmp_path, monkeypatch):
    out = tmp_path / "result.json"
    monkeypatch.setattr(audit, "RESULT", out)
    audit.main()
    data = json.loads(out.read_text())
    assert data["status"] == "complete_finite_balance_controls_missing_averaged_theorem"
    assert data["new_physical_record_samples"] == 0
    assert data["decoder_runs"] == 0
    l3, l4 = data["exact_controls"]
    assert l3["maximum_charge_fiber_sector_ratio_exact"] == "3/2"
    assert l4["maximum_charge_fiber_sector_ratio_exact"] == "6"
    assert l3["optimal_deterministic_switching_congestion"] == 2
    assert l4["optimal_deterministic_switching_congestion"] == 6
    assert l3["extremal_selector_congestion"] == 3
    assert l4["extremal_selector_congestion"] == 16
    assert l4["records_attaining_maximum_ratio"] == 96
    assert l4["physical_mass_of_maximum_ratio_records_exact"] == "21/8192"
    assert l4["first_maximum_ratio_witness"]["switching_graph"] == "K_{1,6}"
    assert l3["conditional_logical_entropy_bits"] == pytest.approx(0.9234596706506673)
    assert l4["conditional_logical_entropy_bits"] == pytest.approx(0.8514082240002299)
    assert data["branch_matrix"]["canonical_imbalance"]["outcome"] == "finite_physical_star_found_no_unbounded_family"
    assert data["decision"]["threshold_claim"] == "No square midpoint noncorrectability or decoding-threshold claim is promoted."
