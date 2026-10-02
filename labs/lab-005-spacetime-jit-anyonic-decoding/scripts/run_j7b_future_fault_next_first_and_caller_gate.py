"""Exact fixed-path future-fault next-first law; frozen caller remains read-only."""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import (
    canonical_record, make_token, payload_digest, setup, token_body,
)


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7b-future-fault-next-first-and-caller-gate-2026-09-25.json"
RESULT = LAB / "results/j7b-future-fault-next-first-and-caller-gate-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6o_result": LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json",
    "j7a_result": LAB / "results/j7a-postselected-next-first-limiting-fixtures-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}
TRIAL_ID = "j7b-fixed-path"
FUTURE_KEY = "j7b-future-exogenous-0"


class Censor(Exception):
    """Registered complexity bound was reached; no wider calculation follows."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(blocks, flips, usage, budget, started):
    count = 2 * sum(len(ops) for ops, _ in blocks[:-1]) + len(blocks[-1][0])
    terms = 1 << count
    if usage["ordered_moment_terms"] + terms > budget["max_ordered_moment_terms"]:
        raise Censor("registered_ordered_moment_term_cap")
    if time.process_time() - started >= budget["max_cpu_seconds"]:
        raise Censor("registered_cpu_cap")
    usage["ordered_moment_terms"] += terms
    return ordered_probability(blocks, flips)


def caller_audit(source: str) -> dict:
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    builder = functions["build_integrated_d4_history_from_draws"]
    evaluator = functions["evaluate_schedule_arm"]
    names = lambda node: {n.func.id for n in ast.walk(node)
                          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    build_calls, evaluate_calls = names(builder), names(evaluator)
    assert "observation_from_error_edges" in build_calls
    assert "provide_action_conditioned_second_record" in evaluate_calls
    history = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "IntegratedD4HistoryV1")
    fields = {node.target.id for node in history.body
              if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)}
    assert {"physical_edge_states", "hidden_projector_states", "record"} <= fields
    return {
        "status": "not_integrated_stateful_future_first_callback",
        "first_observation_built_before_schedule_action": True,
        "physical_and_hidden_trajectory_precomputed": True,
        "phenomenological_second_provider_invoked": True,
        "action_bound_postselected_state_field": any("postselected" in field for field in fields),
        "future_fault_state_callback_invoked": any("future" in name and "first" in name
                                                   for name in evaluate_calls),
        "frozen_caller_modified": False,
    }


def future_public_completion(*, token, first_public, second_public, action_edges,
                             future_key, next_public, positive_next_records):
    if payload_digest(token_body(token)) != token.state_digest:
        raise ValueError("altered private token")
    first = canonical_record(first_public)
    second = None if second_public is None else canonical_record(second_public)
    if action_edges != token.action_edges:
        raise ValueError("action mismatch")
    if payload_digest({"trial_id": token.trial_id, "first_public": first}) != token.first_digest:
        raise ValueError("first prefix mismatch")
    if payload_digest({"trial_id": token.trial_id, "first_digest": token.first_digest,
                       "action_edges": action_edges}) != token.action_digest:
        raise ValueError("action digest mismatch")
    second_digest = None if second is None else payload_digest(
        {"trial_id": token.trial_id, "first_digest": token.first_digest,
         "action_digest": token.action_digest, "second_public": second})
    if second_digest != token.second_digest:
        raise ValueError("second prefix mismatch")
    if future_key != FUTURE_KEY:
        raise ValueError("future exogenous key mismatch")
    nxt = canonical_record(next_public)
    if payload_digest(nxt) not in positive_next_records:
        raise ValueError("next public record absent from exact conditional support")
    public = {"trial_id": token.trial_id, "first_prefix_digest": token.first_digest,
              "action_digest": token.action_digest,
              "second_prefix_digest": token.second_digest,
              "future_key_digest": payload_digest({"trial_id": token.trial_id,
                                                    "future_key": future_key}),
              "next_first_public": nxt}
    return {**public, "completion_digest": payload_digest(public)}


def rejected(function, **kwargs) -> bool:
    try:
        function(**kwargs)
    except ValueError:
        return True
    return False


def future_branch(contract, source, no_fault, red, sites, flips, pairs, started):
    spec, budget = contract["matrix"], contract["budget"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    future, _ = red_boundary(red, spec["future_fault_red_edges_private"])
    first_site = 1
    first_op = conjugated_star(sites[first_site], physical)
    assert len(source["public_law_rows"]) == spec["expected_positive_first_second_prefixes"]
    usage = {"ordered_moment_terms": 0, "positive_next_rows": 0}
    output = []
    controls_example = None
    try:
        for prior in source["public_law_rows"]:
            action = prior["action"]
            edges = tuple(spec["actions"][action])
            assert prior["public_action_red_edge_ids"] == list(edges)
            first = canonical_record(prior["first_public"])
            second = None if prior["second_public"] is None else canonical_record(prior["second_public"])
            assert first["flux"] == first_flux
            action_mask, _ = red_boundary(red, list(edges))
            residual = physical ^ action_mask
            next_mask = residual ^ future
            remaining = set(spec["physical_red_edges_private"]) ^ set(edges) ^ set(spec["future_fault_red_edges_private"])
            _, next_flux = red_boundary(red, sorted(remaining))
            next_eligible, _ = sector_sites(sites, next_mask, flips, pairs)
            assert next_eligible == [s for s, bit in enumerate(next_flux) if not bit]
            first_bit = 1 if first["charge"][first_site] == 0 else -1
            first_block = ([first_op], (first_bit,))
            second_sites = {"defer": [], "partial": [0], "matched": [0, 2]}[action]
            second_ops = [conjugated_star(sites[s], residual) for s in second_sites]
            second_bits = tuple(1 if second["charge"][s] == 0 else -1 for s in second_sites)
            blocks = [first_block] + ([] if second is None else [(second_ops, second_bits)])
            prefix_mass = Fraction(str(prior["first_probability"])) * (
                Fraction(1) if second is None else Fraction(str(prior["second_conditional_probability"])))
            assert exact(blocks, flips, usage, budget, started) == prefix_mass
            deterministic = {}
            variable = []
            next_ops = {}
            for site in next_eligible:
                op = conjugated_star(sites[site], next_mask)
                next_ops[site] = op
                plus = exact(blocks + [([op], (1,))], flips, usage, budget, started) / prefix_mass
                if not 0 <= plus <= 1:
                    raise ValueError("invalid exact one-site conditional")
                if plus in (0, 1):
                    deterministic[site] = int(plus == 0)
                else:
                    variable.append(site)
            if len(variable) > budget["max_variable_next_sites"]:
                raise Censor("registered_variable_next_site_cap")
            random_ops = [next_ops[s] for s in variable]
            positive = []
            total = Fraction()
            for bits in assignments(len(variable)):
                joint = exact(blocks + [(random_ops, bits)], flips, usage, budget, started)
                if joint < 0:
                    raise ValueError("negative joint probability")
                conditional = joint / prefix_mass
                total += conditional
                if not conditional:
                    continue
                usage["positive_next_rows"] += 1
                if usage["positive_next_rows"] > budget["max_positive_next_rows"]:
                    raise Censor("registered_positive_next_row_cap")
                charges = [0] * 24
                for site, bit in deterministic.items():
                    charges[site] = bit
                for site, outcome in zip(variable, bits):
                    charges[site] = int(outcome == -1)
                positive.append({"next_first_public": public_record(next_flux, charges),
                                 "conditional_probability": str(conditional)})
            if total != 1:
                raise ValueError("next first joint law not normalized")
            assert positive
            first_projectors = ((first_site, *first_op, first_bit),)
            second_projectors = tuple((site, *op, bit) for site, op, bit
                                      in zip(second_sites, second_ops, second_bits))
            token = make_token(trial_id=TRIAL_ID, first_public=first, second_public=second,
                action_edges=edges, allowed_actions=tuple(tuple(v) for v in spec["actions"].values()),
                physical_mask=physical, action_mask=action_mask,
                first_projectors=first_projectors, second_projectors=second_projectors)
            support = {payload_digest(row["next_first_public"]) for row in positive}
            for row in positive:
                row["public_completion"] = future_public_completion(
                    token=token, first_public=first, second_public=second,
                    action_edges=edges, future_key=FUTURE_KEY,
                    next_public=row["next_first_public"], positive_next_records=support)
                assert set(row["public_completion"]) == {
                    "trial_id", "first_prefix_digest", "action_digest",
                    "second_prefix_digest", "future_key_digest", "next_first_public",
                    "completion_digest"}
            if controls_example is None and action == "partial":
                controls_example = (token, first, second, edges, positive[0]["next_first_public"], support)
            first_key_digest = payload_digest({"trial_id": TRIAL_ID,
                                               "first_observation_bit": first["charge"][first_site]})
            second_key_digest = None if second is None else payload_digest(
                {"trial_id": TRIAL_ID, "second_exogenous_bit": second["charge"][0]})
            output.append({"action": action, "public_action_red_edge_ids": list(edges),
                           "first_public": first, "second_public": second,
                           "matched_key_digests": {
                               "physical": payload_digest({"trial_id": TRIAL_ID,
                                                           "physical_key": "j7b-fixed-physical"}),
                               "first_observation": first_key_digest,
                               "second_exogenous": second_key_digest,
                               "future_fault": payload_digest({"trial_id": TRIAL_ID,
                                                               "future_key": FUTURE_KEY})},
                           "prefix_mass": str(prefix_mass),
                           "next_variable_sites_private": variable,
                           "next_rows": positive})
        assert len(output) == spec["expected_positive_first_second_prefixes"]
    except Censor as exc:
        return {"status": "censored_at_registered_complexity_cap", "reason": str(exc),
                "completed_prefixes": len(output), "usage": usage,
                "claim_boundary": "No complete future-fault public law or history comparator inferred"}
    for action in spec["actions"]:
        mass = sum(
            (Fraction(row["prefix_mass"]) *
             sum((Fraction(next_row["conditional_probability"])
                  for next_row in row["next_rows"]), Fraction())
             for row in output if row["action"] == action),
            Fraction(),
        )
        assert mass == 1
    assert len({row["matched_key_digests"]["physical"] for row in output}) == 1
    assert len({row["matched_key_digests"]["future_fault"] for row in output}) == 1
    for bit in (0, 1):
        same_first = [row for row in output if row["first_public"]["charge"][first_site] == bit]
        assert len({row["matched_key_digests"]["first_observation"] for row in same_first}) == 1
        for second_bit in (0, 1):
            same_second = [row for row in same_first if row["second_public"] is not None
                           and row["second_public"]["charge"][0] == second_bit]
            assert {row["action"] for row in same_second} == {"partial", "matched"}
            assert len({row["matched_key_digests"]["second_exogenous"] for row in same_second}) == 1
    token, first, second, edges, nxt, support = controls_example
    valid = dict(token=token, first_public=first, second_public=second,
                 action_edges=edges, future_key=FUTURE_KEY,
                 next_public=nxt, positive_next_records=support)
    tampered_first = canonical_record(first)
    tampered_first["charge"][1] ^= 1
    tampered_first["vacuum"][1] ^= 1
    tampered_second = canonical_record(second)
    tampered_second["charge"][0] ^= 1
    tampered_second["vacuum"][0] ^= 1
    tampered_next = canonical_record(nxt)
    tampered_next["charge"][0] ^= 1
    tampered_next["vacuum"][0] ^= 1
    controls = {
        "swapped_action": rejected(future_public_completion, **{**valid, "action_edges": (0, 4)}),
        "tampered_first": rejected(future_public_completion, **{**valid, "first_public": tampered_first}),
        "tampered_second": rejected(future_public_completion, **{**valid, "second_public": tampered_second}),
        "wrong_future_key": rejected(future_public_completion, **{**valid, "future_key": "wrong"}),
        "private_field_injection": rejected(future_public_completion, **{**valid,
            "next_public": {**nxt, "physical_edges": [0, 4]}}),
    }
    # A next-record mutation is rejected only if it lies outside the exact
    # positive support; otherwise it is a valid different quantum outcome.
    if payload_digest(tampered_next) not in support:
        controls["unsupported_next_record"] = rejected(
            future_public_completion, **{**valid, "next_public": tampered_next})
    assert all(controls.values())
    first_values = sorted({row["first_public"]["charge"][1] for row in output})
    tv_by_first = {}
    no_fault_rows = no_fault["two_edge_path"]["rows"]
    _, matched_final_flux = red_boundary(red, [4])
    for bit in first_values:
        a = next(row for row in output if row["action"] == "defer"
                 and row["first_public"]["charge"][1] == bit)
        assert all(r["next_first_public"]["flux"] == matched_final_flux
                   for r in a["next_rows"])
        law_a = {tuple(r["next_first_public"]["charge"]): Fraction(r["conditional_probability"])
                 for r in a["next_rows"]}
        law_b = {}
        for row in no_fault_rows:
            if row["action"] != "partial" or row["first_public"]["charge"][1] != bit:
                continue
            assert row["public_completion"]["next_first_public"]["flux"] == matched_final_flux
            charge = tuple(row["public_completion"]["next_first_public"]["charge"])
            law_b[charge] = law_b.get(charge, Fraction()) + Fraction(
                row["second_conditional_probability"])
        assert sum(law_a.values(), Fraction()) == sum(law_b.values(), Fraction()) == 1
        tv = sum((abs(law_a.get(record, Fraction()) - law_b.get(record, Fraction()))
                  for record in set(law_a) | set(law_b)), Fraction()) / 2
        tv_by_first[str(bit)] = str(tv)
    assert time.process_time() - started < budget["max_cpu_seconds"]
    return {"status": "passed_complete_fixed_path_future_fault_law",
            "positive_prefix_count": len(output), "rows": output,
            "same_final_support_counterfactual_tv_by_first_charge": tv_by_first,
            "binding_controls": controls, "usage": usage,
            "claim_boundary": "One ideal fixed-path orbit/future fault only; same-support contrast changes prior measurement history and is not isolated action causality"}


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    caller = caller_audit(INPUTS["frozen_integrated_history"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    source = json.loads(INPUTS["j6o_result"].read_text())
    no_fault = json.loads(INPUTS["j7a_result"].read_text())
    assert source["status"] == "passed_exact_one_geometry_full_binary_joint_record_only"
    assert no_fault["status"] == "passed_two_exact_no_fault_state_handoff_limits"
    red, sites, flips, pairs = setup(embedding, state)
    future = future_branch(contract, source, no_fault, red, sites, flips, pairs, started)
    assert all(digest(path) == contract["pinned_inputs"][name + "_sha256"]
               for name, path in INPUTS.items())
    return {"schema_version": 1, "id": contract["id"],
            "status": "exact_future_fault_matrix_completed" if future["status"].startswith("passed")
                      else "exact_future_fault_matrix_censored",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "future_fault_fixed_path": future, "frozen_caller_gate": caller,
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Fixed ideal nonzero-future-fault projector law and structural caller audit only; no general noisy D4 feedback kernel, physical five-round integration, JIT risk or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
