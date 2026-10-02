"""Read-only exact two-support error-information audit of J7V public laws."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7w-pair-information-audit-2026-09-27.json"
RESULT = LAB / "results/j7w-pair-information-audit-2026-09-27.json"
INPUTS = {
    "j7v_contract": LAB / "manifests/j7v-joint-second-walsh-reduction-2026-09-27.json",
    "j7v_result": LAB / "results/j7v-joint-second-walsh-reduction-2026-09-27.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_key(public: dict) -> str:
    assert set(public) == {"charge", "flux", "vacuum"}
    assert all(len(public[field]) == 24 for field in public)
    assert all(bit in (0, 1) for field in public for bit in public[field])
    assert all(not (flux and charge) for flux, charge in
               zip(public["flux"], public["charge"]))
    assert public["vacuum"] == [1 - bit for bit in public["charge"]]
    return json.dumps(public, sort_keys=True, separators=(",", ":"))


def extract_law(cell: dict, expected_flux: list[int]) -> dict[str, Fraction]:
    law = {}
    for row in cell["rows"]:
        public = row["public"]
        assert public["flux"] == expected_flux
        key = record_key(public)
        assert key not in law
        probability = Fraction(row["conditional_probability"])
        assert probability > 0
        law[key] = probability
    assert len(law) == cell["positive_second_public_rows"]
    assert sum(law.values(), Fraction()) == 1
    return law


def entropy(q: Fraction) -> float:
    if q in (0, 1):
        return 0.0
    x = float(q)
    return -x * math.log2(x) - (1 - x) * math.log2(1 - x)


def compare(base: dict[str, Fraction], candidate: dict[str, Fraction],
            q: Fraction, max_rows: int) -> dict:
    keys = sorted(set(base) | set(candidate))
    assert len(keys) <= max_rows
    tv = sum((abs(base.get(key, Fraction()) - candidate.get(key, Fraction()))
              for key in keys), Fraction()) / 2
    prior_bayes = min(q, 1 - q)
    conditional_bayes = Fraction()
    conditional_entropy = 0.0
    information_kl = 0.0
    records = []
    for key in keys:
        p0, p1 = base.get(key, Fraction()), candidate.get(key, Fraction())
        joint0, joint1 = (1 - q) * p0, q * p1
        mix = joint0 + joint1
        assert mix > 0
        posterior = joint1 / mix
        conditional_bayes += min(joint0, joint1)
        conditional_entropy += float(mix) * entropy(posterior)
        if p0:
            information_kl += float(joint0) * math.log2(float(p0 / mix))
        if p1:
            information_kl += float(joint1) * math.log2(float(p1 / mix))
        records.append({"public_record_sha256": hashlib.sha256(key.encode()).hexdigest(),
                        "likelihood_base_given_first_and_action": str(p0),
                        "likelihood_candidate_given_first_and_action": str(p1),
                        "mixture_probability_given_first_and_action": str(mix),
                        "posterior_candidate_given_record": str(posterior)})
    assert sum((Fraction(row["mixture_probability_given_first_and_action"])
                for row in records), Fraction()) == 1
    assert conditional_bayes <= prior_bayes
    information = entropy(q) - conditional_entropy
    assert -1e-12 <= information <= entropy(q) + 1e-12
    assert abs(information - information_kl) < 1e-12
    if base == candidate:
        assert tv == 0 and conditional_bayes == prior_bayes
        assert all(Fraction(row["posterior_candidate_given_record"]) == q
                   for row in records)
        information = information_kl = 0.0
    return {"same_complete_public_law": base == candidate,
            "support_union_rows": len(keys),
            "total_variation": str(tv),
            "prior_candidate_weight_given_pair_and_first": str(q),
            "prior_entropy_bits": round(entropy(q), 15),
            "conditional_entropy_bits": round(conditional_entropy, 15),
            "mutual_information_bits": round(information, 15),
            "mutual_information_kl_crosscheck_bits": round(information_kl, 15),
            "prior_only_binary_error_classification_risk": str(prior_bayes),
            "record_aware_binary_error_classification_risk": str(conditional_bayes),
            "binary_error_classification_risk_reduction": str(prior_bayes - conditional_bayes),
            "offline_posterior_rows": records}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    prior = json.loads(INPUTS["j7t_result"].read_text())
    laws = json.loads(INPUTS["j7v_result"].read_text())
    control = json.loads(INPUTS["j7m_result"].read_text())
    assert prior["status"] == "peer_candidates_identified"
    assert laws["status"] == "complete_second_joint_laws_reconstructed_under_cap"
    assert laws["contract_sha256"] == digest(INPUTS["j7v_contract"])
    assert all(laws["pinned_input_checks_before"].values())
    assert all(laws["pinned_input_checks_after"].values())
    assert laws["counters"]["ordered_moment_terms"] == 51816
    assert len(laws["control_replays"]) == 2
    assert all(row["replays_j7m_complete_second_law"] for row in laws["control_replays"])
    peers = prior["selected_peer_initial_errors_private"]
    assert peers == spec["candidate_errors_private"]
    assert [row["initial_error_red_edges_private"] for row in laws["peer_rows"]] == peers
    assert [cell["public_action_red_edges"] for cell in control["cells"]] == spec["public_actions"]
    assert control["first_public"]["charge"] == [0] * 24
    assert control["first_public"]["vacuum"] == [1] * 24
    assert control["first_public_mass"] == spec["base_first_mass"] == "1/4"
    p = Fraction(spec["iid_red_x_rate"])
    assert p == Fraction(1, 10)
    base_edges = spec["base_error_private"]
    base_joint = p ** len(base_edges) * (1 - p) ** (36 - len(base_edges)) * Fraction(1, 4)
    assert base_edges == [0, 4, 3]
    out = []
    for peer_edges, peer_row in zip(peers, laws["peer_rows"]):
        prior_row = next(row for row in prior["candidate_rows"]
                         if row["candidate_initial_error_red_edges_private"] == peer_edges)
        assert prior_row["selected_first_public_mass_given_candidate"] == "1/16"
        candidate_joint = p ** len(peer_edges) * (1 - p) ** (36 - len(peer_edges)) * Fraction(1, 16)
        q = candidate_joint / (base_joint + candidate_joint)
        assert q == Fraction(prior_row["candidate_weight_given_pair_and_first"])
        assert q == Fraction(1, 325)
        cells = []
        for index, action in enumerate(spec["public_actions"]):
            base_cell = control["cells"][index]
            candidate_cell = peer_row["cells"][index]
            assert candidate_cell["public_action_red_edges"] == action
            assert base_cell["public_action_red_edges"] == action
            assert candidate_cell["first_public_mass"] == "1/16"
            assert candidate_cell["second_public_flux"] == base_cell["second_public_flux"]
            base_law = extract_law(base_cell, base_cell["second_public_flux"])
            candidate_law = extract_law(candidate_cell, base_cell["second_public_flux"])
            metrics = compare(base_law, candidate_law, q, budget["max_support_union_rows_per_cell"])
            metrics.update({"public_action_red_edges": action,
                            "same_second_public_flux": True,
                            "base_positive_rows": len(base_law),
                            "candidate_positive_rows": len(candidate_law)})
            cells.append(metrics)
        out.append({"base_error_red_edges_private": base_edges,
                    "candidate_error_red_edges_private": peer_edges,
                    "cells": cells})
    assert len(out) == budget["max_candidate_pairs"] == 2
    assert sum(len(row["cells"]) for row in out) == budget["max_pair_action_cells"] == 4
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    all_null = all(cell["same_complete_public_law"] for row in out for cell in row["cells"])
    return {"schema_version": 1, "id": contract["id"],
            "status": "restricted_pair_conditional_information_audit_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "all_four_complete_law_contrasts_null": all_null,
            "base_candidate_pair_rows": out,
            "counters": {"paired_law_comparisons": 4, "new_ordered_moment_terms": 0,
                         "new_stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Exact information about a binary private initial-error identity in each separate base-versus-candidate IID-prior-restricted pair, conditional on one selected full first public record and one fixed public action. Binary error-classification risk is not logical risk. No full-IID-channel information, unconditional logical risk, policy-emitted JIT benefit, noisy schedule or threshold.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
