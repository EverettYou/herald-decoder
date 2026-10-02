"""Validate signed GF(2) affine moments; resolve nine singleton/site-count cells."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8h-signed-affine-solver-gate-2026-09-27.json"
RESULT = LAB / "results/j8h-signed-affine-solver-gate-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8d_result": LAB / "results/j8d-winding-class-second-law-witness-2026-09-27.json",
    "j8f_result": LAB / "results/j8f-orbit-character-reuse-audit-2026-09-27.json",
    "j8g_result": LAB / "results/j8g-binary-constraint-rank-preflight-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "orbit_source": LAB / "scripts/run_j6m_periodic_operator_ground_orbit.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "compose_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
    "commute_source": LAB / "scripts/run_j8b_alternate_first_complete_second_laws.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def affine_solutions(vectors: list[int], target: int) -> list[int]:
    """Subset-bitmasks solving xor(vectors_i)=target, with kernel basis."""
    basis: dict[int, tuple[int, int]] = {}
    kernel = []
    for index, vector in enumerate(vectors):
        residual, combination = vector, 1 << index
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (residual, combination)
                break
            reduced, combination_bits = basis[pivot]
            residual ^= reduced
            combination ^= combination_bits
        if residual == 0:
            kernel.append(combination)
    particular, residual = 0, target
    while residual:
        pivot = residual.bit_length() - 1
        if pivot not in basis:
            return []
        reduced, combination_bits = basis[pivot]
        residual ^= reduced
        particular ^= combination_bits
    answers = []
    for choice in range(1 << len(kernel)):
        subset = particular
        for index, relation in enumerate(kernel):
            if (choice >> index) & 1:
                subset ^= relation
        assert 0 <= subset < (1 << len(vectors))
        assert _xor_selected(vectors, subset) == target
        answers.append(subset)
    assert len(set(answers)) == len(answers)
    return answers


def _xor_selected(vectors: list[int], subset: int) -> int:
    value = 0
    for index, vector in enumerate(vectors):
        if (subset >> index) & 1:
            value ^= vector
    return value


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    checks_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                     for name, path in INPUTS.items()}
    assert all(checks_before.values()), checks_before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8c_result", "j8d_result", "j8f_result", "j8g_result", "j7m_result", "j6l_result", "j6m_result")}
    assert old["j8g_result"]["status"] == "binary_constraint_rank_closed"
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    source = [branch for branch in old["j8c_result"]["new_support_branches"]
              if branch["cycle_length"] == 8]
    assert len(source) == 1 and len(source[0]["rows"]) == 54
    source_by_error = {tuple(row["candidate_error_red_edges_private"]): row for row in source[0]["rows"]}
    prior = {tuple(row["candidate_error_red_edges_private"]) for row in old["j8f_result"]["rows"]}
    assert len(prior) == 45
    missing = [row for row in source[0]["rows"] if tuple(row["candidate_error_red_edges_private"]) not in prior]
    assert len(missing) == budget["unresolved_supports"] == 9
    controls = old["j8d_result"]["rows"]
    assert len(controls) == budget["replay_control_supports"] == 4
    assert spec["actions"] == [cell["public_action_red_edges"] for cell in controls[0]["cells"]]
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    assert old["j8g_result"]["completed_supports"] == 54
    rank_by_error = {tuple(row["candidate_error_red_edges_private"]): row
                     for row in old["j8g_result"]["rows"]}
    counters = {"affine_signed_terms": 0, "direct_moment_spot_checks": 0,
                "replayed_complete_laws": 0, "new_complete_second_laws": 0,
                "histories": 0, "schedule_arms": 0, "bootstraps": 0}

    def signature(zmask: int) -> int:
        return sum(parity(zmask & flip) << i for i, flip in enumerate(flips))

    def signed_sum(first_ops, first_signatures, tail=()) -> int:
        product = compose(list(tail))
        choices = affine_solutions(first_signatures, signature(product[1]))
        assert len(choices) <= budget["max_affine_class_size"]
        total = 0
        for bits in choices:
            factors = [first_ops[i] for i in range(len(first_ops)) if (bits >> i) & 1]
            factors.extend(tail)
            sign, zmask, _ = compose(factors)
            assert signature(zmask) == 0
            total += sign
            counters["affine_signed_terms"] += 1
            assert counters["affine_signed_terms"] <= budget["max_orbit_moment_terms"]
            if counters["direct_moment_spot_checks"] < budget["max_direct_moment_spot_checks"]:
                assert sign == moment(factors, flips)
                counters["direct_moment_spot_checks"] += 1
        return total

    output = []
    for case_kind, case in [("control", row) for row in controls] + [("unresolved", row) for row in missing]:
        edges = case["error_edges_private"] if case_kind == "control" else case["candidate_error_red_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, first_means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in first_means.values())
        first_variable = sorted(site for site, mean in first_means.items() if mean == 0)
        if tuple(edges) in source_by_error:
            source_row = source_by_error[tuple(edges)]
            assert first_variable == source_row["first_variable_sites_private"]
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(left, right) for left in first_ops for right in first_ops)
        first_signatures = [signature(op[1]) for op in first_ops]
        first_sum = signed_sum(first_ops, first_signatures)
        first_mass = Fraction(first_sum, 1 << len(first_ops))
        expected_mass = (Fraction(case["first_public_mass"]) if case_kind == "control"
                         else Fraction(case["selected_allplus_first_mass"]))
        assert first_mass == expected_mass > 0
        if tuple(edges) in rank_by_error:
            rank_row = rank_by_error[tuple(edges)]
            assert len(first_variable) == rank_row["first_variable_site_count"]
            assert len(affine_solutions(first_signatures, 0)) == rank_row["first_signature_kernel_size"]
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(eligible_second) == budget["eligible_second_sites_per_cell"]
            second_ops = {site: conjugated_star(sites[site], residual) for site in eligible_second}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())

            def conditional(group: tuple[int, ...]) -> Fraction:
                product = compose([second_ops[site] for site in group])
                assert compose([product, product]) == (1, 0, 0)
                if any(not commute(product, first) for first in first_ops):
                    return Fraction(0)
                answer = Fraction(signed_sum(first_ops, first_signatures, (product,)), first_sum)
                assert -1 <= answer <= 1
                return answer

            single = {site: conditional((site,)) for site in eligible_second}
            assert all(value in (-1, 0, 1) for value in single.values())
            variable = sorted(site for site, value in single.items() if value == 0)
            fixed = {str(site): int(value == -1) for site, value in single.items() if value != 0}
            site_gate = len(variable) <= budget["max_variable_second_sites_per_cell"]
            if case_kind == "control":
                old_cell = case["cells"][action_index]
                assert variable == old_cell["variable_second_sites_private"]
                assert fixed == old_cell["deterministic_second_charge_bits"]
                assert second_flux == old_cell["second_public_flux"]
                moments = {(): Fraction(1)}
                for order in range(1, len(variable) + 1):
                    for group in itertools.combinations(variable, order):
                        moments[group] = conditional(group)
                reconstructed = {}
                for bits in itertools.product((0, 1), repeat=len(variable)):
                    probability = sum((value * (-1 if sum(bits[variable.index(site)] for site in group) % 2 else 1)
                                       for group, value in moments.items()), Fraction()) / (1 << len(variable))
                    assert 0 <= probability <= 1
                    if probability:
                        charges = [0] * 24
                        for site, bit in fixed.items():
                            charges[int(site)] = bit
                        for site, bit in zip(variable, bits):
                            charges[site] = bit
                        reconstructed[tuple(charges)] = probability
                expected = {tuple(row["public"]["charge"]): Fraction(row["conditional_probability"])
                            for row in old_cell["rows"]}
                assert reconstructed == expected
                counters["replayed_complete_laws"] += 1
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "variable_second_sites_private": variable,
                          "fixed_second_charge_bits_private": fixed,
                          "site_gate_pass": site_gate,
                          "replayed_existing_complete_law": case_kind == "control"})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
        output.append({"kind": case_kind, "error_edges_private": edges,
                       "first_public_mass": str(first_mass), "cells": cells})
    assert counters["replayed_complete_laws"] == 8
    assert counters["new_complete_second_laws"] == counters["histories"] == counters["schedule_arms"] == counters["bootstraps"] == 0
    assert counters["affine_signed_terms"] + counters["direct_moment_spot_checks"] <= budget["max_orbit_moment_terms"]
    checks_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                    for name, path in INPUTS.items()}
    assert all(checks_after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"], "status": "signed_affine_solver_gate_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": checks_before, "pinned_input_checks_after": checks_after,
            "control_supports": len(controls), "unresolved_supports": len(missing),
            "unresolved_action_cells": 2 * len(missing), "all_unresolved_site_gates_pass":
                all(cell["site_gate_pass"] for row in output if row["kind"] == "unresolved" for cell in row["cells"]),
            "rows": output, "counters": counters, "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "Four existing supports/eight existing complete laws replay exactly. Nine previously unresolved supports receive first masses and second-site singleton/site-count results only. No new complete second law, private-error information, risk, noisy JIT, L=3 or threshold is computed."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
