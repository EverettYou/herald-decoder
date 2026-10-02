"""Exact local X·CZ factor versus X-only diagnostic, not a D4 simulator."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6j-cz-star-factor-representation-2026-09-24.json"
RESULT = LAB / "results/j6j-cz-star-factor-representation-2026-09-24.json"
INPUTS = {
    "paper_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6i_result": LAB / "results/j6i-general-instrument-readiness-2026-09-24.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def action(state: tuple[int, int, int], labels: tuple[int, int, int],
           with_cz: bool) -> tuple[tuple[int, int, int], int]:
    blue, green, red = labels
    target = list(state)
    target[blue] ^= 1
    phase = -1 if with_cz and state[green] == state[red] == 1 else 1
    return tuple(target), phase


def expectation(states: tuple[tuple[int, int, int], ...],
                labels: tuple[int, int, int], with_cz: bool) -> Fraction:
    support = set(states)
    return sum((Fraction(phase, len(states)) for state in states
                for target, phase in [action(state, labels, with_cz)]
                if target in support), Fraction(0))


def rational(value: Fraction) -> str:
    return str(value)


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {name: digest(path) == contract["pinned_inputs"][f"{name}_sha256"]
              for name, path in INPUTS.items()}
    if not all(checks.values()):
        raise ValueError(f"Pinned input drift: {checks}")
    all_states = tuple((a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1))
    rows = []
    for labels in ((0, 1, 2), (2, 0, 1)):
        blue, green, red = labels
        coherent = all_states
        z_fixed = tuple(state for state in all_states if state[green] == state[red] == 0)
        for model, with_cz in (("source_factor", True), ("pauli_truncation", False)):
            for input_name, states in (("coherent_plus", coherent), ("z_fixed_control", z_fixed)):
                mean = expectation(states, labels, with_cz)
                p_plus, p_minus = (1 + mean) / 2, (1 - mean) / 2
                assert p_plus >= 0 and p_minus >= 0 and p_plus + p_minus == 1
                rows.append({"labels_b_g_r": list(labels), "model": model,
                             "input": input_name, "expectation": rational(mean),
                             "P_plus": rational(p_plus), "P_minus": rational(p_minus)})
        for state in all_states:
            target, phase = action(state, labels, True)
            back, back_phase = action(target, labels, True)
            assert back == state and phase * back_phase == 1
            reverse, reverse_phase = action(target, labels, True)
            assert reverse == state and reverse_phase == phase
        # A linear Z-character would obey f(1,1)=f(1,0)f(0,1)/f(0,0).
        phases = {(g, r): (-1 if g == r == 1 else 1)
                  for g in (0, 1) for r in (0, 1)}
        assert phases[(1, 1)] != phases[(1, 0)] * phases[(0, 1)] // phases[(0, 0)]
    assert len(rows) == 8
    for labels in ((0, 1, 2), (2, 0, 1)):
        def probability(model: str, input_name: str) -> str:
            return next(row["P_plus"] for row in rows if row["labels_b_g_r"] == list(labels)
                        and row["model"] == model and row["input"] == input_name)
        assert probability("source_factor", "coherent_plus") == "3/4"
        assert probability("pauli_truncation", "coherent_plus") == "1"
        assert probability("source_factor", "z_fixed_control") == "1"
        assert probability("pauli_truncation", "z_fixed_control") == "1"
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_exact_local_representation_gate_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": checks,
        "rows": rows,
        "operator_checks": {"involution": True, "hermitian": True,
                            "two_outcome_normalization": True,
                            "permutation_covariance": True,
                            "cz_phase_non_pauli_character": True},
        "inference_boundary": "This is an isolated A2 X·CZ factor on arbitrary product inputs, not a complete kagome star or D4 ground-space state. The full physical path/correction joint law and first-record-aware adapter remain unvalidated.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
