"""Exact three-edge, matched-final-support history-memory discriminator."""

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
    canonical_record, make_token, payload_digest, setup, token_body,
)
from run_j7b_future_fault_next_first_and_caller_gate import Censor, exact


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7c-three-edge-history-memory-discriminator-2026-09-25.json"
RESULT = LAB / "results/j7c-three-edge-history-memory-discriminator-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6s_result": LAB / "results/j6s-repeat-transfer-four-site-2026-09-25.json",
    "j7b_result": LAB / "results/j7b-future-fault-next-first-and-caller-gate-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}
TRIAL_ID = "j7c-three-edge-chain"
FUTURE_KEYS = {"A": "j7c-future-key-a", "B": "j7c-no-future-key-b"}
FIRST_SITES = (1, 2)
BRANCHES = {"A": "partial_one", "B": "partial_two"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def completion(*, token, first_public, second_public, action_edges,
               future_key, expected_future_key, next_public, support):
    if payload_digest(token_body(token)) != token.state_digest:
        raise ValueError("private token altered")
    first, second, nxt = (canonical_record(value) for value in
                          (first_public, second_public, next_public))
    if action_edges != token.action_edges or future_key != expected_future_key:
        raise ValueError("action or future key mismatch")
    if payload_digest({"trial_id": token.trial_id, "first_public": first}) != token.first_digest:
        raise ValueError("first prefix mismatch")
    if payload_digest({"trial_id": token.trial_id, "first_digest": token.first_digest,
                       "action_edges": action_edges}) != token.action_digest:
        raise ValueError("action binding mismatch")
    if payload_digest({"trial_id": token.trial_id, "first_digest": token.first_digest,
                       "action_digest": token.action_digest,
                       "second_public": second}) != token.second_digest:
        raise ValueError("second prefix mismatch")
    if payload_digest(nxt) not in support:
        raise ValueError("unsupported next public record")
    public = {"trial_id": token.trial_id, "first_prefix_digest": token.first_digest,
              "action_digest": token.action_digest,
              "second_prefix_digest": token.second_digest,
              "future_key_digest": payload_digest({"trial_id": token.trial_id,
                                                    "future_key": future_key}),
              "next_first_public": nxt}
    return {**public, "completion_digest": payload_digest(public)}


def rejected(fn, **kwargs):
    try:
        fn(**kwargs)
    except ValueError:
        return True
    return False


def run_exact(contract, source, red, sites, flips, pairs, started):
    spec, budget = contract["matrix"], contract["budget"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    first_eligible, _ = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [site for site, bit in enumerate(first_flux) if not bit]
    first_ops = [conjugated_star(sites[s], physical) for s in FIRST_SITES]
    source_cases = {case["action"]: case for case in source["cases"]}
    assert set(BRANCHES.values()) <= set(source_cases)
    assert source_cases["partial_one"]["first_random_sites_private"] == list(FIRST_SITES)
    assert source_cases["partial_two"]["first_random_sites_private"] == list(FIRST_SITES)
    usage = {"ordered_moment_terms": 0, "positive_next_rows": 0}
    out = {}
    example = None
    try:
        for label, action_name in BRANCHES.items():
            branch = spec["branch_" + label.lower()]
            action_edges = tuple(branch["public_action_red_edges"])
            future_edges = branch["future_physical_red_edges_private"]
            action_mask, _ = red_boundary(red, list(action_edges))
            future_mask, _ = red_boundary(red, future_edges)
            residual = physical ^ action_mask
            next_mask = residual ^ future_mask
            remaining = (set(spec["physical_red_edges_private"]) ^
                         set(action_edges) ^ set(future_edges))
            assert remaining == {3}
            _, next_flux = red_boundary(red, sorted(remaining))
            next_eligible, _ = sector_sites(sites, next_mask, flips, pairs)
            assert next_eligible == [site for site, bit in enumerate(next_flux) if not bit]
            prior = source_cases[action_name]
            assert prior["public_action_red_edge_ids"] == list(action_edges)
            assert len(prior["public_law_rows"]) == branch["expected_positive_prior_prefixes"]
            records = []
            for source_row in prior["public_law_rows"]:
                first = canonical_record(source_row["first_public"])
                second = canonical_record(source_row["second_public"])
                assert first["flux"] == first_flux
                first_bits = tuple(1 if first["charge"][s] == 0 else -1 for s in FIRST_SITES)
                second_sites = (0,) if label == "A" else (0, 1)
                second_ops = [conjugated_star(sites[s], residual) for s in second_sites]
                second_bits = tuple(1 if second["charge"][s] == 0 else -1
                                    for s in second_sites)
                blocks = [(first_ops, first_bits), (second_ops, second_bits)]
                prefix_mass = Fraction(source_row["first_probability"]) * Fraction(
                    source_row["second_conditional_probability"])
                assert exact(blocks, flips, usage, budget, started) == prefix_mass
                first_projectors = tuple((s, *op, bit) for s, op, bit
                                         in zip(FIRST_SITES, first_ops, first_bits))
                second_projectors = tuple((s, *op, bit) for s, op, bit
                                          in zip(second_sites, second_ops, second_bits))
                token = make_token(trial_id=TRIAL_ID, first_public=first,
                    second_public=second, action_edges=action_edges,
                    allowed_actions=((0,), (0, 4)), physical_mask=physical,
                    action_mask=action_mask, first_projectors=first_projectors,
                    second_projectors=second_projectors)
                if label == "B":
                    assert second["flux"] == next_flux
                    # Check both random second projectors independently; the
                    # complete commuting second block then repeats without a
                    # new fault by idempotence.
                    for op, bit in zip(second_ops, second_bits):
                        assert exact(blocks + [([op], (bit,))], flips, usage,
                                     budget, started) == prefix_mass
                        assert exact(blocks + [([op], (-bit,))], flips, usage,
                                     budget, started) == 0
                    positive = [{"next_first_public": second,
                                 "conditional_probability": "1"}]
                else:
                    fixed, variable, next_ops = {}, [], {}
                    for site in next_eligible:
                        op = conjugated_star(sites[site], next_mask)
                        next_ops[site] = op
                        plus = exact(blocks + [([op], (1,))], flips, usage,
                                     budget, started) / prefix_mass
                        if not 0 <= plus <= 1:
                            raise ValueError("invalid next-site conditional")
                        if plus in (0, 1):
                            fixed[site] = int(plus == 0)
                        else:
                            variable.append(site)
                    if len(variable) > budget["max_variable_next_sites"]:
                        raise Censor("registered_variable_next_site_cap")
                    variable_ops = [next_ops[s] for s in variable]
                    positive = []
                    total = Fraction()
                    for bits in assignments(len(variable)):
                        joint = exact(blocks + [(variable_ops, bits)], flips,
                                      usage, budget, started)
                        if joint < 0:
                            raise ValueError("negative next joint mass")
                        conditional = joint / prefix_mass
                        total += conditional
                        if not conditional:
                            continue
                        charges = [0] * 24
                        for site, bit in fixed.items():
                            charges[site] = bit
                        for site, bit in zip(variable, bits):
                            charges[site] = int(bit == -1)
                        positive.append({"next_first_public": public_record(next_flux, charges),
                                         "conditional_probability": str(conditional)})
                    if total != 1:
                        raise ValueError("incomplete next public law")
                usage["positive_next_rows"] += len(positive)
                if usage["positive_next_rows"] > budget["max_positive_next_rows"]:
                    raise Censor("registered_positive_next_row_cap")
                support = {payload_digest(row["next_first_public"]) for row in positive}
                for row in positive:
                    row["public_completion"] = completion(
                        token=token, first_public=first, second_public=second,
                        action_edges=action_edges, future_key=FUTURE_KEYS[label],
                        expected_future_key=FUTURE_KEYS[label],
                        next_public=row["next_first_public"], support=support)
                    assert set(row["public_completion"]) == {
                        "trial_id", "first_prefix_digest", "action_digest",
                        "second_prefix_digest", "future_key_digest", "next_first_public",
                        "completion_digest"}
                if example is None and label == "A":
                    example = (token, first, second, action_edges,
                               positive[0]["next_first_public"], support)
                records.append({"first_public": first, "second_public": second,
                                "public_action_red_edge_ids": list(action_edges),
                                "prefix_mass": str(prefix_mass),
                                "next_rows": positive})
            assert len(records) == branch["expected_positive_prior_prefixes"]
            assert sum((Fraction(row["prefix_mass"]) for row in records), Fraction()) == 1
            out[label] = {"status": "passed_complete_exact_next_first_law",
                          "positive_prior_prefixes": len(records), "rows": records,
                          "next_flux": next_flux,
                          "future_fault_count_private": len(future_edges)}
    except Censor as exc:
        return {"status": "censored_at_registered_complexity_cap",
                "reason": str(exc), "completed_branches": list(out), "usage": usage,
                "claim_boundary": "No full-public matched-final-support contrast inferred"}
    token, first, second, action_edges, next_public, support = example
    valid = dict(token=token, first_public=first, second_public=second,
                 action_edges=action_edges, future_key=FUTURE_KEYS["A"],
                 expected_future_key=FUTURE_KEYS["A"],
                 next_public=next_public, support=support)
    tampered_first = canonical_record(first)
    tampered_first["charge"][FIRST_SITES[0]] ^= 1
    tampered_first["vacuum"][FIRST_SITES[0]] ^= 1
    tampered_second = canonical_record(second)
    tampered_second["charge"][0] ^= 1
    tampered_second["vacuum"][0] ^= 1
    controls = {
        "swapped_action": rejected(completion, **{**valid, "action_edges": (0, 4)}),
        "tampered_first": rejected(completion, **{**valid, "first_public": tampered_first}),
        "tampered_second": rejected(completion, **{**valid, "second_public": tampered_second}),
        "wrong_future_key": rejected(completion, **{**valid, "future_key": "wrong"}),
        "private_field_injection": rejected(completion, **{**valid,
            "next_public": {**next_public, "physical_edges": [0, 4, 3]}}),
    }
    assert all(controls.values())
    tv_by_first = {}
    for bits in assignments(len(FIRST_SITES)):
        first_key = tuple(int(bit == -1) for bit in bits)
        laws = {}
        for label in BRANCHES:
            rows = [row for row in out[label]["rows"]
                    if tuple(row["first_public"]["charge"][s]
                             for s in FIRST_SITES) == first_key]
            assert rows and len({row["prefix_mass"] for row in rows}) == 1
            first_mass = Fraction(1, 4)
            law = {}
            for row in rows:
                for nxt in row["next_rows"]:
                    assert nxt["next_first_public"]["flux"] == out[label]["next_flux"]
                    key = payload_digest(nxt["next_first_public"])
                    mass = Fraction(row["prefix_mass"]) * Fraction(
                        nxt["conditional_probability"]) / first_mass
                    law[key] = law.get(key, Fraction()) + mass
            assert sum(law.values(), Fraction()) == 1
            laws[label] = law
        assert out["A"]["next_flux"] == out["B"]["next_flux"]
        tv = sum((abs(laws["A"].get(key, Fraction()) - laws["B"].get(key, Fraction()))
                  for key in set(laws["A"]) | set(laws["B"])), Fraction()) / 2
        tv_by_first["".join(map(str, first_key))] = str(tv)
    if time.process_time() - started >= budget["max_cpu_seconds"]:
        return {"status": "censored_at_registered_complexity_cap",
                "reason": "registered_cpu_cap_after_matrix", "usage": usage,
                "claim_boundary": "No full-public matched-final-support contrast inferred"}
    return {"status": "passed_complete_two_branch_history_discriminator",
            "branch_a": out["A"], "branch_b": out["B"],
            "exact_total_variation_by_first_charge": tv_by_first,
            "binding_controls": controls, "usage": usage,
            "claim_boundary": "One ideal fixed chain and matched final support; branches differ in measurement sector and future-fault timing, so not isolated correction causality"}


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    prior = json.loads(INPUTS["j6s_result"].read_text())
    j7b = json.loads(INPUTS["j7b_result"].read_text())
    assert prior["status"] == "passed_exact_repeat_control_and_four_site_completion"
    assert j7b["frozen_caller_gate"]["status"] == "not_integrated_stateful_future_first_callback"
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    red, sites, flips, pairs = setup(embedding, state)
    matrix = run_exact(contract, prior, red, sites, flips, pairs, started)
    assert all(digest(path) == contract["pinned_inputs"][name + "_sha256"]
               for name, path in INPUTS.items())
    return {"schema_version": 1, "id": contract["id"],
            "status": "exact_three_edge_history_discriminator_complete" if matrix["status"].startswith("passed")
                      else "exact_three_edge_history_discriminator_censored",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "matrix": matrix,
            "frozen_caller_gate": "unchanged_not_integrated_stateful_future_first_callback",
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Exact one-geometry ideal matched-support history contrast only; no physical five-round integration, noisy JIT risk, scaling, general D4 kernel or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
