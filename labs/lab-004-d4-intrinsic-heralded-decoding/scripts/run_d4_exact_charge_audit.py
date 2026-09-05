#!/usr/bin/env python3
"""Audit the unit-weight charge stage against an independent exact T-join oracle."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import build_charge_lattice, classify_closed_charge_chain
from d4_exact import exact_unit_t_join_minimum
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb
from d4_pipeline import decode_physical_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    honeycomb = paper_periodic_honeycomb(2)
    charge_lattices = {
        color: build_charge_lattice(honeycomb, color) for color in (BLUE, GREEN)
    }
    rates = (0.0, 0.05, 0.10)
    modes = ("syndrome_only", "heralded")
    counts: dict[str, Counter] = {"blue": Counter(), "green": Counter()}
    examples = []
    decoded_records = 0
    for error_rate in rates:
        for seed in range(32):
            physical_seed = int(
                np.random.SeedSequence(
                    [seed, int(error_rate * 1000)]
                ).generate_state(1)[0]
            )
            physical = (
                np.random.default_rng(physical_seed).random(honeycomb.edge_count)
                < error_rate
            )
            for mode in modes:
                record = decode_physical_error(
                    honeycomb, physical, mode=mode, seed=20_000 + seed
                )
                if record.charge_recovery is None:
                    continue
                decoded_records += 1
                for name, color, result in (
                    ("blue", BLUE, record.charge_recovery.blue),
                    ("green", GREEN, record.charge_recovery.green),
                ):
                    lattice = charge_lattices[color]
                    exact = exact_unit_t_join_minimum(
                        lattice.vertex_count,
                        lattice.edge_vertices,
                        result.syndrome,
                    )
                    if not np.isclose(
                        result.objective_weight,
                        exact.minimum_weight,
                        rtol=0.0,
                        atol=1e-9,
                    ):
                        raise RuntimeError("charge MWPM objective disagrees with exact T-join")
                    if not any(
                        np.array_equal(result.correction, correction)
                        for correction in exact.minimizers
                    ):
                        raise RuntimeError("charge correction is absent from exact optimum set")
                    logical_set = {
                        classify_closed_charge_chain(
                            lattice, result.effective_error ^ correction
                        ).logical_error
                        for correction in exact.minimizers
                    }
                    bucket = counts[name]
                    bucket["objective_exact"] += 1
                    bucket[f"defects_{int(result.syndrome.sum())}"] += 1
                    bucket[
                        "unique_optimum"
                        if len(exact.minimizers) == 1
                        else "tied_optimum"
                    ] += 1
                    bucket[
                        "logical_unambiguous"
                        if len(logical_set) == 1
                        else "logical_ambiguous"
                    ] += 1
                    if len(exact.minimizers) > 1 and len(examples) < 10:
                        examples.append(
                            {
                                "p": error_rate,
                                "seed": seed,
                                "mode": mode,
                                "color": name,
                                "defect_count": int(result.syndrome.sum()),
                                "minimum_weight": exact.minimum_weight,
                                "minimizer_count": len(exact.minimizers),
                                "candidate_count": exact.candidate_count,
                                "optimal_logical_values": sorted(logical_set),
                                "pipeline_logical": result.logical_error,
                            }
                        )
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "independent bounded charge-stage objective and tie-homology oracle",
        "protocol": {
            "size": 2,
            "charge_vertices_per_color": charge_lattices[BLUE].vertex_count,
            "charge_edges_per_color": charge_lattices[BLUE].edge_count,
            "error_rates": list(rates),
            "seeds_per_rate": 32,
            "modes": list(modes),
            "oracle": "all defect pairings times all shortest paths; positive unit weights",
            "candidate_limit_per_case": 1_000_000,
        },
        "decoded_records": decoded_records,
        "audited_color_records": 2 * decoded_records,
        "counts": {name: dict(sorted(value.items())) for name, value in counts.items()},
        "tie_examples": examples,
        "claim_boundary": (
            "This certifies the second-stage unit-weight MWPM objective on the "
            "registered paper-L=2 cohort and exposes logical ambiguity across "
            "tied optima. It is not the R3 fusion-constrained oracle and not a "
            "Bayes-optimal posterior decoder."
        ),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
