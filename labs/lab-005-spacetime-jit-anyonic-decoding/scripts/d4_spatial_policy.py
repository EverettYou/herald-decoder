"""Observation-only Lab 004 D4 policy adapter for Lab 005.

The online entry points in this module never accept a physical-error chain,
future spacetime record, or logical label.  A scheduler supplies one committed
spatial snapshot, receives a flux action, and may later supply a physically
generated post-action charge record.  Simulation truth remains outside this
module.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Literal, Mapping

import numpy as np


LABS_ROOT = Path(__file__).resolve().parents[2]
LAB004_SCRIPTS = LABS_ROOT / "lab-004-d4-intrinsic-heralded-decoding" / "scripts"
if str(LAB004_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LAB004_SCRIPTS))

from d4_charge import recover_postflux_charges  # noqa: E402
from d4_honeycomb import paper_periodic_honeycomb  # noqa: E402
from d4_matching import (  # noqa: E402
    decode_flux_syndrome,
    edge_chain_boundary,
    published_herald_weights,
    syndrome_only_weights,
)
from d4_postflux import (  # noqa: E402
    PeriodicPostFluxRelations,
    accumulate_postflux_constraints,
)
from spacetime_record import CausalRecordPrefix  # noqa: E402


SCHEMA_VERSION = 1
MODEL_ID = "paper_periodic_coloured_honeycomb_d4"
DecoderMode = Literal["syndrome_only", "heralded"]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_POLICY_SOURCE_HASHES = {
    "d4_honeycomb.py": "0895892c00f1f629ec469d4f7b4e42fb8e83bc07666edbc3b8fc26a1f30eb869",
    "d4_matching.py": "1ad1c96af3bf98353c89820b68eb07183a49c954650c51218ca5c1b5c211739e",
    "d4_charge.py": "c7b528d343abedb052e6bea7f5c29f65de2bab5dae96befa339763198bb17e9a",
    "d4_postflux.py": "5435f1fcea89c9eccf369f8bfef44b23deea1ebe954b5e0f1dea5fce0cf12658",
}


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def causal_prefix_digest(prefix: CausalRecordPrefix) -> str:
    """Digest exactly the causal arrays carried by one prefix, never the future."""

    return canonical_digest(
        {
            "final_round": int(prefix.final_round),
            "syndrome_readout": prefix.syndrome_readout.astype(int).tolist(),
            "syndrome_detectors": prefix.syndrome_detectors.astype(int).tolist(),
            "herald_readout": prefix.herald_readout.astype(int).tolist(),
        }
    )


def _verify_policy_sources() -> str:
    for name, expected in _POLICY_SOURCE_HASHES.items():
        actual = hashlib.sha256((LAB004_SCRIPTS / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Lab 004 policy source changed: {name}")
    return canonical_digest(_POLICY_SOURCE_HASHES)


def _exact_keys(payload: Mapping[str, Any], expected: set[str]) -> None:
    actual = set(payload)
    if actual != expected:
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise ValueError(f"invalid fields; extra={extra}, missing={missing}")


def _validate_digest(name: str, value: str) -> str:
    text = str(value)
    if _SHA256.fullmatch(text) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _sorted_unique_indices(name: str, values: Any, upper: int) -> tuple[int, ...]:
    result = tuple(int(value) for value in values)
    if result != tuple(sorted(set(result))):
        raise ValueError(f"{name} must be sorted and unique")
    if any(value < 0 or value >= upper for value in result):
        raise ValueError(f"{name} contains an out-of-range index")
    return result


def _parse_measurements(
    name: str, values: Any, upper: int
) -> tuple[tuple[int, int], ...]:
    parsed: list[tuple[int, int]] = []
    for item in values:
        if not isinstance(item, Mapping):
            raise ValueError(f"{name} entries must be objects")
        _exact_keys(item, {"vertex", "outcome"})
        vertex = int(item["vertex"])
        outcome = int(item["outcome"])
        if not 0 <= vertex < upper or outcome not in (0, 1):
            raise ValueError(f"{name} contains an invalid vertex or outcome")
        parsed.append((vertex, outcome))
    result = tuple(parsed)
    if tuple(vertex for vertex, _ in result) != tuple(
        sorted({vertex for vertex, _ in result})
    ):
        raise ValueError(f"{name} must be sorted with unique vertices")
    return result


@dataclass(frozen=True)
class D4SpatialCommitRequestV1:
    schema_version: int
    request_id: str
    model_id: str
    size: int
    mode: DecoderMode
    decision_round: int
    committed_through_round: int
    flux_syndrome_vertices: tuple[int, ...]
    initial_charge_measurements: tuple[tuple[int, int], ...]
    causal_prefix_digest: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "D4SpatialCommitRequestV1":
        _exact_keys(
            payload,
            {
                "schema_version",
                "request_id",
                "model_id",
                "size",
                "mode",
                "decision_round",
                "committed_through_round",
                "flux_syndrome_vertices",
                "initial_charge_measurements",
                "causal_prefix_digest",
            },
        )
        size = int(payload["size"])
        lattice = paper_periodic_honeycomb(size)
        mode = str(payload["mode"])
        measurements = _parse_measurements(
            "initial_charge_measurements",
            payload["initial_charge_measurements"],
            lattice.vertex_count,
        )
        request = cls(
            schema_version=int(payload["schema_version"]),
            request_id=str(payload["request_id"]),
            model_id=str(payload["model_id"]),
            size=size,
            mode=mode,  # type: ignore[arg-type]
            decision_round=int(payload["decision_round"]),
            committed_through_round=int(payload["committed_through_round"]),
            flux_syndrome_vertices=_sorted_unique_indices(
                "flux_syndrome_vertices",
                payload["flux_syndrome_vertices"],
                lattice.vertex_count,
            ),
            initial_charge_measurements=measurements,
            causal_prefix_digest=_validate_digest(
                "causal_prefix_digest", str(payload["causal_prefix_digest"])
            ),
        )
        request.validate()
        return request

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.model_id != MODEL_ID:
            raise ValueError("unsupported D4 spatial interface schema or model")
        if self.size not in (2, 3):
            raise ValueError("the validated D4 adapter supports paper L=2 or L=3")
        lattice = paper_periodic_honeycomb(self.size)
        if not self.request_id:
            raise ValueError("request_id must be nonempty")
        if self.mode not in ("syndrome_only", "heralded"):
            raise ValueError("mode must be syndrome_only or heralded")
        if self.decision_round < 0 or self.committed_through_round != self.decision_round:
            raise ValueError("stage 1 must contain exactly the committed causal round")
        if len(self.flux_syndrome_vertices) % 2:
            raise ValueError("periodic D4 flux syndrome must have even cardinality")
        _sorted_unique_indices(
            "flux_syndrome_vertices",
            self.flux_syndrome_vertices,
            lattice.vertex_count,
        )
        if tuple(vertex for vertex, _ in self.initial_charge_measurements) != tuple(
            sorted({vertex for vertex, _ in self.initial_charge_measurements})
        ):
            raise ValueError("initial charge measurements must be sorted and unique")
        if any(
            vertex < 0
            or vertex >= lattice.vertex_count
            or outcome not in (0, 1)
            for vertex, outcome in self.initial_charge_measurements
        ):
            raise ValueError("initial charge measurements contain invalid values")
        if self.mode == "syndrome_only" and self.initial_charge_measurements:
            raise ValueError("syndrome_only mode cannot receive charge measurements")
        _validate_digest("causal_prefix_digest", self.causal_prefix_digest)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "model_id": self.model_id,
            "size": self.size,
            "mode": self.mode,
            "decision_round": self.decision_round,
            "committed_through_round": self.committed_through_round,
            "flux_syndrome_vertices": list(self.flux_syndrome_vertices),
            "initial_charge_measurements": [
                {"vertex": vertex, "outcome": outcome}
                for vertex, outcome in self.initial_charge_measurements
            ],
            "causal_prefix_digest": self.causal_prefix_digest,
        }


@dataclass(frozen=True)
class D4FluxActionV1:
    request_id: str
    status: str
    correction_edges: tuple[int, ...]
    objective_weight: float
    policy_source_digest: str
    action_digest: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "D4FluxActionV1":
        _exact_keys(
            payload,
            {
                "request_id",
                "status",
                "correction_edges",
                "objective_weight",
                "policy_source_digest",
                "action_digest",
            },
        )
        action = cls(
            request_id=str(payload["request_id"]),
            status=str(payload["status"]),
            correction_edges=tuple(int(edge) for edge in payload["correction_edges"]),
            objective_weight=float(payload["objective_weight"]),
            policy_source_digest=_validate_digest(
                "policy_source_digest", str(payload["policy_source_digest"])
            ),
            action_digest=_validate_digest("action_digest", str(payload["action_digest"])),
        )
        if canonical_digest(action.unsigned_dict()) != action.action_digest:
            raise ValueError("flux action digest does not match its contents")
        return action

    def validate(self, *, edge_count: int) -> None:
        if not self.request_id or self.status != "action":
            raise ValueError("invalid flux action identity or status")
        _sorted_unique_indices("correction_edges", self.correction_edges, edge_count)
        if not np.isfinite(self.objective_weight):
            raise ValueError("flux objective must be finite")
        if self.policy_source_digest != _verify_policy_sources():
            raise ValueError("flux action policy source digest is stale")
        if canonical_digest(self.unsigned_dict()) != self.action_digest:
            raise ValueError("flux action digest does not match its contents")

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "correction_edges": list(self.correction_edges),
            "objective_weight": self.objective_weight,
            "policy_source_digest": self.policy_source_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "action_digest": self.action_digest}


@dataclass(frozen=True)
class D4PostFluxObservationV1:
    request_id: str
    action_digest: str
    observation_round: int
    active_vertices: tuple[int, ...]
    entanglement_pairs: tuple[tuple[int, int], ...]
    charge_measurements: tuple[tuple[int, int], ...]
    observation_digest: str

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any], *, vertex_count: int
    ) -> "D4PostFluxObservationV1":
        _exact_keys(
            payload,
            {
                "request_id",
                "action_digest",
                "observation_round",
                "measurement_layout",
                "charge_measurements",
                "observation_digest",
            },
        )
        layout = payload["measurement_layout"]
        if not isinstance(layout, Mapping):
            raise ValueError("measurement_layout must be an object")
        _exact_keys(layout, {"active_vertices", "entanglement_pairs"})
        active = _sorted_unique_indices(
            "active_vertices", layout["active_vertices"], vertex_count
        )
        pairs = tuple(tuple(int(value) for value in pair) for pair in layout["entanglement_pairs"])
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError("each entanglement pair must have two endpoints")
        canonical_pairs = tuple(sorted(set(tuple(sorted(pair)) for pair in pairs)))
        if pairs != canonical_pairs:
            raise ValueError("entanglement_pairs must be canonical, sorted, and unique")
        measurements = _parse_measurements(
            "charge_measurements", payload["charge_measurements"], vertex_count
        )
        observation = cls(
            request_id=str(payload["request_id"]),
            action_digest=_validate_digest("action_digest", str(payload["action_digest"])),
            observation_round=int(payload["observation_round"]),
            active_vertices=active,
            entanglement_pairs=canonical_pairs,
            charge_measurements=measurements,
            observation_digest=_validate_digest(
                "observation_digest", str(payload["observation_digest"])
            ),
        )
        observation.validate(vertex_count=vertex_count)
        return observation

    def validate(self, *, vertex_count: int) -> None:
        if not self.request_id or self.observation_round < 0:
            raise ValueError("invalid post-flux observation identity or round")
        _validate_digest("action_digest", self.action_digest)
        _sorted_unique_indices("active_vertices", self.active_vertices, vertex_count)
        canonical_pairs = tuple(
            sorted(set(tuple(sorted(pair)) for pair in self.entanglement_pairs))
        )
        if self.entanglement_pairs != canonical_pairs:
            raise ValueError("entanglement pairs must be canonical, sorted, and unique")
        active = set(self.active_vertices)
        if any(
            len(pair) != 2
            or pair[0] < 0
            or pair[1] >= vertex_count
            or pair[0] not in active
            or pair[1] not in active
            for pair in self.entanglement_pairs
        ):
            raise ValueError("entanglement pairs must join valid active vertices")
        if tuple(vertex for vertex, _ in self.charge_measurements) != tuple(
            sorted({vertex for vertex, _ in self.charge_measurements})
        ) or any(
            vertex < 0 or vertex >= vertex_count or outcome not in (0, 1)
            for vertex, outcome in self.charge_measurements
        ):
            raise ValueError("charge measurements must be sparse sorted binary records")
        _validate_digest("observation_digest", self.observation_digest)
        if canonical_digest(self.unsigned_dict()) != self.observation_digest:
            raise ValueError("post-flux observation digest does not match its contents")

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action_digest": self.action_digest,
            "observation_round": self.observation_round,
            "measurement_layout": {
                "active_vertices": list(self.active_vertices),
                "entanglement_pairs": [list(pair) for pair in self.entanglement_pairs],
            },
            "charge_measurements": [
                {"vertex": vertex, "outcome": outcome}
                for vertex, outcome in self.charge_measurements
            ],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "observation_digest": self.observation_digest}


@dataclass(frozen=True)
class D4ChargeActionV1:
    request_id: str
    status: str
    blue_correction_edges: tuple[int, ...]
    green_correction_edges: tuple[int, ...]
    blue_objective_weight: float
    green_objective_weight: float
    action_digest: str

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "blue_correction_edges": list(self.blue_correction_edges),
            "green_correction_edges": list(self.green_correction_edges),
            "blue_objective_weight": self.blue_objective_weight,
            "green_objective_weight": self.green_objective_weight,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "action_digest": self.action_digest}


def decode_flux_action(request: D4SpatialCommitRequestV1) -> D4FluxActionV1:
    """Return the public first-stage action from decoder-visible fields only."""

    request.validate()
    lattice = paper_periodic_honeycomb(request.size)
    syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
    syndrome[list(request.flux_syndrome_vertices)] = 1
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    for vertex, outcome in request.initial_charge_measurements:
        charge[vertex] = outcome
    weights = (
        syndrome_only_weights(lattice)
        if request.mode == "syndrome_only"
        else published_herald_weights(lattice, charge)
    )
    decoded = decode_flux_syndrome(lattice, syndrome, weights)
    source_digest = _verify_policy_sources()
    unsigned = {
        "request_id": request.request_id,
        "status": "action",
        "correction_edges": [int(edge) for edge in np.flatnonzero(decoded.correction)],
        "objective_weight": float(decoded.objective_weight),
        "policy_source_digest": source_digest,
    }
    return D4FluxActionV1(
        request_id=request.request_id,
        status="action",
        correction_edges=tuple(unsigned["correction_edges"]),
        objective_weight=float(decoded.objective_weight),
        policy_source_digest=source_digest,
        action_digest=canonical_digest(unsigned),
    )


def decode_charge_action(
    request: D4SpatialCommitRequestV1,
    flux_action: D4FluxActionV1,
    observation: D4PostFluxObservationV1,
) -> D4ChargeActionV1:
    """Return the public second-stage action from a bound post-action record."""

    request.validate()
    if flux_action.request_id != request.request_id:
        raise ValueError("flux action belongs to another request")
    lattice = paper_periodic_honeycomb(request.size)
    flux_action.validate(edge_count=lattice.edge_count)
    supplied_correction = np.zeros(lattice.edge_count, dtype=np.uint8)
    supplied_correction[list(flux_action.correction_edges)] = 1
    supplied_syndrome = tuple(
        int(vertex)
        for vertex in np.flatnonzero(edge_chain_boundary(lattice, supplied_correction))
    )
    if supplied_syndrome != request.flux_syndrome_vertices:
        raise ValueError("flux action does not reproduce the committed syndrome")
    if observation.request_id != request.request_id:
        raise ValueError("post-flux observation belongs to another request")
    if observation.action_digest != flux_action.action_digest:
        raise ValueError("post-flux observation is not bound to the flux action")
    if observation.observation_round < request.decision_round:
        raise ValueError("post-flux observation predates the committed action")

    observation.validate(vertex_count=lattice.vertex_count)
    measured_vertices = tuple(vertex for vertex, _ in observation.charge_measurements)
    if measured_vertices != observation.active_vertices:
        raise ValueError("charge measurements must cover exactly the active vertices")
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    for vertex, outcome in observation.charge_measurements:
        charge[vertex] = outcome
    relations = PeriodicPostFluxRelations(
        applications=(),
        active_vertices=observation.active_vertices,
        entanglement_pairs=observation.entanglement_pairs,
    )
    support = accumulate_postflux_constraints(
        lattice.vertex_count,
        observation.active_vertices,
        observation.entanglement_pairs,
        charge,
    )
    if not support.allowed:
        raise ValueError("post-flux charge record violates its parity support")
    recovered = recover_postflux_charges(
        lattice,
        relations,
        charge,
        flux_components_homologically_trivial=True,
    )
    unsigned = {
        "request_id": request.request_id,
        "status": "action",
        "blue_correction_edges": [
            int(edge) for edge in np.flatnonzero(recovered.blue.correction)
        ],
        "green_correction_edges": [
            int(edge) for edge in np.flatnonzero(recovered.green.correction)
        ],
        "blue_objective_weight": float(recovered.blue.objective_weight),
        "green_objective_weight": float(recovered.green.objective_weight),
    }
    return D4ChargeActionV1(
        request_id=request.request_id,
        status="action",
        blue_correction_edges=tuple(unsigned["blue_correction_edges"]),
        green_correction_edges=tuple(unsigned["green_correction_edges"]),
        blue_objective_weight=float(recovered.blue.objective_weight),
        green_objective_weight=float(recovered.green.objective_weight),
        action_digest=canonical_digest(unsigned),
    )
