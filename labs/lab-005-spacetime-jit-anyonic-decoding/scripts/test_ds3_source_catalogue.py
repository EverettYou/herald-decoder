from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ds3_source_catalogue import SOURCE_EVENTS, audit_catalogue  # noqa: E402


def test_all_registered_contexts_and_fields_are_source_cited() -> None:
    audit = audit_catalogue()
    assert audit["contexts_complete"]
    for event in SOURCE_EVENTS:
        assert event.physical_location
        assert event.time_support
        assert event.detector_support
        assert event.phase_ownership
        assert event.source_locator.startswith("Lyons-Brown")


def test_exact_and_bounded_rows_respect_locality_contract() -> None:
    fault_rows = [
        event
        for event in SOURCE_EVENTS
        if event.mapping_status
        in {"stabilizer_level_exact", "coarse_grained_bound_only"}
    ]
    assert fault_rows
    assert all(event.locality_bound == 1 for event in fault_rows)
    temporal = next(event for event in SOURCE_EVENTS if event.event_id == "r0-bulk-readout")
    assert temporal.detector_support == "D_i(t) and D_i(t+1)"


def test_source_gaps_fail_closed_instead_of_claiming_reproduction() -> None:
    audit = audit_catalogue()
    assert audit["outcome"] == "localized_source_gap"
    assert not audit["exact_source_reproduction_ready"]
    assert set(audit["unresolved_event_ids"]) == {
        "r0-bulk-physical",
        "r0-ungauged-readout",
        "r0-known-computational-motion",
    }
    assert len(audit["blocking_gaps"]) == 3


def test_known_motion_is_not_a_fault_and_no_d4_labels_leak_into_r() -> None:
    motion = next(
        event for event in SOURCE_EVENTS if event.event_id == "r0-known-computational-motion"
    )
    assert motion.mapping_status == "known_motion_not_fault"
    serialized = repr(audit_catalogue()).lower()
    assert "blue" not in serialized
    assert "green" not in serialized
    assert "herald" not in serialized
