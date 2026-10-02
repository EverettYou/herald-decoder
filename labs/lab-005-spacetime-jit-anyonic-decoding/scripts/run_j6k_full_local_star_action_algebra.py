"""Exhaustive 12-qubit source-local D4 star/triangle operator algebra."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6k-full-local-star-action-algebra-2026-09-24.json"
RESULT = LAB / "results/j6k-full-local-star-action-algebra-2026-09-24.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "iqbal_pdf": ROOT / "references/iqbal2023-nonabelian-topological-order/paper.pdf",
    "j6j_result": LAB / "results/j6j-cz-star-factor-representation-2026-09-24.json",
}
OUTER_MASK = sum(1 << site for site in range(6, 12))
RED = (1, 3, 5)
GREEN = (0, 2, 4)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bit(state: int, site: int) -> int:
    return (state >> site) & 1


def ring_phase(state: int) -> int:
    return -1 if sum(bit(state, site) * bit(state, (site + 1) % 6)
                     for site in range(6)) % 2 else 1


def star(state: int) -> tuple[int, int]:
    return state ^ OUTER_MASK, ring_phase(state)


def triangle(state: int, color: str) -> int:
    sites = RED if color == "red" else GREEN
    return -1 if sum(bit(state, site) for site in sites) % 2 else 1


def error_mask(sites: tuple[int, ...]) -> int:
    return sum(1 << site for site in sites)


def conjugated_star(state: int, residual: tuple[int, ...]) -> tuple[int, int]:
    mask = error_mask(residual)
    target, phase = star(state ^ mask)
    return target ^ mask, phase


def neighbor_z_sites(residual: tuple[int, ...]) -> tuple[int, ...]:
    parity = {site: 0 for site in GREEN}
    for red in residual:
        for neighbor in ((red - 1) % 6, (red + 1) % 6):
            parity[neighbor] ^= 1
    return tuple(site for site in GREEN if parity[site])


def z_phase(state: int, sites: tuple[int, ...]) -> int:
    return -1 if sum(bit(state, site) for site in sites) % 2 else 1


def local_projector(state: int) -> dict[int, Fraction]:
    if triangle(state, "red") != 1 or triangle(state, "green") != 1:
        return {}
    target, phase = star(state)
    return {state: Fraction(1, 2), target: Fraction(-phase, 2)}


def apply_projector(vector: dict[int, Fraction]) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for state, amplitude in vector.items():
        for target, coefficient in local_projector(state).items():
            result[target] = result.get(target, Fraction(0)) + amplitude * coefficient
    return {state: amplitude for state, amplitude in result.items() if amplitude}


def run() -> dict:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    checks = {key: digest(path) == contract["pinned_inputs"][f"{key}_sha256"]
              for key, path in INPUTS.items()}
    if not all(checks.values()):
        raise ValueError(f"Pinned input drift: {checks}")
    basis_count = 1 << 12
    assert basis_count == contract["budget"]["max_basis_states"]
    charge_sector_rank = 0
    for state in range(basis_count):
        target, phase = star(state)
        back, back_phase = star(target)
        assert back == state and phase * back_phase == 1
        assert ring_phase(target) == phase  # real-symmetric star matrix
        assert triangle(target, "red") == triangle(state, "red")
        assert triangle(target, "green") == triangle(state, "green")
        projected = apply_projector({state: Fraction(1)})
        assert apply_projector(projected) == projected
        if triangle(state, "red") != 1 or triangle(state, "green") != 1:
            assert not projected
        elif state < target:
            charge_sector_rank += 1

    rows = []
    for physical in ((1, 3), (1, 5)):
        for label, action in (("none", ()), ("matched", physical),
                              ("partial_first_red", (physical[0],))):
            residual = tuple(sorted(set(physical) ^ set(action)))
            dressed = neighbor_z_sites(residual)
            red_sign = -1 if len(residual) % 2 else 1
            for state in range(basis_count):
                target, phase = conjugated_star(state, residual)
                base_target, base_phase = star(state)
                assert target == base_target
                assert phase == base_phase * z_phase(state, dressed)
                assert triangle(state ^ error_mask(residual), "red") == red_sign * triangle(state, "red")
                assert triangle(state ^ error_mask(residual), "green") == triangle(state, "green")
            if label == "matched":
                assert residual == () and dressed == () and red_sign == 1
            rows.append({
                "physical_red_ring_sites": list(physical),
                "action": label,
                "action_red_ring_sites": list(action),
                "residual_red_ring_sites": list(residual),
                "star_z_dressing_green_ring_sites": list(dressed),
                "red_triangle_conjugation_sign": red_sign,
                "green_triangle_conjugation_sign": 1,
                "public_E2_generated": False,
                "basis_states_checked": basis_count,
            })
    assert len(rows) == contract["budget"]["max_branch_cells"]
    assert charge_sector_rank == 512
    assert time.monotonic() - started < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_exact_source_local_star_action_algebra_only",
        "contract_sha256": digest(CONTRACT),
        "pinned_input_checks": checks,
        "qubits": 12,
        "basis_states_checked": basis_count,
        "local_A4_charge_projector_rank": charge_sector_rank,
        "operator_checks": {"star_hermitian_involution": True,
                            "triangles_commute_with_star": True,
                            "A4_projector_idempotent": True,
                            "A4_projector_zero_outside_triangle_vacuum": True},
        "branch_rows": rows,
        "inference_boundary": "Complete one-star 12-qubit operator algebra only. Red ring sites are not embedded into periodic_honeycomb(2) edge IDs, neighboring stars and global ground-state constraints are absent, and no first-to-second public-record conditional probabilities follow.",
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
    print(RESULT)
