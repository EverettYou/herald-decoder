"""Exact finite same-future-key total-action law under the J7G ideal model."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import (
    canonical_record, make_token, payload_digest, setup,
)
from run_j7b_future_fault_next_first_and_caller_gate import Censor
from run_j7c_three_edge_history_memory_discriminator import completion, rejected
from run_j7e_two_edge_complete_next_law import checked_exact, full_law


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7i-same-future-total-action-law-2026-09-26.json"
RESULT = LAB / "results/j7i-same-future-total-action-law-2026-09-26.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7f_result": LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json",
    "j7g_result": LAB / "results/j7g-three-edge-matched-complete-next-law-2026-09-25.json",
    "j7h_result": LAB / "results/j7h-action-future-identifiability-audit-2026-09-26.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}
TRIAL_ID = "j7i-same-future-total-action-exact"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_law(rows: list[dict], first_mass: Fraction) -> dict[str, Fraction]:
    law: dict[str, Fraction] = {}
    for row in rows:
        for nxt in row["next_rows"]:
            key = payload_digest(nxt["next_first_public"])
            mass = Fraction(row["prefix_mass"]) * Fraction(
                nxt["conditional_probability"]) / first_mass
            law[key] = law.get(key, Fraction()) + mass
    assert sum(law.values(), Fraction()) == 1
    return law


def diagonal_replay(rows: list[dict], reference: dict) -> None:
    old = reference["rows"]
    assert len(rows) == len(old)
    def canonical(which):
        return sorted((
            payload_digest(row["second_public"]),
            row["prefix_mass"],
            tuple(sorted((payload_digest(nxt["next_first_public"]),
                          nxt["conditional_probability"])
                         for nxt in row["next_rows"])),
        ) for row in which)
    assert canonical(rows) == canonical(old)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget, spec = contract["budget"], contract["matrix"]
    pins_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                   for name, path in INPUTS.items()}
    assert all(pins_before.values()), pins_before
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    j7f = json.loads(INPUTS["j7f_result"].read_text())
    j7g = json.loads(INPUTS["j7g_result"].read_text())
    j7h = json.loads(INPUTS["j7h_result"].read_text())
    assert j7g["status"] == "exact_three_edge_one_first_complete_public_contrast_closed"
    assert j7h["status"] == "additive_red_x_action_future_identifiability_boundary_passed"
    assert spec["public_actions"] == [[0], [4]]
    assert spec["matched_future_fault_keys_private"] == [[0], [4]]
    red, sites, flips, pairs = setup(embedding, orbit)
    physical, first_flux = red_boundary(red, spec["initial_physical_red_edges_private"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [s for s, bit in enumerate(first_flux) if bit == 0]
    first_sites = spec["first_variable_sites_private"]
    assert [s for s, mean in first_means.items() if mean == 0] == first_sites
    frozen = next(row for row in j7f["rows"] if row["fixture"] == "three_edge_chain")
    first = canonical_record(frozen["first_public"])
    assert first == j7g["matrix"]["first_public"]
    assert first["flux"] == first_flux
    assert set(first) == {"flux", "charge", "vacuum"}
    assert all(len(bits) == 24 for bits in first.values())
    first_ops = [conjugated_star(sites[s], physical) for s in first_sites]
    first_bits = tuple(spec["first_bits"])
    first_block = (first_ops, first_bits)
    usage = {"ordered_moment_terms": 0, "second_rows": 0, "next_rows": 0}
    first_mass = checked_exact([first_block], flips, usage, budget, started)
    assert first_mass == Fraction(spec["first_probability"]) == Fraction(1, 4)
    assert first_mass == Fraction(j7g["matrix"]["first_mass"])
    ledger = {(tuple(row["public_action_red_edges"]),
               tuple(row["future_physical_red_edges_private"])): row
              for row in j7h["primary_matrix"]}
    assert len(ledger) == 4
    cells = []
    example = None
    try:
        for action in spec["public_actions"]:
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            _, second_flux = red_boundary(red,
                sorted(set(spec["initial_physical_red_edges_private"]) ^ set(action)))
            second_eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert second_eligible == [s for s, bit in enumerate(second_flux) if bit == 0]
            second_variable, second_rows = full_law(
                blocks=[first_block], candidate_sites=second_eligible,
                error_mask=residual, flux=second_flux, sites=sites, flips=flips,
                usage=usage, budget=budget, started=started,
                variable_cap="max_variable_second_sites", row_key="second_rows")
            assert sum((Fraction(row["conditional_probability"])
                        for row in second_rows), Fraction()) == 1
            for future in spec["matched_future_fault_keys_private"]:
                future_mask, _ = red_boundary(red, future)
                final = residual ^ future_mask
                final_edges = sorted(set(spec["initial_physical_red_edges_private"])
                                     ^ set(action) ^ set(future))
                expected_mask, next_flux = red_boundary(red, final_edges)
                assert final == expected_mask
                ledger_row = ledger[(tuple(action), tuple(future))]
                assert final_edges == ledger_row["final_red_edges_private"]
                assert next_flux == ledger_row["final_public_flux"]
                next_eligible, _ = sector_sites(sites, final, flips, pairs)
                assert next_eligible == [s for s, bit in enumerate(next_flux) if bit == 0]
                future_key = f"j7i-future-physical-red-{future[0]}"
                rows = []
                for second_row in second_rows:
                    second = canonical_record(second_row["public"])
                    second_ops = [conjugated_star(sites[s], residual)
                                  for s in second_variable]
                    second_bits = tuple(1 if second["charge"][s] == 0 else -1
                                        for s in second_variable)
                    blocks = [first_block, (second_ops, second_bits)]
                    prefix_mass = checked_exact(blocks, flips, usage, budget, started)
                    assert prefix_mass == first_mass * Fraction(
                        second_row["conditional_probability"])
                    next_variable, next_rows = full_law(
                        blocks=blocks, candidate_sites=next_eligible,
                        error_mask=final, flux=next_flux, sites=sites,
                        flips=flips, usage=usage, budget=budget, started=started,
                        variable_cap="max_variable_next_sites", row_key="next_rows")
                    token = make_token(
                        trial_id=TRIAL_ID, first_public=first,
                        second_public=second, action_edges=tuple(action),
                        allowed_actions=((0,), (4,)), physical_mask=physical,
                        action_mask=action_mask,
                        first_projectors=tuple((s, *op, bit) for s, op, bit
                            in zip(first_sites, first_ops, first_bits)),
                        second_projectors=tuple((s, *op, bit) for s, op, bit
                            in zip(second_variable, second_ops, second_bits)))
                    support = {payload_digest(row["public"]) for row in next_rows}
                    for next_row in next_rows:
                        nxt = next_row.pop("public")
                        next_row["next_first_public"] = nxt
                        args = dict(token=token, first_public=first,
                                    second_public=second,
                                    action_edges=tuple(action),
                                    future_key=future_key,
                                    expected_future_key=future_key,
                                    next_public=nxt, support=support)
                        next_row["public_completion"] = completion(**args)
                        assert next_row["public_completion"] == completion(**args)
                        if example is None:
                            example = args
                    rows.append({"first_public": first, "second_public": second,
                                 "public_action_red_edge_ids": action,
                                 "second_variable_sites_private": second_variable,
                                 "next_variable_sites_private": next_variable,
                                 "prefix_mass": str(prefix_mass),
                                 "next_rows": next_rows})
                assert sum((Fraction(row["prefix_mass"]) for row in rows),
                           Fraction()) == first_mass
                if action == [0] and future == [0]:
                    diagonal_replay(rows, j7g["matrix"]["branch_a"])
                if action == [4] and future == [4]:
                    diagonal_replay(rows, j7g["matrix"]["branch_b"])
                cells.append({"public_action_red_edges": action,
                              "future_physical_red_edges_private": future,
                              "final_red_edges_private": final_edges,
                              "final_public_flux": next_flux,
                              "positive_second_prefixes": len(rows),
                              "rows": rows})
        assert len(cells) == 4 and example is not None
        changed_first = canonical_record(first)
        changed_first["charge"][1] ^= 1
        changed_first["vacuum"][1] ^= 1
        changed_second = canonical_record(example["second_public"])
        site = cells[0]["rows"][0]["second_variable_sites_private"][0]
        changed_second["charge"][site] ^= 1
        changed_second["vacuum"][site] ^= 1
        controls = {
            "swapped_action": rejected(completion, **{**example,
                "action_edges": (4,)}),
            "tampered_first": rejected(completion, **{**example,
                "first_public": changed_first}),
            "tampered_second": rejected(completion, **{**example,
                "second_public": changed_second}),
            "wrong_future_key": rejected(completion, **{**example,
                "future_key": "wrong"}),
            "private_field_injection": rejected(completion, **{**example,
                "next_public": {**example["next_public"],
                                "physical_edges": [0, 4, 3]}}),
        }
        assert all(controls.values())
        comparisons = []
        for future in spec["matched_future_fault_keys_private"]:
            left, right = (next(cell for cell in cells
                                if cell["public_action_red_edges"] == action
                                and cell["future_physical_red_edges_private"] == future)
                           for action in spec["public_actions"])
            left_law = public_law(left["rows"], first_mass)
            right_law = public_law(right["rows"], first_mass)
            tv = sum((abs(left_law.get(key, Fraction()) -
                          right_law.get(key, Fraction()))
                       for key in set(left_law) | set(right_law)), Fraction()) / 2
            flux_separated = left["final_public_flux"] != right["final_public_flux"]
            if flux_separated:
                assert tv == 1
                assert not (set(left_law) & set(right_law))
            comparisons.append({"future_physical_red_edges_private": future,
                                "exact_full_public_total_variation": str(tv),
                                "distinct_final_public_flux": flux_separated,
                                "left_public_support_size": len(left_law),
                                "right_public_support_size": len(right_law),
                                "claim_boundary": "Finite ideal total action effect; deterministic flux separation is not a herald-charge or decoder-risk advantage"})
        assert time.process_time() - started <= budget["max_cpu_seconds"]
        status = "exact_same_future_total_action_law_closed"
    except Censor as error:
        status = "exact_same_future_total_action_law_censored"
        controls, comparisons = {}, []
        return {"schema_version": 1, "id": contract["id"], "status": status,
                "reason": str(error), "contract_sha256": digest(CONTRACT),
                "pinned_input_checks_before": pins_before, "cells": cells,
                "usage": usage, "counters": {"stochastic_histories": 0,
                "schedule_arm_evaluations": 0, "bootstrap_replicates": 0},
                "cpu_seconds": round(time.process_time() - started, 6)}
    pins_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                  for name, path in INPUTS.items()}
    assert all(pins_after.values()), pins_after
    return {"schema_version": 1, "id": contract["id"], "status": status,
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": pins_before,
            "pinned_input_checks_after": pins_after,
            "first_public": first, "first_mass": str(first_mass),
            "cells": cells, "same_future_action_comparisons": comparisons,
            "binding_controls": controls, "j7g_diagonal_replay": True,
            "usage": usage,
            "counters": {"stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "frozen_caller_gate": "unchanged_not_integrated_stateful_future_first_callback",
            "inference_boundary": "One selected first record, two same-future total-action columns, exact ideal full public laws. Flux-separated total effects do not imply herald-charge information gain, logical-risk benefit, noisy JIT performance, or general D4 channel validity.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
