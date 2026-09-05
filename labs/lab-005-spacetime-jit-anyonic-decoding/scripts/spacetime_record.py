"""Causal binary spacetime-record primitives for Lab 005.

This module is deliberately model-agnostic.  It does not claim to implement
the D(S3) gauging protocol or the D4 fusion model.  A physical model supplies
truth trajectories (and, for the binary preflight, a check-edge incidence
matrix); this layer applies explicit readout faults, constructs adjacent-round
detectors, and exposes causal prefixes without future information.

Herald observations remain raw repeated observations.  Unlike stabilizer
readings, a generic herald does not automatically have a persistent-check
semantics, so this module does not silently turn adjacent herald differences
into detector events.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


BoolArray = NDArray[np.bool_]


def _as_bool(name: str, value: NDArray[np.generic]) -> BoolArray:
    array = np.asarray(value, dtype=np.bool_)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a rank-2 array")
    return array


def syndrome_trajectory_from_edge_faults(
    check_edge_incidence: NDArray[np.generic],
    edge_faults: NDArray[np.generic],
    *,
    initial_edge_state: NDArray[np.generic] | None = None,
) -> BoolArray:
    """Accumulate binary edge faults and return truth syndromes by round.

    ``edge_faults[t, e]`` occurs between readout rounds ``t`` and ``t+1``.
    The returned array therefore has ``rounds + 1`` rows.
    """

    incidence = _as_bool("check_edge_incidence", check_edge_incidence)
    faults = _as_bool("edge_faults", edge_faults)
    checks, edges = incidence.shape
    if faults.shape[1] != edges:
        raise ValueError("edge_faults width must match incidence edge count")

    if initial_edge_state is None:
        state = np.zeros(edges, dtype=np.bool_)
    else:
        state = np.asarray(initial_edge_state, dtype=np.bool_)
        if state.shape != (edges,):
            raise ValueError("initial_edge_state must have shape (edges,)")
        state = state.copy()

    trajectory = np.zeros((faults.shape[0] + 1, checks), dtype=np.bool_)
    trajectory[0] = (incidence @ state) % 2
    for time_index, fault_row in enumerate(faults):
        state ^= fault_row
        trajectory[time_index + 1] = (incidence @ state) % 2
    return trajectory


@dataclass(frozen=True)
class CausalRecordPrefix:
    """The information available immediately after one readout round."""

    final_round: int
    syndrome_readout: BoolArray
    syndrome_detectors: BoolArray
    herald_readout: BoolArray


@dataclass(frozen=True)
class SpacetimeRecord:
    """Truth-labelled record for verification plus a causal decoder view."""

    syndrome_truth: BoolArray
    syndrome_readout: BoolArray
    syndrome_measurement_faults: BoolArray
    syndrome_detectors: BoolArray
    expected_syndrome_changes: BoolArray
    herald_truth: BoolArray
    herald_readout: BoolArray
    herald_measurement_faults: BoolArray

    def __post_init__(self) -> None:
        syndrome_shape = self.syndrome_truth.shape
        if len(syndrome_shape) != 2 or syndrome_shape[0] < 1:
            raise ValueError("syndrome_truth must contain at least one round")
        for name in ("syndrome_readout", "syndrome_measurement_faults"):
            if getattr(self, name).shape != syndrome_shape:
                raise ValueError(f"{name} must match syndrome_truth")

        detector_shape = (syndrome_shape[0] - 1, syndrome_shape[1])
        for name in ("syndrome_detectors", "expected_syndrome_changes"):
            if getattr(self, name).shape != detector_shape:
                raise ValueError(f"{name} has the wrong detector shape")

        herald_shape = self.herald_truth.shape
        if len(herald_shape) != 2 or herald_shape[0] != syndrome_shape[0]:
            raise ValueError("herald_truth must have one row per readout round")
        for name in ("herald_readout", "herald_measurement_faults"):
            if getattr(self, name).shape != herald_shape:
                raise ValueError(f"{name} must match herald_truth")

        if not np.array_equal(
            self.syndrome_readout,
            self.syndrome_truth ^ self.syndrome_measurement_faults,
        ):
            raise ValueError("syndrome readout/fault identity is violated")
        if not np.array_equal(
            self.herald_readout,
            self.herald_truth ^ self.herald_measurement_faults,
        ):
            raise ValueError("herald readout/fault identity is violated")
        expected_detectors = (
            self.syndrome_readout[1:]
            ^ self.syndrome_readout[:-1]
            ^ self.expected_syndrome_changes
        )
        if not np.array_equal(self.syndrome_detectors, expected_detectors):
            raise ValueError("adjacent-round detector identity is violated")

    @property
    def readout_rounds(self) -> int:
        return int(self.syndrome_truth.shape[0])

    def causal_prefix(self, final_round: int) -> CausalRecordPrefix:
        """Return decoder-visible arrays through ``final_round``, inclusive."""

        if not 0 <= final_round < self.readout_rounds:
            raise ValueError("final_round is outside the record")
        return CausalRecordPrefix(
            final_round=final_round,
            syndrome_readout=self.syndrome_readout[: final_round + 1].copy(),
            syndrome_detectors=self.syndrome_detectors[:final_round].copy(),
            herald_readout=self.herald_readout[: final_round + 1].copy(),
        )


def build_record_from_fault_masks(
    syndrome_truth: NDArray[np.generic],
    syndrome_measurement_faults: NDArray[np.generic],
    herald_truth: NDArray[np.generic],
    herald_measurement_faults: NDArray[np.generic],
    *,
    expected_syndrome_changes: NDArray[np.generic] | None = None,
) -> SpacetimeRecord:
    """Build a deterministic record from supplied truth and readout faults."""

    syndrome = _as_bool("syndrome_truth", syndrome_truth)
    syndrome_faults = _as_bool(
        "syndrome_measurement_faults", syndrome_measurement_faults
    )
    herald = _as_bool("herald_truth", herald_truth)
    herald_faults = _as_bool("herald_measurement_faults", herald_measurement_faults)
    if syndrome_faults.shape != syndrome.shape:
        raise ValueError("syndrome measurement faults must match syndrome truth")
    if herald.shape[0] != syndrome.shape[0] or herald_faults.shape != herald.shape:
        raise ValueError("herald arrays must share the syndrome round count")

    if expected_syndrome_changes is None:
        expected_changes = np.zeros(
            (syndrome.shape[0] - 1, syndrome.shape[1]), dtype=np.bool_
        )
    else:
        expected_changes = _as_bool(
            "expected_syndrome_changes", expected_syndrome_changes
        )
        if expected_changes.shape != (syndrome.shape[0] - 1, syndrome.shape[1]):
            raise ValueError("expected syndrome changes have the wrong shape")

    syndrome_readout = syndrome ^ syndrome_faults
    herald_readout = herald ^ herald_faults
    detectors = (
        syndrome_readout[1:] ^ syndrome_readout[:-1] ^ expected_changes
    )
    return SpacetimeRecord(
        syndrome_truth=syndrome.copy(),
        syndrome_readout=syndrome_readout,
        syndrome_measurement_faults=syndrome_faults.copy(),
        syndrome_detectors=detectors,
        expected_syndrome_changes=expected_changes.copy(),
        herald_truth=herald.copy(),
        herald_readout=herald_readout,
        herald_measurement_faults=herald_faults.copy(),
    )
