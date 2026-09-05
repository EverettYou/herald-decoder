#!/usr/bin/env python3
"""Matched soft-output ablation of Relay-leg selection rules.

All Relay arms still pass only the selected *soft* edge marginals to MWPM.
The thresholded hard vector is used solely as an observation-derived selector
in the two ``valid_*`` arms; no hard BP correction is applied.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from math import comb, sqrt
from pathlib import Path
from time import perf_counter

import numpy as np
import pymatching

from herald_bp_decoder import HeraldAwareBpMatchingDecoder
from lattice_model import honeycomb_graph, sample_observation, square_graph
from legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


ARMS = ("legacy_damped", "proxy", "first_leg", "first_valid", "min_prior_valid")


def wilson(errors: int, shots: int) -> list[float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return [center - radius, center + radius]


def mcnemar(rescued: int, harmed: int) -> float:
    count = rescued + harmed
    if count == 0:
        return 1.0
    tail = sum(comb(count, index) for index in range(min(rescued, harmed) + 1))
    return min(1.0, 2 * tail / (2**count))


def proper(marginals: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    r = np.clip(marginals, 1e-12, 1 - 1e-12)
    x = np.asarray(truth, dtype=float)
    return (
        float(-np.mean(x * np.log(r) + (1 - x) * np.log(1 - r))),
        float(np.mean((r - x) ** 2)),
    )


@dataclass
class Candidate:
    score: float
    marginals: np.ndarray
    hard: np.ndarray
    valid: bool
    converged: bool
    leg: int


def relay_candidates(decoder, syndrome: np.ndarray, herald: np.ndarray) -> list[Candidate]:
    gamma_rng = np.random.default_rng(decoder.relay_seed)
    gamma_sets = [np.full(len(decoder.graph.edges), decoder.gamma0, dtype=float)]
    gamma_sets.extend(
        gamma_rng.uniform(*decoder.gamma_interval, len(decoder.graph.edges))
        for _ in range(decoder.relay_legs)
    )
    initial = np.full(len(decoder.graph.edges), decoder.p, dtype=float)
    candidates: list[Candidate] = []
    for leg, gammas in enumerate(gamma_sets):
        limit = decoder.max_iterations if leg == 0 else decoder.relay_leg_iterations
        marginals, messages, converged, _delta, _iters = decoder._run_leg(
            syndrome, herald, initial, gammas, limit
        )
        score = decoder._candidate_score(
            syndrome, herald, marginals, decoder._factor_beliefs(syndrome, herald, messages)
        )
        hard = (marginals > 0.5).astype(np.uint8)
        candidates.append(Candidate(
            score, marginals, hard,
            bool(np.array_equal(decoder.graph.true_syndrome(hard), syndrome)),
            converged, leg,
        ))
        initial = marginals
    return candidates


def select(candidates: list[Candidate], arm: str) -> Candidate:
    if arm == "proxy":
        return max(candidates, key=lambda candidate: candidate.score)
    if arm == "first_leg":
        return candidates[0]
    valid = [candidate for candidate in candidates if candidate.valid]
    if not valid:
        return max(candidates, key=lambda candidate: candidate.score)
    if arm == "first_valid":
        return valid[0]
    if arm == "min_prior_valid":
        return min(valid, key=lambda candidate: (int(np.sum(candidate.hard)), candidate.leg))
    raise ValueError(arm)


def graph_for(name: str):
    return square_graph(5) if name == "square" else honeycomb_graph(5)


def run_cell(lattice: str, p: float, shots: int, seed: int) -> dict:
    graph = graph_for(lattice)
    memory = HeraldAwareBpMatchingDecoder(
        graph, p=p, q=0.75, p_m=0.0, p_h=0.0, max_iterations=40,
        gamma0=0.15, relay_legs=6, relay_leg_iterations=20,
        gamma_interval=(-0.24, 0.66), relay_seed=0,
    )
    legacy = LegacyDampedBpMatchingDecoder(
        graph, p=p, q=0.75, p_m=0.0, p_h=0.0, max_iterations=40,
        damping=0.25, tolerance=1e-8,
    )
    rng = np.random.default_rng(seed)
    records = {arm: [] for arm in ARMS}
    start = perf_counter()
    for _ in range(shots):
        observation = sample_observation(graph, rng, p=p, q=0.75, p_m=0.0, p_h=0.0)
        legacy_result = legacy.decode(observation.syndrome, observation.herald)
        candidates = relay_candidates(memory, observation.syndrome, observation.herald)
        for arm in ARMS:
            if arm == "legacy_damped":
                marginals = legacy_result.bp.edge_marginals
                valid = None
                leg = None
            else:
                candidate = select(candidates, arm)
                marginals = candidate.marginals
                valid = candidate.valid
                leg = candidate.leg
            matching = pymatching.Matching.from_check_matrix(
                graph.check_matrix,
                weights=memory._matching_weights(marginals),
                use_virtual_boundary_node=True,
            )
            correction = matching.decode(observation.syndrome).astype(np.uint8)
            if not np.array_equal(graph.true_syndrome(correction), observation.syndrome):
                raise RuntimeError("MWPM returned a syndrome-incompatible correction")
            log_loss, brier = proper(marginals, observation.error)
            records[arm].append({
                "failed": bool(graph.logical_parity(observation.error ^ correction)),
                "log_loss": log_loss, "brier": brier, "selected_valid": valid, "leg": leg,
            })
    summaries = {}
    for arm, arm_records in records.items():
        failures = sum(record["failed"] for record in arm_records)
        selected = [record["selected_valid"] for record in arm_records if record["selected_valid"] is not None]
        legs = [record["leg"] for record in arm_records if record["leg"] is not None]
        summaries[arm] = {
            "logical_errors": failures,
            "logical_error_rate": failures / shots,
            "logical_error_ci95": wilson(failures, shots),
            "mean_edge_log_loss": float(np.mean([record["log_loss"] for record in arm_records])),
            "mean_edge_brier": float(np.mean([record["brier"] for record in arm_records])),
            "selected_hard_syndrome_valid_rate": None if not selected else float(np.mean(selected)),
            "selected_leg_counts": None if not legs else {str(k): v for k, v in Counter(legs).items()},
        }
    paired = {}
    baseline = records["legacy_damped"]
    for arm in ARMS[1:]:
        compare = records[arm]
        rescued = sum(a["failed"] and not b["failed"] for a, b in zip(baseline, compare, strict=True))
        harmed = sum(b["failed"] and not a["failed"] for a, b in zip(baseline, compare, strict=True))
        paired[arm] = {
            "rescued": rescued, "introduced": harmed,
            "ler_delta": (harmed - rescued) / shots,
            "mcnemar_exact_p": mcnemar(rescued, harmed),
        }
    return {
        "lattice": lattice, "L": 5, "p": p, "q": 0.75, "shots": shots,
        "arms": summaries, "paired_vs_legacy": paired,
        "wall_seconds": perf_counter() - start,
    }


def render(results: list[dict]) -> str:
    lines = [
        "# Relay-leg soft-selection ablation", "",
        "Every Relay arm returns only selected soft marginals to MWPM. A hard threshold is used only to select an eligible leg; no BP hard correction is applied.", "",
        "| Case | Arm | LER | Edge log loss | Edge Brier | Selected hard valid |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for result in results:
        for arm, metrics in result["arms"].items():
            valid = metrics["selected_hard_syndrome_valid_rate"]
            valid_text = "--" if valid is None else f"{valid:.1%}"
            lines.append(
                f"| {result['lattice']} p={result['p']:.2f} | {arm} | "
                f"{metrics['logical_error_rate']:.4f} | {metrics['mean_edge_log_loss']:.4f} | "
                f"{metrics['mean_edge_brier']:.4f} | {valid_text} |"
            )
        for arm, paired in result["paired_vs_legacy"].items():
            lines.append(
                f"- {result['lattice']} p={result['p']:.2f}, {arm} vs legacy: "
                f"rescued {paired['rescued']}, introduced {paired['introduced']}, "
                f"LER delta {paired['ler_delta']:+.4f}, exact McNemar p={paired['mcnemar_exact_p']:.4g}."
            )
    lines.extend([
        "", "This is a selection-mechanism experiment, not a new production decoder or threshold estimate.", "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1931)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    results = [
        run_cell("square", 0.08, args.shots, args.seed),
        run_cell("honeycomb", 0.18, args.shots, args.seed + 1),
    ]
    payload = {"purpose": "matched soft Relay-leg selection ablation", "results": results}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n")
    args.output_md.write_text(render(results))


if __name__ == "__main__":
    main()
