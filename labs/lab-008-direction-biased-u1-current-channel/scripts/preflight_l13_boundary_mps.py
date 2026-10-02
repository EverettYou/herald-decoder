#!/usr/bin/env python3
"""Zero-production-history prerequisite for the registered L13 acquisition."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import inspect
import json
import math
import platform
import resource
from pathlib import Path
import sys
import time
import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(LAB / "scripts")]

from herald_decoder.lattice_model import square_graph
from boundary_mps_posterior import BoundaryMPSPosterior
from current_oracle import charge_matrix

MANIFEST = LAB / "manifests" / "l13-boundary-mps-acquisition-2026-09-21.json"
RESULT = LAB / "results" / "l13-boundary-mps-preflight-2026-09-21.json"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def rss_gib() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024**3 if platform.system() == "Darwin" else 1024**2)


def logical_path_current(model) -> np.ndarray:
    """Left-to-right unit current on the middle row; endpoints are unmeasured."""
    target_y = (13 - 1) / 2
    current = np.zeros(len(model.edges), dtype=np.int8)
    for edge, (u, v) in enumerate(model.edges):
        a, b = model.vertices[u], model.vertices[v]
        if a.y == target_y and b.y == target_y and abs(a.x - b.x) == 1:
            current[edge] = 1 if b.x > a.x else -1
    return current


def fixtures() -> list[dict]:
    model = square_graph(13)
    D = charge_matrix(model)
    rows = []
    zero = np.zeros(len(model.edges), dtype=np.int8)
    rows.append(("zero-q94", 0.94, zero))
    for name, q, seed in (("seeded-q90", 0.90, 202609211390), ("seeded-q97", 0.97, 202609211397)):
        rng = np.random.default_rng(seed)
        activity = rng.random(len(model.edges))
        orientation = rng.random(len(model.edges))
        current = (activity < 0.30) * np.where(orientation < q, 1, -1)
        rows.append((name, q, current.astype(np.int8)))
    return [
        {
            "fixture_id": name,
            "q": q,
            "charge": np.asarray(D @ current, dtype=np.int16).tolist(),
            "charge_sha256": sha_bytes(np.asarray(D @ current, dtype=np.int16).tobytes()),
            "hidden_current_sha256": sha_bytes(current.tobytes()),
            "hidden_true_sector": int(model.logical_parity((current != 0).astype(np.uint8))),
        }
        for name, q, current in rows
    ]


def evaluate_fixture(fixture: dict) -> dict:
    model = square_graph(13)
    Q = np.asarray(fixture["charge"], dtype=np.int16)
    evaluations = []
    for direction, order in (
        ("left-to-right", list(model.detector_vertices)),
        ("right-to-left", list(reversed(model.detector_vertices))),
    ):
        engine = BoundaryMPSPosterior(model, order=order)
        for chi in (16, 32):
            started = time.monotonic()
            candidate = engine.infer(Q, 0.30, fixture["q"], chi=chi)
            logistic = 0.0 if math.isinf(candidate.signed_gap) else 1 / (1 + math.exp(abs(candidate.signed_gap)))
            evaluations.append({
                "direction": direction,
                "chi": chi,
                "sectors": candidate.sectors.tolist(),
                "bayes_risk": candidate.bayes_risk,
                "signed_gap": candidate.signed_gap if math.isfinite(candidate.signed_gap) else None,
                "gap_infinite_sign": 0 if math.isfinite(candidate.signed_gap) else (1 if candidate.signed_gap > 0 else -1),
                "normalization_error": float(abs(candidate.sectors.sum() - 1)),
                "risk_gap_identity_error": float(abs(candidate.bayes_risk - logistic)),
                "minimum_sector_mass": float(candidate.sectors.min()),
                "discarded_frobenius_sq": candidate.discarded_frobenius_sq,
                "maximum_bond": candidate.maximum_bond,
                "seconds": time.monotonic() - started,
                "worker_peak_memory_gib": rss_gib(),
            })
    return {**fixture, "evaluations": evaluations, "worker_peak_memory_gib": rss_gib()}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    gate = manifest["preflight_gate"]
    first = fixtures()
    second = fixtures()
    fixture_replay = first == second
    model = square_graph(13)
    D = charge_matrix(model)
    zero = np.zeros(len(model.edges), dtype=np.int8)
    path = logical_path_current(model)
    action_blindness = {
        "same_measured_charge": bool(np.array_equal(D @ zero, D @ path)),
        "opposite_hidden_logical_sector": int(model.logical_parity((zero != 0).astype(np.uint8))) != int(model.logical_parity((path != 0).astype(np.uint8))),
        "zero_charge_sha256": sha_bytes(np.asarray(D @ zero, dtype=np.int16).tobytes()),
        "path_charge_sha256": sha_bytes(np.asarray(D @ path, dtype=np.int16).tobytes()),
        "path_current_sha256": sha_bytes(path.tobytes()),
    }
    started = time.monotonic()
    rows = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(evaluate_fixture, fixture) for fixture in first]
        for future in as_completed(futures):
            rows.append(future.result())
    elapsed = time.monotonic() - started
    evaluations = [evaluation for row in rows for evaluation in row["evaluations"]]
    by_fixture = {}
    for row in rows:
        values = {(e["direction"], e["chi"]): np.asarray(e["sectors"]) for e in row["evaluations"]}
        by_fixture[row["fixture_id"]] = {
            "chi16_vs_chi32_gap_difference_by_sweep": {
                direction: float(abs(np.log(values[(direction, 16)][0] / values[(direction, 16)][1]) - np.log(values[(direction, 32)][0] / values[(direction, 32)][1])))
                for direction in ("left-to-right", "right-to-left")
            },
            "chi32_sweep_gap_difference": float(abs(np.log(values[("left-to-right", 32)][0] / values[("left-to-right", 32)][1]) - np.log(values[("right-to-left", 32)][0] / values[("right-to-left", 32)][1]))),
        }
    parameters = set(inspect.signature(BoundaryMPSPosterior.infer).parameters)
    conservative_peak = rss_gib() + sum(row["worker_peak_memory_gib"] for row in rows)
    gates = {
        "fixture_replay": fixture_replay,
        "charge_only_public_interface": "charges" in parameters and "current" not in parameters and "hidden" not in parameters,
        "normalization_le_1e-10": max(e["normalization_error"] for e in evaluations) <= 1e-10,
        "risk_gap_identity_le_1e-10": max(e["risk_gap_identity_error"] for e in evaluations) <= 1e-10,
        "nonnegative_finite_sectors": all(np.isfinite(e["sectors"]).all() and e["minimum_sector_mass"] >= 0 for e in evaluations),
        "sector_swap_invariance": all(abs(min(e["sectors"][::-1]) - e["bayes_risk"]) <= 1e-10 for e in evaluations),
        "action_blindness_fixture": action_blindness["same_measured_charge"] and action_blindness["opposite_hidden_logical_sector"],
        "candidate_evaluations_within_cap": len(evaluations) == 12 and len(evaluations) <= gate["maximum_candidate_evaluations"],
        "runtime_within_cap": elapsed <= gate["maximum_runtime_seconds"],
        "conservative_memory_within_cap": conservative_peak <= gate["maximum_peak_memory_gib"],
        "production_histories_zero": True,
        "bootstrap_replicates_zero": True,
    }
    result = {
        "id": "lab008-l13-boundary-mps-preflight-2026-09-21",
        "status": "complete" if all(gates.values()) else "failed",
        "contract": str(MANIFEST.relative_to(ROOT)),
        "operation": "zero-production-history public-interface and resource preflight",
        "fixtures": sorted(rows, key=lambda row: row["fixture_id"]),
        "fixture_comparisons": by_fixture,
        "action_blindness": action_blindness,
        "gates": gates,
        "candidate_evaluations": len(evaluations),
        "runtime_seconds": elapsed,
        "main_peak_memory_gib": rss_gib(),
        "conservative_main_plus_worker_peak_gib": conservative_peak,
        "production_histories_generated": 0,
        "bootstrap_replicates": 0,
        "production_armed": all(gates.values()),
        "source_hashes": {
            "runner": sha_file(Path(__file__)),
            "implementation": sha_file(LAB / "scripts" / "boundary_mps_posterior.py"),
            "lattice_model": sha_file(ROOT / "src" / "herald_decoder" / "lattice_model.py"),
            "manifest": sha_file(MANIFEST),
        },
        "claim_boundary": "Passing arms only the registered L13 production matrix; it supplies no L13 physical evidence or phase interpretation.",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"], "candidate_evaluations": len(evaluations),
        "runtime_seconds": elapsed, "conservative_peak_gib": conservative_peak,
        "production_armed": result["production_armed"], "gates": gates,
    }, indent=2))
    if result["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
