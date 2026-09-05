#!/usr/bin/env python3
"""Lab 002 fusion-remnant belief propagation followed by PyMatching MWPM.

This module implements only the Lab-specific posterior front end.  The final
matching problem is delegated to the maintained ``pymatching`` package.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import exp, isfinite, log

import numpy as np
import pymatching

from .lattice_model import LatticeGraph
from .numba_bp_kernels import NUMBA_AVAILABLE, dense_topology, memory_leg_dense


def _load_damping_decoder_class():
    """Return the packaged damping recurrence used by the stable decoder API."""
    from .legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder

    return LegacyDampedBpMatchingDecoder


def _normalise(message: np.ndarray) -> np.ndarray:
    # Almost every BP message is binary.  Avoid dispatching a generic NumPy
    # reduction hundreds of thousands of times per decoded observation.
    total = float(message[0] + message[1]) if message.size == 2 else float(np.sum(message))
    if not isfinite(total) or total <= 0:
        raise ValueError("observation has zero probability under the herald model")
    return message / total


def _vertex_likelihood(
    assignment: tuple[int, ...],
    syndrome: int,
    herald: int,
    *,
    q: float,
    p_m: float,
    p_h: float,
) -> float:
    degree = sum(assignment)
    parity_probability = (1 - p_m) if (degree & 1) == syndrome else p_m
    alpha = q * (1 - p_h)
    if herald:
        herald_probability = alpha if degree >= 2 else 0.0
    else:
        herald_probability = (1 - alpha) if degree >= 2 else 1.0
    return parity_probability * herald_probability


@dataclass(frozen=True)
class BpResult:
    edge_marginals: np.ndarray
    iterations: int
    converged: bool
    max_message_delta: float
    score: float | None
    selected_leg: int
    legs: int


@dataclass(frozen=True)
class DecodeResult:
    correction: np.ndarray
    matching_weight: float
    bp: BpResult
    edge_weights: np.ndarray


@dataclass(frozen=True)
class StagedDecodeResult:
    """Diagnostic hard BP predecode followed by syndrome-only PyMatching.

    The production belief-matching decoder does not apply a BP correction.
    This separate path thresholds the BP marginals so that the proposed
    "effective error-rate reduction" mechanism can be tested directly.
    """

    pre_correction: np.ndarray
    residual_syndrome: np.ndarray
    completion_correction: np.ndarray
    correction: np.ndarray
    final_syndrome: np.ndarray
    completion_weight: float


class SyndromeOnlyMatchingDecoder:
    """Static-prior MWPM baseline backed entirely by PyMatching."""

    def __init__(self, graph: LatticeGraph, *, p: float):
        if not 0 < p < 1:
            raise ValueError("p must lie strictly between 0 and 1")
        self.graph = graph
        weight = log((1 - p) / p)
        self.edge_weights = np.full(len(graph.edges), weight, dtype=float)
        self.matching = pymatching.Matching.from_check_matrix(
            graph.check_matrix,
            weights=self.edge_weights,
            use_virtual_boundary_node=True,
        )

    def decode(self, syndrome: np.ndarray) -> tuple[np.ndarray, float]:
        syndrome = np.asarray(syndrome, dtype=np.uint8)
        if syndrome.shape != (len(self.graph.detector_vertices),):
            raise ValueError("syndrome vector has the wrong shape")
        correction, weight = self.matching.decode(syndrome, return_weight=True)
        return correction.astype(np.uint8), float(weight)


class HeraldBeliefMatchingDecoder:
    """Herald-aware sum-product inference plus posterior-weighted PyMatching.

    ``recurrence_mode="damping"`` is the evidence-backed default and uses the
    frozen probability-space message recurrence.  ``"memory"`` opts into the
    experimental relayed log-odds-memory search retained for controlled
    ablations.
    """

    def __init__(
        self,
        graph: LatticeGraph,
        *,
        p: float,
        q: float,
        p_m: float = 0.0,
        p_h: float = 0.0,
        max_iterations: int = 40,
        recurrence_mode: str = "damping",
        damping: float = 0.25,
        tolerance: float = 1e-8,
        gamma0: float = 0.15,
        relay_legs: int = 6,
        relay_leg_iterations: int = 20,
        gamma_interval: tuple[float, float] = (-0.24, 0.66),
        relay_seed: int = 0,
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
        if recurrence_mode not in {"damping", "memory"}:
            raise ValueError("recurrence_mode must be 'damping' or 'memory'")
        if update_schedule not in {"synchronous", "residual_priority"}:
            raise ValueError("update_schedule must be 'synchronous' or 'residual_priority'")
        if residual_priority_order not in {"scan", "stable_sort"}:
            raise ValueError("residual_priority_order must be 'scan' or 'stable_sort'")
        if recurrence_mode == "memory" and (
            update_schedule != "synchronous"
            or residual_priority_order != "scan"
            or residual_priority_buffer_reuse
            or residual_priority_cached_products
        ):
            raise ValueError("residual-priority controls are available only for damping BP")
        if max_iterations < 1 or relay_legs < 0 or relay_leg_iterations < 1 or tolerance <= 0:
            raise ValueError("invalid BP iteration controls")
        if not 0 <= damping < 1:
            raise ValueError("damping must lie in [0, 1)")
        if not np.isfinite(gamma0) or len(gamma_interval) != 2:
            raise ValueError("invalid Relay memory controls")
        if not all(np.isfinite(value) for value in gamma_interval) or gamma_interval[0] > gamma_interval[1]:
            raise ValueError("gamma_interval must be a finite ordered pair")
        self.graph = graph
        self.p = p
        self.q = q
        self.p_m = p_m
        self.p_h = p_h
        self.max_iterations = max_iterations
        self.recurrence_mode = recurrence_mode
        self.damping = damping
        self.tolerance = tolerance
        self.gamma0 = gamma0
        self.relay_legs = relay_legs
        self.relay_leg_iterations = relay_leg_iterations
        self.gamma_interval = gamma_interval
        self.relay_seed = relay_seed
        self.update_schedule = update_schedule
        self.residual_priority_order = residual_priority_order
        self.residual_priority_buffer_reuse = bool(residual_priority_buffer_reuse)
        self.residual_priority_cached_products = bool(residual_priority_cached_products)
        self.use_numba = NUMBA_AVAILABLE if use_numba is None else bool(use_numba)
        if self.use_numba and not NUMBA_AVAILABLE:
            raise RuntimeError("Numba was requested but is unavailable")
        self.prior = np.asarray([1 - p, p], dtype=float)
        self.prior_log_odds = log((1 - p) / p)
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
        self._damping_decoder = None
        if self.recurrence_mode == "damping":
            # Load lazily to keep the frozen A/B implementation independent
            # while exposing one stable public decoder entry point.
            damping_decoder_class = _load_damping_decoder_class()
            self._damping_decoder = damping_decoder_class(
                graph,
                p=p,
                q=q,
                p_m=p_m,
                p_h=p_h,
                max_iterations=max_iterations,
                damping=damping,
                tolerance=tolerance,
                update_schedule=update_schedule,
                residual_priority_order=residual_priority_order,
                residual_priority_buffer_reuse=residual_priority_buffer_reuse,
                residual_priority_cached_products=residual_priority_cached_products,
                use_numba=self.use_numba,
            )

    @staticmethod
    def _from_log_odds(log_odds: float) -> np.ndarray:
        """Return [P(x=0), P(x=1)] from log(P(0)/P(1)) stably."""
        if log_odds >= 0:
            exponential = exp(-log_odds)
            error = exponential / (1 + exponential)
            return np.asarray([1 - error, error])
        exponential = exp(log_odds)
        no_error = exponential / (1 + exponential)
        return np.asarray([no_error, 1 - no_error])

    @staticmethod
    def _log_odds(probability: float) -> float:
        probability = float(probability)
        if probability < 1e-12:
            probability = 1e-12
        elif probability > 1 - 1e-12:
            probability = 1 - 1e-12
        return log((1 - probability) / probability)

    def _factor_beliefs(
        self,
        syndrome: np.ndarray,
        herald: np.ndarray,
        variable_to_factor: dict[tuple[int, int], np.ndarray],
    ) -> list[np.ndarray]:
        beliefs: list[np.ndarray] = []
        for factor, incident in enumerate(self.factor_edges):
            assignments = self.assignments[len(incident)]
            values = self.factor_potentials[
                (len(incident), int(syndrome[factor]), int(herald[factor]))
            ].copy()
            for position, edge in enumerate(incident):
                values *= variable_to_factor[(edge, factor)][assignments[:, position]]
            beliefs.append(_normalise(values))
        return beliefs

    def _candidate_score(
        self,
        syndrome: np.ndarray,
        herald: np.ndarray,
        marginals: np.ndarray,
        factor_beliefs: list[np.ndarray],
    ) -> float:
        """Bethe log-evidence minus local pseudomarginal inconsistency.

        This is an observation-only ranking criterion.  It is deliberately
        not a hard syndrome-validity condition and it never inspects latent
        simulator edge truth.
        """
        free_energy = 0.0
        consistency = 0.0
        for factor, incident in enumerate(self.factor_edges):
            assignments = self.assignments[len(incident)]
            potential = self.factor_potentials[
                (len(incident), int(syndrome[factor]), int(herald[factor]))
            ]
            belief = factor_beliefs[factor]
            positive = belief > 0
            free_energy += float(np.sum(belief[positive] * (np.log(belief[positive]) - np.log(potential[positive]))))
            for position, edge in enumerate(incident):
                local = np.bincount(assignments[:, position], weights=belief, minlength=2)
                consistency += float(np.abs(local[1] - marginals[edge]))
        for edge, factors in enumerate(self.edge_factors):
            belief = np.asarray([1 - marginals[edge], marginals[edge]])
            positive = belief > 0
            free_energy += (1 - len(factors)) * float(
                np.sum(belief[positive] * (np.log(belief[positive]) - np.log(self.prior[positive])))
            )
        return -free_energy - consistency

    def _run_leg(
        self,
        syndrome: np.ndarray,
        herald: np.ndarray,
        initial_marginals: np.ndarray,
        gammas: np.ndarray,
        max_iterations: int,
    ) -> tuple[np.ndarray, dict[tuple[int, int], np.ndarray], bool, float, int]:
        """Run one DMem-BP leg, retaining only relay beliefs between legs."""
        if self.use_numba:
            marginals, dense_messages, converged, max_delta, iteration = memory_leg_dense(
                np.ascontiguousarray(syndrome, dtype=np.uint8),
                np.ascontiguousarray(herald, dtype=np.uint8),
                self.dense_factor_dirs,
                self.dense_factor_degrees,
                self.dense_edge_dirs,
                self.dense_edge_degrees,
                np.ascontiguousarray(initial_marginals, dtype=float),
                np.ascontiguousarray(gammas, dtype=float),
                self.p,
                self.q,
                self.p_m,
                self.p_h,
                max_iterations,
                self.tolerance,
            )
            variable_to_factor = {
                key: dense_messages[index].copy()
                for index, key in enumerate(self.dense_directed_keys)
            }
            return marginals, variable_to_factor, converged, max_delta, iteration
        previous_marginals = np.asarray(initial_marginals, dtype=float).copy()
        variable_to_factor = {
            (edge, factor): self._from_log_odds(
                (1 - gammas[edge]) * self.prior_log_odds
                + gammas[edge] * self._log_odds(previous_marginals[edge])
            )
            for edge, factors in enumerate(self.edge_factors)
            for factor in factors
        }
        factor_to_variable = {key: np.full(2, 0.5) for key in variable_to_factor}
        converged = False
        max_delta = float("inf")

        for iteration in range(1, max_iterations + 1):
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
                    updated_factor[(target_edge, factor)] = _normalise(
                        np.bincount(assignments[:, target_position], weights=values, minlength=2).astype(float)
                    )

            updated_variable: dict[tuple[int, int], np.ndarray] = {}
            marginals = np.zeros(len(self.graph.edges), dtype=float)
            for edge, factors in enumerate(self.edge_factors):
                memory_prior = self._from_log_odds(
                    (1 - gammas[edge]) * self.prior_log_odds
                    + gammas[edge] * self._log_odds(previous_marginals[edge])
                )
                belief = memory_prior.copy()
                for factor in factors:
                    belief *= updated_factor[(edge, factor)]
                marginals[edge] = _normalise(belief)[1]
                for target_factor in factors:
                    message = memory_prior.copy()
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
            previous_marginals = marginals
            if max_delta < self.tolerance:
                converged = True
                break
        return marginals, variable_to_factor, converged, max_delta, iteration

    def infer(self, syndrome: np.ndarray, herald: np.ndarray) -> BpResult:
        syndrome = np.asarray(syndrome, dtype=np.uint8)
        herald = np.asarray(herald, dtype=np.uint8)
        expected = (len(self.graph.detector_vertices),)
        if syndrome.shape != expected or herald.shape != expected:
            raise ValueError("syndrome or herald vector has the wrong shape")
        if np.any(syndrome > 1) or np.any(herald > 1):
            raise ValueError("syndrome and herald must be binary")

        if self.recurrence_mode == "damping":
            result = self._damping_decoder.infer(syndrome, herald)
            return BpResult(
                result.edge_marginals,
                result.iterations,
                result.converged,
                result.max_message_delta,
                None,
                0,
                1,
            )

        rng = np.random.default_rng(self.relay_seed)
        initial = np.full(len(self.graph.edges), self.p, dtype=float)
        candidates: list[tuple[float, np.ndarray, bool, float, int]] = []
        total_iterations = 0
        gamma_sets = [np.full(len(self.graph.edges), self.gamma0, dtype=float)]
        gamma_sets.extend(
            rng.uniform(self.gamma_interval[0], self.gamma_interval[1], len(self.graph.edges))
            for _ in range(self.relay_legs)
        )
        for leg, gammas in enumerate(gamma_sets):
            limit = self.max_iterations if leg == 0 else self.relay_leg_iterations
            marginals, variable_to_factor, converged, max_delta, iterations = self._run_leg(
                syndrome, herald, initial, gammas, limit
            )
            total_iterations += iterations
            factor_beliefs = self._factor_beliefs(syndrome, herald, variable_to_factor)
            score = self._candidate_score(syndrome, herald, marginals, factor_beliefs)
            candidates.append((score, marginals, converged, max_delta, total_iterations))
            initial = marginals
        selected_leg = int(np.argmax([candidate[0] for candidate in candidates]))
        score, marginals, converged, max_delta, iterations = candidates[selected_leg]
        return BpResult(marginals, iterations, converged, max_delta, score, selected_leg, len(candidates))

    def _matching_weights(self, marginals: np.ndarray) -> np.ndarray:
        """Return the clipped posterior LLR required by the MWPM interface.

        ``-log P(error)`` was removed on 2026-08-26: it made likely edges
        cheap but did not penalise leaving them unselected.  LLR includes both
        outcomes in the independent-posterior MAP objective.
        """
        probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1 - 1e-12)
        return np.log((1 - probabilities) / probabilities)

    def decode(self, syndrome: np.ndarray, herald: np.ndarray) -> DecodeResult:
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
        return DecodeResult(correction.astype(np.uint8), float(matching_weight), bp, weights)


# Compatibility alias for notebooks and experiment commands written before the
# public name was aligned with the full soft-BP-plus-matching algorithm.
HeraldAwareBpMatchingDecoder = HeraldBeliefMatchingDecoder


def hard_bp_then_matching(
    graph: LatticeGraph,
    syndrome: np.ndarray,
    edge_marginals: np.ndarray,
    matching_decoder: SyndromeOnlyMatchingDecoder,
    *,
    threshold: float = 0.5,
) -> StagedDecodeResult:
    """Apply marginal-MAP edges, discard heralds, then complete with MWPM.

    This is an intentionally explicit diagnostic decoder, not an internal
    stage of :class:`HeraldBeliefMatchingDecoder`.  It tests whether a hard
    decision made from the herald-aware posterior reduces the measured
    syndrome density before a conventional syndrome-only decoder is called.
    """
    syndrome = np.asarray(syndrome, dtype=np.uint8)
    marginals = np.asarray(edge_marginals, dtype=float)
    if syndrome.shape != (len(graph.detector_vertices),):
        raise ValueError("syndrome vector has the wrong shape")
    if marginals.shape != (len(graph.edges),):
        raise ValueError("edge marginals have the wrong shape")
    if not 0.5 <= threshold < 1:
        raise ValueError("threshold must lie in [0.5, 1)")

    pre_correction = (marginals > threshold).astype(np.uint8)
    residual_syndrome = syndrome ^ graph.true_syndrome(pre_correction)
    completion_correction, completion_weight = matching_decoder.decode(residual_syndrome)
    correction = pre_correction ^ completion_correction
    final_syndrome = syndrome ^ graph.true_syndrome(correction)
    return StagedDecodeResult(
        pre_correction=pre_correction,
        residual_syndrome=residual_syndrome,
        completion_correction=completion_correction,
        correction=correction,
        final_syndrome=final_syndrome,
        completion_weight=completion_weight,
    )


def exact_posterior(
    graph: LatticeGraph,
    syndrome: np.ndarray,
    herald: np.ndarray,
    *,
    p: float,
    q: float,
    p_m: float = 0.0,
    p_h: float = 0.0,
    maximum_edges: int = 22,
) -> tuple[np.ndarray, np.ndarray]:
    """Enumerate a small graph and return edge and logical-class posteriors."""
    edge_count = len(graph.edges)
    if edge_count > maximum_edges:
        raise ValueError(f"exact enumeration is limited to {maximum_edges} edges")
    syndrome = np.asarray(syndrome, dtype=np.uint8)
    herald = np.asarray(herald, dtype=np.uint8)
    if syndrome.shape != (len(graph.detector_vertices),) or herald.shape != syndrome.shape:
        raise ValueError("syndrome or herald vector has the wrong shape")

    log_partition = -np.inf
    edge_log_mass = np.full(edge_count, -np.inf)
    logical_log_mass = np.full(2, -np.inf)
    for mask in range(1 << edge_count):
        error = np.fromiter(((mask >> edge) & 1 for edge in range(edge_count)), dtype=np.uint8)
        ones = int(np.sum(error))
        log_probability = ones * log(p) + (edge_count - ones) * log(1 - p)
        degrees = graph.degrees(error)[list(graph.detector_vertices)]
        possible = True
        for factor, degree in enumerate(degrees):
            likelihood = _vertex_likelihood(
                tuple([1] * int(degree)),
                int(syndrome[factor]),
                int(herald[factor]),
                q=q,
                p_m=p_m,
                p_h=p_h,
            )
            if likelihood <= 0:
                possible = False
                break
            log_probability += log(likelihood)
        if not possible:
            continue
        log_partition = np.logaddexp(log_partition, log_probability)
        logical = graph.logical_parity(error)
        logical_log_mass[logical] = np.logaddexp(logical_log_mass[logical], log_probability)
        for edge in np.flatnonzero(error):
            edge_log_mass[int(edge)] = np.logaddexp(edge_log_mass[int(edge)], log_probability)
    if not np.isfinite(log_partition):
        raise ValueError("observation has zero probability under the exact model")
    return np.exp(edge_log_mass - log_partition), np.exp(logical_log_mass - log_partition)
