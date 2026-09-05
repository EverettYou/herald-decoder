#!/usr/bin/env python3
"""Probability-damped Herald-aware BP recurrence for Lab 002.

This module preserves the probability-space message implementation that
preceded the memory-assisted experiment.  The unified public decoder in
``herald_bp_decoder.py`` delegates here when ``recurrence_mode="damping"``;
the class remains directly importable so frozen A/B experiments stay stable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pymatching

from .herald_bp_decoder import _normalise, _vertex_likelihood
from .lattice_model import LatticeGraph
from .numba_bp_kernels import (
    NUMBA_AVAILABLE,
    dense_topology,
    legacy_infer_dense,
    residual_priority_infer_dense,
    residual_priority_infer_dense_cached,
    residual_priority_infer_dense_reuse,
)


@dataclass(frozen=True)
class LegacyBpResult:
    edge_marginals: np.ndarray
    iterations: int
    converged: bool
    max_message_delta: float


@dataclass(frozen=True)
class LegacyDecodeResult:
    correction: np.ndarray
    matching_weight: float
    bp: LegacyBpResult
    edge_weights: np.ndarray


class LegacyDampedBpMatchingDecoder:
    """Probability-damped loopy BP followed by PyMatching."""

    def __init__(
        self,
        graph: LatticeGraph,
        *,
        p: float,
        q: float,
        p_m: float = 0.0,
        p_h: float = 0.0,
        max_iterations: int = 40,
        damping: float = 0.25,
        tolerance: float = 1e-8,
        update_schedule: str = "synchronous",
        residual_priority_order: str = "scan",
        residual_priority_buffer_reuse: bool = False,
        residual_priority_cached_products: bool = False,
        use_numba: bool | None = None,
    ):
        if not 0 < p < 1:
            raise ValueError("p must lie strictly between 0 and 1")
        if not 0 <= q <= 1 or not 0 <= p_m <= 0.5 or not 0 <= p_h <= 1:
            raise ValueError("q, p_m, or p_h is outside its probability range")
        if max_iterations < 1 or not 0 <= damping < 1 or tolerance <= 0:
            raise ValueError("invalid BP iteration controls")
        if update_schedule not in {"synchronous", "residual_priority"}:
            raise ValueError("update_schedule must be 'synchronous' or 'residual_priority'")
        if residual_priority_order not in {"scan", "stable_sort"}:
            raise ValueError("residual_priority_order must be 'scan' or 'stable_sort'")
        self.graph = graph
        self.p = p
        self.q = q
        self.p_m = p_m
        self.p_h = p_h
        self.max_iterations = max_iterations
        self.damping = damping
        self.tolerance = tolerance
        self.update_schedule = update_schedule
        self.residual_priority_order = residual_priority_order
        self.residual_priority_buffer_reuse = bool(residual_priority_buffer_reuse)
        self.residual_priority_cached_products = bool(residual_priority_cached_products)
        self.use_numba = NUMBA_AVAILABLE if use_numba is None else bool(use_numba)
        if self.use_numba and not NUMBA_AVAILABLE:
            raise RuntimeError("Numba was requested but is unavailable")
        if self.residual_priority_buffer_reuse and (
            not self.use_numba or self.update_schedule != "residual_priority"
        ):
            raise ValueError(
                "residual_priority_buffer_reuse requires compiled residual-priority BP"
            )
        if self.residual_priority_cached_products and (
            not self.use_numba or self.update_schedule != "residual_priority"
        ):
            raise ValueError(
                "residual_priority_cached_products requires compiled residual-priority BP"
            )
        if self.residual_priority_buffer_reuse and self.residual_priority_cached_products:
            raise ValueError("buffer reuse and cached products are separate experimental arms")
        self.prior = np.asarray([1 - p, p], dtype=float)
        detector_row = graph.detector_row
        self.factor_edges = tuple(graph.incident_edges[vertex] for vertex in graph.detector_vertices)
        self.edge_factors: tuple[tuple[int, ...], ...] = tuple(
            tuple(detector_row[vertex] for vertex in edge if vertex in detector_row)
            for edge in graph.edges
        )
        (
            self.dense_factor_dirs,
            self.dense_factor_degrees,
            self.dense_edge_dirs,
            self.dense_edge_degrees,
            self.dense_directed_keys,
        ) = dense_topology(self.factor_edges, self.edge_factors)
        self.dense_direction_edges = np.asarray(
            [edge for edge, _factor in self.dense_directed_keys], dtype=np.int64
        )
        self.dense_direction_factors = np.asarray(
            [factor for _edge, factor in self.dense_directed_keys], dtype=np.int64
        )
        self.assignments: dict[int, np.ndarray] = {
            degree: np.asarray(list(product((0, 1), repeat=degree)), dtype=np.uint8)
            for degree in {len(incident) for incident in self.factor_edges}
        }
        self.factor_potentials: dict[tuple[int, int, int], np.ndarray] = {}
        for degree, assignments in self.assignments.items():
            for observed_syndrome in (0, 1):
                for observed_herald in (0, 1):
                    self.factor_potentials[(degree, observed_syndrome, observed_herald)] = np.asarray(
                        [
                            _vertex_likelihood(
                                tuple(int(bit) for bit in assignment),
                                observed_syndrome,
                                observed_herald,
                                q=self.q,
                                p_m=self.p_m,
                                p_h=self.p_h,
                            )
                            for assignment in assignments
                        ],
                        dtype=float,
                    )

    def _factor_message(
        self,
        syndrome: np.ndarray,
        herald: np.ndarray,
        variable_to_factor: dict[tuple[int, int], np.ndarray],
        factor: int,
        target_position: int,
    ) -> np.ndarray:
        incident = self.factor_edges[factor]
        assignments = self.assignments[len(incident)]
        potential = self.factor_potentials[(len(incident), int(syndrome[factor]), int(herald[factor]))]
        values = potential.copy()
        for position, edge in enumerate(incident):
            if position != target_position:
                values *= variable_to_factor[(edge, factor)][assignments[:, position]]
        return _normalise(
            np.bincount(assignments[:, target_position], weights=values, minlength=2).astype(float)
        )

    def _variable_message(
        self,
        factor_to_variable: dict[tuple[int, int], np.ndarray],
        edge: int,
        target_factor: int,
    ) -> np.ndarray:
        message = self.prior.copy()
        for factor in self.edge_factors[edge]:
            if factor != target_factor:
                message *= factor_to_variable[(edge, factor)]
        return _normalise(message)

    def _infer_residual_priority(self, syndrome: np.ndarray, herald: np.ndarray) -> LegacyBpResult:
        """Deterministic Gauss--Seidel sweep ordered by prior factor residual.

        This is deliberately Python-only and opt-in.  It is the exact C1
        experimental schedule, not a replacement for the Numba synchronous
        default.
        """
        variable_to_factor = {
            (edge, factor): self.prior.copy()
            for edge, factors in enumerate(self.edge_factors)
            for factor in factors
        }
        factor_to_variable = {key: np.full(2, 0.5) for key in variable_to_factor}
        previous_factor_residuals: np.ndarray | None = None
        converged = False
        max_delta = float("inf")
        for iteration in range(1, self.max_iterations + 1):
            variable = {key: value.copy() for key, value in variable_to_factor.items()}
            factors = {key: value.copy() for key, value in factor_to_variable.items()}
            if previous_factor_residuals is None:
                order = range(len(self.factor_edges))
            else:
                order = np.argsort(-previous_factor_residuals, kind="stable")
            factor_residuals = np.zeros(len(self.factor_edges), dtype=float)
            max_delta = 0.0
            for factor in order:
                factor = int(factor)
                for target_position, edge in enumerate(self.factor_edges[factor]):
                    key = (edge, factor)
                    raw = self._factor_message(syndrome, herald, variable, factor, target_position)
                    updated = _normalise(self.damping * factors[key] + (1 - self.damping) * raw)
                    delta = float(np.max(np.abs(updated - factors[key])))
                    max_delta = max(max_delta, delta)
                    factor_residuals[factor] = max(factor_residuals[factor], delta)
                    factors[key] = updated
                    for target_factor in self.edge_factors[edge]:
                        if target_factor == factor:
                            continue
                        variable_key = (edge, target_factor)
                        refreshed = self._variable_message(factors, edge, target_factor)
                        variable_delta = float(np.max(np.abs(refreshed - variable[variable_key])))
                        max_delta = max(max_delta, variable_delta)
                        factor_residuals[target_factor] = max(factor_residuals[target_factor], variable_delta)
                        variable[variable_key] = refreshed
            factor_to_variable = factors
            variable_to_factor = variable
            previous_factor_residuals = factor_residuals
            if max_delta < self.tolerance:
                converged = True
                break
        marginals = np.zeros(len(self.graph.edges), dtype=float)
        for edge, incident_factors in enumerate(self.edge_factors):
            belief = self.prior.copy()
            for factor in incident_factors:
                belief *= factor_to_variable[(edge, factor)]
            marginals[edge] = _normalise(belief)[1]
        return LegacyBpResult(marginals, iteration, converged, max_delta)

    def infer(self, syndrome: np.ndarray, herald: np.ndarray) -> LegacyBpResult:
        syndrome = np.asarray(syndrome, dtype=np.uint8)
        herald = np.asarray(herald, dtype=np.uint8)
        expected = (len(self.graph.detector_vertices),)
        if syndrome.shape != expected or herald.shape != expected:
            raise ValueError("syndrome or herald vector has the wrong shape")
        if np.any(syndrome > 1) or np.any(herald > 1):
            raise ValueError("syndrome and herald must be binary")

        if self.update_schedule == "residual_priority" and self.use_numba:
            infer_dense = (
                residual_priority_infer_dense_cached
                if self.residual_priority_cached_products
                else residual_priority_infer_dense_reuse
                if self.residual_priority_buffer_reuse
                else residual_priority_infer_dense
            )
            marginals, converged, max_delta, iteration = infer_dense(
                np.ascontiguousarray(syndrome, dtype=np.uint8),
                np.ascontiguousarray(herald, dtype=np.uint8),
                self.dense_factor_dirs,
                self.dense_factor_degrees,
                self.dense_edge_dirs,
                self.dense_edge_degrees,
                self.dense_direction_edges,
                self.dense_direction_factors,
                self.p,
                self.q,
                self.p_m,
                self.p_h,
                self.max_iterations,
                self.damping,
                self.tolerance,
                self.residual_priority_order == "stable_sort",
            )
            return LegacyBpResult(marginals, iteration, converged, max_delta)
        if self.update_schedule == "residual_priority":
            return self._infer_residual_priority(syndrome, herald)

        if self.use_numba:
            marginals, converged, max_delta, iteration = legacy_infer_dense(
                np.ascontiguousarray(syndrome, dtype=np.uint8),
                np.ascontiguousarray(herald, dtype=np.uint8),
                self.dense_factor_dirs,
                self.dense_factor_degrees,
                self.dense_edge_dirs,
                self.dense_edge_degrees,
                self.p,
                self.q,
                self.p_m,
                self.p_h,
                self.max_iterations,
                self.damping,
                self.tolerance,
            )
            return LegacyBpResult(marginals, iteration, converged, max_delta)

        variable_to_factor = {
            (edge, factor): self.prior.copy()
            for edge, factors in enumerate(self.edge_factors)
            for factor in factors
        }
        factor_to_variable = {key: np.full(2, 0.5) for key in variable_to_factor}
        converged = False
        max_delta = float("inf")

        for iteration in range(1, self.max_iterations + 1):
            updated_factor: dict[tuple[int, int], np.ndarray] = {}
            for factor, incident in enumerate(self.factor_edges):
                assignments = self.assignments[len(incident)]
                potential = self.factor_potentials[
                    (len(incident), int(syndrome[factor]), int(herald[factor]))
                ]
                for target_position, target_edge in enumerate(incident):
                    values = potential.copy()
                    for position, edge in enumerate(incident):
                        if position != target_position:
                            values *= variable_to_factor[(edge, factor)][assignments[:, position]]
                    message = _normalise(
                        np.bincount(
                            assignments[:, target_position],
                            weights=values,
                            minlength=2,
                        ).astype(float)
                    )
                    previous = factor_to_variable[(target_edge, factor)]
                    updated_factor[(target_edge, factor)] = _normalise(
                        self.damping * previous + (1 - self.damping) * message
                    )

            updated_variable: dict[tuple[int, int], np.ndarray] = {}
            for edge, factors in enumerate(self.edge_factors):
                for target_factor in factors:
                    message = self.prior.copy()
                    for factor in factors:
                        if factor != target_factor:
                            message *= updated_factor[(edge, factor)]
                    updated_variable[(edge, target_factor)] = _normalise(message)

            max_delta = 0.0
            for key, message in updated_factor.items():
                previous = factor_to_variable[key]
                max_delta = max(
                    max_delta,
                    abs(float(message[0] - previous[0])),
                    abs(float(message[1] - previous[1])),
                )
            for key, message in updated_variable.items():
                previous = variable_to_factor[key]
                max_delta = max(
                    max_delta,
                    abs(float(message[0] - previous[0])),
                    abs(float(message[1] - previous[1])),
                )
            factor_to_variable = updated_factor
            variable_to_factor = updated_variable
            if max_delta < self.tolerance:
                converged = True
                break

        marginals = np.zeros(len(self.graph.edges), dtype=float)
        for edge, factors in enumerate(self.edge_factors):
            belief = self.prior.copy()
            for factor in factors:
                belief *= factor_to_variable[(edge, factor)]
            marginals[edge] = _normalise(belief)[1]
        return LegacyBpResult(marginals, iteration, converged, max_delta)

    def _matching_weights(self, marginals: np.ndarray) -> np.ndarray:
        """Return clipped posterior LLR weights for PyMatching.

        Before 2026-08-26 this used ``-log P(error)``. That was wrong for
        MWPM's independent-edge MAP interface because it omitted the
        likelihood of not selecting an edge, ``-log(1 - P(error))``. The
        required weight is the log-likelihood ratio below; clipping prevents
        hard BP beliefs from becoming infinite numerical weights.
        """
        probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1 - 1e-12)
        return np.log((1 - probabilities) / probabilities)

    def decode(self, syndrome: np.ndarray, herald: np.ndarray) -> LegacyDecodeResult:
        bp = self.infer(syndrome, herald)
        weights = self._matching_weights(bp.edge_marginals)
        matching = pymatching.Matching.from_check_matrix(
            self.graph.check_matrix,
            weights=weights,
            use_virtual_boundary_node=True,
        )
        correction, matching_weight = matching.decode(
            np.asarray(syndrome, dtype=np.uint8), return_weight=True
        )
        return LegacyDecodeResult(
            correction.astype(np.uint8),
            float(matching_weight),
            bp,
            weights,
        )
