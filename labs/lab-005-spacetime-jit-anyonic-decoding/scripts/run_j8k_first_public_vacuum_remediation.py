"""Restore J8A/J8B first-public records to the frozen J6O convention."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import time

from run_j6o_full_binary_sequential_public_record import public_record
from run_j8a_alternate_first_record_mass_matrix import run as rerun_first
from run_j8b_alternate_first_complete_second_laws import law, run as rerun_second


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8k-first-public-vacuum-remediation-2026-09-27.json"
SUMMARY = LAB / "results/j8k-first-public-vacuum-remediation-summary-2026-09-27.json"
FIRST = LAB / "results/j8k-corrected-alternate-first-record-masses-2026-09-27.json"
SECOND = LAB / "results/j8k-corrected-alternate-first-complete-second-laws-2026-09-27.json"
INPUTS = {
    "j8a_contract": LAB / "manifests/j8a-alternate-first-record-mass-matrix-2026-09-27.json",
    "j8a_result": LAB / "results/j8a-alternate-first-record-mass-matrix-2026-09-27.json",
    "j8a_runner": LAB / "scripts/run_j8a_alternate_first_record_mass_matrix.py",
    "j8b_contract": LAB / "manifests/j8b-alternate-first-complete-second-laws-2026-09-27.json",
    "j8b_result": LAB / "results/j8b-alternate-first-complete-second-laws-2026-09-27.json",
    "j8b_runner": LAB / "scripts/run_j8b_alternate_first_complete_second_laws.py",
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8c_runner": LAB / "scripts/run_j8c_support_geometry_cost_matrix.py",
    "j8i_result": LAB / "results/j8i-all-support-complete-second-laws-verified-2026-09-27.json",
    "j8j_result": LAB / "results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "public_record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corrected(record: dict) -> dict:
    assert set(record) == {"flux", "charge", "vacuum"}
    assert len(record["flux"]) == len(record["charge"]) == len(record["vacuum"]) == 24
    assert record["vacuum"] == [int(not (f or c)) for f, c in zip(record["flux"], record["charge"])]
    return public_record(record["flux"], record["charge"])


def run() -> tuple[dict, dict, dict]:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget = contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8a_contract", "j8a_result", "j8b_contract", "j8b_result",
            "j8c_result", "j8i_result", "j8j_result", "j7m_result")}
    a0, b0 = old["j8a_result"], old["j8b_result"]
    assert a0["status"] == "alternate_first_record_feasibility_closed"
    assert b0["status"] == "alternate_first_complete_second_laws_closed"
    assert rerun_first()["rows"] == a0["rows"]
    assert rerun_second()["rows"] == b0["rows"]
    assert a0["counters"]["ordered_first_terms"] <= budget["max_j8a_ordered_first_terms"]
    assert b0["counters"]["first_orbit_moments"] + b0["counters"]["second_orbit_moments"] <= budget["max_j8b_orbit_moment_terms"]
    assert b0["counters"]["algebraic_relation_probes"] <= budget["max_j8b_relation_probes"]
    assert b0["allplus_complete_law_replays"] == 26
    a, b = deepcopy(a0), deepcopy(b0)
    a["id"] = contract["id"] + "-corrected-first"
    b["id"] = contract["id"] + "-corrected-second"
    a["status"] = "remediated_first_public_record_verified"
    b["status"] = "remediated_first_public_and_second_laws_verified"
    for payload, source in ((a, "j8a_result"), (b, "j8b_result")):
        payload["remediation_contract_sha256"] = digest(CONTRACT)
        payload["remediation_runner_sha256"] = digest(Path(__file__))
        payload["original_result_sha256"] = digest(INPUTS[source])
        payload["original_public_record_status"] = "withdrawn_vacuum_membership_mismatch"
    assert len(a["rows"]) == len(b["rows"]) == 13
    corrected_a = corrected_b = positive_second = zero_second = 0
    for row_a, row_b in zip(a["rows"], b["rows"]):
        assert row_a["error_edges_private"] == row_b["error_edges_private"]
        assert len(row_a["cases"]) == len(row_b["first_public_cases"]) == 4
        assert len(row_b["cells"]) == 8
        for case_a, case_b in zip(row_a["cases"], row_b["first_public_cases"]):
            assert case_a == case_b
            fixed = corrected(case_a["first_public"])
            assert fixed["vacuum"] != case_a["first_public"]["vacuum"]
            case_a["first_public"] = fixed
            case_b["first_public"] = deepcopy(fixed)
            assert case_a == case_b
            corrected_a += 1
            corrected_b += 1
        actions = [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
        for cell in row_b["cells"]:
            assert cell["public_action_red_edges"] in actions
            if cell["status"] == "zero_first_mass_excluded":
                assert not cell["rows"]
                zero_second += 1
            else:
                assert cell["status"] == "exact_complete_second_law"
                assert law(cell["rows"])
                for second_row in cell["rows"]:
                    second_record = second_row["public"]
                    assert second_record == public_record(second_record["flux"], second_record["charge"])
                positive_second += 1
        assert row_a["cases"][0]["first_public"] == old["j7m_result"]["first_public"]
    assert (corrected_a, corrected_b, positive_second, zero_second) == (52, 52, 96, 8)
    assert a["positive_candidate_counts_by_alternative"] == [11, 11, 10]
    assert b["different_alternate_candidate_action_cells"] == 0
    assert b["complete_second_law_cells"] == 96
    j8c_source = INPUTS["j8c_runner"].read_text()
    consumed = re.findall(r'old\["j8b_result"\]\["([^"]+)"\]', j8c_source)
    assert sorted(consumed) == ["complete_second_law_cells", "different_alternate_candidate_action_cells"]
    assert all(b[name] == b0[name] for name in consumed)
    assert old["j8c_result"]["status"] == "support_geometry_cost_matrix_closed"
    known = {tuple(sorted(row["error_edges_private"])) for row in b["rows"]}
    known.update(tuple(sorted(row["error_edges_private"])) for row in old["j8i_result"]["rows"])
    assert len(known) == old["j8j_result"]["known_complete_law_error_count"] == 67
    assert old["j8j_result"]["uncovered_same_flux_error_count"] == 8125
    assert all(row["first_public_cases"][0]["first_public"] == old["j8i_result"]["first_public"] for row in b["rows"])
    assert time.process_time() - started < budget["max_cpu_seconds"]
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    summary = {
        "schema_version": 1, "id": contract["id"], "status": "first_public_vacuum_remediation_closed",
        "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
        "pinned_input_checks_before": before, "pinned_input_checks_after": after,
        "original_first_and_second_status": "withdrawn_public_first_vacuum_only",
        "corrected_first_records": corrected_a, "corrected_embedded_first_records": corrected_b,
        "verified_complete_second_law_cells": positive_second,
        "verified_zero_first_mass_action_exclusions": zero_second,
        "verified_allplus_replays": b["allplus_complete_law_replays"],
        "changed_numeric_masses_or_second_laws": 0,
        "changed_j8c_consumed_fields": 0,
        "j8c_consumed_fields": sorted(consumed),
        "j8j_known_support_count_revalidated": len(known),
        "counters": {"histories": 0, "schedule_arms": 0, "bootstraps": 0},
        "claim_boundary": "Corrected public first-record representation only; original exact masses, second laws and J8C geometry inputs unchanged. J8J selected-flux prior coverage remains finite-slice evidence, not full-prior information, risk, noisy JIT, L=3 or threshold.",
        "cpu_seconds": round(time.process_time() - started, 6),
    }
    return summary, a, b


if __name__ == "__main__":
    summary, first, second = run()
    for path, payload in ((FIRST, first), (SECOND, second), (SUMMARY, summary)):
        path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in
          ("status", "corrected_first_records", "corrected_embedded_first_records",
           "verified_complete_second_law_cells", "changed_numeric_masses_or_second_laws",
           "changed_j8c_consumed_fields", "j8j_known_support_count_revalidated", "cpu_seconds")}, indent=2))
