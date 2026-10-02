#!/usr/bin/env python3
"""Run the registered paired finite-chi boundary-MPS validation matrix."""
from __future__ import annotations

import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
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

MANIFEST = LAB / "manifests" / "beyond-l11-mps-validation-2026-09-21.json"
COHORT = LAB / "results" / "boundary-mps-validation-cohort-2026-09-21.json"
RESULT = LAB / "results" / "boundary-mps-validation-2026-09-21.json"


def sha_bytes(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def peak_gib() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024**3 if platform.system() == "Darwin" else 1024**2)


def load_cell(L: int, q: float) -> tuple[Path, dict, list[dict]]:
    tag = int(round(100 * q))
    if L == 9 and tag in (90, 97):
        path = LAB / "results" / "size-bias-extension-cells" / f"square-L9-p30-q{tag}-extension.json"
    else:
        path = LAB / "results" / "posterior-gap-boundary-tail-cells" / f"square-L{L}-p30-q{tag}-boundary-tail.json"
    data = json.loads(path.read_text())
    model = square_graph(L)
    D = charge_matrix(model)
    rows = []
    if data["records"] and "Q" in data["records"][0]:
        for record in data["records"]:
            Q = np.asarray(record["Q"], dtype=np.int16)
            rows.append({"record": record, "Q": Q})
    else:
        seed = int(data["stream_seed"])
        # The acquisition runner drew the full registered 1024-row activity
        # block before drawing the orientation block.  Replay that exact RNG
        # consumption, not merely the retained prefix.
        count = 1024
        rng = np.random.default_rng(seed)
        activity = rng.random((count, len(model.edges)))
        orientation = rng.random((count, len(model.edges)))
        for record in data["records"]:
            i = int(record["sample_index"])
            current = (activity[i] < 0.30) * np.where(orientation[i] < q, 1, -1)
            Q = np.asarray(D @ current, dtype=np.int16)
            if sha_bytes(Q.tobytes()) != record["charge_sha256"]:
                raise RuntimeError(f"charge replay mismatch: {path.name}:{i}")
            rows.append({"record": record, "Q": Q})
    return path, data, rows


def absolute_gap(record: dict) -> float:
    if record.get("gap_infinite_sign", 0):
        return math.inf
    return abs(float(record["signed_gap"]))


