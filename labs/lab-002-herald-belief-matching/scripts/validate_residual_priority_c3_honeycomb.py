#!/usr/bin/env python3
"""Cross-geometry C3 equivalence validation for compiled residual-priority BP."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from herald_decoder.lattice_model import honeycomb_graph, sample_observation
from herald_decoder.legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder


RESULT = Path(__file__).resolve().parents[1] / "results" / "residual-priority-c3-honeycomb.json"
SEEDS = tuple(range(9301, 9309))


def main() -> None:
    graph = honeycomb_graph(5)
    python = LegacyDampedBpMatchingDecoder(
        graph, p=0.20, q=1.0, max_iterations=80, update_schedule="residual_priority", use_numba=False
    )
    compiled = LegacyDampedBpMatchingDecoder(
        graph, p=0.20, q=1.0, max_iterations=80, update_schedule="residual_priority", use_numba=True
    )
    rows = []
    for seed in SEEDS:
        observation = sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0)
        first = python.decode(observation.syndrome, observation.herald)
        second = compiled.decode(observation.syndrome, observation.herald)
        exact = (
            np.array_equal(first.bp.edge_marginals, second.bp.edge_marginals)
            and np.array_equal(first.edge_weights, second.edge_weights)
            and np.array_equal(first.correction, second.correction)
            and first.bp.iterations == second.bp.iterations
            and first.bp.converged == second.bp.converged
            and first.bp.max_message_delta == second.bp.max_message_delta
        )
        if not exact:
            raise RuntimeError(f"Python/Numba residual-priority mismatch on honeycomb seed {seed}")
        if not np.array_equal(graph.true_syndrome(second.correction), observation.syndrome):
            raise RuntimeError(f"compiled correction is not syndrome faithful on honeycomb seed {seed}")
        rows.append({"seed": seed, "bit_identical": True, "converged": bool(second.bp.converged), "iterations": int(second.bp.iterations)})
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transition": "Lab 002 C3 honeycomb residual-priority Python/Numba equivalence validation",
        "sample_design": {"lattice": "honeycomb", "L": 5, "p": 0.20, "q": 1.0, "seeds": list(SEEDS), "max_iterations": 80},
        "all_bit_identical": True,
        "all_syndrome_faithful": True,
        "rows": rows,
    }
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"result": str(RESULT), "all_bit_identical": True, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
