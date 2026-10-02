"""Exact selected-flux first-record tail certificates; no Born-law evaluation."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
MANIFEST = LAB / "manifests/j8l-first-record-tail-certificate-2026-09-27.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(relative: str) -> dict:
    return json.loads((LAB / relative).read_text())


def support(row: dict) -> tuple[int, ...]:
    edges = row["error_edges_private"]
    assert len(edges) == len(set(edges)) and all(0 <= e < 36 for e in edges)
    return tuple(sorted(edges))


def prior(edges: tuple[int, ...]) -> Fraction:
    n = len(edges)
    return Fraction(9**(36 - n), 10**36)


def public_key(record: dict) -> str:
    assert set(record) == {"flux", "charge", "vacuum"}
    assert all(len(record[name]) == 24 for name in record)
    assert all(x in (0, 1) for name in record for x in record[name])
    assert all(v == 1 - c for v, c in zip(record["vacuum"], record["charge"]))
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def run() -> dict:
    started = time.process_time()
    manifest = json.loads(MANIFEST.read_text())
    assert digest(Path(__file__)) == manifest["runner_sha256_before_execution"]
    assert all(digest(LAB / path) == expected for path, expected in manifest["pinned_inputs"].items())
    coverage = load("results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json")
    first = load("results/j8k-corrected-alternate-first-record-masses-2026-09-27.json")
    second = load("results/j8k-corrected-alternate-first-complete-second-laws-2026-09-27.json")
    extended = load("results/j8i-all-support-complete-second-laws-verified-2026-09-27.json")
    assert coverage["same_first_flux_error_count"] == 8192
    assert coverage["known_complete_law_error_count"] == 67
    assert coverage["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert second["different_alternate_candidate_action_cells"] == 0
    assert extended["different_candidate_action_cells"] == 0
    assert first["rows"] and len(first["rows"]) == len(second["rows"]) == 13
    assert len(extended["rows"]) == 55
    assert second["actions"] == extended["actions"] == manifest["matrix"]["actions"]
    known_first = {support(row): row for row in first["rows"]}
    known_extended = {support(row): row for row in extended["rows"]}
    assert len(known_first) == 13 and len(known_extended) == 55
    assert len(set(known_first) | set(known_extended)) == 67
    assert set(support(row) for row in second["rows"]) == set(known_first)
    selected_key = public_key(extended["first_public"])
    flux = extended["first_public"]["flux"]
    selected_sector_mass = Fraction(coverage["selected_flux_prior_mass"])
    assert selected_sector_mass > 0
    assert sum(prior(e) for e in set(known_first) | set(known_extended)) == Fraction(coverage["known_support_prior_mass"])

    records = {}
    for error, row in known_first.items():
        assert len(row["cases"]) == 4
        for case in row["cases"]:
            key = public_key(case["first_public"])
            assert case["first_public"]["flux"] == flux
            assert Fraction(case["mass"]) >= 0
            records.setdefault(key, {"public": case["first_public"], "known_masses": {}})["known_masses"][error] = Fraction(case["mass"])
    assert len(records) == 4
    assert selected_key in records
    for error, row in known_extended.items():
        mass = Fraction(row["first_public_mass"])
        if error in records[selected_key]["known_masses"]:
            assert records[selected_key]["known_masses"][error] == mass
        records[selected_key]["known_masses"][error] = mass

    output_rows = []
    for key, data in sorted(records.items(), key=lambda item: sum(item[1]["public"]["charge"])):
        masses = data["known_masses"]
        assert len(masses) == (67 if key == selected_key else 13)
        known_prior = sum((prior(e) for e in masses), Fraction())
        observed_joint = sum((prior(e) * mass for e, mass in masses.items()), Fraction())
        assert all(0 <= mass <= 1 for mass in masses.values())
        omitted_prior = selected_sector_mass - known_prior
        assert observed_joint > 0 and omitted_prior >= 0
        bound = omitted_prior / (observed_joint + omitted_prior)
        assert 0 <= bound <= 1
        output_rows.append({
            "first_charge_sites": [i for i, bit in enumerate(data["public"]["charge"]) if bit],
            "first_public": data["public"],
            "known_law_error_count": len(masses),
            "positive_known_first_mass_count": sum(mass > 0 for mass in masses.values()),
            "known_prior_mass": str(known_prior),
            "known_first_record_joint_mass": str(observed_joint),
            "omitted_prior_mass_upper_bound": str(omitted_prior),
            "first_record_probability_lower_bound": str(observed_joint),
            "first_record_probability_upper_bound": str(observed_joint + omitted_prior),
            "omitted_posterior_mass_upper_bound": str(bound),
            "omitted_posterior_mass_upper_bound_decimal": round(float(bound), 12),
            "known_second_law_equality_verified": True,
        })
    assert {tuple(row["first_charge_sites"]) for row in output_rows} == {(), (1,), (2,), (1, 2)}
    elapsed = time.process_time() - started
    assert elapsed <= manifest["budget"]["max_cpu_seconds"]
    assert sum(row["known_law_error_count"] for row in output_rows) <= manifest["budget"]["max_known_error_record_cells"]
    assert all(digest(LAB / path) == expected for path, expected in manifest["pinned_inputs"].items())
    return {
        "schema_version": 1,
        "id": manifest["id"],
        "status": "selected_flux_four_first_record_tail_bounds_verified",
        "contract_sha256": digest(MANIFEST),
        "runner_sha256": digest(Path(__file__)),
        "selected_flux_prior_mass": str(selected_sector_mass),
        "rows": output_rows,
        "counters": {"known_error_record_cells": sum(row["known_law_error_count"] for row in output_rows), "new_born_terms": 0, "new_second_laws": 0, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
        "cpu_seconds": round(elapsed, 6),
        "claim_boundary": "Rigorous omitted-posterior upper bounds for only four complete first records sharing one selected L=2 first-flux sector, p_X=1/10, ideal fixed two-action law. Does not evaluate omitted first laws, full-IID information, logical risk, noisy JIT, L=3 or threshold.",
    }


if __name__ == "__main__":
    result = run()
    output = LAB / "results/j8l-first-record-tail-certificate-2026-09-27.json"
    assert not output.exists(), "Refuse to overwrite an existing result"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "bounds": [(r["first_charge_sites"], r["omitted_posterior_mass_upper_bound_decimal"]) for r in result["rows"]], "cpu_seconds": result["cpu_seconds"]}))
