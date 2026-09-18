#!/usr/bin/env python3
"""Run the registered compact matched D4 scan and persist counts only."""
from __future__ import annotations
import argparse, json, multiprocessing as mp, os, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(name, "1")

LAB = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_dense_template, run_r6d_dense_template, require_r6d_dense_backend
from d4_matching import edge_chain_boundary, published_herald_weights, syndrome_only_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import trajectory_seeds, llr_weights
from d4_belief_factorization import PublicD4Observation

MANIFEST = LAB / "manifests/r6al-dense-crossing-scan-2026-09-09.json"
OUTPUT = LAB / "results/r6al-dense-crossing-scan-2026-09-09.json"
_CACHE: dict[tuple[int, float], tuple[object, object]] = {}

def empty(n=0):
    return {"attempted": n, "terminal_physical_winding": 0, "O0_failures": 0,
            "O2_failures": 0, "BP_failures": 0, "decoded": 0, "BP_converged": 0,
            "BP_nonconverged": 0, "O2_BP_discordant": 0, "O2_improves_over_BP": 0,
            "O2_regresses_vs_BP": 0}

def add(a, b):
    for k, v in b.items(): a[k] = a.get(k, 0) + int(v)
    return a

def run_chunk(job):
    size, rate, start, stop, salt, cap, tol = job
    key = (size, rate)
    if key not in _CACHE:
        lattice = paper_periodic_honeycomb(size)
        _CACHE[key] = (lattice, build_r6d_dense_template(lattice, error_rate=rate))
    lattice, template = _CACHE[key]
    out = empty(stop - start)
    for index in range(start, stop):
        ps, osd = trajectory_seeds(salt, size, rate, index)
        physical = (np.random.default_rng(ps).random(lattice.edge_count) < rate).astype(np.uint8)
        obs = observation_from_error_edges(lattice, physical, seed=osd)
        if obs.status == "logical_failure":
            out["terminal_physical_winding"] += 1
            out["O0_failures"] += 1; out["O2_failures"] += 1; out["BP_failures"] += 1
            continue
        if obs.status != "sampled" or obs.charge_outcomes is None:
            raise RuntimeError(f"unexpected observation status {obs.status!r}")
        public = PublicD4Observation(tuple(map(int, edge_chain_boundary(lattice, physical))), tuple(map(int, obs.charge_outcomes)))
        o0 = decode_and_score_flux_recovery(lattice, physical, syndrome_only_weights(lattice))
        o2 = decode_and_score_flux_recovery(lattice, physical, published_herald_weights(lattice, np.asarray(obs.charge_outcomes, dtype=np.int64)))
        bp = run_r6d_dense_template(template, public, old_message_weight=.25, max_iterations=cap, tolerance=tol)
        bpr = decode_and_score_flux_recovery(lattice, physical, llr_weights(bp.marginals[:lattice.edge_count, 1]))
        out["decoded"] += 1
        out["O0_failures"] += int(o0.logical_error); out["O2_failures"] += int(o2.logical_error); out["BP_failures"] += int(bpr.logical_error)
        out["BP_converged"] += int(bp.converged); out["BP_nonconverged"] += int(not bp.converged)
        out["O2_BP_discordant"] += int(bool(o2.logical_error) != bool(bpr.logical_error))
        out["O2_improves_over_BP"] += int(bool(o2.logical_error) and not bool(bpr.logical_error))
        out["O2_regresses_vs_BP"] += int(not bool(o2.logical_error) and bool(bpr.logical_error))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int); ap.add_argument("--histories", type=int); ap.add_argument("--chunk-size", type=int, default=64); args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text()); design = manifest["scan_design"]
    workers = args.workers or int(design["workers"]); histories = args.histories or int(design["histories_per_cell"])
    require_r6d_dense_backend()
    cells = [(int(s), float(p)) for s in design["sizes"] for p in design["p_X_grid"]]
    result = {"status":"running", "manifest":MANIFEST.name, "workers":workers, "histories_per_cell":histories, "cells":[], "storage_contract":manifest["storage_contract"], "claim_boundary":manifest["claim_boundary"]}
    for size, rate in cells:
        jobs = [(size, rate, i, min(i+args.chunk_size, histories), int(design["seed_salt"]), int(design["bp_max_iterations"]), float(design["bp_tolerance"])) for i in range(0, histories, args.chunk_size)]
        started = time.perf_counter(); total = empty()
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
            for part in pool.map(run_chunk, jobs): add(total, part)
        total.update({"size":size, "p_X":rate, "elapsed_seconds":time.perf_counter()-started})
        result["cells"].append(total)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True); OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print(json.dumps(total), flush=True)
    result["status"] = "complete"; OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")

if __name__ == "__main__": main()
