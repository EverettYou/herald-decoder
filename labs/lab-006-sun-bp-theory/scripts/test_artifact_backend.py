import numpy as np
import pytest
from pathlib import Path

from artifact_backend import MAX_BP_ITERATIONS, _dynamic_fusion_rules, artifact_payload, warm_numba_kernels
import numba_fusion_decoder as decoder_module
from numba_fusion_decoder import group_fusion_distribution


def test_three_group_fusion_rules_are_distinct_and_normalized():
    assert group_fusion_distribution("U1", ("anti", "fund")) == {"0": 1.0}
    assert group_fusion_distribution("SU2", ("anti", "fund")) == {"1": .25, "3": .75}
    assert group_fusion_distribution("SU3", ("anti", "fund")) == {"1": 1 / 9, "8": 8 / 9}
    for group in ("None", "U1", "SU2", "SU3"):
        for leaves in ((), ("fund",), ("anti",), ("fund", "fund"), ("anti", "fund"), ("fund",) * 3, ("fund", "fund", "anti", "anti")):
            assert sum(group_fusion_distribution(group, leaves).values()) == pytest.approx(1)


def test_numba_warmup_compiles_binary_and_ternary_kernel_signatures():
    # Shapes vary with L, but Numba specialization is determined by rank/dtype.
    warm_numba_kernels()
    assert MAX_BP_ITERATIONS == 300


def test_directed_kernel_signature_is_group_lattice_and_syndrome_agnostic():
    """Only dtype/rank specialize Numba; group and record are data."""
    warm_numba_kernels()
    before = len(decoder_module._infer_inplace.signatures)
    for group, lattice, size, seed in (
        ("U1", "square", 3, 3),
        ("SU2", "honeycomb", 3, 4),
        ("SU3", "square", 5, 5),
    ):
        artifact_payload({
            "group": group, "lattice": lattice, "L": size,
            "p": .18, "damping": .65, "seed": seed,
        })
    assert len(decoder_module._infer_inplace.signatures) == before


@pytest.mark.parametrize("group,lattice", [(group, lattice) for group in ("U1", "SU2", "SU3") for lattice in ("square", "honeycomb")])
def test_artifact_is_deterministic_numba_backed_and_syndrome_faithful(group, lattice):
    request = {"group": group, "lattice": lattice, "L": 3, "p": .18, "seed": 91}
    first = artifact_payload(request)
    second = artifact_payload(request)
    assert first["observation"] == second["observation"]
    np.testing.assert_array_equal(first["posterior"]["edge_marginals"], second["posterior"]["edge_marginals"])
    assert first["model"]["backend"].startswith("cached-preallocated-numba")
    assert first["model"]["damping"] == .5
    assert first["model"]["boundaries"] == "display coordinates: open rough top/bottom; smooth left/right"
    assert first["decoder"]["syndrome_faithful"]
    assert first["decoder"]["residual_m_vertices"] == []
    trivial = first["model"]["trivial_irrep"]
    assert all(mark["label"] != trivial for mark in first["observation"]["irrep_marks"])
    edge_count = len(first["graph"]["edges"])
    assert len(first["posterior"]["edge_weights"]) == edge_count
    assert len(first["m_only_baseline"]["edge_marginals"]) == edge_count
    full_weights = np.asarray(first["posterior"]["edge_weights"])
    baseline_weights = np.asarray(first["m_only_baseline"]["edge_weights"])
    effect = first["m_only_baseline"]
    np.testing.assert_allclose(effect["error_llr_shift_from_irrep"], baseline_weights - full_weights)
    assert effect["max_abs_error_llr_shift"] >= effect["mean_abs_error_llr_shift"]
    assert effect["effect_convention"] == "logit P(error|m,R) - logit P(error|m)"
    assert {v["boundary_side"] for v in first["graph"]["vertices"] if not v["detector"]} == {"left", "right"}
    assert first["graph"]["logical_edge_indices"]
    disconnected = {
        index for index, vertex in enumerate(first["graph"]["vertices"])
        if not vertex["visible"]
    }
    incident = {vertex for edge in first["graph"]["edges"] for vertex in edge}
    assert disconnected.isdisjoint(incident)
    if lattice == "honeycomb":
        assert disconnected, "honeycomb virtual rough-boundary coordinates must be hidden"


def test_artifact_rejects_invalid_controls():
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU4", "lattice": "square", "L": 3, "p": .1, "seed": 1})
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU3", "lattice": "square", "orientation": "sideways", "L": 3, "p": .1, "seed": 1})
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU3", "lattice": "square", "L": 3, "p": .1, "damping": 1.0, "seed": 1})
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU3", "lattice": "square", "L": 17, "p": .1, "seed": 1})
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU3", "lattice": "square", "L": 3, "p": .51, "seed": 1})
    with pytest.raises(ValueError):
        artifact_payload({"group": "SU3", "lattice": "square", "L": 3, "p": .1, "seed": 1, "algorithm": "max_product"})


