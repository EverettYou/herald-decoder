#!/usr/bin/env python3
"""Checkpointed acquisition for the registered posterior-gap boundary matrix."""

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


MANIFEST_PATH = LAB / "manifests" / "posterior-gap-boundary-tail-acquisition-2026-09-21.json"
RESULT_DIR = LAB / "results" / "posterior-gap-boundary-tail-cells"
PROGRESS_PATH = LAB / "results" / "posterior-gap-boundary-tail-acquisition-progress-2026-09-21.json"
SOURCE_PATHS = [
    Path(__file__).resolve(),
    LAB / "scripts" / "current_oracle.py",
    ROOT / "src" / "herald_decoder" / "lattice_model.py",
]
Z95 = 1.959963984540054


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_design(manifest: dict) -> dict:
    excluded = {"status", "completed_at", "analysis", "not_yet_run"}
    return {key: value for key, value in manifest.items() if key not in excluded}


def peak_rss_gib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / (1024.0**3 if platform.system() == "Darwin" else 1024.0**2)


def q_tag(q: float) -> str:
    return f"q{int(round(100 * q)):02d}"


def cell_id(L: int, q: float) -> str:
    return f"square-L{L}-p30-{q_tag(q)}-boundary-tail"


def wilson_half_width(successes: int, n: int) -> float:
    if n == 0:
        return math.inf
    proportion = successes / n
    denominator = 1.0 + Z95**2 / n
    radius = Z95 * math.sqrt(proportion * (1.0 - proportion) / n + Z95**2 / (4.0 * n**2)) / denominator
    return radius


