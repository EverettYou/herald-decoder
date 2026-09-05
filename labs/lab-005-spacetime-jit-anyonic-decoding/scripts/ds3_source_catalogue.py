"""Source-completeness catalogue for the Lab 005 D(S3) reproduction branch.

This is an audit object, not a circuit simulator.  It records what
Lyons--Brown specify exactly at stabilizer/detector level, what is available
only as a coarse-grained locality bound, and which circuit-to-detector maps are
still missing.  Missing details fail closed rather than being inferred from
the unrelated D4 or generic herald layers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


MappingStatus = Literal[
    "stabilizer_level_exact",
    "coarse_grained_bound_only",
    "explicitly_absent",
    "known_motion_not_fault",
]


@dataclass(frozen=True)
class SourceEventClass:
    event_id: str
    context: str
    physical_location: str
    time_support: str
    detector_support: str
    phase_ownership: str
    source_locator: str
    mapping_status: MappingStatus
    locality_bound: int | None
    unresolved_detail: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SOURCE_EVENTS = (
    SourceEventClass(
        event_id="r0-bulk-physical",
        context="bulk D(S3)",
        physical_location="one local physical fault in a spacetime unit cube",
        time_support="one coarse-grained spatial time slice",
        detector_support="spatial-string endpoints within the 1-neighborhood of the fault support",
        phase_ownership="bulk D(S3)",
        source_locator="Lyons-Brown pp.2-3; Methods C.1; Eq. (36); Methods C.2 after Eq. (40)",
        mapping_status="coarse_grained_bound_only",
        locality_bound=1,
        unresolved_detail="The source does not enumerate a gate-level D(S3) stabilizer-extraction circuit and its exact detector set for every primitive circuit fault.",
    ),
    SourceEventClass(
        event_id="r0-bulk-readout",
        context="bulk D(S3)",
        physical_location="one false stabilizer reading S_i(t)",
        time_support="measurement rounds t and t+1",
        detector_support="D_i(t) and D_i(t+1)",
        phase_ownership="bulk D(S3)",
        source_locator="Lyons-Brown pp.2-3, D_i(t)=S_i(t)-S_i(t-1) and the false-readout example",
        mapping_status="stabilizer_level_exact",
        locality_bound=1,
    ),
    SourceEventClass(
        event_id="r0-boundary-mu",
        context="D(S3)-D(Z3) gauging boundary",
        physical_location="mu stabilizer comparison at ungauging time t*",
        time_support="t*-1 and t*",
        detector_support="D_p^mu(t*)=beta_p(t*)-beta_p(t*-1)",
        phase_ownership="D(S3)-D(Z3) boundary",
        source_locator="Lyons-Brown Methods B.3, Eq. (34), p.11",
        mapping_status="stabilizer_level_exact",
        locality_bound=1,
    ),
    SourceEventClass(
        event_id="r0-boundary-em",
        context="D(S3)-D(Z3) gauging boundary",
        physical_location="e/m counterpart stabilizer comparison at ungauging time t*",
        time_support="t*-1 and t*",
        detector_support="D_v/p^(e/m)(t*)=S_v/p^Z3(t*)-S_v/p(t*-1)",
        phase_ownership="D(S3)-D(Z3) boundary",
        source_locator="Lyons-Brown Methods B.3, Eq. (35), p.11",
        mapping_status="stabilizer_level_exact",
        locality_bound=1,
    ),
    SourceEventClass(
        event_id="r0-boundary-eta",
        context="D(S3)-D(Z3) gauging boundary",
        physical_location="eta excitation at the gauging boundary",
        time_support="boundary lifetime",
        detector_support="no boundary-spanning detector; eta may be absorbed or emitted",
        phase_ownership="D(S3)-D(Z3) boundary",
        source_locator="Lyons-Brown Methods B.3 immediately after Eqs. (34)-(35), p.11",
        mapping_status="explicitly_absent",
        locality_bound=None,
    ),
    SourceEventClass(
        event_id="r0-ungauged-readout",
        context="ungauged D(Z3) region",
        physical_location="one local stabilizer or ungauging-readout fault",
        time_support="one local circuit neighborhood around the readout round",
        detector_support="local D(Z3) stabilizer changes and corrected sigma-Z loop/open-string constraints",
        phase_ownership="ungauged D(Z3)",
        source_locator="Lyons-Brown Methods B.3-B.4, pp.11-13; Methods C.1",
        mapping_status="coarse_grained_bound_only",
        locality_bound=1,
        unresolved_detail="The source gives stabilizer and loop constraints but not a complete primitive-fault-to-detector table for the ungauging, waiting, and re-gauging circuits.",
    ),
    SourceEventClass(
        event_id="r0-known-computational-motion",
        context="bulk D(S3)",
        physical_location="declared computational-anyon position or motion",
        time_support="known scheduled trajectory",
        detector_support="detector values are adjusted using the known computational-anyon locations",
        phase_ownership="schedule-owned known motion, not a fault",
        source_locator="Lyons-Brown p.3, final paragraph of Detectors",
        mapping_status="known_motion_not_fault",
        locality_bound=None,
        unresolved_detail="The paper states the adjustment rule operationally but does not provide a complete index-level formula for arbitrary motion in the microscopic D(S3) lattice.",
    ),
)


BLOCKING_GAPS = (
    "gate-level D(S3) stabilizer-extraction circuits and exact detector support for every primitive circuit fault",
    "complete primitive-fault catalogue for ungauging, waiting in D(Z3), and re-gauging",
    "index-level detector adjustment for arbitrary known computational-anyon motion",
)


def audit_catalogue() -> dict[str, object]:
    contexts = {event.context for event in SOURCE_EVENTS}
    required = {
        "bulk D(S3)",
        "D(S3)-D(Z3) gauging boundary",
        "ungauged D(Z3) region",
    }
    unresolved = tuple(
        event.event_id for event in SOURCE_EVENTS if event.unresolved_detail is not None
    )
    return {
        "schema_version": 1,
        "branch": "R-ds3-source",
        "contexts_complete": contexts.issuperset(required),
        "source_rows": [event.to_dict() for event in SOURCE_EVENTS],
        "unresolved_event_ids": list(unresolved),
        "blocking_gaps": list(BLOCKING_GAPS),
        "exact_source_reproduction_ready": False,
        "outcome": "localized_source_gap",
    }
