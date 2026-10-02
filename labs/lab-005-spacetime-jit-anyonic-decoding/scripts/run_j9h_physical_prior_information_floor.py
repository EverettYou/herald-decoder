"""Exact physical-prior information floor from frozen finite D4 witnesses."""

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9h-physical-prior-information-floor-2026-10-01.json"
RESULT = LAB / "results/j9h-physical-prior-information-floor-2026-10-01.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def law(rows):
    answer = {}
    for row in rows:
        key = json.dumps(row["public"], sort_keys=True, separators=(",", ":"))
        assert key not in answer
        answer[key] = Fraction(row["conditional_probability"])
    assert answer and all(value > 0 for value in answer.values())
    assert sum(answer.values(), Fraction()) == 1
    return answer


def tv(first, second):
    return sum((abs(first.get(key, 0) - second.get(key, 0))
                for key in first.keys() | second.keys()), Fraction()) / 2


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    paths = {key: LAB / value["path"] for key, value in contract["pinned_inputs"].items()}
    assert all(sha(path) == contract["pinned_inputs"][key]["sha256"]
               for key, path in paths.items())
    source = json.loads(paths["j8v_result"].read_text())
    previous = json.loads(paths["j8w_result"].read_text())
    assert source["status"] == "equal_prior_collision_second_law_matrix_verified"
    assert previous["status"] == "same_flux_posterior_bounds_verified"
    assert source["contract_sha256"] == sha(paths["j8v_contract"])
    assert source["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert len(source["rows"]) == len(previous["rows"]) == 3
    assert [row["base_first_likelihood_stratum"] for row in source["rows"]] == ["1", "1/2", "1/4"]
    actions = [[0], [1, 30, 32, 34, 35]]
    assert contract["matrix"]["public_actions_red_edges"] == actions
    first_records = set()
    cells = []
    coefficient_by_action = {tuple(action): Fraction() for action in actions}
    count_laws = 0
    prior = Fraction(1, 10) ** 3 * Fraction(9, 10) ** 33
    for row, old in zip(source["rows"], previous["rows"]):
        assert row["base_first_likelihood_stratum"] == old["base_first_likelihood_stratum"]
        assert row["equal_prior_error_weight"] == 3
        assert row["first_flux_mask"] == old["first_flux_mask"]
        first_key = json.dumps(row["first_public"], sort_keys=True, separators=(",", ":"))
        assert first_key not in first_records
        first_records.add(first_key)
        assert row["first_public"]["charge"] == [0] * 24
        assert len(row["pair_rows"]) == 2
        pair = row["pair_rows"]
        assert all(len(item["error_edges_private"]) == 3 for item in pair)
        assert pair[0]["error_edges_private"] != pair[1]["error_edges_private"]
        assert [item["error_edges_private"] for item in pair] == old["selected_error_edges_private"]
        mass = Fraction(pair[0]["first_public_mass"])
        assert mass == Fraction(pair[1]["first_public_mass"]) == Fraction(row["base_first_likelihood_stratum"])
        joint_mass = 2 * prior * mass
        assert joint_mass == Fraction(old["selected_pair_joint_first_mass"])
        assert prior == Fraction(old["each_selected_error_prior_mass"])
        action_rows = []
        for index, action in enumerate(actions):
            assert pair[0]["cells"][index]["public_action_red_edges"] == action
            assert pair[1]["cells"][index]["public_action_red_edges"] == action
            p = law(pair[0]["cells"][index]["rows"])
            q = law(pair[1]["cells"][index]["rows"])
            count_laws += 2
            contrast = tv(p, q)
            assert contrast == Fraction(row["paired_action_differences"][index]["conditional_second_total_variation"])
            assert contrast == Fraction(old["action_rows"][index]["selected_pair_second_total_variation"])
            assert row["paired_action_differences"][index]["public_action_red_edges"] == action
            assert old["action_rows"][index]["public_action_red_edges"] == action
            coefficient = joint_mass * contrast * contrast
            coefficient_by_action[tuple(action)] += coefficient
            action_rows.append({"public_action_red_edges": action,
                                "pair_conditional_second_tv": str(contrast),
                                "physical_prior_information_floor_numerator": str(coefficient),
                                "floor_bits_formula": f"{coefficient}/(2 ln 2)",
                                "floor_bits_approx": float(coefficient) / (2 * math.log(2))})
        cells.append({"first_likelihood_stratum": row["base_first_likelihood_stratum"],
                      "first_flux_mask": row["first_flux_mask"],
                      "selected_pair_joint_first_probability": str(joint_mass),
                      "action_rows": action_rows})
        assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    assert count_laws == 12 and len(first_records) == 3
    assert coefficient_by_action[(0,)] > 0
    assert coefficient_by_action[(1, 30, 32, 34, 35)] > coefficient_by_action[(0,)]
    assert all(sha(path) == contract["pinned_inputs"][key]["sha256"]
               for key, path in paths.items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "physical_prior_information_floor_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "cells": cells,
            "fixed_action_global_channel_floors": [
                {"public_action_red_edges": list(action),
                 "exact_coefficient": str(value),
                 "conditional_mutual_information_floor_bits_formula": f"{value}/(2 ln 2)",
                 "conditional_mutual_information_floor_bits_approx": float(value) / (2 * math.log(2))}
                for action, value in coefficient_by_action.items()],
            "derivation": "For disjoint selected first records o_i and fixed action a, I(E;O2|O1,a) is the physical-prior sum over o. At o_i, introduce B_i indicating membership in its selected equal-posterior private-error pair. Chain rule and nonnegativity give P(o_i) I(E;O2|o_i,a) >= P(E in pair_i,o_i) JS(P_i,Q_i). Binary Pinsker gives JS(P_i,Q_i) >= TV(P_i,Q_i)^2/(2 ln 2) bits. Summing these nonnegative contributions yields the floor without any omitted first or second law.",
            "counters": {"replayed_complete_second_laws": count_laws,
                         "new_born_terms": 0, "new_complete_second_laws": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "A strictly positive conservative lower bound on ideal two-stage physical-prior conditional mutual information about private E for either globally fixed public charge action at L=2,p_X=1/10. It uses only three preselected disjoint full first records and 12 known laws; omitted outcomes contribute nonnegative information. This does not identify the actual full-channel information, logical information/risk, adaptive JIT gain, noisy measurement behavior, scaling or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite an existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "floors": result["fixed_action_global_channel_floors"],
                      "cpu_seconds": result["cpu_seconds"]}))
