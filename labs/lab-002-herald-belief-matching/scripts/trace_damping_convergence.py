#!/usr/bin/env python3
"""Trace the frozen probability-damped BP recurrence without changing it.

This measurement-only diagnostic owns no decoder decisions.  It reproduces
the registered square L=9, p=0.20, q=1, seed=12 sample, records message and
local-consistency residuals after every synchronous update, and verifies that
its final edge marginals equal the production Python recurrence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from herald_decoder.lattice_model import sample_observation, square_graph
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JSON = ROOT / "labs/lab-002-herald-belief-matching/results/convergence-trace-seed12.json"
DEFAULT_PNG = ROOT / "labs/lab-002-herald-belief-matching/figures/convergence-trace-seed12.png"


def normalise(message: np.ndarray) -> np.ndarray:
    total = float(message[0] + message[1])
    if not np.isfinite(total) or total <= 0:
        raise ValueError("zero-probability message encountered")
    return message / total


def max_pair_delta(current: np.ndarray, previous: np.ndarray) -> float:
    return float(np.max(np.abs(current - previous)))


def edge_marginals(
    decoder: LegacyDampedBpMatchingDecoder,
    factor_to_variable: dict[tuple[int, int], np.ndarray],
) -> np.ndarray:
    marginals = np.zeros(len(decoder.graph.edges), dtype=float)
    for edge, factors in enumerate(decoder.edge_factors):
        belief = decoder.prior.copy()
        for factor in factors:
            belief *= factor_to_variable[(edge, factor)]
        marginals[edge] = normalise(belief)[1]
    return marginals


def factor_marginal_disagreement(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
    variable_to_factor: dict[tuple[int, int], np.ndarray],
    marginals: np.ndarray,
) -> tuple[float, np.ndarray]:
    by_factor = np.zeros(len(decoder.factor_edges), dtype=float)
    for factor, incident in enumerate(decoder.factor_edges):
        assignments = decoder.assignments[len(incident)]
        belief = decoder.factor_potentials[
            (len(incident), int(syndrome[factor]), int(herald[factor]))
        ].copy()
        for position, edge in enumerate(incident):
            belief *= variable_to_factor[(edge, factor)][assignments[:, position]]
        total = float(np.sum(belief))
        if not np.isfinite(total) or total <= 0:
            raise ValueError("zero-probability factor belief encountered")
        belief /= total
        for position, edge in enumerate(incident):
            factor_error_probability = float(np.sum(belief[assignments[:, position] == 1]))
            by_factor[factor] = max(
                by_factor[factor],
                abs(factor_error_probability - float(marginals[edge])),
            )
    return float(np.max(by_factor)), by_factor


def trace(
    decoder: LegacyDampedBpMatchingDecoder,
    syndrome: np.ndarray,
    herald: np.ndarray,
) -> tuple[list[dict], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    variable_to_factor = {
        (edge, factor): decoder.prior.copy()
        for edge, factors in enumerate(decoder.edge_factors)
        for factor in factors
    }
    factor_to_variable = {key: np.full(2, 0.5) for key in variable_to_factor}
    factor_two_back = None
    variable_two_back = None
    previous_marginals = np.full(len(decoder.graph.edges), decoder.p, dtype=float)
    records: list[dict] = []
    final_factor_residual = np.zeros(len(decoder.factor_edges), dtype=float)
    final_edge_residual = np.zeros(len(decoder.graph.edges), dtype=float)
    final_inconsistency = np.zeros(len(decoder.factor_edges), dtype=float)

    for iteration in range(1, decoder.max_iterations + 1):
        updated_factor: dict[tuple[int, int], np.ndarray] = {}
        for factor, incident in enumerate(decoder.factor_edges):
            assignments = decoder.assignments[len(incident)]
            potential = decoder.factor_potentials[
                (len(incident), int(syndrome[factor]), int(herald[factor]))
            ]
            for target_position, target_edge in enumerate(incident):
                values = potential.copy()
                for position, edge in enumerate(incident):
                    if position != target_position:
                        values *= variable_to_factor[(edge, factor)][assignments[:, position]]
                raw = normalise(
                    np.bincount(
                        assignments[:, target_position],
                        weights=values,
                        minlength=2,
                    ).astype(float)
                )
                previous = factor_to_variable[(target_edge, factor)]
                updated_factor[(target_edge, factor)] = normalise(
                    decoder.damping * previous + (1 - decoder.damping) * raw
                )

        updated_variable: dict[tuple[int, int], np.ndarray] = {}
        for edge, factors in enumerate(decoder.edge_factors):
            for target_factor in factors:
                message = decoder.prior.copy()
                for factor in factors:
                    if factor != target_factor:
                        message *= updated_factor[(edge, factor)]
                updated_variable[(edge, target_factor)] = normalise(message)

        factor_residual = np.zeros(len(decoder.factor_edges), dtype=float)
        edge_residual = np.zeros(len(decoder.graph.edges), dtype=float)
        factor_delta = 0.0
        variable_delta = 0.0
        for key, message in updated_factor.items():
            edge, factor = key
            delta = max_pair_delta(message, factor_to_variable[key])
            factor_delta = max(factor_delta, delta)
            factor_residual[factor] = max(factor_residual[factor], delta)
            edge_residual[edge] = max(edge_residual[edge], delta)
        for key, message in updated_variable.items():
            edge, factor = key
            delta = max_pair_delta(message, variable_to_factor[key])
            variable_delta = max(variable_delta, delta)
            factor_residual[factor] = max(factor_residual[factor], delta)
            edge_residual[edge] = max(edge_residual[edge], delta)

        period2_delta = None
        if factor_two_back is not None and variable_two_back is not None:
            period2_delta = max(
                max(
                    max_pair_delta(updated_factor[key], factor_two_back[key])
                    for key in updated_factor
                ),
                max(
                    max_pair_delta(updated_variable[key], variable_two_back[key])
                    for key in updated_variable
                ),
            )

        marginals = edge_marginals(decoder, updated_factor)
        maximum_inconsistency, inconsistency_by_factor = factor_marginal_disagreement(
            decoder,
            syndrome,
            herald,
            updated_variable,
            marginals,
        )
        belief_drift = float(np.max(np.abs(marginals - previous_marginals)))
        records.append(
            {
                "iteration": iteration,
                "max_message_delta": max(factor_delta, variable_delta),
                "max_factor_message_delta": factor_delta,
                "max_variable_message_delta": variable_delta,
                "max_belief_drift": belief_drift,
                "max_factor_marginal_disagreement": maximum_inconsistency,
                "period2_message_delta": period2_delta,
                "worst_factor_row": int(np.argmax(factor_residual)),
                "worst_edge": int(np.argmax(edge_residual)),
            }
        )

        factor_two_back = factor_to_variable
        variable_two_back = variable_to_factor
        factor_to_variable = updated_factor
        variable_to_factor = updated_variable
        previous_marginals = marginals
        final_factor_residual = factor_residual
        final_edge_residual = edge_residual
        final_inconsistency = inconsistency_by_factor

    return records, final_factor_residual, final_edge_residual, final_inconsistency, marginals


def ranked_factor_payload(
    decoder: LegacyDampedBpMatchingDecoder,
    observation,
    residuals: np.ndarray,
    inconsistencies: np.ndarray,
) -> list[dict]:
    detector_vertices = decoder.graph.detector_vertices
    rows = np.argsort(residuals)[::-1][:12]
    return [
        {
            "factor_row": int(row),
            "vertex": int(detector_vertices[row]),
            "x": float(decoder.graph.vertices[detector_vertices[row]].x),
            "y": float(decoder.graph.vertices[detector_vertices[row]].y),
            "syndrome": int(observation.syndrome[row]),
            "herald": int(observation.herald[row]),
            "true_degree": int(observation.detector_degrees[row]),
            "message_residual": float(residuals[row]),
            "marginal_disagreement": float(inconsistencies[row]),
        }
        for row in rows
    ]


def ranked_edge_payload(
    decoder: LegacyDampedBpMatchingDecoder,
    residuals: np.ndarray,
) -> list[dict]:
    rows = np.argsort(residuals)[::-1][:12]
    return [
        {
            "edge": int(edge),
            "vertices": [int(vertex) for vertex in decoder.graph.edges[edge]],
            "message_residual": float(residuals[edge]),
        }
        for edge in rows
    ]


def render_figure(payload: dict, destination: Path) -> None:
    records = payload["iterations"]
    x = np.asarray([row["iteration"] for row in records])
    delta = np.asarray([row["max_message_delta"] for row in records])
    period2 = np.asarray(
        [np.nan if row["period2_message_delta"] is None else row["period2_message_delta"] for row in records]
    )
    inconsistency = np.asarray([row["max_factor_marginal_disagreement"] for row in records])
    drift = np.asarray([row["max_belief_drift"] for row in records])
    factors = payload["final_bottlenecks"]["factors"]

    figure, axes = plt.subplots(1, 3, figsize=(14.5, 4.5), constrained_layout=True)
    axes[0].semilogy(x, delta, label="one-step message residual", color="#0072B2")
    axes[0].semilogy(x, period2, label="two-step residual", color="#D55E00")
    axes[0].axhline(payload["decoder"]["tolerance"], color="#222222", linestyle="--", linewidth=1)
    axes[0].set(xlabel="iteration", ylabel="maximum absolute change", title="Message convergence")
    axes[0].legend(fontsize=8)

    axes[1].semilogy(x, inconsistency, label="factor-variable disagreement", color="#009E73")
    axes[1].semilogy(x, drift, label="edge-belief drift", color="#CC79A7")
    axes[1].set(xlabel="iteration", ylabel="maximum absolute residual", title="Local consistency")
    axes[1].legend(fontsize=8)

    scatter = axes[2].scatter(
        [row["x"] for row in factors],
        [row["y"] for row in factors],
        c=[max(row["message_residual"], 1e-16) for row in factors],
        s=[45 + 320 * row["message_residual"] / max(factors[0]["message_residual"], 1e-16) for row in factors],
        cmap="magma",
        norm="log",
        edgecolor="#222222",
        linewidth=0.5,
    )
    axes[2].invert_yaxis()
    axes[2].set_aspect("equal")
    axes[2].set(title="Largest iteration-80 factor residuals", xlabel="x", ylabel="y")
    figure.colorbar(scatter, ax=axes[2], label="message residual")
    figure.suptitle("Herald BP convergence trace · square L=9, p=0.20, q=1, seed=12")
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--figure", type=Path, default=DEFAULT_PNG)
    args = parser.parse_args()

    graph = square_graph(9)
    observation = sample_observation(
        graph,
        np.random.default_rng(12),
        p=0.20,
        q=1.0,
        p_m=0.0,
        p_h=0.0,
    )
    decoder = LegacyDampedBpMatchingDecoder(
        graph,
        p=0.20,
        q=1.0,
        p_m=0.0,
        p_h=0.0,
        max_iterations=80,
        damping=0.25,
        tolerance=1e-8,
        use_numba=False,
    )
    records, factor_residual, edge_residual, inconsistency, traced_marginals = trace(
        decoder,
        observation.syndrome,
        observation.herald,
    )
    production = decoder.infer(observation.syndrome, observation.herald)
    if records[-1]["max_message_delta"] != production.max_message_delta:
        raise RuntimeError("trace does not reproduce production max-message delta")
    if not np.array_equal(traced_marginals, production.edge_marginals):
        raise RuntimeError("trace does not reproduce production edge marginals")

    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 Phase C0 measurement-only BP convergence trace",
        "sample": {
            "lattice": "square",
            "L": 9,
            "p": 0.20,
            "q": 1.0,
            "p_m": 0.0,
            "p_h": 0.0,
            "seed": 12,
            "syndrome_weight": int(np.sum(observation.syndrome)),
            "herald_weight": int(np.sum(observation.herald)),
        },
        "decoder": {
            "recurrence": "probability_damping",
            "damping": 0.25,
            "max_iterations": 80,
            "tolerance": 1e-8,
            "matching_projection": "posterior_llr",
            "changed_decoder_output": False,
        },
        "validation": {
            "production_converged": bool(production.converged),
            "production_iterations": int(production.iterations),
            "final_marginals_bit_identical": True,
            "script_sha256": script_hash,
        },
        "iterations": records,
        "final_bottlenecks": {
            "factors": ranked_factor_payload(decoder, observation, factor_residual, inconsistency),
            "edges": ranked_edge_payload(decoder, edge_residual),
        },
        "evidence_boundary": "One deterministic measurement-only trace; no tuning, convergence-rate, or LER inference.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    render_figure(payload, args.figure)
    print(json.dumps({
        "output": str(args.output),
        "figure": str(args.figure),
        "converged": production.converged,
        "final_delta": production.max_message_delta,
        "worst_factor": payload["final_bottlenecks"]["factors"][0],
    }, indent=2))


if __name__ == "__main__":
    main()
