import json
from pathlib import Path

import audit_midpoint_minority_mass_lower_bound as audit


def test_midpoint_minority_mass_audit(tmp_path, monkeypatch):
    out = tmp_path / "result.json"
    monkeypatch.setattr(audit, "RESULT", out)
    audit.main()
    data = json.loads(out.read_text())
    assert data["status"] == "complete_rsw_and_nmp_information_obstruction"
    assert data["new_physical_record_samples"] == 0
    assert data["decoder_runs"] == 0
    l3, l4 = data["finite_controls"]
    assert l3["ambiguity_probability_exact"] == "119/128"
    assert l4["ambiguity_probability_exact"] == "116411/131072"
    assert l3["selector_maximum_congestion"] == 3
    assert l4["selector_maximum_congestion"] == 16
    assert l3["bounded_congestion_certificate_exact"] == "119/512"
    assert l4["bounded_congestion_certificate_exact"] == "116411/2228224"
    assert l3["straight_channel_gadget"]["L_edge_disjoint_straight_channels_union_probability_exact"] == "7/8"
    assert l4["straight_channel_gadget"]["L_edge_disjoint_straight_channels_union_probability_exact"] == "175/256"
    assert data["information_theoretic_countermodel"]["normalized_matching_property"] is True
    assert data["information_theoretic_countermodel"]["minority_fraction"] == "1/(M+1)"
    assert data["decision"]["threshold_claim"] == "No square midpoint noncorrectability or decoding-threshold claim is promoted."
    assert len(data["primary_source_applicability"]) == 3
