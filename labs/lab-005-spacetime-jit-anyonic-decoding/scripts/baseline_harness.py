"""Shared-history deterministic scheduling harness for Lab 005.

This preflight verifies timing, causal prefix access, history identity, and a
common truth-free callback across four schedule branches.  It intentionally
contains no logical scorer, stochastic generator, or performance metric.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from lyons_absorber import AbsorberGeometry
from persistent_clusters import PersistentCluster, PersistentClusterTracker
from spacetime_record import CausalRecordPrefix, SpacetimeRecord


Branch = Literal[
    "immediate",
    "fixed_delay_1",
    "jit_lyons_brown",
    "offline_full_history",
]


def _array_payload(array: NDArray[np.generic]) -> dict[str, object]:
    value = np.asarray(array)
    if value.dtype.kind in "OUS":
        data: list[object] = value.astype(str).reshape(-1).tolist()
    else:
        data = value.astype(np.uint8).reshape(-1).tolist()
    return {
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "data": data,
    }


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def visible_history_digest(record: SpacetimeRecord) -> str:
    """Digest decoder-visible full-history fields, excluding truth sidecars."""

    return _digest(
        {
            "syndrome_readout": _array_payload(record.syndrome_readout),
            "syndrome_detectors": _array_payload(record.syndrome_detectors),
            "expected_syndrome_changes": _array_payload(
                record.expected_syndrome_changes
            ),
            "herald_readout": _array_payload(record.herald_readout),
        }
    )


def prefix_digest(prefix: CausalRecordPrefix) -> str:
    return _digest(
        {
            "final_round": prefix.final_round,
            "syndrome_readout": _array_payload(prefix.syndrome_readout),
            "syndrome_detectors": _array_payload(prefix.syndrome_detectors),
            "herald_readout": _array_payload(prefix.herald_readout),
        }
    )


@dataclass(frozen=True)
class InnerDecoderRequest:
    branch: Branch
    trial_id: str
    prefix_digest: str
    prefix: CausalRecordPrefix
    cluster_id: str
    event_ids: tuple[str, ...]
    noncausal: bool

    @property
    def request_digest(self) -> str:
        return _digest(
            {
                "branch": self.branch,
                "trial_id": self.trial_id,
                "prefix_digest": self.prefix_digest,
                "prefix_final_round": self.prefix.final_round,
                "cluster_id": self.cluster_id,
                "event_ids": self.event_ids,
                "noncausal": self.noncausal,
            }
        )


@dataclass(frozen=True)
class InnerDecoderResponse:
    decoder_version: str
    implementation_digest: str
    request_digest: str
    correction_token: str

    @property
    def response_digest(self) -> str:
        return _digest(
            {
                "decoder_version": self.decoder_version,
                "implementation_digest": self.implementation_digest,
                "request_digest": self.request_digest,
                "correction_token": self.correction_token,
            }
        )


@dataclass
class DeterministicInnerDecoder:
    """Protocol fixture shared by all branches; not a physical decoder."""

    version: str = "deterministic-preflight-v1"
    requests: list[InnerDecoderRequest] = field(default_factory=list)

    @property
    def implementation_digest(self) -> str:
        return _digest(
            {
                "protocol": "lab005-inner-decoder-v1",
                "class": type(self).__name__,
                "version": self.version,
            }
        )

    def __call__(self, request: InnerDecoderRequest) -> InnerDecoderResponse:
        self.requests.append(request)
        token = _digest(
            {
                "protocol": "canonical-no-physics-token",
                "cluster_id": request.cluster_id,
                "event_ids": request.event_ids,
            }
        )
        return InnerDecoderResponse(
            decoder_version=self.version,
            implementation_digest=self.implementation_digest,
            request_digest=request.request_digest,
            correction_token=token,
        )


@dataclass(frozen=True)
class PolicyEvent:
    branch: Branch
    round: int
    cluster_id: str
    action: Literal["defer", "invoke"]
    history_digest: str
    request_digest: str | None
    response_digest: str | None
    prefix_final_round: int | None
    noncausal: bool


@dataclass(frozen=True)
class BranchRun:
    branch: Branch
    history_digest: str
    events: tuple[PolicyEvent, ...]


@dataclass(frozen=True)
class BaselineRun:
    trial_id: str
    history_digest: str
    decoder_version: str
    decoder_implementation_digest: str
    branches: tuple[BranchRun, ...]


def _invoke(
    *,
    branch: Branch,
    trial_id: str,
    history_digest: str,
    record: SpacetimeRecord,
    cluster: PersistentCluster,
    round_: int,
    noncausal: bool,
    decoder: DeterministicInnerDecoder,
) -> PolicyEvent:
    prefix = record.causal_prefix(round_)
    request = InnerDecoderRequest(
        branch=branch,
        trial_id=trial_id,
        prefix_digest=prefix_digest(prefix),
        prefix=prefix,
        cluster_id=cluster.persistent_id,
        event_ids=tuple(event.event_id for event in cluster.snapshot.events),
        noncausal=noncausal,
    )
    response = decoder(request)
    if response.decoder_version != decoder.version:
        raise AssertionError("inner decoder changed version across branches")
    if response.implementation_digest != decoder.implementation_digest:
        raise AssertionError("inner decoder changed implementation across branches")
    return PolicyEvent(
        branch=branch,
        round=round_,
        cluster_id=cluster.persistent_id,
        action="invoke",
        history_digest=history_digest,
        request_digest=request.request_digest,
        response_digest=response.response_digest,
        prefix_final_round=prefix.final_round,
        noncausal=noncausal,
    )


def run_shared_history_baselines(
    *,
    trial_id: str,
    record: SpacetimeRecord,
    check_positions: tuple[tuple[int, ...], ...],
    geometry: AbsorberGeometry,
    decoder: DeterministicInnerDecoder,
    connectivity_radius: int = 1,
) -> BaselineRun:
    """Run the four registered timing branches on one immutable history."""

    if not trial_id:
        raise ValueError("shared-history run requires a nonempty trial id")
    final_round = record.readout_rounds - 1
    if final_round < 1:
        raise ValueError("baseline preflight requires at least one detector round")
    history = visible_history_digest(record)
    branches: list[BranchRun] = []

    for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
        tracker = PersistentClusterTracker(check_positions, connectivity_radius)
        first_seen: dict[str, int] = {}
        invoked: set[str] = set()
        events: list[PolicyEvent] = []
        for current_round in range(1, final_round + 1):
            tracked = tracker.update(
                record.causal_prefix(current_round), geometry=geometry
            )
            for cluster in tracked:
                cluster_id = cluster.persistent_id
                first_seen.setdefault(cluster_id, current_round)
                if cluster_id in invoked:
                    continue
                should_invoke = False
                if branch == "immediate":
                    should_invoke = current_round == first_seen[cluster_id]
                elif branch == "fixed_delay_1":
                    should_invoke = current_round >= first_seen[cluster_id] + 1
                else:
                    distance = cluster.snapshot.nearest_absorber_distance
                    if distance is None:
                        raise ValueError(
                            "JIT baseline requires an active nearest absorber"
                        )
                    should_invoke = cluster.snapshot.age >= distance
                    if not should_invoke:
                        events.append(
                            PolicyEvent(
                                branch=branch,
                                round=current_round,
                                cluster_id=cluster_id,
                                action="defer",
                                history_digest=history,
                                request_digest=None,
                                response_digest=None,
                                prefix_final_round=current_round,
                                noncausal=False,
                            )
                        )
                if should_invoke:
                    events.append(
                        _invoke(
                            branch=branch,
                            trial_id=trial_id,
                            history_digest=history,
                            record=record,
                            cluster=cluster,
                            round_=current_round,
                            noncausal=False,
                            decoder=decoder,
                        )
                    )
                    invoked.add(cluster_id)
        branches.append(BranchRun(branch, history, tuple(events)))

    offline_branch: Branch = "offline_full_history"
    offline_tracker = PersistentClusterTracker(check_positions, connectivity_radius)
    offline_clusters = offline_tracker.update(
        record.causal_prefix(final_round), geometry=geometry
    )
    offline_events = tuple(
        _invoke(
            branch=offline_branch,
            trial_id=trial_id,
            history_digest=history,
            record=record,
            cluster=cluster,
            round_=final_round,
            noncausal=True,
            decoder=decoder,
        )
        for cluster in offline_clusters
    )
    branches.append(BranchRun(offline_branch, history, offline_events))

    if visible_history_digest(record) != history:
        raise AssertionError("a scheduling branch mutated the shared history")
    if any(branch.history_digest != history for branch in branches):
        raise AssertionError("baseline branch history digests diverged")
    return BaselineRun(
        trial_id=trial_id,
        history_digest=history,
        decoder_version=decoder.version,
        decoder_implementation_digest=decoder.implementation_digest,
        branches=tuple(branches),
    )
