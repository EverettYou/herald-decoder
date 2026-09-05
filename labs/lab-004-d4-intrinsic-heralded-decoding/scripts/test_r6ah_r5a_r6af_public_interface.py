from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_r6ah_r5a_r6af_public_interface.py")
SPEC = importlib.util.spec_from_file_location("r6ah_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_registered_audit_reaches_only_bounded_incompatible_verdict() -> None:
    manifest = MODULE._load(MODULE.DEFAULT_MANIFEST)
    payload = MODULE.build_audit(manifest)
    assert payload["overall_verdict"] == "incompatible"
    assert payload["unclassified_dimension_count"] == 0
    assert payload["new_computation"] == {
        "histories": 0,
        "arm_evaluations": 0,
        "bootstrap_replicates": 0,
    }
    verdicts = {row["dimension"]: row["verdict"] for row in payload["dimension_matrix"]}
    assert verdicts["first observation and timing"] == "incompatible"
    assert verdicts["second public record"] == "incompatible"
    assert verdicts["claim usability"] == "provenance_only"


def test_raw_schema_witness_distinguishes_private_storage_from_public_action() -> None:
    manifest = MODULE._load(MODULE.DEFAULT_MANIFEST)
    payload = MODULE.build_audit(manifest)
    raw = payload["raw_schema_audit"]
    assert raw["record_count"] == 40000
    assert raw["paired_history_count"] == 20000
    assert raw["physical_pair_mismatch_count"] == 0
    assert raw["first_record_pair_mismatch_count"] == 0
    assert raw["first_record_value_domain"] == [-1, 0, 1]
    assert raw["second_record_value_domain"] == [-1, 0, 1]
    assert raw["second_records_full_binary"] == 0
    assert raw["records_with_explicit_public_transcript"] == 0
    assert raw["stored_loss_composition_mismatch_count"] == 0
