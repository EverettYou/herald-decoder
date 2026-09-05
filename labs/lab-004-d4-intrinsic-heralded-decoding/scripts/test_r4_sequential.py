from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_charge import build_charge_lattice  # noqa: E402
from d4_exact import enumerate_affine_chains  # noqa: E402
from d4_honeycomb import BLUE, GREEN, periodic_honeycomb  # noqa: E402
from d4_matching import d4_check_matrix  # noqa: E402
from d4_sequential import (  # noqa: E402
    binary_record_to_internal,
    charge_action_quotient,
    exact_second_record_channel,
    sequential_observation_key,
)


def test_empty_union_has_one_all_zero_second_record() -> None:
    lattice = periodic_honeycomb(2)
    empty = np.zeros(lattice.edge_count, dtype=np.uint8)
    channel = exact_second_record_channel(lattice, empty, empty)
    assert not channel.terminal_failure
    assert channel.binary_records == ((0,) * lattice.vertex_count,)
    assert channel.probability_per_record == 1.0
    assert channel.active_vertex_count == 0
    assert channel.component_count == 0


def test_winding_first_union_is_terminal_and_emits_no_second_record() -> None:
    lattice = periodic_honeycomb(2)
    empty = np.zeros(lattice.edge_count, dtype=np.uint8)
    actions = enumerate_affine_chains(
        d4_check_matrix(lattice), np.zeros(lattice.vertex_count, dtype=np.uint8)
    )
    terminal = next(
        action
        for action in actions
        if exact_second_record_channel(lattice, empty, action).terminal_failure
    )
    channel = exact_second_record_channel(lattice, empty, terminal)
    assert channel.terminal_failure
    assert channel.binary_records == ()
    assert channel.probability_per_record == 0.0


def test_second_record_is_binary_and_internal_sentinel_is_not_observable() -> None:
    lattice = periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[0] = 1
    physical[1] = 1
    syndrome = (d4_check_matrix(lattice) @ physical) % 2
    correction = enumerate_affine_chains(d4_check_matrix(lattice), syndrome)[0]
    channel = exact_second_record_channel(lattice, physical, correction)
    if channel.terminal_failure:
        correction = physical.copy()
        channel = exact_second_record_channel(lattice, physical, correction)
    assert not channel.terminal_failure
    for record in channel.binary_records:
        assert set(record) <= {0, 1}
        key = sequential_observation_key((tuple(syndrome),), 0, record)
        assert len(key) == 3
        assert set(key[2]) <= {0, 1}
    if channel.active_vertex_count:
        active = tuple(range(channel.active_vertex_count))
        record = (0,) * lattice.vertex_count
        internal = binary_record_to_internal(record, active)
        assert set(internal) <= {-1, 0}


def test_primitive_charge_lattice_fails_closed_on_parallel_edge_degeneracy() -> None:
    honeycomb = periodic_honeycomb(2)
    for color in (BLUE, GREEN):
        with pytest.raises(ValueError, match="duplicate edge"):
            build_charge_lattice(honeycomb, color)
