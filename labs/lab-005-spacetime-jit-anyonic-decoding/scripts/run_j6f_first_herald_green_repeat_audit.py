"""Exact source-semantic comparison; never samples physical histories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6f-first-herald-green-repeat-audit-2026-09-24.json"
RESULT = LAB / "results/j6f-first-herald-green-repeat-audit-2026-09-24.json"
INPUTS = {
    "j6e_result": LAB / "results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json",
    "d4_postflux": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_postflux.py",
    "d4_pipeline": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_pipeline.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    start = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {
        name: sha(path) == contract["pinned_inputs"][f"{name}_sha256"]
        for name, path in INPUTS.items()
    }
    if not all(checks.values()):
        raise ValueError(f"pinned source mismatch: {checks}")
    j6e = json.loads(INPUTS["j6e_result"].read_text())
    geometry = j6e["geometry"]
    fixture = contract["frozen_fixture"]
    assert geometry["selected_green_center"] == fixture["green_center"]
    assert geometry["selected_blue_endpoints"] == fixture["blue_endpoints"]
    assert geometry["selected_two_edge_path"] == fixture["physical_red_edges"]
    case = j6e["exact_cases"]["two_edge_path"]
    first = case["first_public_full_binary_support"]
    old_post = case["branches"]["matching_red_x"]["postflux_e2"]["public_full_binary_records"]
    center = fixture["green_center"]
    left, right = fixture["blue_endpoints"]
    first_bits = sorted({row["public"]["charge"][center] for row in first})
    assert first_bits == [0, 1]
    assert all(row["charge"][left] == row["charge"][right] for row in old_post)
    assert sorted({row["charge"][left] for row in old_post}) == [0, 1]

    matrix = []
    for first_green in first_bits:
        for common_blue in (0, 1):
            # Jing A.4 Eq. (A13): p2 A_green survives matching correction.
            # Eq. (A14): both blue endpoints carry the same p eigenvalue.
            expected = {str(center): first_green, str(left): common_blue,
                        str(right): common_blue}
            old_matching = [
                row for row in old_post
                if row["charge"][center] == first_green
                and row["charge"][left] == common_blue
                and row["charge"][right] == common_blue
            ]
            matrix.append({
                "first_green_bit": first_green,
                "post_blue_common_bit": common_blue,
                "source_required_active_charge_bits": expected,
                "existing_postflux_has_required_record": bool(old_matching),
            })
    assert len(matrix) == 4
    assert [row["existing_postflux_has_required_record"] for row in matrix] == [
        True, True, False, False
    ]
    assert time.monotonic() - start < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_detected_source_semantic_mismatch",
        "contract_sha256": sha(CONTRACT),
        "pinned_input_checks": checks,
        "exact_matrix": matrix,
        "decisive_counterexample": "First green charge bit 1 (p2=-1) has positive first-round support in J6E, but all its existing postflux records set green bit 0; Jing A.4 Eq. (A13) retains p2 at that green star after the matching correction.",
        "scope": {
            "invalid": "J6E source-bounded postflux support and any D4 physical-risk/performance interpretation relying on the unconditional singleton-even postflux sampler",
            "still_valid_as_kinematic_or_structural_only": "Selected L=2 graph and flux-chain XOR identities, blue-pair parity, and ideal repeatability once the actual second projector outcome is fixed",
            "unresolved": "Joint probabilities for general geometry, arbitrary action and faults; no universal D4 conditional channel is derived here"
        },
        "affected_interface": "Lab 004 d4_pipeline.sample_postflux_charge_outcomes has no first herald argument; Lab 005 d4_integrated_history inherits it. Audit dependent results before any reuse.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - start, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
