"""Generic repeated-measurement history generator for Lab 005.

This module is the registered ``G-generic-preflight`` layer.  It samples a
phenomenological binary data/syndrome record and a categorical
``none``/``blue``/``green`` herald record.  It is intentionally neither a
Lyons--Brown D(S3) circuit reproduction nor a derived noisy D4 model.

Only causal readout prefixes are passed to scheduling or decoder code.  Truth,
fault masks, and raw random variates remain verification sidecars.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from spacetime_record import CausalRecordPrefix, syndrome_trajectory_from_edge_faults


BoolArray = NDArray[np.bool_]
FloatArray = NDArray[np.float64]
StringArray = NDArray[np.str_]

HERALD_LABELS = ("none", "blue", "green")
_HERALD_LABEL_SET = frozenset(HERALD_LABELS)


def _as_bool_2d(name: str, value: NDArray[np.generic]) -> BoolArray:
    array = np.asarray(value, dtype=np.bool_)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a rank-2 array")
    return array


def _as_herald_2d(name: str, value: NDArray[np.generic]) -> StringArray:
    array = np.asarray(value, dtype="<U5")
    if array.ndim != 2:
        raise ValueError(f"{name} must be a rank-2 array")
    invalid = set(np.unique(array)) - _HERALD_LABEL_SET
    if invalid:
        raise ValueError(f"{name} contains invalid herald labels: {sorted(invalid)}")
    return array


def _freeze_copy(value: NDArray[np.generic]) -> NDArray[np.generic]:
    result = np.array(value, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class GenericNoiseParameters:
    """Registered independent phenomenological channel probabilities."""

    p_data: float
    p_syndrome: float
    p_fp: float
    p_fn: float
    p_confuse: float

    def __post_init__(self) -> None:
        for name in ("p_data", "p_syndrome", "p_fp", "p_fn", "p_confuse"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.p_fn + self.p_confuse > 1.0:
            raise ValueError("p_fn + p_confuse must not exceed one")


def herald_confusion_matrix(parameters: GenericNoiseParameters) -> FloatArray:
    """Return rows indexed by true label and columns by observed label."""

    matrix = np.asarray(
        [
            [1.0 - parameters.p_fp, parameters.p_fp / 2.0, parameters.p_fp / 2.0],
            [parameters.p_fn, 1.0 - parameters.p_fn - parameters.p_confuse, parameters.p_confuse],
            [parameters.p_fn, parameters.p_confuse, 1.0 - parameters.p_fn - parameters.p_confuse],
        ],
        dtype=np.float64,
    )
    if np.any(matrix < 0.0) or not np.allclose(matrix.sum(axis=1), 1.0):
        raise AssertionError("registered herald confusion matrix is not stochastic")
    return matrix


def _sample_herald_readout(
    truth: StringArray,
    uniforms: FloatArray,
    parameters: GenericNoiseParameters,
) -> tuple[StringArray, StringArray]:
    """Apply the registered categorical channel to fixed U[0,1) draws."""

    if uniforms.shape != truth.shape:
        raise ValueError("herald_uniforms must match herald_truth")
    if np.any(~np.isfinite(uniforms)) or np.any(uniforms < 0.0) or np.any(uniforms >= 1.0):
        raise ValueError("herald_uniforms must lie in [0, 1)")

    readout = np.empty(truth.shape, dtype="<U5")
    error_kind = np.full(truth.shape, "none", dtype="<U16")

    none = truth == "none"
    blue = truth == "blue"
    green = truth == "green"

    readout[none] = "none"
    false_positive = none & (uniforms >= 1.0 - parameters.p_fp)
    readout[false_positive & (uniforms < 1.0 - parameters.p_fp / 2.0)] = "blue"
    readout[false_positive & (uniforms >= 1.0 - parameters.p_fp / 2.0)] = "green"
    error_kind[false_positive] = "false_positive"

    false_negative_blue = blue & (uniforms < parameters.p_fn)
    correct_blue = blue & ~false_negative_blue & (
        uniforms < 1.0 - parameters.p_confuse
    )
    confused_blue = blue & ~(false_negative_blue | correct_blue)
    readout[false_negative_blue] = "none"
    readout[correct_blue] = "blue"
    readout[confused_blue] = "green"
    error_kind[false_negative_blue] = "false_negative"
    error_kind[confused_blue] = "label_confusion"

    false_negative_green = green & (uniforms < parameters.p_fn)
    confused_green = green & ~false_negative_green & (
        uniforms < parameters.p_fn + parameters.p_confuse
    )
    correct_green = green & ~(false_negative_green | confused_green)
    readout[false_negative_green] = "none"
    readout[confused_green] = "blue"
    readout[correct_green] = "green"
    error_kind[false_negative_green] = "false_negative"
    error_kind[confused_green] = "label_confusion"

    return readout, error_kind


@dataclass(frozen=True)
class GenericRepeatedMeasurementHistory:
    """Immutable generated history with private truth/fault sidecars."""

    master_seed: int
    parameters: GenericNoiseParameters
    check_edge_incidence: BoolArray
    edge_faults: BoolArray
    syndrome_truth: BoolArray
    syndrome_readout: BoolArray
    syndrome_measurement_faults: BoolArray
    syndrome_detectors: BoolArray
    expected_syndrome_changes: BoolArray
    herald_truth: StringArray
    herald_readout: StringArray
    herald_error_kind: StringArray
    herald_uniforms: FloatArray

    def __post_init__(self) -> None:
        syndrome_shape = self.syndrome_truth.shape
        if len(syndrome_shape) != 2 or syndrome_shape[0] < 1:
            raise ValueError("syndrome_truth must contain at least one round")
        if self.syndrome_readout.shape != syndrome_shape:
            raise ValueError("syndrome_readout must match syndrome_truth")
        if self.syndrome_measurement_faults.shape != syndrome_shape:
            raise ValueError("syndrome_measurement_faults must match syndrome_truth")
        detector_shape = (syndrome_shape[0] - 1, syndrome_shape[1])
        if self.syndrome_detectors.shape != detector_shape:
            raise ValueError("syndrome_detectors has the wrong shape")
        if self.expected_syndrome_changes.shape != detector_shape:
            raise ValueError("expected_syndrome_changes has the wrong shape")
        if self.herald_truth.shape[0] != syndrome_shape[0]:
            raise ValueError("herald truth must have one row per readout round")
        for name in ("herald_readout", "herald_error_kind", "herald_uniforms"):
            if getattr(self, name).shape != self.herald_truth.shape:
                raise ValueError(f"{name} must match herald_truth")

        if not np.array_equal(
            self.syndrome_readout,
            self.syndrome_truth ^ self.syndrome_measurement_faults,
        ):
            raise ValueError("syndrome readout/fault identity is violated")
        expected_detectors = (
            self.syndrome_readout[1:]
            ^ self.syndrome_readout[:-1]
            ^ self.expected_syndrome_changes
        )
        if not np.array_equal(self.syndrome_detectors, expected_detectors):
            raise ValueError("adjacent-round detector identity is violated")

        for field_name in (
            "check_edge_incidence",
            "edge_faults",
            "syndrome_truth",
            "syndrome_readout",
            "syndrome_measurement_faults",
            "syndrome_detectors",
            "expected_syndrome_changes",
            "herald_truth",
            "herald_readout",
            "herald_error_kind",
            "herald_uniforms",
        ):
            object.__setattr__(self, field_name, _freeze_copy(getattr(self, field_name)))

    @property
    def readout_rounds(self) -> int:
        return int(self.syndrome_truth.shape[0])

    def causal_prefix(self, final_round: int) -> CausalRecordPrefix:
        """Expose readouts through ``final_round`` but never truth sidecars."""

        if not 0 <= final_round < self.readout_rounds:
            raise ValueError("final_round is outside the history")
        return CausalRecordPrefix(
            final_round=final_round,
            syndrome_readout=self.syndrome_readout[: final_round + 1].copy(),
            syndrome_detectors=self.syndrome_detectors[:final_round].copy(),
            herald_readout=self.herald_readout[: final_round + 1].copy(),
        )


def build_generic_history_from_draws(
    *,
    master_seed: int,
    parameters: GenericNoiseParameters,
    check_edge_incidence: NDArray[np.generic],
    edge_faults: NDArray[np.generic],
    syndrome_measurement_faults: NDArray[np.generic],
    herald_truth: NDArray[np.generic],
    herald_uniforms: NDArray[np.generic],
    initial_edge_state: NDArray[np.generic] | None = None,
    expected_syndrome_changes: NDArray[np.generic] | None = None,
) -> GenericRepeatedMeasurementHistory:
    """Build a deterministic generic history from explicit channel draws."""

    if not isinstance(master_seed, (int, np.integer)) or int(master_seed) < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    incidence = _as_bool_2d("check_edge_incidence", check_edge_incidence)
    faults = _as_bool_2d("edge_faults", edge_faults)
    syndrome_faults = _as_bool_2d(
        "syndrome_measurement_faults", syndrome_measurement_faults
    )
    herald = _as_herald_2d("herald_truth", herald_truth)
    uniforms = np.asarray(herald_uniforms, dtype=np.float64)
    if uniforms.ndim != 2:
        raise ValueError("herald_uniforms must be a rank-2 array")

    syndrome_truth = syndrome_trajectory_from_edge_faults(
        incidence, faults, initial_edge_state=initial_edge_state
    )
    if syndrome_faults.shape != syndrome_truth.shape:
        raise ValueError("syndrome measurement faults have the wrong shape")
    if herald.shape[0] != syndrome_truth.shape[0]:
        raise ValueError("herald truth must have one row per readout round")

    if expected_syndrome_changes is None:
        expected_changes = np.zeros_like(syndrome_truth[1:])
    else:
        expected_changes = _as_bool_2d(
            "expected_syndrome_changes", expected_syndrome_changes
        )
        if expected_changes.shape != syndrome_truth[1:].shape:
            raise ValueError("expected syndrome changes have the wrong shape")

    syndrome_readout = syndrome_truth ^ syndrome_faults
    syndrome_detectors = (
        syndrome_readout[1:] ^ syndrome_readout[:-1] ^ expected_changes
    )
    herald_readout, herald_error_kind = _sample_herald_readout(
        herald, uniforms, parameters
    )
    return GenericRepeatedMeasurementHistory(
        master_seed=int(master_seed),
        parameters=parameters,
        check_edge_incidence=incidence,
        edge_faults=faults,
        syndrome_truth=syndrome_truth,
        syndrome_readout=syndrome_readout,
        syndrome_measurement_faults=syndrome_faults,
        syndrome_detectors=syndrome_detectors,
        expected_syndrome_changes=expected_changes,
        herald_truth=herald,
        herald_readout=herald_readout,
        herald_error_kind=herald_error_kind,
        herald_uniforms=uniforms,
    )


def generate_generic_history(
    *,
    master_seed: int,
    parameters: GenericNoiseParameters,
    check_edge_incidence: NDArray[np.generic],
    herald_truth: NDArray[np.generic],
    initial_edge_state: NDArray[np.generic] | None = None,
    expected_syndrome_changes: NDArray[np.generic] | None = None,
) -> GenericRepeatedMeasurementHistory:
    """Sample the three registered channels from independent seeded streams."""

    if not isinstance(master_seed, (int, np.integer)) or int(master_seed) < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    incidence = _as_bool_2d("check_edge_incidence", check_edge_incidence)
    herald = _as_herald_2d("herald_truth", herald_truth)
    if herald.shape[0] < 1:
        raise ValueError("herald_truth must contain at least one round")

    data_seed, syndrome_seed, herald_seed = np.random.SeedSequence(
        int(master_seed)
    ).spawn(3)
    data_rng = np.random.default_rng(data_seed)
    syndrome_rng = np.random.default_rng(syndrome_seed)
    herald_rng = np.random.default_rng(herald_seed)

    edge_faults = data_rng.random((herald.shape[0] - 1, incidence.shape[1])) < parameters.p_data
    syndrome_faults = syndrome_rng.random((herald.shape[0], incidence.shape[0])) < parameters.p_syndrome
    herald_uniforms = herald_rng.random(herald.shape)
    return build_generic_history_from_draws(
        master_seed=int(master_seed),
        parameters=parameters,
        check_edge_incidence=incidence,
        edge_faults=edge_faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_truth=herald,
        herald_uniforms=herald_uniforms,
        initial_edge_state=initial_edge_state,
        expected_syndrome_changes=expected_syndrome_changes,
    )
