#!/usr/bin/env python3
"""Mechanism diagnostic for transferring Relay-BP memory to Herald BP.

This is deliberately not a decoder.  It inspects every soft Relay candidate
on simulated observations and asks whether the conventional Relay criterion
would have had anything to select: a hard thresholded candidate that satisfies
the measured syndrome.  Truth is used only to audit ranking quality.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from math import log
from pathlib import Path

import numpy as np

from herald_bp_decoder import HeraldBeliefMatchingDecoder
from lattice_model import sample_observation, square_graph, honeycomb_graph


@dataclass
class Summary:
    shots: int
    any_syndrome_valid_hard_candidate_rate: float
    proxy_selected_syndrome_valid_rate: float
    mean_valid_candidates_per_shot: float
    proxy_selected_mean_edge_log_loss: float
    oracle_best_leg_mean_edge_log_loss: float
    mean_proxy_rank_by_truth: float
    first_leg_syndrome_valid_rate: float
    relay_compatible_hard_ler: float
    proxy_selected_valid_hard_ler: float | None
    selected_leg_counts: dict[str, int]
    numerical_fixed_point_rate: float


def edge_log_loss(marginals: np.ndarray, truth: np.ndarray) -> float:
    r = np.clip(marginals, 1e-12, 1 - 1e-12)
    x = np.asarray(truth, dtype=float)
    return float(-np.mean(x * np.log(r) + (1 - x) * np.log(1 - r)))


def graph_for(name: str):
    return square_graph(5) if name == "square" else honeycomb_graph(5)


def run_case(
    *, lattice: str, p: float, q: float, shots: int, seed: int,
    first_iterations: int, relay_legs: int, leg_iterations: int,
) -> Summary:
    graph = graph_for(lattice)
    decoder = HeraldBeliefMatchingDecoder(
        graph, p=p, q=q, p_m=0.0, p_h=0.0,
        recurrence_mode="memory",
        max_iterations=first_iterations, gamma0=0.15,
        relay_legs=relay_legs, relay_leg_iterations=leg_iterations,
        gamma_interval=(-0.24, 0.66), relay_seed=0,
    )
    rng = np.random.default_rng(seed)
    any_valid = 0
    selected_valid = 0
    valid_counts: list[int] = []
    proxy_losses: list[float] = []
    best_losses: list[float] = []
    proxy_ranks: list[int] = []
    selected = Counter()
    fixed_points = 0
    first_valid = 0
    relay_hard_failures = 0
    proxy_valid_hard_failures = 0
    proxy_valid_hard_shots = 0

    for _ in range(shots):
        observation = sample_observation(graph, rng, p=p, q=q, p_m=0.0, p_h=0.0)
        gamma_sets = [np.full(len(graph.edges), decoder.gamma0, dtype=float)]
        gamma_rng = np.random.default_rng(decoder.relay_seed)
        gamma_sets.extend(
            gamma_rng.uniform(*decoder.gamma_interval, len(graph.edges))
            for _ in range(decoder.relay_legs)
        )
        initial = np.full(len(graph.edges), p, dtype=float)
        candidates = []
        for leg, gammas in enumerate(gamma_sets):
            limit = decoder.max_iterations if leg == 0 else decoder.relay_leg_iterations
            marginals, messages, converged, _delta, _iterations = decoder._run_leg(
                observation.syndrome, observation.herald, initial, gammas, limit
            )
            score = decoder._candidate_score(
                observation.syndrome, observation.herald, marginals,
                decoder._factor_beliefs(observation.syndrome, observation.herald, messages),
            )
            hard = (marginals > 0.5).astype(np.uint8)
            valid = bool(np.array_equal(graph.true_syndrome(hard), observation.syndrome))
            candidates.append((score, marginals, hard, valid, converged))
            initial = marginals

        scores = np.asarray([candidate[0] for candidate in candidates])
        selected_leg = int(np.argmax(scores))
        selected[str(selected_leg)] += 1
        valid = np.asarray([candidate[3] for candidate in candidates], dtype=bool)
        losses = np.asarray([edge_log_loss(candidate[1], observation.error) for candidate in candidates])
        rank = int(np.argsort(np.argsort(losses))[selected_leg]) + 1
        proxy_ranks.append(rank)
        proxy_losses.append(float(losses[selected_leg]))
        best_losses.append(float(np.min(losses)))
        valid_counts.append(int(np.sum(valid)))
        any_valid += int(np.any(valid))
        selected_valid += int(valid[selected_leg])
        fixed_points += int(candidates[selected_leg][4])
        first_valid += int(valid[0])
        if np.any(valid):
            valid_indices = np.flatnonzero(valid)
            # For uniform p, Relay's original-prior weight is proportional to
            # the number of selected hard-error edges.
            selected_hard = min(
                (candidates[index][2] for index in valid_indices), key=np.sum
            )
            relay_hard_failures += int(graph.logical_parity(observation.error ^ selected_hard))
        if valid[selected_leg]:
            proxy_valid_hard_shots += 1
            proxy_valid_hard_failures += int(
                graph.logical_parity(observation.error ^ candidates[selected_leg][2])
            )

    return Summary(
        shots=shots,
        any_syndrome_valid_hard_candidate_rate=any_valid / shots,
        proxy_selected_syndrome_valid_rate=selected_valid / shots,
        mean_valid_candidates_per_shot=float(np.mean(valid_counts)),
        proxy_selected_mean_edge_log_loss=float(np.mean(proxy_losses)),
        oracle_best_leg_mean_edge_log_loss=float(np.mean(best_losses)),
        mean_proxy_rank_by_truth=float(np.mean(proxy_ranks)),
        first_leg_syndrome_valid_rate=first_valid / shots,
        relay_compatible_hard_ler=relay_hard_failures / shots,
        proxy_selected_valid_hard_ler=(
            proxy_valid_hard_failures / proxy_valid_hard_shots
            if proxy_valid_hard_shots else None
        ),
        selected_leg_counts=dict(selected),
        numerical_fixed_point_rate=fixed_points / shots,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=200)
    parser.add_argument("--seed", type=int, default=741)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [
        ("square", 0.08),
        ("honeycomb", 0.18),
    ]
    payload = {
        "purpose": "mechanism-only Relay transfer audit; no result is used by the decoder",
        "settings": {
            "q": 0.75, "p_m": 0.0, "p_h": 0.0, "gamma0": 0.15,
            "gamma_interval": [-0.24, 0.66], "threshold": 0.5,
        },
        "default_transfer": {},
        "longer_relay_budget": {},
    }
    for lattice, p in cases:
        key = f"{lattice}_p{p:.2f}"
        payload["default_transfer"][key] = asdict(run_case(
            lattice=lattice, p=p, q=0.75, shots=args.shots, seed=args.seed,
            first_iterations=40, relay_legs=6, leg_iterations=20,
        ))
        payload["longer_relay_budget"][key] = asdict(run_case(
            lattice=lattice, p=p, q=0.75, shots=max(20, args.shots // 10), seed=args.seed,
            first_iterations=80, relay_legs=60, leg_iterations=60,
        ))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
