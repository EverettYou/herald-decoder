"""Exact prior-mass coverage envelope for four selected-flux first records."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction
from math import comb
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8n-four-record-channel-coverage-2026-09-27.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((LAB / path).read_text())


def decimal(value: Fraction) -> float:
    return round(float(value), 15)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == expected
               for path, expected in contract["pinned_inputs"].items())
    prior = load("results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json")
    known = load("results/j8l-first-record-tail-certificate-2026-09-27.json")
    bounded = load("results/j8m-structural-tail-and-cost-screen-verified-2026-09-27.json")
    assert prior["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert (prior["boundary_rank"], prior["kernel_dimension"],
            prior["same_first_flux_error_count"]) == (23, 13, 8192)
    assert sum((Fraction(comb(36, w) * 9 ** (36 - w), 10 ** 36)
                for w in range(37)), Fraction()) == 1
    W = Fraction(prior["selected_flux_prior_mass"])
    assert W == Fraction(known["selected_flux_prior_mass"]) and 0 < W < 1
    first_rows = {tuple(row["first_charge_sites"]): row for row in known["rows"]}
    bound_rows = {tuple(row["first_charge_sites"]): row for row in bounded["rows"]}
    assert len(first_rows) == len(bound_rows) == 4
    assert set(first_rows) == set(bound_rows) == {(), (1,), (2,), (1, 2)}
    first_flux = None
    A = U = Fraction()
    cells = []
    for sites in ((), (1,), (2,), (1, 2)):
        first, tail = first_rows[sites], bound_rows[sites]
        public = first["first_public"]
        assert set(public) == {"flux", "charge", "vacuum"}
        assert all(len(public[key]) == 24 for key in public)
        assert all(bit in (0, 1) for key in public for bit in public[key])
        assert tuple(i for i, charge in enumerate(public["charge"]) if charge) == sites
        assert all(vacuum == 1 - charge for vacuum, charge in
                   zip(public["vacuum"], public["charge"]))
        if first_flux is None:
            first_flux = public["flux"]
        assert public["flux"] == first_flux
        assert tail["omitted_error_count"] == 8192 - first["known_law_error_count"]
        a = Fraction(first["known_first_record_joint_mass"])
        u = Fraction(tail["one_site_omitted_joint_mass_upper_bound"])
        assert 0 < a and 0 <= u
        assert Fraction(tail["one_site_omitted_posterior_upper_bound"]) == u / (a + u)
        assert u <= Fraction(first["omitted_prior_mass_upper_bound"])
        A += a
        U += u
        cells.append({"first_charge_sites": list(sites), "known_joint_mass": str(a),
                      "omitted_joint_mass_upper_bound": str(u),
                      "record_prior_mass_lower_bound": str(a),
                      "record_prior_mass_upper_bound": str(a + u)})
    assert first_flux == first_rows[()]["first_public"]["flux"]
    assert 0 < A <= A + U < W
    other_flux = 1 - W
    other_charge_lower = W - A - U
    other_charge_upper = W - A
    four_given_flux_lower = A / W
    four_given_flux_upper = (A + U) / W
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    assert all(sha(LAB / path) == expected
               for path, expected in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "four_record_channel_coverage_envelope_verified",
        "contract_sha256": sha(CONTRACT),
        "runner_sha256": sha(Path(__file__)),
        "physical_prior": prior["physical_prior"],
        "selected_first_flux_prior_mass": str(W),
        "selected_first_flux_prior_mass_decimal": decimal(W),
        "four_complete_first_records": cells,
        "four_record_prior_mass_lower_bound": str(A),
        "four_record_prior_mass_upper_bound": str(A + U),
        "four_record_prior_mass_lower_bound_decimal": decimal(A),
        "four_record_prior_mass_upper_bound_decimal": decimal(A + U),
        "four_record_fraction_of_selected_flux_lower_bound": str(four_given_flux_lower),
        "four_record_fraction_of_selected_flux_upper_bound": str(four_given_flux_upper),
        "four_record_fraction_of_selected_flux_lower_bound_decimal": decimal(four_given_flux_lower),
        "four_record_fraction_of_selected_flux_upper_bound_decimal": decimal(four_given_flux_upper),
        "other_first_charge_same_flux_prior_mass_lower_bound": str(other_charge_lower),
        "other_first_charge_same_flux_prior_mass_upper_bound": str(other_charge_upper),
        "other_first_charge_same_flux_fraction_lower_bound_decimal": decimal(other_charge_lower / W),
        "other_first_charge_same_flux_fraction_upper_bound_decimal": decimal(other_charge_upper / W),
        "other_first_flux_prior_mass": str(other_flux),
        "other_first_flux_prior_mass_decimal": decimal(other_flux),
        "counters": {"reused_complete_first_records": 4,
                     "new_born_terms": 0, "new_first_masses": 0,
                     "new_second_laws": 0, "histories": 0,
                     "schedule_arms": 0, "bootstraps": 0},
        "cpu_seconds": round(elapsed, 6),
        "claim_boundary": "Exact interval for prior mass of four existing complete first records, residual first-charge mass in one selected first-flux sector, and exact complementary first-flux mass at L=2 p_X=1/10. No other first law, second law, full-IID information/risk, noisy JIT, size scaling or threshold was evaluated."
    }


if __name__ == "__main__":
    output = LAB / "results/j8n-four-record-channel-coverage-2026-09-27.json"
    assert not output.exists(), "Refuse to overwrite an existing result"
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "four_record_fraction_of_selected_flux": [
            result["four_record_fraction_of_selected_flux_lower_bound_decimal"],
            result["four_record_fraction_of_selected_flux_upper_bound_decimal"]],
        "other_first_flux_prior_mass": result["other_first_flux_prior_mass_decimal"],
        "cpu_seconds": result["cpu_seconds"]}))
