from __future__ import annotations

from dataclasses import fields
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from baseline_harness import (  # noqa: E402
    DeterministicInnerDecoder,
    run_shared_history_baselines,
)
from generic_history import (  # noqa: E402
    GenericNoiseParameters,
    build_generic_history_from_draws,
    generate_generic_history,
    herald_confusion_matrix,
)
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox  # noqa: E402


def _parameters(**overrides: float) -> GenericNoiseParameters:
    values = {
        "p_data": 0.25,
        "p_syndrome": 0.25,
        "p_fp": 0.2,
        "p_fn": 0.3,
        "p_confuse": 0.1,
    }
    values.update(overrides)
    return GenericNoiseParameters(**values)


def _truth(rounds: int = 4) -> np.ndarray:
    row = np.asarray(["none", "blue", "green"], dtype="<U5")
    return np.tile(row, (rounds, 1))


def test_confusion_matrix_is_normalized_on_registered_domain_grid() -> None:
    for p_fp, p_fn, p_confuse in itertools.product(
        (0.0, 0.25, 1.0), (0.0, 0.25, 1.0), (0.0, 0.25, 1.0)
    ):
        if p_fn + p_confuse > 1.0:
            continue
        matrix = herald_confusion_matrix(
            _parameters(p_fp=p_fp, p_fn=p_fn, p_confuse=p_confuse)
        )
        assert np.all(matrix >= 0.0)
        assert np.allclose(matrix.sum(axis=1), 1.0)
    with pytest.raises(ValueError, match="must not exceed"):
        _parameters(p_fn=0.6, p_confuse=0.5)


def test_each_herald_parameter_changes_only_its_registered_channel() -> None:
    incidence = np.asarray([[1]], dtype=bool)
    edge_faults = np.zeros((1, 1), dtype=bool)
    syndrome_faults = np.zeros((2, 1), dtype=bool)
    truth = _truth(2)
    uniforms = np.asarray([[0.75, 0.1, 0.1], [0.75, 0.9, 0.9]])

    fp = build_generic_history_from_draws(
        master_seed=1,
        parameters=_parameters(p_fp=1.0, p_fn=0.0, p_confuse=0.0),
        check_edge_incidence=incidence,
        edge_faults=edge_faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_truth=truth,
        herald_uniforms=uniforms,
    )
    assert np.all(fp.herald_readout[:, 0] != "none")
    assert np.array_equal(fp.herald_readout[:, 1:], truth[:, 1:])

    fn = build_generic_history_from_draws(
        master_seed=1,
        parameters=_parameters(p_fp=0.0, p_fn=1.0, p_confuse=0.0),
        check_edge_incidence=incidence,
        edge_faults=edge_faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_truth=truth,
        herald_uniforms=uniforms,
    )
    assert np.array_equal(fn.herald_readout[:, 0], truth[:, 0])
    assert np.all(fn.herald_readout[:, 1:] == "none")

    confused = build_generic_history_from_draws(
        master_seed=1,
        parameters=_parameters(p_fp=0.0, p_fn=0.0, p_confuse=1.0),
        check_edge_incidence=incidence,
        edge_faults=edge_faults,
        syndrome_measurement_faults=syndrome_faults,
        herald_truth=truth,
        herald_uniforms=uniforms,
    )
    assert np.array_equal(confused.herald_readout[:, 0], truth[:, 0])
    assert np.all(confused.herald_readout[:, 1] == "green")
    assert np.all(confused.herald_readout[:, 2] == "blue")


def test_zero_data_and_syndrome_noise_recover_truth_and_detector_identity() -> None:
    history = generate_generic_history(
        master_seed=11,
        parameters=_parameters(p_data=0.0, p_syndrome=0.0, p_fp=0.0, p_fn=0.0, p_confuse=0.0),
        check_edge_incidence=np.asarray([[1, 0], [0, 1]], dtype=bool),
        herald_truth=_truth(5),
        initial_edge_state=np.asarray([1, 0], dtype=bool),
    )
    assert not history.edge_faults.any()
    assert not history.syndrome_measurement_faults.any()
    assert np.array_equal(history.syndrome_readout, history.syndrome_truth)
    assert np.array_equal(
        history.syndrome_detectors,
        history.syndrome_truth[1:] ^ history.syndrome_truth[:-1],
    )
    assert np.array_equal(history.herald_readout, history.herald_truth)


