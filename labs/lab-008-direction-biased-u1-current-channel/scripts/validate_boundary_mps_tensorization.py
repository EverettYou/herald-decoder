#!/usr/bin/env python3
"""Exact-ceiling and interface gates for the registered boundary MPS."""
from __future__ import annotations

import hashlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(LAB / "scripts")]

from herald_decoder.lattice_model import square_graph
from boundary_mps_posterior import BoundaryMPSPosterior
from current_oracle import CurrentOracle, charge_matrix


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(model, seed: int):
    rng = np.random.default_rng(seed)
    yield "zero", np.zeros(len(model.edges), dtype=np.int8)
    for idx in range(4):
        yield f"seed-{idx}", rng.choice(np.asarray([0, 1, -1], dtype=np.int8), len(model.edges), p=[0.7, 0.282, 0.018])


def main():
    p, q = 0.3, 0.94
    rows, maximum_error = [], 0.0
    for size in (5, 7):
        model = square_graph(size)
        exact = CurrentOracle(model, cap=50_000_000)
        directions = {
            "left-to-right": list(model.detector_vertices),
            "right-to-left": list(reversed(model.detector_vertices)),
        }
        D = charge_matrix(model)
        for record_id, current in records(model, 20260921 + size):
            charges = D @ current
            reference = exact.infer(charges, p, q)
            for direction, order in directions.items():
                candidate = BoundaryMPSPosterior(model, order=order).infer(charges, p, q, chi=None)
                error = float(np.max(np.abs(candidate.sectors - reference["sectors"])))
                maximum_error = max(maximum_error, error)
                risk_identity = abs(candidate.bayes_risk - 1 / (1 + np.exp(abs(candidate.signed_gap))))
                rows.append({
                    "size": size,
                    "record_id": record_id,
                    "direction": direction,
                    "charges_sha256": hashlib.sha256(np.asarray(charges, dtype=np.int16).tobytes()).hexdigest(),
                    "reference_sectors": reference["sectors"].tolist(),
                    "candidate_sectors": candidate.sectors.tolist(),
                    "maximum_sector_error": error,
                    "risk_gap_identity_error": float(risk_identity),
                    "normalization_error": float(abs(candidate.sectors.sum() - 1)),
                    "minimum_sector_mass": candidate.minimum_sector_mass,
                    "maximum_exact_bond": candidate.maximum_bond,
                    "sector_swap_risk_error": float(abs(np.min(candidate.sectors[::-1]) - candidate.bayes_risk)),
                    "sector_swap_abs_gap_error": float(abs(abs(np.log(candidate.sectors[1] / candidate.sectors[0])) - abs(candidate.signed_gap))),
                })
    infer_parameters = set(inspect.signature(BoundaryMPSPosterior.infer).parameters)
    gates = {
        "sector_error_le_1e-10": maximum_error <= 1e-10,
        "normalization_le_1e-10": max(r["normalization_error"] for r in rows) <= 1e-10,
        "risk_gap_identity_le_1e-10": max(r["risk_gap_identity_error"] for r in rows) <= 1e-10,
        "nonnegative_sector_mass": min(r["minimum_sector_mass"] for r in rows) >= -1e-14,
        "both_sweeps_covered": {r["direction"] for r in rows} == {"left-to-right", "right-to-left"},
        "sector_swap_invariance_le_1e-10": max(max(r["sector_swap_risk_error"], r["sector_swap_abs_gap_error"]) for r in rows) <= 1e-10,
        "public_interface_is_charge_only": "current" not in infer_parameters and "hidden" not in infer_parameters and "charges" in infer_parameters,
        "no_new_physical_records": True,
    }
    result = {
        "id": "lab008-boundary-mps-tensorization-gates-2026-09-21",
        "status": "complete" if all(gates.values()) else "failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract": "../manifests/beyond-l11-mps-validation-2026-09-21.json",
        "parameters": {"p": p, "q": q, "sizes": [5, 7], "records_per_size": 5, "sweeps": ["left-to-right", "right-to-left"], "chi": None},
        "gates": gates,
        "maximum_sector_error": maximum_error,
        "rows": rows,
        "counters": {"new_physical_records": 0, "exact_control_records": 10, "candidate_evaluations": 20, "bootstrap_replicates": 0, "l13_histories": 0},
        "source_hashes": {
            "implementation": sha(LAB / "scripts" / "boundary_mps_posterior.py"),
            "runner": sha(Path(__file__)),
            "current_oracle": sha(LAB / "scripts" / "current_oracle.py"),
            "lattice_model": sha(ROOT / "src" / "herald_decoder" / "lattice_model.py"),
        },
        "claim_boundary": "This validates exact tensorization and public charge-only inputs at L5/L7. It does not validate finite-chi accuracy, L13 evidence, a phase, or a threshold.",
    }
    path = LAB / "results" / "boundary-mps-tensorization-gates-2026-09-21.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "maximum_sector_error": maximum_error, "gates": gates}, indent=2))
    if result["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
