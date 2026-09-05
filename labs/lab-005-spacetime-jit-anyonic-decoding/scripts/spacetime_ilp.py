"""Bounded compiler for the spacetime fusion-channel ILP of Jing et al. (2026).

The implementation mirrors Eqs. (18)--(21) at the level needed for tiny exact
fixtures.  A physical model supplies the allowed local fusion channels.  Each
channel records multiplicities of spatial, incoming-temporal, and
outgoing-temporal strings for every anyon species. Binary physical-error,
measurement-error, and one-hot channel variables are then linked by linear
equalities and optimized with SciPy MILP. SciPy minimizes, so callers must
supply additive costs equal to the negative of the paper's log weights (up to
irrelevant constants); raw log probabilities must not be passed without this
sign conversion.

This module is not yet the complete D4 channel table or a scalable decoder.
It is the solver contract those model-specific layers must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class FusionChannel:
    name: str
    spatial: tuple[int, ...]
    incoming: tuple[int, ...]
    outgoing: tuple[int, ...]
    cost: float = 0.0


@dataclass(frozen=True)
class PhysicalEvent:
    name: str
    cost: float
    incidence: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class SpacetimeSite:
    name: str
    previous_site: int | None
    channels: tuple[FusionChannel, ...]


@dataclass(frozen=True)
class SpacetimeIlpProblem:
    species: tuple[str, ...]
    sites: tuple[SpacetimeSite, ...]
    physical_events: tuple[PhysicalEvent, ...]
    measurement_costs: NDArray[np.float64]


@dataclass(frozen=True)
class SpacetimeIlpResult:
    objective: float
    selected_physical_events: tuple[str, ...]
    selected_measurement_errors: tuple[tuple[str, str], ...]
    selected_channels: tuple[tuple[str, str], ...]


def _validate(problem: SpacetimeIlpProblem) -> NDArray[np.float64]:
    species_count = len(problem.species)
    if species_count == 0 or len(set(problem.species)) != species_count:
        raise ValueError("species must be nonempty and unique")
    measurement_costs = np.asarray(problem.measurement_costs, dtype=np.float64)
    if measurement_costs.shape != (len(problem.sites), species_count):
        raise ValueError("measurement_costs must have shape (sites, species)")
    if not np.isfinite(measurement_costs).all():
        raise ValueError("measurement costs must be finite")
    if len({site.name for site in problem.sites}) != len(problem.sites):
        raise ValueError("site names must be unique")
    if len({event.name for event in problem.physical_events}) != len(
        problem.physical_events
    ):
        raise ValueError("physical-event names must be unique")
    for site_index, site in enumerate(problem.sites):
        if not site.channels:
            raise ValueError(f"site {site.name} has no allowed fusion channel")
        if len({channel.name for channel in site.channels}) != len(site.channels):
            raise ValueError("fusion-channel names must be unique within a site")
        if site.previous_site is not None and not 0 <= site.previous_site < site_index:
            raise ValueError("previous_site must point to an earlier spacetime site")
        for channel in site.channels:
            if not np.isfinite(channel.cost):
                raise ValueError("fusion-channel costs must be finite")
            vectors = (channel.spatial, channel.incoming, channel.outgoing)
            if any(len(vector) != species_count for vector in vectors):
                raise ValueError("fusion-channel vectors must match species count")
            if any(value not in (0, 1) for vector in vectors for value in vector):
                raise ValueError("bounded preflight supports binary multiplicities only")
    for event in problem.physical_events:
        if not np.isfinite(event.cost):
            raise ValueError("physical-event costs must be finite")
        for site_index, species_index, multiplicity in event.incidence:
            if not 0 <= site_index < len(problem.sites):
                raise ValueError("physical incidence references an unknown site")
            if not 0 <= species_index < species_count:
                raise ValueError("physical incidence references an unknown species")
            if multiplicity not in (0, 1):
                raise ValueError("bounded preflight supports binary incidence only")
    return measurement_costs


def solve_spacetime_fusion_ilp(problem: SpacetimeIlpProblem) -> SpacetimeIlpResult:
    """Solve the bounded fusion-channel ILP with open temporal boundaries."""

    measurement_costs = _validate(problem)
    species_count = len(problem.species)
    physical_count = len(problem.physical_events)
    measurement_count = len(problem.sites) * species_count
    channel_offsets: list[int] = []
    variable_count = physical_count + measurement_count
    for site in problem.sites:
        channel_offsets.append(variable_count)
        variable_count += len(site.channels)

    objective = np.zeros(variable_count, dtype=np.float64)
    objective[:physical_count] = [event.cost for event in problem.physical_events]
    objective[physical_count : physical_count + measurement_count] = measurement_costs.ravel()
    for site_index, site in enumerate(problem.sites):
        offset = channel_offsets[site_index]
        objective[offset : offset + len(site.channels)] = [
            channel.cost for channel in site.channels
        ]

    rows: list[NDArray[np.float64]] = []
    targets: list[float] = []

    # Exactly one measured-syndrome-compatible fusion channel per site.
    for site_index, site in enumerate(problem.sites):
        row = np.zeros(variable_count, dtype=np.float64)
        offset = channel_offsets[site_index]
        row[offset : offset + len(site.channels)] = 1.0
        rows.append(row)
        targets.append(1.0)

    def measurement_index(site_index: int, species_index: int) -> int:
        return physical_count + site_index * species_count + species_index

    # Eq. (19): spatial, incoming-temporal, and outgoing-temporal
    # multiplicities must match the selected local fusion channel.
    for site_index, site in enumerate(problem.sites):
        channel_offset = channel_offsets[site_index]
        for species_index in range(species_count):
            spatial_row = np.zeros(variable_count, dtype=np.float64)
            for event_index, event in enumerate(problem.physical_events):
                spatial_row[event_index] = sum(
                    multiplicity
                    for incident_site, incident_species, multiplicity in event.incidence
                    if incident_site == site_index and incident_species == species_index
                )
            for channel_index, channel in enumerate(site.channels):
                spatial_row[channel_offset + channel_index] -= channel.spatial[species_index]
            rows.append(spatial_row)
            targets.append(0.0)

            outgoing_row = np.zeros(variable_count, dtype=np.float64)
            outgoing_row[measurement_index(site_index, species_index)] = 1.0
            for channel_index, channel in enumerate(site.channels):
                outgoing_row[channel_offset + channel_index] -= channel.outgoing[species_index]
            rows.append(outgoing_row)
            targets.append(0.0)

            incoming_row = np.zeros(variable_count, dtype=np.float64)
            if site.previous_site is not None:
                incoming_row[measurement_index(site.previous_site, species_index)] = 1.0
            for channel_index, channel in enumerate(site.channels):
                incoming_row[channel_offset + channel_index] -= channel.incoming[species_index]
            rows.append(incoming_row)
            targets.append(0.0)

    matrix = np.stack(rows) if rows else np.zeros((0, variable_count))
    target = np.asarray(targets, dtype=np.float64)
    result = milp(
        objective,
        integrality=np.ones(variable_count, dtype=np.uint8),
        bounds=Bounds(np.zeros(variable_count), np.ones(variable_count)),
        constraints=LinearConstraint(matrix, target, target),
        options={"presolve": True},
    )
    if not result.success or result.x is None or result.fun is None:
        raise ValueError(f"spacetime fusion ILP is infeasible: {result.message}")

    selected_physical = tuple(
        event.name
        for index, event in enumerate(problem.physical_events)
        if result.x[index] > 0.5
    )
    selected_measurement = tuple(
        (site.name, problem.species[species_index])
        for site_index, site in enumerate(problem.sites)
        for species_index in range(species_count)
        if result.x[measurement_index(site_index, species_index)] > 0.5
    )
    selected_channels = []
    for site_index, site in enumerate(problem.sites):
        offset = channel_offsets[site_index]
        channel_index = int(np.argmax(result.x[offset : offset + len(site.channels)]))
        selected_channels.append((site.name, site.channels[channel_index].name))
    return SpacetimeIlpResult(
        objective=float(result.fun),
        selected_physical_events=selected_physical,
        selected_measurement_errors=selected_measurement,
        selected_channels=tuple(selected_channels),
    )
