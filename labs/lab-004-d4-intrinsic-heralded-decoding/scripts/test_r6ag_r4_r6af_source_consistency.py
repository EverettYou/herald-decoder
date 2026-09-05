import json
from pathlib import Path

from synthesize_r6ag_r4_r6af_source_consistency import build_synthesis


LAB_DIR = Path(__file__).resolve().parents[1]


def test_r6ag_preserves_nonuniversal_boundary_and_zero_sampling():
    manifest = json.loads(
        (
            LAB_DIR
            / "manifests/r6ag-r4-r6af-source-consistency-synthesis-manifest-2026-09-01.json"
        ).read_text(encoding="utf-8")
    )
    result = build_synthesis(manifest)
    assert result["verdict"] == "qualitatively_consistent_with_nonuniversal_boundary"
    assert result["unclassified_quantity_count"] == 0
    assert result["new_computation"] == {
        "histories": 0,
        "arm_evaluations": 0,
        "bootstrap_replicates": 0,
    }
    p06 = [row for row in result["r4_exact_primitive_extraction"] if row["p"] == 0.6]
    assert len(p06) == 1
    assert p06[0]["public_fixed_direction"] == "regression"


def test_r6ag_classifies_numeric_cross_study_quantities_as_incommensurate():
    manifest = json.loads(
        (
            LAB_DIR
            / "manifests/r6ag-r4-r6af-source-consistency-synthesis-manifest-2026-09-01.json"
        ).read_text(encoding="utf-8")
    )
    result = build_synthesis(manifest)
    classes = {row["quantity"]: row["class"] for row in result["comparison_matrix"]}
    assert classes["risk and delta magnitudes"] == "incommensurate"
    assert classes["sign of public fixed O2-minus-O0 risk"] == "qualitative_only"
    assert all(
        row["o2_first_action_excess_exceeds_second_stage_excess"]
        for row in result["r4_exact_primitive_extraction"]
    )
    assert all(
        row["first_union_reduction_dominates_charge_difference"]
        for row in result["r6af_complete_pipeline_extraction"]
    )
