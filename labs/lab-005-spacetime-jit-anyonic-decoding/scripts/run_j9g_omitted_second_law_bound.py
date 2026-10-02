"""Exact selected-record worst-case second-law contamination certificate."""

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9g-omitted-second-law-bound-2026-09-28.json"
RESULT = LAB / "results/j9g-omitted-second-law-bound-2026-09-28.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_law(rows):
    answer = {}
    for row in rows:
        key = json.dumps(row["public"], sort_keys=True, separators=(",", ":"))
        assert key not in answer
        answer[key] = Fraction(row["conditional_probability"])
    assert all(value > 0 for value in answer.values())
    assert sum(answer.values(), Fraction()) == 1
    return answer


def binary_entropy(probability):
    if probability in (0, 1):
        return 0.0
    p = float(probability)
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    paths = {name: LAB / spec["path"] for name, spec in contract["pinned_inputs"].items()}
    assert all(sha(path) == contract["pinned_inputs"][name]["sha256"]
               for name, path in paths.items())
    census = json.loads(paths["j9f_result"].read_text())
    old = json.loads(paths["j8i_result"].read_text())
    prior_contract = json.loads(paths["j9f_contract"].read_text())
    assert census["status"] == "selected_first_mass_census_complete"
    assert census["contract_sha256"] == sha(paths["j9f_contract"])
    assert old["status"] == "all_support_complete_second_laws_closed"
    assert len(census["rows"]) == census["completed_errors"] == 8192
    assert len(old["rows"]) == 55 and old["different_candidate_action_cells"] == 0
    assert prior_contract["budget"]["max_errors"] == 8192
    assert prior_contract["model_boundary"].find("p_X=1/10") >= 0
    assert old["actions"] == [[0], [1, 30, 32, 34, 35]]
    assert old["first_public"]["charge"] == [0] * 24
    assert old["first_public"]["flux"] == [1, 0, 0, 1] + [0] * 20
    known = {sum(1 << edge for edge in row["error_edges_private"]): row
             for row in old["rows"]}
    assert len(known) == 55
    seen = set()
    total = Fraction()
    known_total = Fraction()
    for row in census["rows"]:
        mask = row["private_error_mask_analysis_only"]
        assert mask not in seen and row["error_weight"] == mask.bit_count()
        seen.add(mask)
        first_mass = Fraction(row["first_public_mass"])
        assert first_mass > 0
        weight = Fraction(9 ** (36 - row["error_weight"]), 10 ** 36)
        contribution = weight * first_mass
        total += contribution
        if mask in known:
            assert first_mass == Fraction(known[mask]["first_public_mass"])
            known_total += contribution
    assert len(seen) == 8192 and set(known) <= seen
    assert total == Fraction(census["summary"]["selected_complete_first_public_mass"])
    known_share = known_total / total
    assert known_share == Fraction(census["summary"]
                                   ["known_55_weighted_fraction_of_selected_record"])
    omitted = 1 - known_share
    assert 0 < omitted < Fraction(1, 100)
    unknown_count = 8192 - 55
    information_cap_bits = binary_entropy(omitted) + float(omitted) * math.log2(unknown_count)
    assert information_cap_bits < 1
    cells = []
    for action_index, action in enumerate(old["actions"]):
        reference = public_law(old["rows"][0]["cells"][action_index]["rows"])
        for error in old["rows"]:
            cell = error["cells"][action_index]
            assert cell["public_action_red_edges"] == action
            assert public_law(cell["rows"]) == reference
            assert all(item["public"]["flux"] == cell["second_public_flux"]
                       for item in cell["rows"])
        assert len(reference) == (2 if action_index == 0 else 32)
        cells.append({"public_action_red_edges": action,
                      "replayed_identical_known_laws": 55,
                      "common_known_public_law_positive_rows": len(reference),
                      "unknown_error_count": unknown_count,
                      "known_posterior_weight": str(known_share),
                      "unknown_posterior_weight": str(omitted),
                      "worst_case_full_mixture_tv_from_common_known_law_at_most": str(omitted),
                      "worst_case_bayes_risk_reduction_for_fixed_hidden_target_and_zero_one_loss_at_most": str(omitted),
                      "conditional_private_error_information_gain_upper_bits":
                          round(information_cap_bits, 12)})
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert all(sha(path) == contract["pinned_inputs"][name]["sha256"]
               for name, path in paths.items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "omitted_second_law_worst_case_bounds_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "selected_first_public_record": old["first_public"],
            "selected_first_public_probability": str(total),
            "known_55_posterior_weight": str(known_share),
            "unknown_8137_posterior_weight": str(omitted),
            "action_cells": cells,
            "derivation": {
                "mixture": "For either fixed action, every 55-error known law equals Q, so the full conditional second law is M=(1-epsilon)Q+epsilon R for an unknown valid law R. Thus TV(M,Q)<=epsilon for any omitted laws.",
                "bounded_loss": "For any fixed hidden target and 0-1 decision loss independent of the second observation, Y carries no information about target within the known-error class because every known law equals Q. A first-only decision optimized for that class has total risk at most (1-epsilon) times its class-optimal risk plus epsilon, while any second-record decision has total risk at least (1-epsilon) times that class-optimal risk. Hence possible Bayes-risk improvement is at most epsilon at this selected first record and fixed action.",
                "information": "With B indicating omitted error, I(E;Y|first,action)=I(B;Y)+epsilon I(E;Y|B=omitted,first,action) <= h2(epsilon)+epsilon log2(8137). The numerical upper bound is for private-error information at this one first record, not measured information gain or a full-channel quantity."
            },
            "counters": {"replayed_complete_known_laws": 110,
                         "new_complete_second_laws": 0, "new_born_terms": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "Exact worst-case bounds for one selected L=2 first public record and each of two separately fixed public actions. No omitted second law was fabricated. Bayes-risk statement requires a fixed hidden target and observation-independent 0-1 loss, not adaptive JIT action selection or unconditional Boolean-union scoring. No actual mutual information/risk, full-IID aggregate, noisy JIT, scaling or threshold is computed."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "epsilon": result["unknown_8137_posterior_weight"],
                      "cells": result["action_cells"],
                      "cpu_seconds": result["cpu_seconds"]}))