@pytest.mark.parametrize("orientation", ["directed", "undirected"])
def test_min_sum_numba_backend_accepts_both_edge_channels(orientation):
    payload = artifact_payload({
        "group": "SU3", "lattice": "square", "orientation": orientation,
        "algorithm": "min_sum", "L": 3, "p": .18, "damping": .5, "seed": 3,
    })
    assert payload["model"]["algorithm"] == "min_sum"
    assert payload["decoder"]["syndrome_faithful"]
    marginals = np.asarray(payload["posterior"]["edge_marginals"])
    assert np.all(np.isfinite(marginals))
    assert np.all((0 <= marginals) & (marginals <= 1))


def test_undirected_model_marginalizes_the_hidden_half_half_pair_orientation():
    request = {"group": "SU3", "lattice": "square", "orientation": "undirected", "L": 3, "p": .18, "seed": 91}
    first = artifact_payload(request)
    second = artifact_payload(request)
    assert first["model"]["orientation_mode"] == "undirected"
    assert "probability 1/2" in first["model"]["orientation"]
    assert first["observation"] == second["observation"]
    np.testing.assert_array_equal(first["posterior"]["edge_marginals"], second["posterior"]["edge_marginals"])
    assert first["decoder"]["syndrome_faithful"]
    assert first["decoder"]["end_to_end_ms"] >= first["decoder"]["decode_ms"]


def test_none_group_is_exactly_the_m_only_belief_matching_baseline():
    result = artifact_payload({"group": "None", "lattice": "square", "L": 3, "p": .18, "seed": 91})
    assert result["model"]["trivial_irrep"] == "1"
    assert result["observation"]["irrep_marks"] == []
    np.testing.assert_allclose(result["posterior"]["edge_marginals"], result["m_only_baseline"]["edge_marginals"])
    np.testing.assert_allclose(result["m_only_baseline"]["error_llr_shift_from_irrep"], 0.0)
    assert result["model"]["fusion_rule"] == "R = 1 (no symmetry record)"


def test_dynamic_su3_fusion_table_lists_binary_steps_through_intermediate_irreps():
    rules = _dynamic_fusion_rules("SU3", [("fund", "fund", "fund", "anti")])
    assert all(len(rule["inputs"]) == 2 for rule in rules)
    by_inputs = {tuple(rule["inputs"]): rule["outputs"] for rule in rules}
    assert by_inputs[("3", "3")] == [{"label": "3bar", "multiplicity": 1}, {"label": "6", "multiplicity": 1}]
    assert by_inputs[("10", "3bar")] == [{"label": "6", "multiplicity": 1}, {"label": "24", "multiplicity": 1}]


def test_dynamic_su2_fusion_table_deduplicates_pseudoreal_pair_orientations():
    rules = _dynamic_fusion_rules("SU2", [("fund", "fund"), ("fund", "anti"), ("anti", "anti")])
    assert rules == [{
        "inputs": ["2", "2"],
        "outputs": [{"label": "1", "multiplicity": 1}, {"label": "3", "multiplicity": 1}],
    }]


def test_dynamic_su2_fusion_table_covers_four_when_three_fundamentals_are_used():
    rules = _dynamic_fusion_rules("SU2", [("fund", "fund", "anti")])
    assert rules[1] == {
        "inputs": ["3", "2"],
        "outputs": [{"label": "2", "multiplicity": 1}, {"label": "4", "multiplicity": 1}],
    }


def test_dynamic_u1_fusion_table_tracks_sequential_charge_addition():
    rules = _dynamic_fusion_rules("U1", [("fund", "fund", "anti")])
    assert rules == [
        {"inputs": ["+1", "+1"], "outputs": [{"label": "+2", "multiplicity": 1}]},
        {"inputs": ["+2", "-1"], "outputs": [{"label": "+1", "multiplicity": 1}]},
    ]


def test_dynamic_fusion_outputs_are_dimension_sorted():
    rules = _dynamic_fusion_rules("SU3", [("fund", "fund", "fund", "anti")])
    dimensions = {"3bar": 3, "6": 6, "24": 24}
    outputs = {tuple(rule["inputs"]): rule["outputs"] for rule in rules}
    assert [dimensions[item["label"]] for item in outputs[("3", "3")]] == [3, 6]
    assert [dimensions[item["label"]] for item in outputs[("10", "3bar")]] == [6, 24]


def test_boundary_trapped_irreps_are_part_of_the_full_observation_and_bp():
    payload = artifact_payload({"group": "SU3", "lattice": "square", "L": 3, "p": .45, "seed": 5, "measure_boundary_representation": True})
    boundary = {index for index, vertex in enumerate(payload["graph"]["vertices"]) if not vertex["detector"]}
    marks = {mark["vertex"] for mark in payload["observation"]["irrep_marks"]}
    assert boundary & marks, "active boundary endpoints must expose their trapped irreps"
    assert not (boundary & set(payload["observation"]["m_vertices"]))
    assert payload["model"]["boundary_m"] == "unmeasured (displayed as 0; marginalized in BP)"
    assert payload["decoder"]["syndrome_faithful"]


