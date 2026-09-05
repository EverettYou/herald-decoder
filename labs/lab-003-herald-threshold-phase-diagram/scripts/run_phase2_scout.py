#!/usr/bin/env python3
"""Run one immutable Lab 003 Phase 2 (lattice, q) discovery shard."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from time import perf_counter

import numba
import numpy as np
import pymatching
import scipy

from herald_decoder import (
    NUMBA_AVAILABLE,
    HeraldAwareBpMatchingDecoder,
    honeycomb_graph,
    square_graph,
)


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_SIZES = (5, 7, 9, 11)
DEFAULT_SEEDS = (520001, 520002, 520003, 520004, 520005)
CAMPAIGN = "phase2-q-skeleton-discovery-2026-08-27"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def artifact_path(path: Path) -> str:
    try:
        return str(path.relative_to(LAB_DIR))
    except ValueError:
        return str(path)


def q_tag(q: float) -> str:
    return f"q{int(round(100 * q)):03d}"


def validate_q(q: float) -> float:
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must lie in [0, 1]")
    step = round(q * 20)
    if abs(q - step / 20) > 1e-12:
        raise ValueError("Phase 2 discovery q must lie on the registered 0.05 skeleton")
    return step / 20


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    z = 1.959963984540054
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * sqrt((rate * (1 - rate) + z * z / (4 * shots)) / shots) / denominator
    return center - radius, center + radius


def require_syndrome_fidelity(*, graph, correction: np.ndarray, syndrome: np.ndarray, context: str) -> None:
    """Fail closed before a mismatched correction can enter a durable shard."""
    correction_syndrome = graph.true_syndrome(correction)
    if not np.array_equal(correction_syndrome, syndrome):
        mismatch_count = int(np.count_nonzero(correction_syndrome ^ syndrome))
        raise RuntimeError(
            f"correction-syndrome fidelity failure ({mismatch_count} detector mismatches): {context}"
        )


def runtime_provenance() -> dict:
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "numba_version": numba.__version__,
        "scipy_version": scipy.__version__,
        "pymatching_version": pymatching.__version__,
        "numba_available": bool(NUMBA_AVAILABLE),
    }


def source_hashes() -> dict:
    return {
        "runner": sha256(Path(__file__)),
        "lattice_model": sha256(PROJECT_ROOT / "src/herald_decoder/lattice_model.py"),
        "decoder": sha256(PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py"),
        "damping_decoder": sha256(
            PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py"
        ),
        "numba_kernels": sha256(PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py"),
    }


def require_source_stability(*, expected: dict[str, str], observed: dict[str, str]) -> None:
    """Reject a shard when any loaded-source fingerprint changes during its run."""
    changed = sorted(
        name
        for name in set(expected) | set(observed)
        if expected.get(name) != observed.get(name)
    )
    if changed:
        raise RuntimeError(
            "source drift detected before atomic shard finalization: "
            + ", ".join(changed)
        )


def config_payload(*, campaign: str, lattice: str, q: float, p_grid: tuple[float, ...], sizes: tuple[int, ...], seeds: tuple[int, ...], shots_per_seed: int, max_iterations: int, update_schedule: str, residual_priority_order: str, residual_priority_buffer_reuse: bool, residual_priority_cached_products: bool) -> dict:
    return {
        "campaign": campaign,
        "lattice": lattice,
        "q": q,
        "p_grid": list(p_grid),
        "sizes": list(sizes),
        "seeds": list(seeds),
        "shots_per_seed": shots_per_seed,
        "decoder": {
            "name": "HeraldAwareBpMatchingDecoder",
            "recurrence_mode": "damping",
            "damping": 0.25,
            "max_iterations": max_iterations,
            "update_schedule": update_schedule,
            "residual_priority_order": residual_priority_order,
            "residual_priority_buffer_reuse": residual_priority_buffer_reuse,
            "residual_priority_cached_products": residual_priority_cached_products,
            "matching_projection": "posterior_llr",
            "p_m": 0.0,
            "p_h": 0.0,
            "use_numba": True,
        },
        "sampling": {
            "nested_common_random_numbers": True,
            "master_rng": "numpy.default_rng(SeedSequence([0x48445233, lattice_id, L, seed]))",
            "error_rule": "x_e(p) = 1[u_e < p]",
            "herald_rule": "h_v(p,q) = 1[d_v(p)>=2] 1[u_v<q]",
        },
    }


def run_shard(*, campaign: str = CAMPAIGN, lattice: str, q: float, p_grid: tuple[float, ...], sizes: tuple[int, ...], seeds: tuple[int, ...], shots_per_seed: int, max_iterations: int, update_schedule: str, residual_priority_order: str, residual_priority_buffer_reuse: bool, residual_priority_cached_products: bool, raw_path: Path, expected_source_hashes: dict[str, str] | None = None, source_hash_reader=source_hashes) -> dict:
    start_source_hashes = dict(expected_source_hashes or source_hash_reader())
    make_graph = square_graph if lattice == "square" else honeycomb_graph
    lattice_id = 1 if lattice == "square" else 2
    counts = {(size, p): 0 for size in sizes for p in p_grid}
    convergence = {(size, p): 0 for size in sizes for p in p_grid}
    iterations = {(size, p): 0 for size in sizes for p in p_grid}
    max_deltas = {(size, p): 0.0 for size in sizes for p in p_grid}
    elapsed = {(size, p): 0.0 for size in sizes for p in p_grid}
    syndrome_faithful = {(size, p): 0 for size in sizes for p in p_grid}
    per_seed = []
    raw_count = 0
    temporary_raw = raw_path.with_name(f".{raw_path.name}.tmp-{os.getpid()}")
    with gzip.open(temporary_raw, "wt", encoding="utf-8", compresslevel=6) as raw:
        for size in sizes:
            graph = make_graph(size)
            detector_indices = list(graph.detector_vertices)
            decoders = {
                p: HeraldAwareBpMatchingDecoder(
                    graph,
                    p=p,
                    q=q,
                    p_m=0.0,
                    p_h=0.0,
                    recurrence_mode="damping",
                    damping=0.25,
                    max_iterations=max_iterations,
                    update_schedule=update_schedule,
                    residual_priority_order=residual_priority_order,
                    residual_priority_buffer_reuse=residual_priority_buffer_reuse,
                    residual_priority_cached_products=residual_priority_cached_products,
                    use_numba=True,
                )
                for p in p_grid
            }
            for seed in seeds:
                seed_counts = {p: 0 for p in p_grid}
                rng = np.random.default_rng(np.random.SeedSequence([0x48445233, lattice_id, size, seed]))
                for shot in range(shots_per_seed):
                    edge_uniforms = rng.random(len(graph.edges))
                    herald_uniforms = rng.random(len(detector_indices))
                    observation_id = f"{campaign}:{lattice}:L{size}:seed{seed}:shot{shot}"
                    for p in p_grid:
                        error = (edge_uniforms < p).astype(np.uint8)
                        detector_degree = graph.degrees(error)[detector_indices]
                        syndrome = (detector_degree & 1).astype(np.uint8)
                        herald = ((detector_degree >= 2) & (herald_uniforms < q)).astype(np.uint8)
                        started = perf_counter()
                        result = decoders[p].decode(syndrome, herald)
                        decode_ms = 1000 * (perf_counter() - started)
                        require_syndrome_fidelity(
                            graph=graph,
                            correction=result.correction,
                            syndrome=syndrome,
                            context=f"lattice={lattice}, L={size}, p={p}, q={q}, seed={seed}, shot={shot}",
                        )
                        logical_failure = bool(graph.logical_parity(error ^ result.correction))
                        key = (size, p)
                        counts[key] += logical_failure
                        seed_counts[p] += logical_failure
                        convergence[key] += result.bp.converged
                        iterations[key] += result.bp.iterations
                        max_deltas[key] += result.bp.max_message_delta
                        elapsed[key] += decode_ms
                        syndrome_faithful[key] += 1
                        raw.write(json.dumps({
                            "campaign": campaign,
                            "lattice": lattice,
                            "L": size,
                            "p": p,
                            "q": q,
                            "decoder": f"herald_{update_schedule}_bp_llr_mwpm",
                            "seed": seed,
                            "shot": shot,
                            "observation_id": observation_id,
                            "logical_failure": logical_failure,
                            "syndrome_faithful": True,
                            "matching_weight": result.matching_weight,
                            "bp_converged": result.bp.converged,
                            "bp_iterations": result.bp.iterations,
                            "bp_max_message_delta": result.bp.max_message_delta,
                            "decode_ms": decode_ms,
                        }, separators=(",", ":")) + "\n")
                        raw_count += 1
                for p in p_grid:
                    per_seed.append({
                        "lattice": lattice,
                        "L": size,
                        "p": p,
                        "q": q,
                        "seed": seed,
                        "shots": shots_per_seed,
                        "logical_errors": seed_counts[p],
                    })
    try:
        end_source_hashes = dict(source_hash_reader())
        require_source_stability(
            expected=start_source_hashes,
            observed=end_source_hashes,
        )
    except Exception:
        temporary_raw.unlink(missing_ok=True)
        raise
    os.replace(temporary_raw, raw_path)
    total_shots = len(seeds) * shots_per_seed
    summaries = []
    for size in sizes:
        graph = make_graph(size)
        for p in p_grid:
            key = (size, p)
            low, high = wilson_interval(counts[key], total_shots)
            summaries.append({
                "lattice": lattice,
                "L": size,
                "edges": len(graph.edges),
                "detectors": len(graph.detector_vertices),
                "p": p,
                "q": q,
                "decoder": f"herald_{update_schedule}_bp_llr_mwpm",
                "shots": total_shots,
                "logical_errors": counts[key],
                "logical_error_rate": counts[key] / total_shots,
                "logical_error_ci95": [low, high],
                "bp_convergence_rate": convergence[key] / total_shots,
                "mean_bp_iterations": iterations[key] / total_shots,
                "mean_bp_max_message_delta": max_deltas[key] / total_shots,
                "mean_decode_ms": elapsed[key] / total_shots,
                "syndrome_faithful_shots": syndrome_faithful[key],
                "syndrome_fidelity_rate": syndrome_faithful[key] / total_shots,
            })
    faithful_count = sum(syndrome_faithful.values())
    return {
        "source_stability": {
            "start_equals_end": True,
            "checked_files": sorted(start_source_hashes),
            "enforcement": "fail before raw atomic finalization",
        },
        "raw_records": {
            "path": artifact_path(raw_path),
            "format": "gzip_json_lines",
            "records": raw_count,
            "sha256": sha256(raw_path),
        },
        "syndrome_fidelity": {
            "checked_corrections": raw_count,
            "faithful_corrections": faithful_count,
            "failures": raw_count - faithful_count,
            "all_faithful": faithful_count == raw_count,
            "enforcement": "raise before raw-row write and atomic shard finalization",
        },
        "per_seed": per_seed,
        "summaries": summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lattice", choices=("square", "honeycomb"), required=True)
    parser.add_argument("--q", type=float, required=True)
    parser.add_argument("--p", type=float, nargs="+", required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    parser.add_argument("--shots-per-seed", type=int, default=200)
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--update-schedule", choices=("synchronous", "residual_priority"), default="synchronous")
    parser.add_argument("--residual-priority-order", choices=("scan", "stable_sort"), default="scan")
    parser.add_argument("--residual-priority-buffer-reuse", action="store_true")
    parser.add_argument("--residual-priority-cached-products", action="store_true")
    parser.add_argument("--allow-honeycomb-high-p", action="store_true")
    parser.add_argument("--campaign", default=CAMPAIGN)
    parser.add_argument("--stem")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    q = validate_q(args.q)
    p_grid = tuple(sorted(set(args.p)))
    sizes = tuple(dict.fromkeys(args.sizes))
    seeds = tuple(dict.fromkeys(args.seeds))
    if not NUMBA_AVAILABLE:
        raise SystemExit("accelerated Numba runtime is required; use run_research_python.sh")
    if not p_grid or any(not 0 < p < 1 for p in p_grid):
        raise SystemExit("BP Phase 2 p values must lie strictly between 0 and 1")
    if any(p >= 0.5 for p in p_grid) and (args.lattice != "honeycomb" or not args.allow_honeycomb_high_p):
        raise SystemExit("p >= 0.5 is an explicitly enabled honeycomb-only experiment; pass --allow-honeycomb-high-p")
    if len(sizes) < 2 or any(size < 2 for size in sizes):
        raise SystemExit("at least two valid sizes are required")
    if not seeds or args.shots_per_seed < 1:
        raise SystemExit("seeds and shots-per-seed must be positive")
    if args.max_iterations < 1:
        raise SystemExit("max_iterations must be positive")
    if (args.residual_priority_buffer_reuse or args.residual_priority_cached_products) and args.update_schedule != "residual_priority":
        raise SystemExit("residual-priority experimental controls require --update-schedule residual_priority")
    stem = args.stem or f"phase2-{args.lattice}-{q_tag(q)}-discovery-1000-2026-08-27"
    results_dir = LAB_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    result_path = results_dir / f"{stem}.json"
    raw_path = results_dir / f"{stem}-raw.jsonl.gz"
    config = config_payload(campaign=args.campaign, lattice=args.lattice, q=q, p_grid=p_grid, sizes=sizes, seeds=seeds, shots_per_seed=args.shots_per_seed, max_iterations=args.max_iterations, update_schedule=args.update_schedule, residual_priority_order=args.residual_priority_order, residual_priority_buffer_reuse=args.residual_priority_buffer_reuse, residual_priority_cached_products=args.residual_priority_cached_products)
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if result_path.exists():
        existing = json.loads(result_path.read_text())
        if args.skip_existing and existing.get("config_sha256") == config_hash and raw_path.is_file():
            print(json.dumps({"status": "already_complete", "result": str(result_path)}))
            return
        raise SystemExit(f"refusing to overwrite existing shard: {result_path}")
    start_source_hashes = source_hashes()
    generated = run_shard(campaign=args.campaign, lattice=args.lattice, q=q, p_grid=p_grid, sizes=sizes, seeds=seeds, shots_per_seed=args.shots_per_seed, max_iterations=args.max_iterations, update_schedule=args.update_schedule, residual_priority_order=args.residual_priority_order, residual_priority_buffer_reuse=args.residual_priority_buffer_reuse, residual_priority_cached_products=args.residual_priority_cached_products, raw_path=raw_path, expected_source_hashes=start_source_hashes)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "Lab 003 Phase 2 full q-skeleton discovery shard",
        "config_sha256": config_hash,
        **config,
        "total_shots_per_cell": len(seeds) * args.shots_per_seed,
        "runtime": runtime_provenance(),
        "source_hashes": start_source_hashes,
        **generated,
        "evidence_boundary": "Phase 2 finite-size scouting cell map; crossings require adaptive refinement and confirmation before threshold claims.",
    }
    atomic_json(result_path, payload)
    print(json.dumps({"status": "complete", "result": str(result_path), "raw": str(raw_path), "records": generated["raw_records"]["records"]}))


if __name__ == "__main__":
    main()
