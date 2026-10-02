"""Exact one-site projector identity on J7N's fixed-future four-cell matrix."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7d_cross_round_commutation_screen import cross_vacuum_anticommutes


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7o-witness-projector-reduction-2026-09-26.json"
RESULT = LAB / "results/j7o-witness-projector-reduction-2026-09-26.json"
INPUTS = {
    "j7n_result": LAB / "results/j7n-fixed-future-next-first-feasibility-2026-09-26.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "commutation_source": LAB / "scripts/run_j7d_cross_round_commutation_screen.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hermitian_involution(op: tuple[int, int, int]) -> bool:
    """Real-sign ZX is Hermitian and squares to I iff X/Z overlap is even."""
    sign, zmask, xmask = op
    return sign in (-1, 1) and parity(zmask & xmask) == 0


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    matrix_spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7n = json.loads(INPUTS["j7n_result"].read_text())
    j7m = json.loads(INPUTS["j7m_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    assert j7n["status"] == "fixed_future_structural_cost_audit_closed"
    assert j7m["status"] == "five_site_complete_second_charge_law_closed"
    assert j7m["same_second_public_flux"]
    assert Fraction(j7m["first_public_mass"]) == Fraction(1, 4)
    assert matrix_spec["public_actions"] == [row["public_action_red_edges"]
                                             for row in j7m["cells"]]
    assert matrix_spec["public_actions"] == [[0], [1, 30, 32, 34, 35]]
    assert matrix_spec["matched_later_fault_keys_private"] == [[0], [4]]
    assert len(j7n["matrix"]) == budget["max_action_future_cells"] == 4
    _red, sites, _flips, _pairs = setup(embedding, orbit)
    assert len(sites) == 24
    rows = []
    pair_checks = 0
    prefix_checks = 0
    for future in matrix_spec["matched_later_fault_keys_private"]:
        for action, prior in zip(matrix_spec["public_actions"], j7m["cells"]):
            cell = next(row for row in j7n["matrix"]
                        if row["public_action_red_edges"] == action
                        and row["future_physical_red_edges_private"] == future)
            assert cell["positive_second_prefixes"] == len(prior["rows"])
            assert cell["second_next_anticommuting_pair_count"] == 1
            witness = cell["first_anticommuting_witness_private"]
            assert witness == matrix_spec["expected_unique_witnesses_by_future"][str(future)]
            assert witness[0] in cell["second_eligible_sites_private"]
            assert witness[1] in cell["next_eligible_sites_private"]
            assert sorted(set(cell["final_red_edges_private"])
                          ^ set(future)) == prior["residual_red_edges_private"]
            second_ops = {s: conjugated_star(sites[s],
                          _edge_mask_from_rows(cell, "second", embedding))
                          for s in cell["second_eligible_sites_private"]}
            next_ops = {s: conjugated_star(sites[s],
                        _edge_mask_from_rows(cell, "next", embedding))
                        for s in cell["next_eligible_sites_private"]}
            next_op = next_ops[witness[1]]
            assert all(hermitian_involution(op) for op in second_ops.values())
            assert all(hermitian_involution(op) for op in next_ops.values())
            second_sites = sorted(second_ops)
            for i, left in enumerate(second_sites):
                for right in second_sites[i + 1:]:
                    pair_checks += 1
                    assert pair_checks <= budget["max_operator_pair_checks"]
                    assert not cross_vacuum_anticommutes(second_ops[left],
                                                         second_ops[right])
            witnesses = []
            for second_site, second_op in second_ops.items():
                for next_site, candidate in next_ops.items():
                    pair_checks += 1
                    assert pair_checks <= budget["max_operator_pair_checks"]
                    if cross_vacuum_anticommutes(second_op, candidate):
                        witnesses.append([second_site, next_site])
            assert witnesses == [witness]
            assert cell["next_public_flux"][witness[1]] == 0
            mass = Fraction()
            witness_bits = set()
            for second_row in prior["rows"]:
                prefix_checks += 1
                assert prefix_checks <= budget["max_positive_prefix_checks"]
                public = second_row["public"]
                assert set(public) == {"flux", "charge", "vacuum"}
                assert all(len(public[field]) == 24 for field in public)
                assert public["flux"] == prior["second_public_flux"]
                assert public["vacuum"] == [1 - bit for bit in public["charge"]]
                bit = public["charge"][witness[0]]
                assert bit in (0, 1) and public["flux"][witness[0]] == 0
                witness_bits.add(bit)
                probability = Fraction(second_row["conditional_probability"])
                assert probability > 0
                mass += probability
                # Complete second measurement includes P_a at the witness,
                # even when its outcome was deterministic and omitted from
                # variable-only numerical blocks. P_a B P_a=0 because {A,B}=0.
                # Therefore Tr(P_b rho_prefix)=(1+b Tr(B rho_prefix))/2=1/2.
            assert mass == 1
            rows.append({"public_action_red_edges": action,
                         "future_physical_red_edges_private": future,
                         "second_next_witness_private": witness,
                         "positive_complete_second_prefixes": len(prior["rows"]),
                         "second_witness_charge_bits_seen": sorted(witness_bits),
                         "conditional_next_site_private": witness[1],
                         "conditional_next_charge_probabilities_for_every_prefix":
                             {"0": "1/2", "1": "1/2"},
                         "basis": "P_a B P_a=0 for measured second A and next B"})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert prefix_checks == budget["max_positive_prefix_checks"] == 68
    assert pair_checks <= budget["max_operator_pair_checks"]
    for future in matrix_spec["matched_later_fault_keys_private"]:
        next_fluxes = [cell["next_public_flux"] for cell in j7n["matrix"]
                       if cell["future_physical_red_edges_private"] == future]
        assert len(next_fluxes) == 2 and next_fluxes[0] == next_fluxes[1]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "witness_one_site_projector_identity_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "cells": rows, "operator_pair_checks": pair_checks,
            "positive_prefix_checks": prefix_checks,
            "identity": "For Hermitian involutions A,B with AB=-BA, P_a=(I+aA)/2 gives P_a B P_a=0. Each positive complete second record includes measured A; next B has conditional mean 0 and each charge bit has probability 1/2.",
            "interpretation_boundary": "Only the one-site next charge at site 1 is fixed; other next sites and correlations remain unresolved. No complete next law, information/risk/policy benefit, or noisy schedule result.",
            "counters": {"ordered_moment_terms_evaluated": 0,
                         "next_first_joint_laws_evaluated": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": round(time.process_time() - started, 6)}


def _edge_mask_from_rows(cell: dict, round_name: str, embedding: dict) -> int:
    """Replay J7N's private edge support using frozen red-edge identities."""
    red = {qubit["lab004_red_edge_id"]: qubit["id"]
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    assert len(red) == 36
    if round_name == "next":
        edges = cell["final_red_edges_private"]
    else:
        edges = sorted(set(cell["final_red_edges_private"])
                       ^ set(cell["future_physical_red_edges_private"]))
    result = 0
    for edge in edges:
        result ^= 1 << red[edge]
    return result


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