def test_boundary_representation_toggle_controls_only_the_optional_boundary_record():
    request = {"group": "SU3", "lattice": "square", "L": 3, "p": .45, "seed": 5}
    measured = artifact_payload({**request, "measure_boundary_representation": True})
    hidden = artifact_payload({**request, "measure_boundary_representation": False})
    boundary = {index for index, vertex in enumerate(measured["graph"]["vertices"]) if not vertex["detector"]}
    assert measured["model"]["measure_boundary_representation"]
    assert not hidden["model"]["measure_boundary_representation"]
    assert boundary & {mark["vertex"] for mark in measured["observation"]["irrep_marks"]}
    assert not (boundary & {mark["vertex"] for mark in hidden["observation"]["irrep_marks"]})


def test_removed_eta_field_cannot_break_a_stale_artifact_client():
    request = {"group": "SU3", "lattice": "square", "L": 3, "p": .18, "seed": 91}
    stale_request = {**request, "eta": "obsolete-and-not-a-number"}
    current = artifact_payload(request)
    stale = artifact_payload(stale_request)
    assert stale["model"] == current["model"]
    assert stale["observation"] == current["observation"]
    assert "eta" not in stale["model"]


def test_workbench_contains_three_groups_backend_route_and_color_contract():
    html = Path(__file__).parents[1].joinpath("figures/fusion-belief-matching.html").read_text()
    assert 'id="fusion-belief-workbench"' in html
    assert "/api/labs/lab-006-sun-bp-theory/artifact" in html
    assert "location.protocol==='file:'" in html
    assert "http://127.0.0.1:8010/api/labs/lab-006-sun-bp-theory/artifact" in html
    for group in ("None", "U1", "SU2", "SU3"):
        assert f'data-group="{group}"' in html
    for algorithm in ("sum_product", "min_sum"):
        assert f'data-algorithm="{algorithm}"' in html
    assert "algorithm,measure_boundary_representation" in html
    for color in ("#0f9d8a", "#e4572e", "#2563eb", "#188f65", "#8b5cf6"):
        assert color in html
    for lattice in ("square", "honeycomb"):
        assert f'data-lattice="{lattice}"' in html
    assert 'id="fb-edge-directed" type="checkbox" checked' in html
    assert "Edge directed" in html
    assert "Directed pairs" not in html
    assert "j=" not in html
    assert 'stroke-dasharray="3 2"' not in html
    assert '<rect x="${p.x-3}"' not in html
    assert 'r="4" fill="var(--panel)" stroke="var(--muted)"' not in html
    assert 'r="${active?8:2.7}" fill="var(--panel)"' in html
    assert "if(!v.detector){out+=`<circle" not in html
    assert "const rotate=p=>({...p,x:p.y,y:-p.x})" in html
    assert ">rough</text>" not in html
    assert ">smooth</text>" not in html
    assert 'id="fb-measure-boundary-representation" type="checkbox">' in html
    assert "Boundary charge" in html
    assert "Rough-boundary m is unmeasured (shown as 0)." not in html
    assert 'id="fb-direction-arrow"' not in html
    assert 'marker-end="url(#fb-direction-arrow)"' not in html
    assert 'mx=(u.x+v.x)/2,my=(u.y+v.y)/2' in html
    assert '<polyline points="${leftX},${leftY} ${mx},${my} ${rightX},${rightY}"' in html
    assert "arrow: F̄ → F" not in html
    assert "error corrected" in html
    assert "miss correction" in html
    assert "error uncorrected" in html
    assert "fb-ring" in html
    assert "orientation==='directed'?`<polyline" in html
    assert "orientation='directed'" in html
    assert "end_to_end_ms" in html
    assert 'id="fb-damping" type="range" min="0" max="0.9" step="0.05" value="0.5"' in html
    assert 'max="15" step="2" value="9"' in html
    assert 'id="fb-p" type="range" min="0.01" max="0.5" step="0.01"' in html
    assert 'r="15" fill="none" stroke="${color.coral}"' not in html
    assert 'r="${active?12:10.5}"' not in html
    assert "${active?`<circle" in html
    assert 'r="12" fill="none" stroke="${color.teal}"' in html
    assert 'x="${p.x}" y="${p.y+3.3}"' in html
    for excluded in ("fb-eta", '"eta"', "coarse"):
        assert excluded not in html
    assert "Δ error LLR" in html
    assert "P(error | m, R) − P(error | m)" not in html
    assert 'id="fb-rule"' not in html
    assert 'id="fb-rule-table"' in html
    assert "fusionRuleTable()" in html
