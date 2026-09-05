"""Matched end-to-end records for the published two-stage D4 decoder.

This module joins the independently audited Lab 004 layers without changing
their scientific roles: the first charge record conditions the flux-matching
weights, Boolean union homology gates the second stage, a second stabilizer
measurement is sampled uniformly subject to one even constraint per active
colour component, and blue/green charge recovery supplies the final decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from d4_charge import (
    D4ChargeRecoveryResult,
    decode_public_postflux_charges,
    public_postflux_charge_record,
    score_public_postflux_charge_action,
)
from d4_honeycomb import PeriodicHoneycomb
from d4_matching import (
    D4FluxRecoveryResult,
    published_herald_weights,
    syndrome_only_weights,
)
from d4_postflux import (
    PeriodicPostFluxRelations,
    accumulate_postflux_constraints,
    infer_periodic_postflux_relations,
)
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import D4ObservationRecord, observation_from_error_edges


DecoderMode = Literal["syndrome_only", "heralded"]
PIPELINE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class D4DecoderRecord:
    """One physical error followed through every applicable decoder stage."""

    schema_version: int
    mode: DecoderMode
    size: int
    seed: int
    status: str
    logical_error: bool
    physical_error_edges: tuple[int, ...]
    observation: D4ObservationRecord
    flux_recovery: D4FluxRecoveryResult | None
    postflux_relations: PeriodicPostFluxRelations | None
    postflux_charge_outcomes: tuple[int, ...] | None
    charge_recovery: D4ChargeRecoveryResult | None

    def public_transcript(self) -> dict:
        """Return only the records and known actions available online."""

        flux_syndrome = np.zeros(self.observation.size * self.observation.size * 6, dtype=np.uint8)
        flux_syndrome[list(self.observation.flux_vertices)] = 1
        first_charge = (
            None
            if self.observation.charge_outcomes is None
            else list(self.observation.charge_outcomes)
        )
        flux_correction = (
            None
            if self.flux_recovery is None
            else [int(value) for value in np.flatnonzero(self.flux_recovery.correction)]
        )
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "size": self.size,
            "first_record": {
                "flux_syndrome": flux_syndrome.tolist(),
                "charge_signals": first_charge,
            },
            "flux_correction_edges": flux_correction,
            "second_charge_record": (
                None
                if self.postflux_charge_outcomes is None
                else list(self.postflux_charge_outcomes)
            ),
        }

    def to_dict(self) -> dict:
        """Return a JSON-safe provenance record without discarding truth fields."""

        def selected(array: NDArray[np.generic]) -> list[int]:
            return [int(value) for value in np.flatnonzero(array)]

        def windings(analysis) -> list[list[list[int]]]:
            return [
                [list(vector) for vector in component.winding_vectors]
                for component in analysis.components
            ]

        payload = {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "size": self.size,
            "seed": self.seed,
            "status": self.status,
            "logical_error": self.logical_error,
            "physical_error_edges": list(self.physical_error_edges),
            "observation": self.observation.to_dict(),
            "flux_recovery": None,
            "postflux_relations": None,
            "postflux_charge_outcomes": (
                None
                if self.postflux_charge_outcomes is None
                else list(self.postflux_charge_outcomes)
            ),
            "charge_recovery": None,
        }
        if self.flux_recovery is not None:
            flux = self.flux_recovery
            payload["flux_recovery"] = {
                "syndrome_vertices": selected(flux.syndrome),
                "correction_edges": selected(flux.correction),
                "xor_residual_edges": selected(flux.residual),
                "union_edges": selected(flux.physical_correction_union),
                "xor_residual_windings": windings(flux.residual_analysis),
                "union_windings": windings(flux.union_analysis),
                "objective_weight": flux.objective_weight,
                "logical_error": flux.logical_error,
            }
        if self.postflux_relations is not None:
            payload["postflux_relations"] = {
                "active_vertices": list(self.postflux_relations.active_vertices),
                "entanglement_pairs": [
                    list(pair)
                    for pair in self.postflux_relations.entanglement_pairs
                ],
            }
        if self.charge_recovery is not None:
            payload["charge_recovery"] = {
                "logical_error": self.charge_recovery.logical_error,
                "colors": {
                    str(result.color): {
                        "syndrome_vertices": selected(result.syndrome),
                        "effective_error_edges": selected(result.effective_error),
                        "correction_edges": selected(result.correction),
                        "residual_edges": selected(result.residual),
                        "component_windings": [
                            [list(vector) for vector in component]
                            for component in result.residual_analysis.component_windings
                        ],
                        "objective_weight": result.objective_weight,
                        "logical_error": result.logical_error,
                    }
                    for result in (
                        self.charge_recovery.blue,
                        self.charge_recovery.green,
                    )
                },
            }
        return payload


def _derived_seed(seed: int, tag: int) -> int:
    return int(np.random.SeedSequence([int(seed), int(tag)]).generate_state(1)[0])


def sample_postflux_charge_outcomes(
    vertex_count: int,
    relations: PeriodicPostFluxRelations,
    *,
    seed: int,
) -> NDArray[np.int64]:
    """Uniformly sample binary outcomes subject to every even DSU constraint.

    Commuting stabilizer measurements on the post-flux stabilizer state are
    uniform over their affine support. For each independent component, all but
    one deterministic pivot are sampled and the pivot enforces even parity.
    """

    charge = np.full(vertex_count, -1, dtype=np.int64)
    charge[list(relations.active_vertices)] = 0
    zero_analysis = accumulate_postflux_constraints(
        vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        charge,
    )
    rng = np.random.default_rng(seed)
    for component in zero_analysis.components:
        pivot = max(component)
        others = tuple(vertex for vertex in component if vertex != pivot)
        if others:
            charge[list(others)] = rng.integers(0, 2, size=len(others))
        charge[pivot] = int(np.sum(charge[list(others)], dtype=np.int64) % 2)
    validation = accumulate_postflux_constraints(
        vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        charge,
    )
    if not validation.allowed:
        raise RuntimeError("post-flux sampler violated an even parity constraint")
    return charge


def decode_physical_error(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    *,
    mode: DecoderMode,
    seed: int,
) -> D4DecoderRecord:
    """Run one physical error through the matched public two-stage pipeline."""

    return decode_physical_error_with_keys(
        lattice,
        physical_error,
        mode=mode,
        provenance_seed=int(seed),
        first_observation_seed=_derived_seed(seed, 0xD401),
        second_exogenous_seed=_derived_seed(seed, 0xD402),
    )


def decode_physical_error_with_keys(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    *,
    mode: DecoderMode,
    provenance_seed: int,
    first_observation_seed: int,
    second_exogenous_seed: int,
) -> D4DecoderRecord:
    """Run one history with explicit matched measurement-randomness keys."""

    if mode not in ("syndrome_only", "heralded"):
        raise ValueError("mode must be syndrome_only or heralded")
    physical = np.asarray(physical_error, dtype=np.uint8)
    if physical.shape != (lattice.edge_count,) or np.any(physical > 1):
        raise ValueError("physical_error must be binary with one value per edge")
    physical_edges = tuple(int(edge) for edge in np.flatnonzero(physical))
    observation = observation_from_error_edges(
        lattice,
        physical,
        seed=int(first_observation_seed),
    )
    if observation.status == "logical_failure":
        return D4DecoderRecord(
            PIPELINE_SCHEMA_VERSION,
            mode,
            lattice.size,
            int(provenance_seed),
            "physical_winding_failure",
            True,
            physical_edges,
            observation,
            None,
            None,
            None,
            None,
        )
    if observation.charge_outcomes is None:
        raise RuntimeError("sampled observation lacks charge outcomes")
    first_charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    weights = (
        syndrome_only_weights(lattice)
        if mode == "syndrome_only"
        else published_herald_weights(lattice, first_charge)
    )
    flux = decode_and_score_flux_recovery(lattice, physical, weights)
    if flux.logical_error:
        return D4DecoderRecord(
            PIPELINE_SCHEMA_VERSION,
            mode,
            lattice.size,
            int(provenance_seed),
            "flux_union_logical_failure",
            True,
            physical_edges,
            observation,
            flux,
            None,
            None,
            None,
        )
    relations = infer_periodic_postflux_relations(
        lattice, physical, flux.correction
    )
    internal_second_charge = sample_postflux_charge_outcomes(
        lattice.vertex_count,
        relations,
        seed=int(second_exogenous_seed),
    )
    second_charge = public_postflux_charge_record(internal_second_charge)
    charge_action = decode_public_postflux_charges(lattice, second_charge)
    charge_recovery = score_public_postflux_charge_action(
        lattice,
        relations,
        second_charge,
        charge_action,
        flux_components_homologically_trivial=True,
    )
    return D4DecoderRecord(
        PIPELINE_SCHEMA_VERSION,
        mode,
        lattice.size,
        int(provenance_seed),
        "decoded",
        charge_recovery.logical_error,
        physical_edges,
        observation,
        flux,
        relations,
        tuple(int(value) for value in second_charge),
        charge_recovery,
    )
