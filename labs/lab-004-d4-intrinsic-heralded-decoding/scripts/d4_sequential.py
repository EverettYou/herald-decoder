"""Exact bounded helpers for the R4.5 sequential D4 decision channel.

The post-flux relation graph is hidden generative metadata.  Public observation
keys contain only the initial record, the known first action, and a full binary
second charge record with deterministic zero outside the active union support.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
from numpy.typing import NDArray

from d4_charge import (
    ChargeLattice,
    charge_check_matrix,
    classify_closed_charge_chain,
    decode_charge_syndrome,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import PeriodicHoneycomb
from d4_matching import classify_physical_correction_union
from d4_postflux import (
    PeriodicPostFluxRelations,
    accumulate_postflux_constraints,
    infer_periodic_postflux_relations,
)


ChargeSector = tuple[int, int]


@dataclass(frozen=True)
class SecondRecordChannel:
    """Exact second-record support for one hidden error and first action."""

    terminal_failure: bool
    binary_records: tuple[tuple[int, ...], ...]
    probability_per_record: float
    active_vertex_count: int
    component_count: int


def chain_mask(chain: NDArray[np.generic]) -> int:
    selected = np.asarray(chain, dtype=np.uint8)
    if selected.ndim != 1 or np.any(selected > 1):
        raise ValueError("chain must be a one-dimensional binary array")
    return sum(int(bit) << edge for edge, bit in enumerate(selected))


def binary_record_to_internal(
    binary_record: tuple[int, ...] | NDArray[np.generic],
    active_vertices: tuple[int, ...],
) -> NDArray[np.int64]:
    """Restore the simulator sentinel only inside the hidden likelihood layer."""

    record = np.asarray(binary_record, dtype=np.int64)
    if record.ndim != 1 or np.any((record != 0) & (record != 1)):
        raise ValueError("decoder-visible second record must be binary")
    active = tuple(int(vertex) for vertex in active_vertices)
    if len(active) != len(set(active)) or any(
        vertex < 0 or vertex >= len(record) for vertex in active
    ):
        raise ValueError("active_vertices must be unique and in range")
    inactive = set(range(len(record))) - set(active)
    if any(record[vertex] != 0 for vertex in inactive):
        raise ValueError("binary second record must be zero outside hidden support")
    internal = np.full(len(record), -1, dtype=np.int64)
    if active:
        internal[np.asarray(active, dtype=np.int64)] = record[
            np.asarray(active, dtype=np.int64)
        ]
    return internal


def enumerate_binary_second_records(
    vertex_count: int,
    relations: PeriodicPostFluxRelations,
) -> tuple[tuple[int, ...], ...]:
    """Enumerate the full binary record on the exact even-parity support."""

    zero = np.full(vertex_count, -1, dtype=np.int64)
    if relations.active_vertices:
        zero[np.asarray(relations.active_vertices, dtype=np.int64)] = 0
    analysis = accumulate_postflux_constraints(
        vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        zero,
    )
    component_records: list[tuple[tuple[int, ...], ...]] = []
    for component in analysis.components:
        pivot = max(component)
        free = tuple(vertex for vertex in component if vertex != pivot)
        records = []
        for bits in product((0, 1), repeat=len(free)):
            values = [0] * vertex_count
            for vertex, bit in zip(free, bits, strict=True):
                values[vertex] = int(bit)
            values[pivot] = sum(bits) % 2
            records.append(tuple(values))
        component_records.append(tuple(records))
    if not component_records:
        return ((0,) * vertex_count,)
    combined = []
    for choices in product(*component_records):
        values = [0] * vertex_count
        for choice in choices:
            for vertex, bit in enumerate(choice):
                values[vertex] |= int(bit)
        combined.append(tuple(values))
    records = tuple(sorted(set(combined)))
    expected = 1 << (len(relations.active_vertices) - len(analysis.components))
    if len(records) != expected:
        raise RuntimeError("second-record affine-support dimension mismatch")
    for record in records:
        internal = binary_record_to_internal(record, relations.active_vertices)
        validation = accumulate_postflux_constraints(
            vertex_count,
            relations.active_vertices,
            relations.entanglement_pairs,
            internal,
        )
        if not validation.allowed:
            raise RuntimeError("enumerated second record violates parity support")
    return records


def exact_second_record_channel(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    first_correction: NDArray[np.generic],
) -> SecondRecordChannel:
    """Return the exact terminal/second-observation channel for ``(E,A)``."""

    physical = np.asarray(physical_error, dtype=np.uint8)
    correction = np.asarray(first_correction, dtype=np.uint8)
    if physical.shape != (lattice.edge_count,) or np.any(physical > 1):
        raise ValueError("physical_error must be binary on honeycomb edges")
    if correction.shape != (lattice.edge_count,) or np.any(correction > 1):
        raise ValueError("first_correction must be binary on honeycomb edges")
    union = classify_physical_correction_union(lattice, physical, correction)
    if any(not component.homologically_trivial for component in union.components):
        return SecondRecordChannel(True, (), 0.0, 0, 0)
    relations = infer_periodic_postflux_relations(lattice, physical, correction)
    records = enumerate_binary_second_records(lattice.vertex_count, relations)
    zero = np.full(lattice.vertex_count, -1, dtype=np.int64)
    if relations.active_vertices:
        zero[np.asarray(relations.active_vertices, dtype=np.int64)] = 0
    components = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        zero,
    ).components
    probability = 2.0 ** (len(components) - len(relations.active_vertices))
    if abs(probability * len(records) - 1.0) > 1e-12:
        raise RuntimeError("second-record channel does not normalize")
    return SecondRecordChannel(
        False,
        records,
        probability,
        len(relations.active_vertices),
        len(components),
    )


def sequential_observation_key(
    initial_observation: tuple,
    first_action_mask: int,
    binary_second_record: tuple[int, ...],
) -> tuple:
    """Build an observation-only key with no hidden relation metadata."""

    if first_action_mask < 0:
        raise ValueError("first_action_mask must be nonnegative")
    record = tuple(int(value) for value in binary_second_record)
    if any(value not in (0, 1) for value in record):
        raise ValueError("binary_second_record must contain only zero and one")
    return initial_observation, int(first_action_mask), record


def closed_charge_sector(
    lattice: ChargeLattice,
    closed_chain: NDArray[np.generic],
) -> ChargeSector:
    """Return the GF(2) torus homology of a closed charge chain."""

    selected = np.asarray(closed_chain, dtype=np.uint8)
    analysis = classify_closed_charge_chain(lattice, selected)
    first = 0
    second = 0
    for component in analysis.component_windings:
        for winding_x, winding_y in component:
            first ^= int(winding_x) & 1
            second ^= int(winding_y) & 1
    return first, second


def charge_action_quotient(
    lattice: ChargeLattice,
    syndrome: NDArray[np.generic],
) -> dict[ChargeSector, tuple[NDArray[np.uint8], ...]]:
    """Group every affine charge correction into its four relative sectors."""

    actions = enumerate_affine_chains(charge_check_matrix(lattice), syndrome)
    masks = np.asarray([chain_mask(action) for action in actions], dtype=np.int64)
    reference = actions[int(np.argmin(masks))]
    groups: dict[ChargeSector, list[NDArray[np.uint8]]] = {}
    for action in actions:
        sector = closed_charge_sector(lattice, action ^ reference)
        groups.setdefault(sector, []).append(action.copy())
    return {
        sector: tuple(sorted(chains, key=chain_mask))
        for sector, chains in sorted(groups.items())
    }


def validate_charge_quotient(lattice: ChargeLattice) -> dict:
    """Exhaustively validate the four-class quotient for every even syndrome."""

    check = charge_check_matrix(lattice)
    zero_syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
    closed = enumerate_affine_chains(check, zero_syndrome)
    closed_loss = {
        chain_mask(chain): classify_closed_charge_chain(lattice, chain).logical_error
        for chain in closed
    }
    supported = []
    quotient_failures = 0
    within_sector_loss_failures = 0
    public_membership_failures = 0
    class_sizes: set[int] = set()
    comparison_count = 0
    for syndrome_mask in range(1 << lattice.vertex_count):
        syndrome = np.asarray(
            [
                (syndrome_mask >> vertex) & 1
                for vertex in range(lattice.vertex_count)
            ],
            dtype=np.uint8,
        )
        if int(np.sum(syndrome)) % 2:
            continue
        groups = charge_action_quotient(lattice, syndrome)
        actions = enumerate_affine_chains(check, syndrome)
        supported.append(syndrome_mask)
        if set(groups) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
            quotient_failures += 1
        class_sizes.update(len(group) for group in groups.values())
        public, _ = decode_charge_syndrome(lattice, syndrome)
        if chain_mask(public) not in {chain_mask(action) for action in actions}:
            public_membership_failures += 1
        for effective in actions:
            for group in groups.values():
                losses = {
                    closed_loss[chain_mask(effective ^ correction)]
                    for correction in group
                }
                comparison_count += len(group)
                if len(losses) != 1:
                    within_sector_loss_failures += 1
    return {
        "supported_even_syndrome_count": len(supported),
        "affine_actions_per_syndrome": len(closed),
        "sector_count_expected": 4,
        "class_sizes": sorted(class_sizes),
        "quotient_failures": quotient_failures,
        "within_sector_loss_failures": within_sector_loss_failures,
        "public_membership_failures": public_membership_failures,
        "effective_action_loss_comparisons": comparison_count,
    }
