"""Exact full-public two-edge cross-round Born-law discriminator."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import (
    canonical_record, make_token, payload_digest, setup,
)
from run_j7b_future_fault_next_first_and_caller_gate import Censor, exact
from run_j7c_three_edge_history_memory_discriminator import completion, rejected


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7e-two-edge-complete-next-law-2026-09-25.json"
RESULT = LAB / "results/j7e-two-edge-complete-next-law-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6o_result": LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json",
    "j7c_result": LAB / "results/j7c-three-edge-history-memory-discriminator-2026-09-25.json",
    "j7d_result": LAB / "results/j7d-cross-round-commutation-screen-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}
TRIAL_ID = "j7e-two-edge-exact"
FUTURE_KEYS = {"A": "j7e-fault-edge-0", "B": "j7e-fault-edge-4"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_exact(blocks, flips, usage, budget, started):
    return exact(blocks, flips, usage, budget, started)


def full_law(*, blocks, candidate_sites, error_mask, flux, sites, flips,
             usage, budget, started, variable_cap, row_key):
    denominator = checked_exact(blocks, flips, usage, budget, started)
    assert denominator > 0
    fixed, variable, operators = {}, [], {}
    for site in candidate_sites:
        op = conjugated_star(sites[site], error_mask)
        operators[site] = op
        plus = checked_exact(blocks + [([op], (1,))], flips, usage, budget,
                             started) / denominator
        if not 0 <= plus <= 1:
            raise ValueError("invalid one-site Born marginal")
        if plus in (0, 1):
            fixed[site] = int(plus == 0)
        else:
            variable.append(site)
    if len(variable) > budget[variable_cap]:
        raise Censor("registered_" + variable_cap)
    variable_ops = [operators[s] for s in variable]
    rows = []
    mass = Fraction()
    for bits in assignments(len(variable)):
        joint = checked_exact(blocks + [(variable_ops, bits)], flips, usage,
                              budget, started)
        if joint < 0:
            raise ValueError("negative exact joint mass")
        conditional = joint / denominator
        mass += conditional
        if not conditional:
            continue
        usage[row_key] += 1
        if usage[row_key] > budget["max_positive_" + row_key]:
            raise Censor("registered_" + row_key)
        charge = [0] * 24
        for site, bit in fixed.items():
            charge[site] = bit
        for site, bit in zip(variable, bits):
            charge[site] = int(bit == -1)
        rows.append({"public": public_record(flux, charge),
                     "conditional_probability": str(conditional)})
    if mass != 1 or not rows:
        raise ValueError("incomplete full public Born law")
    return variable, rows


def run_matrix(contract, prior, red, sites, flips, pairs, started):
    spec, budget = contract["matrix"], contract["budget"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [s for s, bit in enumerate(first_flux) if not bit]
    assert [s for s, mean in first_means.items() if mean == 0] == [1]
    assert all(mean == 1 for site, mean in first_means.items() if site != 1)
    first_op = conjugated_star(sites[1], physical)
    reference_first = {payload_digest(row["first_public"]): row["first_public"]
                       for row in prior["public_law_rows"] if row["action"] == "defer"}
    assert len(reference_first) == 2
    usage = {"ordered_moment_terms": 0, "second_rows": 0, "next_rows": 0}
    branches = {}
    controls_example = None
    try:
        for label in ("A", "B"):
            branch = spec["branch_" + label.lower()]
            action = tuple(branch["public_action_red_edges"])
            future = branch["future_physical_red_edges_private"]
            action_mask, _ = red_boundary(red, list(action))
            future_mask, _ = red_boundary(red, future)
            residual = physical ^ action_mask
            final = residual ^ future_mask
            assert final == physical
            residual_edges = branch["residual_red_edges_private"]
            _, second_flux = red_boundary(red, residual_edges)
            second_eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert second_eligible == [s for s, bit in enumerate(second_flux) if not bit]
            next_eligible, _ = sector_sites(sites, final, flips, pairs)
            assert next_eligible == first_eligible
            prior_rows = []
            for first_bit in (1, -1):
                charge = [0] * 24
                charge[1] = int(first_bit == -1)
                first = public_record(first_flux, charge)
                assert payload_digest(first) in reference_first
                blocks_first = [([first_op], (first_bit,))]
                first_mass = checked_exact(blocks_first, flips, usage, budget, started)
                assert first_mass == Fraction(1, 2)
                second_variable, second_rows = full_law(
                    blocks=blocks_first, candidate_sites=second_eligible,
                    error_mask=residual, flux=second_flux, sites=sites,
                    flips=flips, usage=usage, budget=budget, started=started,
                    variable_cap="max_variable_second_sites", row_key="second_rows")
                if label == "A":
                    reference = {payload_digest(row["second_public"]): Fraction(
                        str(row["second_conditional_probability"]))
                        for row in prior["public_law_rows"]
                        if row["action"] == "partial" and row["first_public"] == first}
                    assert len(reference) == len(second_rows)
                    assert {payload_digest(row["public"]): Fraction(
                        row["conditional_probability"]) for row in second_rows} == reference
                for second_row in second_rows:
                    second = canonical_record(second_row["public"])
                    second_bits = tuple(1 if second["charge"][s] == 0 else -1
                                        for s in second_variable)
                    second_ops = [conjugated_star(sites[s], residual)
                                  for s in second_variable]
                    blocks = blocks_first + [(second_ops, second_bits)]
                    prefix_mass = checked_exact(blocks, flips, usage, budget,
                                                started)
                    assert prefix_mass == first_mass * Fraction(
                        second_row["conditional_probability"])
                    # On unchanged residual support, measured variable
                    # projectors repeat with probability one.
                    for op, bit in zip(second_ops, second_bits):
                        assert checked_exact(blocks + [([op], (bit,))], flips,
                            usage, budget, started) == prefix_mass
                        assert checked_exact(blocks + [([op], (-bit,))], flips,
                            usage, budget, started) == 0
                    next_variable, next_rows = full_law(
                        blocks=blocks, candidate_sites=next_eligible,
                        error_mask=final, flux=first_flux, sites=sites,
                        flips=flips, usage=usage, budget=budget, started=started,
                        variable_cap="max_variable_next_sites", row_key="next_rows")
                    token = make_token(trial_id=TRIAL_ID, first_public=first,
                        second_public=second, action_edges=action,
                        allowed_actions=((0,), (4,)), physical_mask=physical,
                        action_mask=action_mask,
                        first_projectors=((1, *first_op, first_bit),),
                        second_projectors=tuple((s, *op, bit) for s, op, bit
                                                in zip(second_variable, second_ops, second_bits)))
                    support = {payload_digest(row["public"]) for row in next_rows}
                    for next_row in next_rows:
                        nxt = next_row.pop("public")
                        next_row["next_first_public"] = nxt
                        next_row["public_completion"] = completion(
                            token=token, first_public=first, second_public=second,
                            action_edges=action, future_key=FUTURE_KEYS[label],
                            expected_future_key=FUTURE_KEYS[label],
                            next_public=nxt, support=support)
                    if controls_example is None:
                        controls_example = (token, first, second, action,
                                            next_rows[0]["next_first_public"], support)
                    prior_rows.append({"first_public": first, "second_public": second,
                                       "public_action_red_edge_ids": list(action),
                                       "second_variable_sites_private": second_variable,
                                       "next_variable_sites_private": next_variable,
                                       "prefix_mass": str(prefix_mass),
                                       "next_rows": next_rows})
            assert sum((Fraction(row["prefix_mass"]) for row in prior_rows),
                       Fraction()) == 1
            branches[label] = {"status": "passed_complete_public_laws",
                               "positive_prefixes": len(prior_rows),
                               "next_flux": first_flux, "rows": prior_rows}
    except Censor as exc:
        return {"status": "censored_at_registered_cap", "reason": str(exc),
                "completed_branches": list(branches), "usage": usage}
    token, first, second, action, nxt, support = controls_example
    valid = dict(token=token, first_public=first, second_public=second,
                 action_edges=action, future_key=FUTURE_KEYS["A"],
                 expected_future_key=FUTURE_KEYS["A"], next_public=nxt,
                 support=support)
    altered_first = canonical_record(first)
    altered_first["charge"][1] ^= 1
    altered_first["vacuum"][1] ^= 1
    altered_second = canonical_record(second)
    altered_second["charge"][0] ^= 1
    altered_second["vacuum"][0] ^= 1
    controls = {
        "swapped_action": rejected(completion, **{**valid, "action_edges": (4,)}),
        "tampered_first": rejected(completion, **{**valid, "first_public": altered_first}),
        "tampered_second": rejected(completion, **{**valid, "second_public": altered_second}),
        "wrong_future_key": rejected(completion, **{**valid, "future_key": "wrong"}),
        "private_field_injection": rejected(completion, **{**valid,
            "next_public": {**nxt, "physical_edges": [0, 4]}}),
    }
    assert all(controls.values())
    tv = {}
    for first_charge in (0, 1):
        laws = {}
        for label in branches:
            law = {}
            for row in branches[label]["rows"]:
                if row["first_public"]["charge"][1] != first_charge:
                    continue
                for nxt_row in row["next_rows"]:
                    key = payload_digest(nxt_row["next_first_public"])
                    mass = Fraction(row["prefix_mass"]) * Fraction(
                        nxt_row["conditional_probability"]) / Fraction(1, 2)
                    law[key] = law.get(key, Fraction()) + mass
            assert sum(law.values(), Fraction()) == 1
            laws[label] = law
        tv[str(first_charge)] = str(sum((abs(laws["A"].get(key, Fraction()) -
            laws["B"].get(key, Fraction())) for key in set(laws["A"]) |
            set(laws["B"])), Fraction()) / 2)
    if time.process_time() - started >= budget["max_cpu_seconds"]:
        return {"status": "censored_at_registered_cap", "reason": "cpu_after_matrix",
                "usage": usage}
    return {"status": "passed_two_branch_complete_public_law",
            "branch_a": branches["A"], "branch_b": branches["B"],
            "exact_total_variation_by_first_charge": tv,
            "binding_controls": controls, "usage": usage,
            "claim_boundary": "One ideal two-edge fixture; second sectors and future-fault timing differ, so not isolated correction causality"}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    prior = json.loads(INPUTS["j6o_result"].read_text())
    j7c = json.loads(INPUTS["j7c_result"].read_text())
    j7d = json.loads(INPUTS["j7d_result"].read_text())
    assert prior["status"] == "passed_exact_one_geometry_full_binary_joint_record_only"
    assert j7c["matrix"]["exact_total_variation_by_first_charge"] == {
        "00": "0", "10": "0", "01": "0", "11": "0"}
    assert j7d["ranked_open_pairs_first_32"][0]["fixture"] == "two_edge_path"
    assert j7d["ranked_open_pairs_first_32"][0]["a_action"] == [0]
    assert j7d["ranked_open_pairs_first_32"][0]["b_action"] == [4]
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    red, sites, flips, pairs = setup(embedding, state)
    matrix = run_matrix(contract, prior, red, sites, flips, pairs, started)
    pins_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                  for name, path in INPUTS.items()}
    assert all(pins_after.values())
    return {"schema_version": 1, "id": contract["id"],
            "status": ("exact_two_edge_complete_public_discriminator_closed"
                       if matrix["status"].startswith("passed") else
                       "exact_two_edge_complete_public_discriminator_censored"),
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "pinned_input_checks_after": pins_after,
            "matrix": matrix,
            "frozen_caller_gate": "unchanged_not_integrated_stateful_future_first_callback",
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Exact one-geometry ideal support-matched history comparison; no physical five-round integration, noisy JIT risk, scaling, general D4 kernel or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
    print(RESULT)