def freeze_cohort() -> dict:
    cells = []
    for L in (9, 11):
        for q in (0.90, 0.94, 0.97):
            path, _, source = load_cell(L, q)
            ordered = sorted(source, key=lambda x: (absolute_gap(x["record"]), int(x["record"]["sample_index"])))
            strata = np.array_split(np.arange(len(ordered)), 8)
            selected = []
            for stratum, indices in enumerate(strata):
                if len(indices) < 2:
                    raise RuntimeError("stratum has fewer than two records")
                positions = [int(indices[(len(indices) - 1) // 3]), int(indices[(2 * (len(indices) - 1)) // 3])]
                if positions[0] == positions[1]:
                    positions[1] = int(indices[-1])
                for split, position in zip(("development", "heldout"), positions):
                    item = ordered[position]
                    record = item["record"]
                    sectors = [float(x) for x in record["sector_probabilities"]]
                    selected.append({
                        "split": split,
                        "stratum": stratum,
                        "sample_index": int(record["sample_index"]),
                        "record_key": record.get("record_key", f"{path.stem}:index{record['sample_index']}"),
                        "charge": item["Q"].astype(int).tolist(),
                        "charge_sha256": sha_bytes(item["Q"].tobytes()),
                        "exact_sectors": sectors,
                        "exact_gap": absolute_gap(record),
                        "exact_risk": float(min(sectors)),
                    })
            cells.append({
                "L": L,
                "q": q,
                "source": str(path.relative_to(ROOT)),
                "source_sha256": sha_file(path),
                "source_records": len(source),
                "selected": selected,
            })
    cohort = {
        "id": "lab008-boundary-mps-validation-cohort-2026-09-21",
        "status": "frozen",
        "selection": "eight exact-gap rank strata per cell; deterministic one-third development and two-thirds heldout positions within each stratum",
        "cells": cells,
        "records": sum(len(c["selected"]) for c in cells),
        "development_records": sum(sum(r["split"] == "development" for r in c["selected"]) for c in cells),
        "heldout_records": sum(sum(r["split"] == "heldout" for r in c["selected"]) for c in cells),
        "new_physical_records": 0,
    }
    COHORT.write_text(json.dumps(cohort, indent=2) + "\n")
    return cohort


def risk_share(gaps: np.ndarray, risks: np.ndarray, cutoff: float) -> float:
    denominator = float(risks.sum())
    return float(risks[gaps <= cutoff].sum() / denominator) if denominator else 0.0


def analyze(rows: list[dict]) -> tuple[list[dict], list[int]]:
    metrics = []
    cutoffs = (0.5, 1.0, 2.0, 4.0)
    for L in (9, 11):
        for q in (0.90, 0.94, 0.97):
            for direction in ("left-to-right", "right-to-left"):
                for chi in (16, 32, 64, 128):
                    block = [r for r in rows if r["L"] == L and r["q"] == q and r["direction"] == direction and r["chi"] == chi and r["split"] == "heldout"]
                    exact_g = np.asarray([r["exact_gap"] for r in block])
                    cand_g = np.asarray([r["candidate_gap"] for r in block])
                    exact_r = np.asarray([r["exact_risk"] for r in block])
                    cand_r = np.asarray([r["candidate_risk"] for r in block])
                    gap_error = np.abs(cand_g - exact_g)
                    risk_error = np.abs(cand_r - exact_r)
                    cdf_errors = {str(a): abs(float(np.mean(cand_g <= a) - np.mean(exact_g <= a))) for a in cutoffs}
                    share_errors = {str(a): abs(risk_share(cand_g, cand_r, a) - risk_share(exact_g, exact_r, a)) for a in cutoffs}
                    gate = {
                        "median_gap_error": float(np.median(gap_error)) <= 0.10,
                        "p95_gap_error": float(np.quantile(gap_error, 0.95)) <= 0.25,
                        "p95_risk_error": float(np.quantile(risk_error, 0.95)) <= 0.01,
                        "cdf_errors": max(cdf_errors.values()) <= 0.02,
                        "risk_share_errors": max(share_errors.values()) <= 0.02,
                        "nonnegative_finite": all(np.isfinite(r["candidate_sectors"]).all() and min(r["candidate_sectors"]) >= 0 for r in block),
                    }
                    metrics.append({
                        "L": L, "q": q, "direction": direction, "chi": chi,
                        "heldout_records": len(block),
                        "median_abs_gap_error": float(np.median(gap_error)),
                        "p95_abs_gap_error": float(np.quantile(gap_error, 0.95)),
                        "p95_abs_risk_error": float(np.quantile(risk_error, 0.95)),
                        "cdf_absolute_errors": cdf_errors,
                        "risk_share_absolute_errors": share_errors,
                        "gates": gate,
                        "all_gates_pass": all(gate.values()),
                    })
    passing = [chi for chi in (16, 32, 64, 128) if all(m["all_gates_pass"] for m in metrics if m["chi"] == chi)]
    return metrics, passing


def evaluate_group(task: dict) -> list[dict]:
    """Evaluate the remaining chi values for one record and sweep."""
    L, q = int(task["L"]), float(task["q"])
    model = square_graph(L)
    order = list(model.detector_vertices)
    if task["direction"] == "right-to-left":
        order = list(reversed(order))
    engine = BoundaryMPSPosterior(model, order=order)
    Q = np.asarray(task["record"]["charge"], dtype=np.int16)
    output = []
    for chi in task["chis"]:
        t0 = time.monotonic()
        candidate = engine.infer(Q, 0.30, q, chi=int(chi))
        record = task["record"]
        output.append({
            "L": L, "q": q, "record_key": record["record_key"], "charge_sha256": record["charge_sha256"],
            "split": record["split"], "stratum": record["stratum"], "direction": task["direction"], "chi": int(chi),
            "exact_sectors": record["exact_sectors"], "candidate_sectors": candidate.sectors.tolist(),
            "exact_gap": record["exact_gap"], "candidate_gap": abs(candidate.signed_gap),
            "exact_risk": record["exact_risk"], "candidate_risk": candidate.bayes_risk,
            "discarded_frobenius_sq": candidate.discarded_frobenius_sq,
            "maximum_bond": candidate.maximum_bond, "seconds": time.monotonic() - t0,
        })
    return output


def main():
    manifest = json.loads(MANIFEST.read_text())
    if not manifest["tensorization_preflight"]["all_gates_pass"]:
        raise RuntimeError("tensorization prerequisite not passed")
    cohort = freeze_cohort()
    cohort_hash = sha_file(COHORT)
    rows = []
    prior_runtime = 0.0
    if RESULT.exists():
        old = json.loads(RESULT.read_text())
        if old.get("cohort_sha256") != cohort_hash:
            raise RuntimeError("cohort changed since checkpoint")
        rows = old.get("rows", [])
        prior_runtime = float(old.get("runtime_seconds_cumulative", old.get("runtime_seconds_this_invocation", 0.0)))
    done = {(r["L"], r["q"], r["record_key"], r["direction"], r["chi"]) for r in rows}
    started = time.monotonic()
    tasks = []
    for cell in cohort["cells"]:
        L, q = int(cell["L"]), float(cell["q"])
        for record in cell["selected"]:
            for direction in ("left-to-right", "right-to-left"):
                chis = [chi for chi in (16, 32, 64, 128) if (L, q, record["record_key"], direction, chi) not in done]
                if chis:
                    tasks.append({"L": L, "q": q, "record": record, "direction": direction, "chis": chis})
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(evaluate_group, task) for task in tasks]
        for future in as_completed(futures):
            batch = future.result()
            rows.extend(batch)
            for row in batch:
                done.add((row["L"], row["q"], row["record_key"], row["direction"], row["chi"]))
            elapsed = time.monotonic() - started
            checkpoint = {
                "status": "running", "contract": str(MANIFEST.relative_to(ROOT)), "cohort": str(COHORT.relative_to(ROOT)),
                "cohort_sha256": cohort_hash, "rows_completed": len(rows), "rows_budget": 768,
                "new_physical_records": 0, "bootstrap_replicates": 0, "l13_histories": 0,
                "runtime_seconds_this_invocation": elapsed, "runtime_seconds_cumulative": prior_runtime + elapsed,
                "peak_memory_gib_main_process": peak_gib(), "workers": 4, "rows": rows,
            }
            RESULT.write_text(json.dumps(checkpoint, separators=(",", ":")) + "\n")
            if len(rows) % 32 < len(batch):
                print(f"ROWS {len(rows)}/768 cumulative_runtime={prior_runtime+elapsed:.1f}s", flush=True)
            if prior_runtime + elapsed > manifest["budget"]["maximum_runtime_seconds"]:
                checkpoint["status"] = "censored_runtime_cap"
                RESULT.write_text(json.dumps(checkpoint, separators=(",", ":")) + "\n")
                for item in futures:
                    item.cancel()
                return
    metrics, passing = analyze(rows)
    result = {
        "status": "complete", "contract": str(MANIFEST.relative_to(ROOT)), "cohort": str(COHORT.relative_to(ROOT)),
        "cohort_sha256": cohort_hash, "rows_completed": len(rows), "rows_budget": 768,
        "new_physical_records": 0, "bootstrap_replicates": 0, "l13_histories": 0,
        "runtime_seconds_this_invocation": time.monotonic() - started,
        "runtime_seconds_cumulative": prior_runtime + time.monotonic() - started,
        "peak_memory_gib_main_process": peak_gib(), "workers": 4,
        "metrics": metrics, "common_passing_chi": passing, "smallest_common_passing_chi": min(passing) if passing else None,
        "decision": "validation_passed" if passing else "close_boundary_mps_route_at_chi_128",
        "rows": rows,
        "source_hashes": {"runner": sha_file(Path(__file__)), "implementation": sha_file(LAB / "scripts" / "boundary_mps_posterior.py")},
        "claim_boundary": "Finite-chi method validation against exact L9/L11 records only; no L13 data, phase, threshold, crossing, or thermodynamic claim.",
    }
    RESULT.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "rows_completed", "smallest_common_passing_chi", "decision", "runtime_seconds_cumulative", "peak_memory_gib_main_process")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
