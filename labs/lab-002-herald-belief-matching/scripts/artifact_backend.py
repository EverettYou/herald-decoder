#!/usr/bin/env python3
"""Lab 002 data endpoint for the interactive belief-matching artifact."""

from __future__ import annotations

from time import perf_counter

import numpy as np

from herald_bp_decoder import (
    HeraldBeliefMatchingDecoder,
    SyndromeOnlyMatchingDecoder,
    hard_bp_then_matching,
)
from lattice_model import honeycomb_graph, sample_observation, square_graph


def _probability(body: dict, name: str, upper: float) -> float:
    value = body.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not 0 <= value <= upper:
        raise ValueError(f"{name} must lie in [0, {upper}]")
    return value


def _indices(bits: np.ndarray) -> list[int]:
    return np.flatnonzero(bits).astype(int).tolist()


def _soft_metrics(probabilities: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """Proper scoring rules for a simulated latent edge configuration."""
    probabilities = np.clip(np.asarray(probabilities, dtype=float), 1e-12, 1 - 1e-12)
    truth = np.asarray(truth, dtype=float)
    log_loss = -np.mean(truth * np.log(probabilities) + (1 - truth) * np.log(1 - probabilities))
    return {
        "log_loss": float(log_loss),
        "brier": float(np.mean((probabilities - truth) ** 2)),
    }


def artifact_payload(body: dict) -> dict:
    """Sample one configuration and expose every inference layer."""
    lattice = body.get("lattice")
    if lattice not in {"square", "honeycomb"}:
        raise ValueError("lattice must be square or honeycomb")
    size = body.get("L")
    seed = body.get("seed")
    if isinstance(size, bool) or not isinstance(size, int) or not 3 <= size <= 11:
        raise ValueError("L must be an integer in [3, 11]")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be a uint32 integer")
    p = _probability(body, "p", 1.0)
    q = _probability(body, "q", 1.0)
    p_m = _probability(body, "p_m", 0.5)
    p_h = _probability(body, "p_h", 1.0)
    recurrence_mode = body.get("recurrence_mode", "damping")
    if recurrence_mode not in {"damping", "memory"}:
        raise ValueError("recurrence_mode must be damping or memory")
    threshold = float(body.get("bp_threshold", 0.5))
    if not 0.5 <= threshold < 1:
        raise ValueError("bp_threshold must lie in [0.5, 1)")

    graph = square_graph(size) if lattice == "square" else honeycomb_graph(size)
    observation = sample_observation(
        graph, np.random.default_rng(seed), p=p, q=q, p_m=p_m, p_h=p_h
    )
    # The exact p endpoints are valid sampling controls.  Decoder weights use a
    # limiting value to avoid infinite logarithms in the interactive endpoint.
    decoder_p = min(max(p, 1e-9), 1.0 - 1e-9)

    start = perf_counter()
    baseline_decoder = SyndromeOnlyMatchingDecoder(graph, p=decoder_p)
    baseline_correction, baseline_weight = baseline_decoder.decode(observation.syndrome)
    baseline_ms = 1000 * (perf_counter() - start)

    syndrome_bp_decoder = HeraldBeliefMatchingDecoder(
        graph,
        p=decoder_p,
        q=0,
        p_m=p_m,
        p_h=p_h,
        max_iterations=80,
        recurrence_mode=recurrence_mode,
    )
    start = perf_counter()
    syndrome_result = syndrome_bp_decoder.decode(
        observation.syndrome, np.zeros_like(observation.herald)
    )
    syndrome_bp_ms = 1000 * (perf_counter() - start)

    herald_decoder = HeraldBeliefMatchingDecoder(
        graph,
        p=decoder_p,
        q=q,
        p_m=p_m,
        p_h=p_h,
        max_iterations=80,
        recurrence_mode=recurrence_mode,
    )
    start = perf_counter()
    herald_result = herald_decoder.decode(observation.syndrome, observation.herald)
    herald_ms = 1000 * (perf_counter() - start)

    start = perf_counter()
    staged = hard_bp_then_matching(
        graph,
        observation.syndrome,
        herald_result.bp.edge_marginals,
        baseline_decoder,
        threshold=threshold,
    )
    staged_ms = 1000 * (perf_counter() - start)

    baseline_residual = observation.error ^ baseline_correction
    syndrome_bp_residual = observation.error ^ syndrome_result.correction
    herald_residual = observation.error ^ herald_result.correction
    herald_residual_syndrome = graph.true_syndrome(herald_residual)
    herald_correction_degrees = graph.degrees(herald_result.correction)
    staged_pre_residual = observation.error ^ staged.pre_correction
    staged_final_residual = observation.error ^ staged.correction
    detector_ids = graph.detector_vertices
    syndrome_vertices = [detector_ids[row] for row in _indices(observation.syndrome)]
    herald_vertices = [detector_ids[row] for row in _indices(observation.herald)]
    prior_probabilities = np.full(len(graph.edges), p, dtype=float)

    return {
        "model": {
            "lattice": lattice,
            "L": size,
            "p": p,
            "q": q,
            "p_m": p_m,
            "p_h": p_h,
            "seed": seed,
            "matching_projection": "posterior_llr",
            "recurrence_mode": recurrence_mode,
            "bp_recurrence": {
                "mode": recurrence_mode,
                "damping": herald_decoder.damping if recurrence_mode == "damping" else None,
            },
            "bp_threshold": threshold,
            "bp_search": {
                "enabled": recurrence_mode == "memory",
                "initial_memory": herald_decoder.gamma0,
                "additional_candidates": herald_decoder.relay_legs,
                "candidate_iterations": herald_decoder.relay_leg_iterations,
                "memory_interval": list(herald_decoder.gamma_interval),
                "seed": herald_decoder.relay_seed,
            },
        },
        "graph": {
            "vertices": [
                {
                    "id": index,
                    "x": vertex.x,
                    "y": vertex.y,
                    "detector": vertex.detector,
                    "boundary_side": vertex.boundary_side,
                }
                for index, vertex in enumerate(graph.vertices)
            ],
            "edges": [list(edge) for edge in graph.edges],
            "logical_edge_indices": sorted(graph.logical_edges),
            "logical_line": [{"x": point.x, "y": point.y} for point in graph.logical_line],
        },
        "observation": {
            "error_edge_indices": _indices(observation.error),
            "syndrome_vertices": syndrome_vertices,
            "herald_vertices": herald_vertices,
            "detector_degrees": {
                str(vertex): int(observation.detector_degrees[row])
                for row, vertex in enumerate(detector_ids)
            },
        },
        "posterior": {
            "prior": p,
            "syndrome_only": syndrome_result.bp.edge_marginals.tolist(),
            "herald_aware": herald_result.bp.edge_marginals.tolist(),
            "herald_delta": (
                herald_result.bp.edge_marginals - syndrome_result.bp.edge_marginals
            ).tolist(),
            "matching_weights": herald_result.edge_weights.tolist(),
        },
        "baseline": {
            "correction_edge_indices": _indices(baseline_correction),
            "residual_edge_indices": _indices(baseline_residual),
            "logical_error": bool(graph.logical_parity(baseline_residual)),
            "matching_weight": baseline_weight,
            "decode_ms": baseline_ms,
        },
        "syndrome_bp_decoder": {
            "correction_edge_indices": _indices(syndrome_result.correction),
            "residual_edge_indices": _indices(syndrome_bp_residual),
            "logical_error": bool(graph.logical_parity(syndrome_bp_residual)),
            "matching_weight": syndrome_result.matching_weight,
            "decode_ms": syndrome_bp_ms,
            "bp": {
                "converged": syndrome_result.bp.converged,
                "iterations": syndrome_result.bp.iterations,
                "max_message_delta": syndrome_result.bp.max_message_delta,
                "score": syndrome_result.bp.score,
                "selected_leg": syndrome_result.bp.selected_leg,
                "legs": syndrome_result.bp.legs,
            },
        },
        "herald_decoder": {
            "correction_edge_indices": _indices(herald_result.correction),
            "residual_edge_indices": _indices(herald_residual),
            "residual_syndrome_vertices": [
                detector_ids[row] for row in _indices(herald_residual_syndrome)
            ],
            "unexplained_herald_vertices": [
                detector_ids[row]
                for row, vertex in enumerate(detector_ids)
                if observation.herald[row] and herald_correction_degrees[vertex] < 2
            ],
            "logical_error": bool(graph.logical_parity(herald_residual)),
            "matching_weight": herald_result.matching_weight,
            "decode_ms": herald_ms,
            "bp": {
                "converged": herald_result.bp.converged,
                "iterations": herald_result.bp.iterations,
                "max_message_delta": herald_result.bp.max_message_delta,
                "score": herald_result.bp.score,
                "selected_leg": herald_result.bp.selected_leg,
                "legs": herald_result.bp.legs,
            },
        },
        "staged_diagnostic": {
            "definition": "hard marginal-MAP BP predecode, discard heralds, then static-weight syndrome-only PyMatching",
            "threshold": threshold,
            "pre_correction_edge_indices": _indices(staged.pre_correction),
            "pre_residual_edge_indices": _indices(staged_pre_residual),
            "residual_syndrome_vertices": [
                detector_ids[row] for row in _indices(staged.residual_syndrome)
            ],
            "completion_correction_edge_indices": _indices(staged.completion_correction),
            "correction_edge_indices": _indices(staged.correction),
            "final_residual_edge_indices": _indices(staged_final_residual),
            "final_syndrome_vertices": [
                detector_ids[row] for row in _indices(staged.final_syndrome)
            ],
            "logical_error": bool(graph.logical_parity(staged_final_residual)),
            "completion_weight": staged.completion_weight,
            "decode_ms": staged_ms,
            "density_flow": {
                "input_syndrome": float(np.mean(observation.syndrome)),
                "after_soft_bp_inference": float(np.mean(observation.syndrome)),
                "after_hard_bp_predecode": float(np.mean(staged.residual_syndrome)),
                "after_mwpm_completion": float(np.mean(staged.final_syndrome)),
                "input_true_error": float(np.mean(observation.error)),
                "after_hard_bp_true_residual": float(np.mean(staged_pre_residual)),
                "after_mwpm_true_residual": float(np.mean(staged_final_residual)),
            },
        },
        "syndrome_bp": {
            "decode_ms": syndrome_bp_ms,
            "converged": syndrome_result.bp.converged,
            "iterations": syndrome_result.bp.iterations,
            "score": syndrome_result.bp.score,
            "selected_leg": syndrome_result.bp.selected_leg,
            "legs": syndrome_result.bp.legs,
        },
        "soft_quality": {
            "scope": "simulation-only latent-edge diagnostic; logical error remains primary",
            "prior": _soft_metrics(prior_probabilities, observation.error),
            "syndrome_bp": _soft_metrics(syndrome_result.bp.edge_marginals, observation.error),
            "herald_bp": _soft_metrics(herald_result.bp.edge_marginals, observation.error),
        },
    }
