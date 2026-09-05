from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spacetime_record import (  # noqa: E402
    build_record_from_fault_masks,
    syndrome_trajectory_from_edge_faults,
)


def _empty_heralds(rounds: int) -> np.ndarray:
    return np.zeros((rounds, 2), dtype=bool)


def test_spatial_edge_fault_creates_same_round_detector_endpoints() -> None:
    incidence = np.array([[1], [1]], dtype=bool)
    edge_faults = np.array([[0], [1], [0]], dtype=bool)
    truth = syndrome_trajectory_from_edge_faults(incidence, edge_faults)
    record = build_record_from_fault_masks(
        truth,
        np.zeros_like(truth),
        _empty_heralds(4),
        _empty_heralds(4),
    )
    assert record.syndrome_detectors.tolist() == [
        [False, False],
        [True, True],
        [False, False],
    ]


def test_one_measurement_fault_has_two_time_adjacent_detector_events() -> None:
    truth = np.zeros((4, 1), dtype=bool)
    readout_faults = np.array([[0], [1], [0], [0]], dtype=bool)
    record = build_record_from_fault_masks(
        truth,
        readout_faults,
        np.zeros((4, 0), dtype=bool),
        np.zeros((4, 0), dtype=bool),
    )
    assert record.syndrome_detectors[:, 0].tolist() == [True, True, False]


def test_known_computational_motion_is_removed_from_detector_record() -> None:
    truth = np.array([[0, 0], [1, 0], [1, 0]], dtype=bool)
    expected_change = np.array([[1, 0], [0, 0]], dtype=bool)
    record = build_record_from_fault_masks(
        truth,
        np.zeros_like(truth),
        np.zeros((3, 1), dtype=bool),
        np.zeros((3, 1), dtype=bool),
        expected_syndrome_changes=expected_change,
    )
    assert not record.syndrome_detectors.any()


def test_herald_readout_faults_remain_raw_observations() -> None:
    truth = np.zeros((3, 1), dtype=bool)
    herald_truth = np.array([[0, 1], [1, 0], [1, 1]], dtype=bool)
    herald_faults = np.array([[0, 0], [0, 1], [1, 0]], dtype=bool)
    record = build_record_from_fault_masks(
        truth,
        np.zeros_like(truth),
        herald_truth,
        herald_faults,
    )
    assert np.array_equal(record.herald_readout, herald_truth ^ herald_faults)
    assert not hasattr(record, "herald_detectors")


def test_causal_prefix_contains_no_future_rounds() -> None:
    truth = np.zeros((5, 2), dtype=bool)
    record = build_record_from_fault_masks(
        truth,
        np.zeros_like(truth),
        np.zeros((5, 1), dtype=bool),
        np.zeros((5, 1), dtype=bool),
    )
    prefix = record.causal_prefix(2)
    assert prefix.syndrome_readout.shape == (3, 2)
    assert prefix.syndrome_detectors.shape == (2, 2)
    assert prefix.herald_readout.shape == (3, 1)
    with pytest.raises(ValueError):
        record.causal_prefix(5)


def test_detector_identity_exhaustively_for_tiny_measurement_history() -> None:
    truth = np.array([[0], [1], [1]], dtype=bool)
    herald = np.zeros((3, 0), dtype=bool)
    for bits in itertools.product((False, True), repeat=3):
        faults = np.asarray(bits, dtype=bool).reshape(3, 1)
        record = build_record_from_fault_masks(
            truth,
            faults,
            herald,
            herald,
        )
        expected = record.syndrome_readout[1:] ^ record.syndrome_readout[:-1]
        assert np.array_equal(record.syndrome_detectors, expected)
