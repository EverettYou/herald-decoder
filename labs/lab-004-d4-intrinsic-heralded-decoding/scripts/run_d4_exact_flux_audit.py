#!/usr/bin/env python3
"""Exhaustively audit paper-L=2 flux objectives on the matched R2 cohort."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_exact import exhaustive_chain_minimum
from d4_honeycomb import paper_periodic_honeycomb
from d4_matching import (
    classify_physical_correction_union,
    d4_check_matrix,
    published_herald_weights,
    syndrome_only_weights,
)
from d4_pipeline import decode_physical_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lattice = paper_periodic_honeycomb(2)
    check = d4_check_matrix(lattice)
    modes = ("syndrome_only", "heralded")
    rates = (0.0, 0.05, 0.10)
    counts = {mode: Counter() for mode in modes}
    examples = []
    audited = 0
    for error_rate in rates:
        for seed in range(32):
            physical_seed = int(
                np.random.SeedSequence(
                    [seed, int(error_rate * 1000)]
                ).generate_state(1)[0]
            )
            physical = (
                np.random.default_rng(physical_seed).random(lattice.edge_count)
                < error_rate
            )
            for mode in modes:
                record = decode_physical_error(
                    lattice, physical, mode=mode, seed=20_000 + seed
                )
                if record.flux_recovery is None:
                    counts[mode]["pre_flux_short_circuit"] += 1
                    continue
                charge = np.asarray(record.observation.charge_outcomes, dtype=np.int64)
                weights = (
                    syndrome_only_weights(lattice)
                    if mode == "syndrome_only"
                    else published_herald_weights(lattice, charge)
                )
                exact = exhaustive_chain_minimum(
                    check, record.flux_recovery.syndrome, weights
                )
                if not np.isclose(
                    record.flux_recovery.objective_weight,
                    exact.minimum_weight,
                    rtol=0.0,
                    atol=1e-9,
                ):
                    raise RuntimeError("PyMatching objective disagrees with exhaustive minimum")
                if not any(
                    np.array_equal(record.flux_recovery.correction, correction)
                    for correction in exact.minimizers
                ):
                    raise RuntimeError("PyMatching correction is absent from optimal set")
                logical_set = {
                    any(
                        not component.homologically_trivial
                        for component in classify_physical_correction_union(
                            lattice, physical, correction
                        ).components
                    )
                    for correction in exact.minimizers
                }
                counts[mode]["objective_exact"] += 1
                counts[mode]["unique_optimum" if len(exact.minimizers) == 1 else "tied_optimum"] += 1
                counts[mode]["logical_unambiguous" if len(logical_set) == 1 else "logical_ambiguous"] += 1
                audited += 1
                if len(exact.minimizers) > 1 and len(examples) < 8:
                    examples.append(
                        {
                            "p": error_rate,
                            "seed": seed,
                            "mode": mode,
                            "minimum_weight": exact.minimum_weight,
                            "minimizer_count": len(exact.minimizers),
                            "optimal_union_logical_values": sorted(logical_set),
                            "pipeline_union_logical": record.flux_recovery.logical_error,
                        }
                    )
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "source-normalized exhaustive first-stage execution oracle",
        "protocol": {
            "size": 2,
            "edge_count": lattice.edge_count,
            "affine_dimension": 13,
            "chains_per_syndrome": 8192,
            "error_rates": list(rates),
            "seeds_per_rate": 32,
            "modes": list(modes),
        },
        "audited_flux_records": audited,
        "counts": {
            mode: dict(sorted(value.items())) for mode, value in counts.items()
        },
        "tie_examples": examples,
        "claim_boundary": (
            "This is an exhaustive execution-objective and tie-homology audit "
            "for the first MWPM stage. It is not the R3 constrained fusion "
            "oracle and not a Bayes-optimal logical posterior."
        ),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
