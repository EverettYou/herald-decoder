#!/usr/bin/env python3
"""Run the bounded, non-LER end-to-end Lab 004 truth audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import build_charge_lattice, charge_chain_boundary
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb
from d4_matching import edge_chain_boundary
from d4_pipeline import PIPELINE_SCHEMA_VERSION, decode_physical_error
from d4_postflux import accumulate_postflux_constraints


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    lattice = paper_periodic_honeycomb(2)
    rates = (0.0, 0.05, 0.10)
    modes = ("syndrome_only", "heralded")
    seeds = range(32)
    status_counts: dict[str, Counter] = {
        mode: Counter() for mode in modes
    }
    logical_counts: dict[str, int] = {mode: 0 for mode in modes}
    checks = Counter()
    examples: dict[str, dict] = {}
    total_records = 0

    for error_rate in rates:
        for seed in seeds:
            physical_seed = int(
                np.random.SeedSequence(
                    [seed, int(error_rate * 1000)]
                ).generate_state(1)[0]
            )
            physical = (
                np.random.default_rng(physical_seed).random(lattice.edge_count)
                < error_rate
            )
            records = {
                mode: decode_physical_error(
                    lattice, physical, mode=mode, seed=20_000 + seed
                )
                for mode in modes
            }
            if records[modes[0]].physical_error_edges != records[modes[1]].physical_error_edges:
                raise RuntimeError("matched modes received different physical errors")
            if records[modes[0]].observation != records[modes[1]].observation:
                raise RuntimeError("matched modes received different observations")
            checks["matched_mode_input_and_observation"] += 1
            for mode, record in records.items():
                total_records += 1
                status_counts[mode][record.status] += 1
                logical_counts[mode] += int(record.logical_error)
                examples.setdefault(f"{mode}:{record.status}", record.to_dict())
                if record.flux_recovery is not None:
                    flux = record.flux_recovery
                    if np.any(edge_chain_boundary(lattice, flux.residual)):
                        raise RuntimeError("flux XOR residual has nonzero boundary")
                    expected_flux_logical = any(
                        not component.homologically_trivial
                        for component in flux.union_analysis.components
                    )
                    if flux.logical_error != expected_flux_logical:
                        raise RuntimeError("flux decision disagrees with union homology")
                    checks["closed_flux_xor_and_union_decision"] += 1
                if record.status != "decoded":
                    if not record.logical_error:
                        raise RuntimeError("early failure lacks logical-error flag")
                    checks["early_failure_consistency"] += 1
                    continue
                if (
                    record.postflux_relations is None
                    or record.postflux_charge_outcomes is None
                    or record.charge_recovery is None
                ):
                    raise RuntimeError("decoded record is missing a decoder stage")
                constraints = accumulate_postflux_constraints(
                    lattice.vertex_count,
                    record.postflux_relations.active_vertices,
                    record.postflux_relations.entanglement_pairs,
                    np.asarray(record.postflux_charge_outcomes),
                )
                if not constraints.allowed:
                    raise RuntimeError("post-flux charge record violates support")
                checks["postflux_constraint_support"] += 1
                for color, result in (
                    (BLUE, record.charge_recovery.blue),
                    (GREEN, record.charge_recovery.green),
                ):
                    if np.any(
                        charge_chain_boundary(
                            build_charge_lattice(lattice, color), result.residual
                        )
                    ):
                        raise RuntimeError("charge residual has nonzero boundary")
                    checks["closed_charge_residual"] += 1
                if record.logical_error != record.charge_recovery.logical_error:
                    raise RuntimeError("final decision disagrees with charge recovery")
                checks["final_decision_consistency"] += 1

    sources = (
        "run_d4_pipeline_truth_audit.py",
        "d4_pipeline.py",
        "d4_recovery.py",
        "d4_matching.py",
        "d4_postflux.py",
        "d4_charge.py",
    )
    payload = {
        "schema_version": 1,
        "pipeline_schema_version": PIPELINE_SCHEMA_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "bounded end-to-end truth audit; not an LER estimate",
        "protocol": {
            "lattice": "paper-normalized periodic honeycomb",
            "size": 2,
            "edge_count": lattice.edge_count,
            "error_rates": list(rates),
            "seeds_per_rate": len(tuple(seeds)),
            "modes": list(modes),
            "matched_observation_seed": "20000 + seed",
            "physical_seed": "SeedSequence([seed, int(1000*p)])",
        },
        "total_records": total_records,
        "status_counts": {
            mode: dict(sorted(counts.items()))
            for mode, counts in status_counts.items()
        },
        "logical_counts": logical_counts,
        "invariant_checks": dict(sorted(checks.items())),
        "examples": examples,
        "source_sha256": {
            name: sha256(script_dir / name) for name in sources
        },
        "claim_boundary": (
            "This audit verifies record continuity and truth invariants for "
            "both public modes. It does not estimate logical error rates or a threshold."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