def bootstrap_risk_half_width(values: np.ndarray, seed: int, replicates: int) -> tuple[float, list[float]]:
    rng = np.random.default_rng(seed)
    n = len(values)
    means = np.empty(replicates, dtype=float)
    block = 256
    for start in range(0, replicates, block):
        count = min(block, replicates - start)
        indices = rng.integers(0, n, size=(count, n))
        means[start : start + count] = values[indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float((high - low) / 2.0), [float(low), float(high)]


def record_from_current(model, oracle: CurrentOracle, current: np.ndarray, *, L: int, q: float, index: int, seed: int) -> dict:
    charge = oracle.D @ current
    exact = oracle.infer(charge, 0.30, q)
    sectors = np.asarray(exact["sectors"], dtype=float)
    gap = float(exact["signed_gap"])
    absolute_gap = math.inf if math.isinf(gap) else abs(gap)
    expected_risk = 0.0 if math.isinf(absolute_gap) else 1.0 / (1.0 + math.exp(absolute_gap))
    if abs(expected_risk - float(exact["bayes_risk"])) > 1e-12:
        raise RuntimeError("risk-gap identity failure")
    if abs(float(sectors.sum()) - 1.0) > 1e-12 or np.any(sectors < -1e-12):
        raise RuntimeError("posterior normalization failure")
    entropy = -sum(float(value) * math.log2(float(value)) for value in sectors if value > 0)
    stream = f"L{L}:seed{seed}:index{index}"
    return {
        "record_key": f"{cell_id(L, q)}:index{index}",
        "activity_stream_key": stream + ":activity",
        "orientation_uniform_stream_key": stream + ":orientation",
        "sample_index": index,
        "current_sha256": sha256_bytes(np.asarray(current, dtype=np.int8).tobytes()),
        "charge_sha256": sha256_bytes(np.asarray(charge, dtype=np.int16).tobytes()),
        "true_sector": int(model.logical_parity((current != 0).astype(np.uint8))),
        "sector_probabilities": sectors.tolist(),
        "bayes_risk": float(exact["bayes_risk"]),
        "signed_gap": gap if math.isfinite(gap) else None,
        "gap_infinite_sign": 0 if math.isfinite(gap) else (1 if gap > 0 else -1),
        "conditional_logical_entropy_bits": entropy,
        "log_evidence": float(exact["log_evidence"]),
    }


def gap(record: dict) -> float:
    return math.inf if record["gap_infinite_sign"] else abs(float(record["signed_gap"]))


def summarize(records: list[dict], *, L: int, q: float, bootstrap_seed: int, replicates: int) -> dict:
    risks = np.asarray([row["bayes_risk"] for row in records], dtype=float)
    gaps = np.asarray([gap(row) for row in records], dtype=float)
    low_gap_count = int(np.count_nonzero(gaps <= 1.0))
    risk_half_width, risk_interval = bootstrap_risk_half_width(
        risks, bootstrap_seed + 1000 * L + int(round(100 * q)) + len(records), replicates
    )
    cdf_half_width = wilson_half_width(low_gap_count, len(records))
    return {
        "records": len(records),
        "Bayes_risk": float(risks.mean()),
        "Bayes_risk_bootstrap_interval95": risk_interval,
        "Bayes_risk_bootstrap_half_width95": risk_half_width,
        "C_L_1": low_gap_count / len(records),
        "C_L_1_Wilson_half_width95": cdf_half_width,
        "precision_targets_pass": cdf_half_width <= 0.04 and risk_half_width <= 0.025,
        "median_abs_DeltaF": float(np.quantile(gaps, 0.5)),
        "lower_quartile_abs_DeltaF": float(np.quantile(gaps, 0.25)),
    }


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    if manifest["status"] != "production_armed_preflight_passed" or not manifest["preflight_outcome"]["all_gates_pass"]:
        raise RuntimeError("production is not armed by a passed preflight")
    execution = manifest["production_execution"]
    matrix = manifest["matrix"]
    budget = manifest["budget"]
    source_hashes = {str(path.relative_to(ROOT)): sha256_file(path) for path in SOURCE_PATHS}
    design_sha256 = sha256_bytes(json.dumps(canonical_design(manifest), sort_keys=True).encode())
    cells_by_size: dict[int, list[float]] = {}
    for cell in matrix["new_cells"]:
        cells_by_size.setdefault(int(cell["L"]), []).append(float(cell["q"]))

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    oracles = {}
    streams = {}
    outputs = {}
    stopped = {}

    for L, q_values in sorted(cells_by_size.items()):
        model = square_graph(L)
        oracles[L] = (model, CurrentOracle(model, directed=False, cap=manifest["preflight_gate"]["maximum_candidate_transitions"]))
        seed = int(execution["stream_seed_by_size"][str(L)])
        rng = np.random.default_rng(seed)
        activity_uniform = rng.random((matrix["maximum_records_per_new_cell"], len(model.edges)))
        orientation_uniform = rng.random((matrix["maximum_records_per_new_cell"], len(model.edges)))
        streams[L] = (seed, activity_uniform, orientation_uniform)
        for q in sorted(q_values):
            path = RESULT_DIR / f"{cell_id(L, q)}.json"
            if path.exists():
                output = json.loads(path.read_text())
                if output["source_sha256"] != source_hashes or output["design_sha256"] != design_sha256:
                    raise RuntimeError(f"resume provenance mismatch: {path.name}")
            else:
                output = {
                    "status": "running",
                    "cell": {"id": cell_id(L, q), "lattice": "square", "L": L, "p": 0.30, "q": q},
                    "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
                    "design_sha256": design_sha256,
                    "source_sha256": source_hashes,
                    "stream_seed": seed,
                    "oracle_profile": oracles[L][1].profile,
                    "records": [],
                    "compute_seconds": 0.0,
                    "batch_summaries": [],
                }
            # Verify every resumed record against the frozen streams before appending.
            for row in output["records"]:
                i = int(row["sample_index"])
                current = (activity_uniform[i] < 0.30) * np.where(orientation_uniform[i] < q, 1, -1)
                if row["current_sha256"] != sha256_bytes(np.asarray(current, dtype=np.int8).tobytes()):
                    raise RuntimeError(f"resume stream mismatch: {path.name}:{i}")
            outputs[(L, q)] = (path, output)
            stopped[(L, q)] = output["status"] == "complete"

    batch = int(matrix["batch_records"])
    minimum = int(matrix["minimum_records_per_new_cell"])
    maximum = int(matrix["maximum_records_per_new_cell"])
    bootstrap_replicates = int(manifest["matched_sampling"]["bootstrap_replicates"])
    total_runtime_cap = float(execution["runtime_stop_seconds"])

    while not all(stopped.values()):
        for L, q_values in sorted(cells_by_size.items()):
            model, oracle = oracles[L]
            seed, activity_uniform, orientation_uniform = streams[L]
            for q in sorted(q_values):
                key = (L, q)
                if stopped[key]:
                    continue
                path, output = outputs[key]
                start_index = len(output["records"])
                stop_index = min(start_index + batch, maximum)
                batch_started = time.monotonic()
                for i in range(start_index, stop_index):
                    current = (activity_uniform[i] < 0.30) * np.where(orientation_uniform[i] < q, 1, -1)
                    output["records"].append(record_from_current(model, oracle, current, L=L, q=q, index=i, seed=seed))
                output["compute_seconds"] += time.monotonic() - batch_started
                summary = summarize(
                    output["records"], L=L, q=q,
                    bootstrap_seed=int(execution["bootstrap_seed"]), replicates=bootstrap_replicates,
                )
                summary["batch_end"] = stop_index
                output["batch_summaries"].append(summary)
                stopped[key] = stop_index >= minimum and (summary["precision_targets_pass"] or stop_index >= maximum)
                output["status"] = "complete" if stopped[key] else "running"
                output["stop_reason"] = (
                    "precision_targets_passed" if stopped[key] and summary["precision_targets_pass"]
                    else "hard_cap_reached" if stopped[key]
                    else None
                )
                output["final_summary"] = summary
                write_json(path, output)
                print(
                    output["cell"]["id"], stop_index, output["status"],
                    "risk", round(summary["Bayes_risk"], 6),
                    "C1", round(summary["C_L_1"], 6),
                    "wilson_hw", round(summary["C_L_1_Wilson_half_width95"], 6),
                    "risk_hw", round(summary["Bayes_risk_bootstrap_half_width95"], 6),
                    flush=True,
                )
                progress = {
                    "status": "complete" if all(stopped.values()) else "running",
                    "contract": str(MANIFEST_PATH.relative_to(ROOT)),
                    "design_sha256": design_sha256,
                    "new_physical_records": sum(len(value[1]["records"]) for value in outputs.values()),
                    "maximum_new_physical_records": int(budget["maximum_new_physical_records"]),
                    "cells": [
                        {
                            "id": value[1]["cell"]["id"],
                            "status": value[1]["status"],
                            "records": len(value[1]["records"]),
                            "stop_reason": value[1].get("stop_reason"),
                            "summary": value[1].get("final_summary"),
                        }
                        for value in outputs.values()
                    ],
                    "runtime_seconds": time.monotonic() - started,
                    "peak_memory_gib": peak_rss_gib(),
                    "bootstrap_replicates_per_batch_analysis": bootstrap_replicates,
                    "integrity": {
                        "unique_record_keys": len({row["record_key"] for value in outputs.values() for row in value[1]["records"]})
                        == sum(len(value[1]["records"]) for value in outputs.values()),
                        "production_cells_match_registration": len(outputs) == int(budget["maximum_new_cells"]),
                        "record_budget_respected": sum(len(value[1]["records"]) for value in outputs.values())
                        <= int(budget["maximum_new_physical_records"]),
                    },
                }
                write_json(PROGRESS_PATH, progress)
                if time.monotonic() - started > total_runtime_cap:
                    progress["status"] = "censored_runtime_cap"
                    progress["censor_reason"] = "registered production runtime cap reached"
                    write_json(PROGRESS_PATH, progress)
                    print("RUNTIME_CAP", flush=True)
                    return

    print("ALL_CELLS_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
