"""Source-derived symbolic L=2 stabilizer instrument for A6/A13/A14.

The A13/A14 operator diagrams and the stated anticommutation are transcribed
in the registered contract. This is not a full D4 Pauli tableau simulation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json"
RESULT = LAB / "results/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json"
INPUTS = {
    "paper_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6e_result": LAB / "results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json",
    "j6g_result": LAB / "results/j6g-source-stabilizer-disambiguation-2026-09-24.json",
    "d4_honeycomb": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_honeycomb.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(bit: int) -> int:
    return 1 - 2 * bit


def public_e2(charge: list[int]) -> dict:
    return {
        "flux": [0] * len(charge),
        "charge": charge,
        "vacuum": [1 - bit for bit in charge],
    }


def run() -> dict:
    start = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {
        key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
        for key, path in INPUTS.items()
    }
    if not all(checks.values()):
        raise ValueError(f"Pinned input mismatch: {checks}")
    j6e = json.loads(INPUTS["j6e_result"].read_text())
    j6g = json.loads(INPUTS["j6g_result"].read_text())
    assert j6g["status"] == "passed_retracted_j6f_false_source_transcription"
    geometry = j6e["geometry"]
    assert geometry["size"] == 2 and geometry["vertices"] == 24
    assert geometry["selected_two_edge_path"] == [0, 4]
    assert geometry["selected_green_center"] == 1
    assert geometry["selected_blue_endpoints"] == [0, 2]
    old = j6e["exact_cases"]["two_edge_path"]
    first_rows = old["first_public_full_binary_support"]
    old_post = old["branches"]["matching_red_x"]["postflux_e2"]["public_full_binary_records"]
    assert sorted(row["public"]["charge"][1] for row in first_rows) == [0, 1]
    assert all(row["first_probability"] == 0.5 for row in first_rows)
    old_patterns = {tuple(row["charge"]) for row in old_post}
    assert old["branches"]["defer"]["postflux_e2"] is None
    assert old["branches"]["matching_red_x"]["public_action_edges"] == [0, 4]
    assert not any(old["branches"]["matching_red_x"]["private_residual_flux"])

    rows = []
    defer_controls = []
    for first in first_rows:
        first_charge = first["public"]["charge"]
        first_bit = first_charge[1]
        p2 = sign(first_bit)
        first_public = {
            "flux": first["public"]["flux"],
            "charge": first_charge,
            "vacuum": [1 - bit for bit in first_charge],
        }
        assert len(first_public["flux"]) == len(first_public["charge"]) == 24
        assert [i for i, bit in enumerate(first_public["flux"]) if bit] == [0, 2]
        defer_controls.append({
            "first_green_bit": first_bit,
            "public_action_edges": [],
            "postflux_e2": None,
        })
        for blue_bit in (0, 1):
            p = sign(blue_bit)
            charge = [0] * 24
            charge[0] = charge[2] = blue_bit
            assert tuple(charge) in old_patterns
            post_public = public_e2(charge)
            assert all(v + c == 1 for v, c in zip(post_public["vacuum"], post_public["charge"]))
            assert not any(post_public["flux"])
            rows.append({
                "first_green_bit": first_bit,
                "first_eigenvalue_p2": p2,
                "post_blue_common_bit": blue_bit,
                "post_eigenvalue_p": p,
                "first_probability": 0.5,
                "post_conditional_probability": 0.5,
                "joint_probability": 0.25,
                "first_public": first_public,
                "public_action_edges": [0, 4],
                "postflux_public": post_public,
                "private_symbolic_stabilizer_update": {
                    "after_first_A6": {
                        "first_green_measurement_eigenvalue": p2,
                        "blue_pair_generator_eigenvalue": 1,
                        "dressed_green_generator_eigenvalue": p2,
                    },
                    "after_matching_correction_A13": {
                        "blue_pair_generator_eigenvalue": 1,
                        "bare_green_generator_eigenvalue": 1,
                        "dressed_green_generator_eigenvalue": p2,
                        "remaining_Z_type_generator_eigenvalue": 1,
                    },
                    "measurement_rule": "Blue-star measurement anticommutes only with dressed-green generator; outcome p is equiprobable given p2 and replaces that generator.",
                    "after_blue_measurement_A14": {
                        "blue_0_generator_eigenvalue": p,
                        "blue_2_generator_eigenvalue": p,
                        "bare_green_generator_eigenvalue": 1,
                        "dressed_green_generator": "replaced",
                    },
                },
            })
    assert len(rows) == 4 and sum(row["joint_probability"] for row in rows) == 1
    for first_bit in (0, 1):
        conditional = [row for row in rows if row["first_green_bit"] == first_bit]
        assert len(conditional) == 2
        assert sum(row["post_conditional_probability"] for row in conditional) == 1
        assert {tuple(row["postflux_public"]["charge"]) for row in conditional} == old_patterns
    assert len(defer_controls) == 2 and all(row["postflux_e2"] is None for row in defer_controls)
    assert time.monotonic() - start < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_source_derived_local_symbolic_instrument_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": checks,
        "geometry": geometry,
        "conditioned_rows": rows,
        "defer_controls": defer_controls,
        "conditional_blue_bit_matrix_first_green_0_1_by_post_blue_0_1": [[0.5, 0.5], [0.5, 0.5]],
        "joint_first_green_by_post_blue": [[0.25, 0.25], [0.25, 0.25]],
        "inference_boundary": "The source diagrams and anticommuting-generator rule determine this ideal short-path local stabilizer instrument; they do not establish a general D4 tableau, global density-operator equality across p2 branches, arbitrary correction policy, noisy record, five-round transition or schedule risk.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - start, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
