#!/usr/bin/env python3
"""Run only the registered R5a 200-history preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
LAB_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from d4_charge import build_charge_lattice, charge_chain_boundary  # noqa: E402
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_matching import (  # noqa: E402
    edge_chain_boundary,
    published_herald_weights,
    syndrome_only_weights,
)
from d4_pipeline import decode_physical_error  # noqa: E402
from d4_postflux import accumulate_postflux_constraints  # noqa: E402


ALLOWED_STATUSES = {
    "physical_winding_failure",
    "flux_union_logical_failure",
    "decoded",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def max_rss_gib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0**3)
    return value * 1024.0 / (1024.0**3)


def trajectory_seeds(salt: int, size: int, error_rate: float, seed_index: int) -> tuple[int, int]:
    sequence = np.random.SeedSequence(
        [salt, size, int(round(10_000 * error_rate)), seed_index]
    )
    physical_seed, decoder_seed = (
        int(value) for value in sequence.generate_state(2, dtype=np.uint32)
    )
    return physical_seed, decoder_seed


def stage_outcome(record) -> str:
    if record.status == "physical_winding_failure":
        return "terminal_physical_winding"
    if record.status == "flux_union_logical_failure":
        return "first_stage_union_winding"
    if record.status != "decoded" or record.charge_recovery is None:
        return "invalid_status"
    return "second_stage_logical_failure" if record.logical_error else "decoded_success"


def validate_record(lattice, record) -> list[str]:
    failures: list[str] = []
    if record.status not in ALLOWED_STATUSES:
        failures.append("unknown_status")
        return failures
    if record.status == "physical_winding_failure":
        if not record.logical_error or record.flux_recovery is not None:
            failures.append("terminal_status_contract")
        return failures
    if record.flux_recovery is None:
        failures.append("missing_flux_recovery")
        return failures
    flux = record.flux_recovery
    if not np.array_equal(edge_chain_boundary(lattice, flux.correction), flux.syndrome):
        failures.append("flux_syndrome_fidelity")
    expected_weights = (
        syndrome_only_weights(lattice)
        if record.mode == "syndrome_only"
        else published_herald_weights(
            lattice, np.asarray(record.observation.charge_outcomes, dtype=np.int64)
        )
    )
    # Recompute the objective from the decoder-visible correction and weights.
    if abs(float(np.dot(expected_weights, flux.correction)) - flux.objective_weight) > 1e-9:
        failures.append("flux_objective_recompute")
    if record.status == "flux_union_logical_failure":
        if not record.logical_error or record.charge_recovery is not None:
            failures.append("flux_failure_status_contract")
        return failures
    if record.postflux_relations is None or record.postflux_charge_outcomes is None:
        failures.append("missing_postflux_record")
        return failures
    if record.charge_recovery is None:
        failures.append("missing_charge_recovery")
        return failures
    support = accumulate_postflux_constraints(
        lattice.vertex_count,
        record.postflux_relations.active_vertices,
        record.postflux_relations.entanglement_pairs,
        np.asarray(record.postflux_charge_outcomes, dtype=np.int64),
    )
    if not support.allowed:
        failures.append("postflux_support")
    for color, result in (
        (BLUE, record.charge_recovery.blue),
        (GREEN, record.charge_recovery.green),
    ):
        if np.any(charge_chain_boundary(build_charge_lattice(lattice, color), result.residual)):
            failures.append(f"charge_residual_boundary_{color}")
    if bool(record.logical_error) != bool(record.charge_recovery.logical_error):
        failures.append("decoded_logical_status")
    return failures


def run_preflight(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "registered" or manifest.get("phase") != "R5a":
        raise ValueError("manifest is not an active R5a registration")

    source_checks = []
    for relative, expected in manifest["source_freeze"].items():
        path = LAB_DIR / relative
        actual = sha256(path)
        source_checks.append(
            {"path": relative, "expected": expected, "actual": actual, "passed": actual == expected}
        )

    preflight = manifest["preflight"]["matrix"]
    design = manifest["design"]
    salt = int(design["seed_salt"])
    failure_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    cell_counts: Counter[str] = Counter()
    representative_failures: list[dict] = []
    topology = []
    evaluations = 0
    histories = 0
    started = time.perf_counter()

    for size in preflight["sizes"]:
        lattice = paper_periodic_honeycomb(int(size))
        degree = np.bincount(lattice.edge_vertices.ravel(), minlength=lattice.vertex_count)
        topo = {
            "size": int(size),
            "vertices": lattice.vertex_count,
            "edges": lattice.edge_count,
            "degree_values": sorted(int(value) for value in set(degree.tolist())),
            "period_rank": int(np.linalg.matrix_rank(lattice.period_matrix.astype(float))),
            "forcing_scale": 3 * lattice.edge_count,
            "expected_vertices": 6 * int(size) ** 2,
            "expected_edges": 9 * int(size) ** 2,
            "expected_forcing_scale": 27 * int(size) ** 2,
        }
        topo["passed"] = (
            topo["vertices"] == topo["expected_vertices"]
            and topo["edges"] == topo["expected_edges"]
            and topo["degree_values"] == [3]
            and topo["period_rank"] == 2
            and topo["forcing_scale"] == topo["expected_forcing_scale"]
        )
        topology.append(topo)

        for error_rate in preflight["physical_error_rates"]:
            for seed_index in range(int(preflight["histories_per_size_rate"])):
                physical_seed, decoder_seed = trajectory_seeds(
                    salt, int(size), float(error_rate), seed_index
                )
                physical = (
                    np.random.default_rng(physical_seed).random(lattice.edge_count)
                    < float(error_rate)
                ).astype(np.uint8)
                records = {}
                histories += 1
                for mode in preflight["policies"]:
                    evaluations += 1
                    try:
                        record = decode_physical_error(
                            lattice, physical, mode=str(mode), seed=decoder_seed
                        )
                        records[str(mode)] = record
                        status_counts[f"{mode}:{record.status}"] += 1
                        cell_counts[
                            f"L{size}:p{float(error_rate):.2f}:{mode}:{stage_outcome(record)}"
                        ] += 1
                        for failure in validate_record(lattice, record):
                            failure_counts[failure] += 1
                            if len(representative_failures) < 20:
                                representative_failures.append(
                                    {
                                        "size": int(size),
                                        "error_rate": float(error_rate),
                                        "seed_index": seed_index,
                                        "mode": str(mode),
                                        "failure": failure,
                                    }
                                )
                    except Exception as exc:  # fail closed and preserve witness
                        failure_counts["decoder_exception"] += 1
                        if len(representative_failures) < 20:
                            representative_failures.append(
                                {
                                    "size": int(size),
                                    "error_rate": float(error_rate),
                                    "seed_index": seed_index,
                                    "mode": str(mode),
                                    "failure": "decoder_exception",
                                    "exception": repr(exc),
                                }
                            )
                if set(records) == {"syndrome_only", "heralded"}:
                    left, right = records["syndrome_only"], records["heralded"]
                    if left.physical_error_edges != right.physical_error_edges:
                        failure_counts["matched_physical_error"] += 1
                    if left.observation != right.observation:
                        failure_counts["matched_initial_observation"] += 1

    elapsed = time.perf_counter() - started
    projected_seconds = elapsed / max(evaluations, 1) * int(
        manifest["compute_budget"]["maximum_public_decoder_evaluations"]
    )
    rss_gib = max_rss_gib()
    source_passed = all(item["passed"] for item in source_checks)
    topology_passed = all(item["passed"] for item in topology)
    scientific_passed = not failure_counts
    resource_passed = (
        projected_seconds
        <= 60.0 * float(manifest["compute_budget"]["maximum_production_wall_time_minutes"])
        and rss_gib <= float(manifest["compute_budget"]["maximum_resident_memory_gib"])
    )
    all_passed = source_passed and topology_passed and scientific_passed and resource_passed
    return {
        "status": "r5a_preflight_passed" if all_passed else "r5a_preflight_failed",
        "manifest": manifest_path.name,
        "histories": histories,
        "public_decoder_evaluations": evaluations,
        "source_checks": source_checks,
        "topology_checks": topology,
        "failure_counts": dict(sorted(failure_counts.items())),
        "representative_failures": representative_failures,
        "status_counts": dict(sorted(status_counts.items())),
        "cell_stage_counts": dict(sorted(cell_counts.items())),
        "resource": {
            "preflight_wall_seconds": elapsed,
            "projected_production_wall_seconds": projected_seconds,
            "maximum_rss_gib": rss_gib,
            "registered_wall_limit_seconds": 60.0
            * float(manifest["compute_budget"]["maximum_production_wall_time_minutes"]),
            "registered_rss_limit_gib": float(
                manifest["compute_budget"]["maximum_resident_memory_gib"]
            ),
        },
        "gates": {
            "source_hashes": source_passed,
            "paper_topology": topology_passed,
            "matched_initial_records_and_pipeline_invariants": scientific_passed,
            "resource_projection": resource_passed,
            "all_passed": all_passed,
        },
        "claim_boundary": "Structural/resource preflight only. No production LER, paired risk inference, crossing, threshold, phase, noisy-measurement, or fault-tolerance result.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=LAB_DIR / "r5a-paper-lattice-public-decoder-pilot-manifest-2026-08-29.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LAB_DIR / "results/r5a-paper-lattice-public-decoder-preflight.json",
    )
    args = parser.parse_args()
    result = run_preflight(args.manifest.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gates"], indent=2))
    if not result["gates"]["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
