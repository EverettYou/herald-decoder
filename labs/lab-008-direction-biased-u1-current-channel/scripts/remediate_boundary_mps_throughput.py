#!/usr/bin/env python3
"""Test row-boundary TT truncation as a zero-history throughput remediation."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
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

OUT = LAB / "results" / "boundary-mps-throughput-remediation-2026-09-21.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_gib() -> float:
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return v / (1024**3 if platform.system() == "Darwin" else 1024**2)


def tasks() -> list[dict]:
    cohort = json.loads((LAB / "results" / "boundary-mps-validation-cohort-2026-09-21.json").read_text())
    validation = json.loads((LAB / "results" / "boundary-mps-validation-2026-09-21.json").read_text())
    output = []
    for cell in cohort["cells"]:
        if int(cell["L"]) != 11:
            continue
        record = sorted((r for r in cell["selected"] if r["split"] == "heldout"), key=lambda r: (r["stratum"], r["record_key"]))[0]
        baseline = {
            (r["direction"], int(r["chi"])): r["candidate_sectors"]
            for r in validation["rows"]
            if r["L"] == 11 and r["q"] == cell["q"] and r["record_key"] == record["record_key"]
        }
        output.append({"kind": "L11-control", "id": record["record_key"], "L": 11, "q": cell["q"], "charge": record["charge"], "baseline": baseline})
    preflight = json.loads((LAB / "results" / "l13-boundary-mps-preflight-2026-09-21.json").read_text())
    for fixture in preflight["fixtures"]:
        baseline = {(e["direction"], int(e["chi"])): e["sectors"] for e in fixture["evaluations"]}
        output.append({"kind": "L13-frozen-preflight", "id": fixture["fixture_id"], "L": 13, "q": fixture["q"], "charge": fixture["charge"], "baseline": baseline})
    return output


def evaluate(task: dict) -> dict:
    model = square_graph(int(task["L"]))
    Q = np.asarray(task["charge"], dtype=np.int16)
    rows = []
    for direction, order in (("left-to-right", list(model.detector_vertices)), ("right-to-left", list(reversed(model.detector_vertices)))):
        engine = BoundaryMPSPosterior(model, order=order)
        for chi in (16, 32):
            started = time.monotonic()
            candidate = engine.infer(Q, 0.30, float(task["q"]), chi=chi, truncation_schedule="row")
            baseline = np.asarray(task["baseline"][(direction, chi)])
            rows.append({
                "direction": direction, "chi": chi, "sectors": candidate.sectors.tolist(),
                "baseline_sectors": baseline.tolist(),
                "maximum_sector_replay_error": float(np.max(np.abs(candidate.sectors - baseline))),
                "seconds": time.monotonic() - started,
            })
    return {"kind": task["kind"], "id": task["id"], "L": task["L"], "q": task["q"], "rows": rows, "worker_peak_gib": rss_gib()}


def main() -> None:
    work = tasks()
    started = time.monotonic()
    results = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(evaluate, task) for task in work]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = time.monotonic() - started
    rows = [row for result in results for row in result["rows"]]
    l13 = [row for result in results if result["L"] == 13 for row in result["rows"]]
    means = {
        f"chi{chi}_{direction}": float(np.mean([r["seconds"] for r in l13 if r["chi"] == chi and r["direction"] == direction]))
        for chi in (16, 32) for direction in ("left-to-right", "right-to-left")
    }
    worker_seconds = 1152 * means["chi16_left-to-right"] + 144 * (
        means["chi16_right-to-left"] + means["chi32_left-to-right"] + means["chi32_right-to-left"]
    )
    projected = worker_seconds / 4
    max_error = max(row["maximum_sector_replay_error"] for row in rows)
    gates = {
        "all_24_frozen_evaluations_complete": len(rows) == 24,
        "maximum_sector_replay_error_le_1e-10": max_error <= 1e-10,
        "minimum_matrix_projection_le_7200_seconds": projected <= 7200,
        "conservative_memory_le_8_gib": rss_gib() + sum(r["worker_peak_gib"] for r in results) <= 8,
        "production_histories_zero": True,
    }
    result = {
        "id": "lab008-boundary-mps-throughput-remediation-2026-09-21",
        "status": "accepted" if all(gates.values()) else "rejected",
        "candidate": "dense frontier update with identical local tensors and chi, TT-SVD only at completed lattice-row boundaries",
        "gates": gates,
        "maximum_sector_replay_error": max_error,
        "l13_mean_seconds": means,
        "minimum_matrix_projected_worker_seconds": worker_seconds,
        "minimum_matrix_projected_four_worker_wall_seconds": projected,
        "measured_matrix_wall_seconds": elapsed,
        "conservative_main_plus_worker_peak_gib": rss_gib() + sum(r["worker_peak_gib"] for r in results),
        "results": sorted(results, key=lambda x: (x["L"], x["q"], x["id"])),
        "production_histories_generated": 0,
        "bootstrap_replicates": 0,
        "source_hashes": {
            "runner": sha(Path(__file__)),
            "implementation": sha(LAB / "scripts" / "boundary_mps_posterior.py"),
            "L11_baseline": sha(LAB / "results" / "boundary-mps-validation-2026-09-21.json"),
            "L13_baseline": sha(LAB / "results" / "l13-boundary-mps-preflight-2026-09-21.json")
        },
        "decision": "Promote only if both semantic replay and unchanged-matrix throughput gates pass; otherwise retain the vertex schedule and keep production unarmed."
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "gates": gates, "maximum_sector_replay_error": max_error, "projected_wall_seconds": projected, "measured_wall_seconds": elapsed}, indent=2))


if __name__ == "__main__":
    main()
