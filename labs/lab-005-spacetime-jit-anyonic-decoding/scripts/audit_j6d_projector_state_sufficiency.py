"""Exact, zero-sampling necessary-condition audit for the J6D state boundary."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6d-projector-state-sufficiency-2026-09-24.json"
RESULT = LAB / "results/j6d-projector-state-sufficiency-2026-09-24.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pinned = contract["upstream"]
    paths = {
        "j6c_result": LAB / pinned["j6c_result"],
        "integrated_history_source": LAB / "scripts/d4_integrated_history.py",
        "lab004_pipeline": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_pipeline.py",
        "lab004_postflux": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_postflux.py",
    }
    hash_keys = {
        "j6c_result": "j6c_sha256",
        "integrated_history_source": "integrated_history_source_sha256",
        "lab004_pipeline": "lab004_pipeline_sha256",
        "lab004_postflux": "lab004_postflux_sha256",
    }
    checks = {key: digest(path) == pinned[hash_keys[key]] for key, path in paths.items()}
    if not all(checks.values()):
        raise ValueError(f"pinned input mismatch: {checks}")
    j6c = json.loads(paths["j6c_result"].read_text())
    checks["j6c_passed"] = j6c.get("status") == "passed_deterministic_interface_only"
    if not checks["j6c_passed"]:
        raise ValueError(f"upstream J6C status unresolved: {j6c.get('status')}")

    # GF(2) Pauli-X chain bookkeeping, not a D4 fusion/charge calculation.
    chain_cases = {
        "no_fault_no_action": 0 ^ 0 ^ 0,
        "one_fault_no_action": 0 ^ 1 ^ 0,
        "one_fault_cancelling_action": 0 ^ 1 ^ 1,
    }
    checks["chain_xor_limits"] = chain_cases == {
        "no_fault_no_action": 0,
        "one_fault_no_action": 1,
        "one_fault_cancelling_action": 0,
    }

    # Generic C^3 Hilbert-space witness; these basis vectors are NOT D4 labels.
    # Pi_x spans |0>,|1>; U_a swaps |1> and |2>; Pi_y selects |2>.
    transition = (0, 2, 1)
    initial_states = (0, 1)
    next_y_probabilities = [int(transition[state] == 2) for state in initial_states]
    compressed_operator_diagonal = next_y_probabilities
    checks["generic_rank_two_non_lumpability"] = (
        next_y_probabilities == [0, 1]
        and compressed_operator_diagonal[0] != compressed_operator_diagonal[1]
    )
    checks["within_budget"] = time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    if not all(checks.values()):
        raise ValueError(f"exact check failed: {checks}")

    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_source_sufficiency_audit_only",
        "contract_sha256": digest(CONTRACT),
        "input_hash_checks": checks,
        "exact_matrix": {
            "red_x_chain_bookkeeping": chain_cases,
            "generic_projector_example": {
                "dimension": 3,
                "current_coarse_subspace_basis": [0, 1],
                "action_unitary_basis_permutation": list(transition),
                "next_projector_basis": [2],
                "future_y_probability_for_same_label_states": next_y_probabilities,
                "compressed_operator_diagonal": compressed_operator_diagonal,
                "necessary_condition": "Pi_x U^dagger Pi_y U Pi_x = k Pi_x for every target y, action, fault, and admitted state; violated by this generic witness only"
            }
        },
        "source_boundary": {
            "jing_2025_appendix_a4": "post-flux charge parity on physical-plus-correction union within a measurement episode; no arbitrary cross-round action-conditioned hidden-state kernel",
            "jing_2025_appendix_d": "time-ordered errors and syndrome projectors; requires a propagated state for repeated rounds",
            "jing_2026_appendix_b": "complete local D(G) projector family; completeness does not by itself prove coarse-label Markov lumpability",
            "jing_2026_appendix_d2": "ordered density-channel composition for measurement/correction; not a supplied three-label stochastic transition table",
            "lab004_postflux": "static same-episode action-conditioned parity sampler, not propagated hidden state",
            "lab005_integrated_history": "precomputed action-invariant physical/hidden first-record history"
        },
        "conclusion": "The currently cited sources and pinned implementation do not specify a unique numeric cross-round vacuum/m_flux/e_charge action-conditioned kernel. This is lack of derivation, not proof that the physical D4 coarse labels fail lumpability.",
        "next_gate": "Derive and preregister a geometry-matched two-round D4 projector/density-state fixture with explicit action, state update, first/second public records, and no-action/cancelling-action limits before any numeric kernel or integrated-caller claim.",
        "claim_boundary": "Only exact generic necessary-condition and source-provenance audit; no D4-specific counterexample, fusion probability, schedule performance, or threshold.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - started, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