def test_one_syndrome_fault_creates_adjacent_time_detector_pair() -> None:
    history = build_generic_history_from_draws(
        master_seed=2,
        parameters=_parameters(),
        check_edge_incidence=np.asarray([[1]], dtype=bool),
        edge_faults=np.zeros((3, 1), dtype=bool),
        syndrome_measurement_faults=np.asarray([[0], [1], [0], [0]], dtype=bool),
        herald_truth=np.full((4, 0), "none", dtype="<U5"),
        herald_uniforms=np.zeros((4, 0), dtype=float),
    )
    assert history.syndrome_detectors[:, 0].tolist() == [True, True, False]


def test_seeded_substreams_replay_and_isolate_parameter_changes() -> None:
    common = dict(
        master_seed=37,
        check_edge_incidence=np.asarray([[1, 1], [0, 1]], dtype=bool),
        herald_truth=_truth(8),
    )
    first = generate_generic_history(parameters=_parameters(), **common)
    replay = generate_generic_history(parameters=_parameters(), **common)
    assert np.array_equal(first.edge_faults, replay.edge_faults)
    assert np.array_equal(first.syndrome_measurement_faults, replay.syndrome_measurement_faults)
    assert np.array_equal(first.herald_uniforms, replay.herald_uniforms)
    assert np.array_equal(first.herald_readout, replay.herald_readout)

    changed_data = generate_generic_history(
        parameters=_parameters(p_data=0.75), **common
    )
    assert np.array_equal(first.syndrome_measurement_faults, changed_data.syndrome_measurement_faults)
    assert np.array_equal(first.herald_uniforms, changed_data.herald_uniforms)

    changed_syndrome = generate_generic_history(
        parameters=_parameters(p_syndrome=0.75), **common
    )
    assert np.array_equal(first.edge_faults, changed_syndrome.edge_faults)
    assert np.array_equal(first.herald_uniforms, changed_syndrome.herald_uniforms)


def test_causal_prefix_is_categorical_and_excludes_sidecars_and_future() -> None:
    history = generate_generic_history(
        master_seed=5,
        parameters=_parameters(),
        check_edge_incidence=np.asarray([[1]], dtype=bool),
        herald_truth=_truth(5),
    )
    prefix = history.causal_prefix(2)
    assert prefix.herald_readout.dtype.kind == "U"
    assert prefix.herald_readout.shape == (3, 3)
    assert prefix.syndrome_readout.shape[0] == 3
    assert prefix.syndrome_detectors.shape[0] == 2
    assert set(field.name for field in fields(prefix)) == {
        "final_round",
        "syndrome_readout",
        "syndrome_detectors",
        "herald_readout",
    }
    assert not {"truth", "faults", "uniforms"}.intersection(vars(prefix))


def test_generated_history_binds_all_four_schedules_to_one_digest() -> None:
    parameters = _parameters(
        p_data=0.5,
        p_syndrome=0.0,
        p_fp=0.0,
        p_fn=0.0,
        p_confuse=0.0,
    )
    history = generate_generic_history(
        master_seed=32,
        parameters=parameters,
        check_edge_incidence=np.asarray([[1]], dtype=bool),
        herald_truth=_truth(4),
    )
    geometry = AbsorberGeometry()
    geometry.open(
        AbsorbingRegion(
            "boundary",
            "spatial_boundary",
            SpacetimeBox((2, 0), (2, 3)),
            0,
        ),
        current_round=0,
    )
    decoder = DeterministicInnerDecoder()
    result = run_shared_history_baselines(
        trial_id="generic-32",
        record=history,
        check_positions=((0,),),
        geometry=geometry,
        decoder=decoder,
    )
    assert {branch.history_digest for branch in result.branches} == {
        result.history_digest
    }
    assert tuple(branch.branch for branch in result.branches) == (
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    )
    assert {request.branch for request in decoder.requests} == {
        "immediate",
        "fixed_delay_1",
        "jit_lyons_brown",
        "offline_full_history",
    }
    assert all(not hasattr(request, "history_digest") for request in decoder.requests)


def test_categorical_labels_are_never_silently_coerced_to_boolean() -> None:
    history = generate_generic_history(
        master_seed=23,
        parameters=_parameters(p_data=0.0, p_syndrome=0.0),
        check_edge_incidence=np.asarray([[1]], dtype=bool),
        herald_truth=_truth(3),
    )
    assert history.herald_truth.dtype.kind == "U"
    assert history.herald_readout.dtype.kind == "U"
    assert set(np.unique(history.herald_truth)) == {"none", "blue", "green"}
    with pytest.raises(ValueError, match="invalid herald labels"):
        generate_generic_history(
            master_seed=23,
            parameters=_parameters(),
            check_edge_incidence=np.asarray([[1]], dtype=bool),
            herald_truth=np.asarray([["red"]]),
        )
