#!/usr/bin/env python3
"""Resource and identity preflight for the registered L=11, q=0.94 oracle.

This script deliberately generates no stochastic or production histories.  It
constructs the exact oracle once and replays a fixed set of deterministic
charge records, then writes a fail-closed preflight result.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(LAB / "scripts"))

from herald_decoder.lattice_model import square_graph
from current_oracle import CurrentOracle


MANIFEST = LAB / "manifests" / "posterior-gap-boundary-tail-acquisition-2026-09-21.json"
RESULT = LAB / "results" / "posterior-gap-boundary-tail-preflight-2026-09-21.json"
ORACLE_SOURCE = LAB / "scripts" / "current_oracle.py"
MODEL_SOURCE = ROOT / "src" / "herald_decoder" / "lattice_model.py"

L = 11
P = 0.30
Q = 0.94
MAX_RUNTIME_SECONDS = 600.0
MAX_PEAK_MEMORY_GIB = 8.0
MAX_CANDIDATE_TRANSITIONS = 50_000_000
TOLERANCE = 1e-10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def peak_rss_gib() -> float:
    raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # macOS reports bytes; Linux reports KiB.
    denominator = 1024.0**3 if platform.system() == "Darwin" else 1024.0**2
    return raw / denominator


def logical_row_current(model) -> np.ndarray:
    """A deterministic left-to-right current with zero measured charge."""
    row = L // 2
    current = np.zeros(len(model.edges), dtype=np.int8)
    edge_index = {edge: index for index, edge in enumerate(model.edges)}
    for x in range(L - 1):
        u = row * L + x
        v = u + 1
        index = edge_index[(u, v)]
        current[index] = 1
    return current


def deterministic_currents(model) -> dict[str, np.ndarray]:
    n = len(model.edges)
    zero = np.zeros(n, dtype=np.int8)
    positive_edge = zero.copy()
    positive_edge[0] = 1
    negative_edge = zero.copy()
    negative_edge[0] = -1
    sparse_mixed = zero.copy()
    indices = np.arange(3, n, 23, dtype=int)
    sparse_mixed[indices] = np.where(np.arange(len(indices)) % 2 == 0, 1, -1)
    return {
        "zero_current": zero,
        "single_positive_edge": positive_edge,
        "single_negative_edge": negative_edge,
        "sparse_alternating_current": sparse_mixed,
        "rough_to_rough_logical_current": logical_row_current(model),
    }


def risk_from_gap(gap: float) -> float:
    if math.isinf(gap):
        return 0.0
    magnitude = abs(gap)
    if magnitude > 700:
        return 0.0
    return 1.0 / (1.0 + math.exp(magnitude))


def evaluate_record(oracle: CurrentOracle, name: str, current: np.ndarray) -> dict:
    charges = oracle.D @ current
    start = time.monotonic()
    first = oracle.infer(charges, P, Q)
    first_seconds = time.monotonic() - start
    start = time.monotonic()
    replay = oracle.infer(charges, P, Q)
    replay_seconds = time.monotonic() - start

    sectors = np.asarray(first["sectors"], dtype=float)
    marginals = np.asarray(first["marginals"], dtype=float)
    swapped = sectors[::-1]
    expected_risk = risk_from_gap(float(first["signed_gap"]))
    checks = {
        "posterior_normalized": abs(float(sectors.sum()) - 1.0) <= TOLERANCE,
        "posterior_nonnegative": bool(np.all(sectors >= -TOLERANCE)),
        "marginals_bounded": bool(np.all(marginals >= -TOLERANCE) and np.all(marginals <= 1.0 + TOLERANCE)),
        "risk_is_minimum_sector": abs(float(first["bayes_risk"]) - float(sectors.min())) <= TOLERANCE,
        "risk_gap_identity": abs(float(first["bayes_risk"]) - expected_risk) <= TOLERANCE,
        "sector_swap_risk_invariant": abs(float(sectors.min()) - float(swapped.min())) <= TOLERANCE,
        "sector_swap_absolute_gap_invariant": abs(
            abs(float(first["signed_gap"]))
            - abs(float(-first["signed_gap"]))
        ) <= TOLERANCE,
        "deterministic_replay": bool(
            np.array_equal(first["sectors"], replay["sectors"])
            and np.array_equal(first["marginals"], replay["marginals"])
            and first["signed_gap"] == replay["signed_gap"]
            and first["bayes_risk"] == replay["bayes_risk"]
        ),
        "finite_response_when_defined": first["response"] is None or math.isfinite(float(first["response"])),
    }
    return {
        "name": name,
        "charge_sha256": hashlib.sha256(np.asarray(charges, dtype=np.int64).tobytes()).hexdigest(),
        "charge_l1": int(np.abs(charges).sum()),
        "charge_nonzero_count": int(np.count_nonzero(charges)),
        "physical_current_nonzero_count": int(np.count_nonzero(current)),
        "true_logical_parity": int(oracle.model.logical_parity((current != 0).astype(np.uint8))),
        "sectors": sectors.tolist(),
        "bayes_risk": float(first["bayes_risk"]),
        "signed_gap": float(first["signed_gap"]),
        "inference_seconds": first_seconds,
        "replay_seconds": replay_seconds,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def main() -> None:
    started = time.monotonic()
    result: dict = {
        "id": "lab008-posterior-gap-boundary-tail-preflight-2026-09-21",
        "contract": str(MANIFEST.relative_to(ROOT)),
        "operation": "exact L=11, q=0.94 oracle construction and deterministic identity replay only",
        "registered_parameters": {"L": L, "p": P, "q": Q},
        "production_histories_generated": 0,
        "new_physical_record_samples": 0,
        "bootstrap_replicates": 0,
        "production_armed": False,
        "resource_caps": {
            "runtime_seconds": MAX_RUNTIME_SECONDS,
            "peak_memory_gib": MAX_PEAK_MEMORY_GIB,
            "candidate_transitions": MAX_CANDIDATE_TRANSITIONS,
        },
        "provenance": {
            str(MANIFEST.relative_to(ROOT)): sha256(MANIFEST),
            str(ORACLE_SOURCE.relative_to(ROOT)): sha256(ORACLE_SOURCE),
            str(MODEL_SOURCE.relative_to(ROOT)): sha256(MODEL_SOURCE),
            str(Path(__file__).resolve().relative_to(ROOT)): sha256(Path(__file__).resolve()),
        },
    }

    try:
        model = square_graph(L)
        construction_started = time.monotonic()
        oracle = CurrentOracle(model, directed=False, cap=MAX_CANDIDATE_TRANSITIONS)
        construction_wall_seconds = time.monotonic() - construction_started

        records = [evaluate_record(oracle, name, current) for name, current in deterministic_currents(model).items()]

        limiting = oracle.infer(np.zeros(len(model.detector_vertices), dtype=int), 0.0, Q)
        limiting_checks = {
            "zero_activity_sector_zero_is_certain": abs(float(limiting["sectors"][0]) - 1.0) <= TOLERANCE,
            "zero_activity_risk_is_zero": abs(float(limiting["bayes_risk"])) <= TOLERANCE,
            "zero_activity_gap_is_positive_infinity": math.isinf(float(limiting["signed_gap"]))
            and float(limiting["signed_gap"]) > 0,
        }

        logical = next(record for record in records if record["name"] == "rough_to_rough_logical_current")
        zero = next(record for record in records if record["name"] == "zero_current")
        logical_relation_checks = {
            "rough_to_rough_current_has_zero_public_charge": logical["charge_l1"] == 0,
            "rough_to_rough_current_flips_true_logical_sector": logical["true_logical_parity"] == 1,
            "zero_and_logical_currents_share_public_record": logical["charge_sha256"] == zero["charge_sha256"],
        }

        elapsed = time.monotonic() - started
        peak = peak_rss_gib()
        resource_checks = {
            "candidate_transitions_within_cap": int(oracle.profile["candidate_transitions"])
            <= MAX_CANDIDATE_TRANSITIONS,
            "runtime_within_cap": elapsed <= MAX_RUNTIME_SECONDS,
            "peak_memory_within_cap": peak <= MAX_PEAK_MEMORY_GIB,
        }
        all_checks = (
            all(record["all_checks_pass"] for record in records)
            and all(limiting_checks.values())
            and all(logical_relation_checks.values())
            and all(resource_checks.values())
        )
        result.update(
            {
                "status": "passed_exact_preflight_production_not_started" if all_checks else "censored_preflight_failed",
                "decision": "pass" if all_checks else "censor_L11_and_stop",
                "oracle_profile": oracle.profile,
                "construction_wall_seconds": construction_wall_seconds,
                "deterministic_record_count": len(records),
                "exact_inference_evaluations": 2 * len(records) + 1,
                "records": records,
                "limiting_record_checks": limiting_checks,
                "logical_relation_checks": logical_relation_checks,
                "resource_observation": {
                    "total_runtime_seconds": elapsed,
                    "peak_memory_gib": peak,
                    "platform_ru_maxrss_units": "bytes" if platform.system() == "Darwin" else "KiB",
                },
                "resource_checks": resource_checks,
                "all_gates_pass": all_checks,
                "next_action": (
                    "Acquire only the five registered production cells in bounded batches."
                    if all_checks
                    else "Censor the L=11 branch and stop this contract without approximation or scope expansion."
                ),
            }
        )
    except Exception as exc:  # fail closed while preserving the diagnostic
        result.update(
            {
                "status": "censored_preflight_exception",
                "decision": "censor_L11_and_stop",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "resource_observation": {
                    "total_runtime_seconds": time.monotonic() - started,
                    "peak_memory_gib": peak_rss_gib(),
                    "platform_ru_maxrss_units": "bytes" if platform.system() == "Darwin" else "KiB",
                },
                "all_gates_pass": False,
                "next_action": "Censor the L=11 branch and stop this contract without approximation or scope expansion.",
            }
        )

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in ("status", "decision", "all_gates_pass", "resource_observation", "oracle_profile")}, indent=2))


if __name__ == "__main__":
    main()
