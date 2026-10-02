"""Pinned, zero-sampling audit of the next D4 instrument prerequisites."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6i-general-instrument-readiness-2026-09-24.json"
RESULT = LAB / "results/j6i-general-instrument-readiness-2026-09-24.json"
INPUTS = {
    "paper_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6h_result": LAB / "results/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json",
    "d4_pipeline": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_pipeline.py",
    "integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(path: Path, name: str) -> ast.FunctionDef:
    matches = [node for node in ast.parse(path.read_text()).body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {name} in {path}")
    return matches[0]


def called_with(node: ast.FunctionDef, callee: str) -> list[ast.Call]:
    return [item for item in ast.walk(node) if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name) and item.func.id == callee]


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
              for key, path in INPUTS.items()}
    if not all(checks.values()):
        raise ValueError(f"Pinned input drift: {checks}")
    local = json.loads(INPUTS["j6h_result"].read_text())
    rows = local["conditioned_rows"]
    assert len(rows) == 4
    assert sum(row["joint_probability"] for row in rows) == 1
    assert all(sum(row["post_conditional_probability"] for row in rows
                   if row["first_green_bit"] == bit) == 1 for bit in (0, 1))

    sampler = function(INPUTS["d4_pipeline"], "sample_postflux_charge_outcomes")
    sampler_args = [arg.arg for arg in sampler.args.args + sampler.args.kwonlyargs]
    lab4 = function(INPUTS["d4_pipeline"], "decode_physical_error_with_keys")
    lab5 = function(INPUTS["integrated_history"], "provide_action_conditioned_second_record")
    calls4 = called_with(lab4, "sample_postflux_charge_outcomes")
    calls5 = called_with(lab5, "sample_postflux_charge_outcomes")
    assert len(calls4) == len(calls5) == 1
    keywords4 = [keyword.arg for keyword in calls4[0].keywords]
    keywords5 = [keyword.arg for keyword in calls5[0].keywords]
    assert "first_charge" not in sampler_args
    assert not any("first" in (name or "") for name in keywords4 + keywords5)
    assert "relations" in sampler_args and "seed" in sampler_args
    assert "second_exogenous_key" in ast.unparse(lab5)
    assert "flux_action_digest" in ast.unparse(lab5)
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_readiness_audit_general_instrument_unvalidated",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": checks,
        "matrix": {
            "illustrated_local_matched_action": "J6H four-row joint/conditional normalization reconfirmed; source-derived only",
            "general_geometry_or_other_action": "No validated executable lattice-wide D4 operator-state update is supplied by pinned production modules or J6H",
            "lab004_postflux_sampler": {"parameters": sampler_args, "call_keywords": keywords4,
                                         "first_public_record_input": False},
            "lab005_second_record_adapter": {"call_keywords": keywords5,
                                             "first_public_record_input_to_sampler": False,
                                             "action_and_exogenous_key_binding": True}
        },
        "inference_boundary": "A missing first-record input is an interface coverage gap, not proof that the parity sampler has wrong probabilities on any particular geometry. A2/A4 operators require a separate lattice-wide state derivation and exact fixture before a general physical schedule claim.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
