"""Exact local support audit of the visually checked A13/A14 transcription.

This runner verifies the pinned transcript against prior machine records. It
does not independently read the paper's equation graphics or simulate D4.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6g-source-stabilizer-disambiguation-2026-09-24.json"
RESULT = LAB / "results/j6g-source-stabilizer-disambiguation-2026-09-24.json"
INPUTS = {
    "paper_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6e_result": LAB / "results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json",
    "j6f_result": LAB / "results/j6f-first-herald-green-repeat-audit-2026-09-24.json",
    "d4_postflux": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_postflux.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    start = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {
        name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
        for name, path in INPUTS.items()
    }
    if not all(checks.values()):
        raise ValueError(f"Pinned input drift: {checks}")
    j6e = json.loads(INPUTS["j6e_result"].read_text())
    j6f = json.loads(INPUTS["j6f_result"].read_text())
    geom = j6e["geometry"]
    assert geom["selected_two_edge_path"] == [0, 4]
    assert geom["selected_green_center"] == 1
    assert geom["selected_blue_endpoints"] == [0, 2]
    first = j6e["exact_cases"]["two_edge_path"]["first_public_full_binary_support"]
    old_post = j6e["exact_cases"]["two_edge_path"]["branches"]["matching_red_x"]["postflux_e2"]["public_full_binary_records"]
    assert sorted((row["public"]["charge"][1], row["first_probability"]) for row in first) == [(0, 0.5), (1, 0.5)]
    old_local = {(row["charge"][0], row["charge"][1], row["charge"][2]) for row in old_post}
    assert old_local == {(0, 0, 0), (1, 0, 1)}

    # Source transcription, checked against PDF p. 13 before registration:
    # A13 has bare A_green,2=+1 separately from p2 * dressed A_green,2.
    # Measuring either blue star replaces the latter, not the bare stabilizer.
    # A14 retains bare A_green,2=+1 and equal blue-star eigenvalues p.
    matrix = []
    for first_green in (0, 1):
        for post_blue in (0, 1):
            source_local = (post_blue, 0, post_blue)
            old_j6f = next(
                row for row in j6f["exact_matrix"]
                if row["first_green_bit"] == first_green
                and row["post_blue_common_bit"] == post_blue
            )
            matrix.append({
                "first_green_bit": first_green,
                "post_blue_common_bit": post_blue,
                "source_a14_local_bits_blue_green_blue": list(source_local),
                "j6e_contains_source_record": source_local in old_local,
                "j6f_predicted_post_green_bit": int(old_j6f["source_required_active_charge_bits"]["1"]),
                "j6f_prediction_matches_source": int(old_j6f["source_required_active_charge_bits"]["1"]) == 0,
            })
    assert len(matrix) == 4
    assert all(row["j6e_contains_source_record"] for row in matrix)
    assert [row["j6f_prediction_matches_source"] for row in matrix] == [True, True, False, False]
    assert time.monotonic() - start < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_retracted_j6f_false_source_transcription",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": checks,
        "source_visual_transcription": {
            "A13_second": "Bare green star 2 has +1 stabilizer eigenvalue.",
            "A13_third": "p2 multiplies a distinct red-Z-dressed green-star operator, not the bare postflux charge measurement.",
            "A13_to_A14": "Blue measurement replaces the dressed stabilizer; bare green +1 remains, blue stars 1 and 3 share eigenvalue p.",
            "A14_postflux_green_bit": 0,
        },
        "exact_matrix": matrix,
        "interpretation": {
            "retracted": "J6F's alleged green-repeat contradiction, its withdrawal of J6E postflux support, and the J6F-only freeze of the Lab 004 sampler.",
            "retained_narrowly": "J6E L=2 two-edge postflux support (blue 00 or 11, green vacuum), flux-chain identities and ideal projector repeatability are source-consistent; this is not a general-channel verification.",
            "unresolved": "The general-geometry action-conditioned D4 instrument and dependent five-round physical validity remain unproved; J6/J6B remain censored for their original reasons."
        },
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - start, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
