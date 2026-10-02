"""Exact first-record feasibility matrix; no second law or stochastic sampling."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
CONTRACT = LAB / "manifests/j8a-alternate-first-record-mass-matrix-2026-09-27.json"
RESULT = LAB / "results/j8a-alternate-first-record-mass-matrix-2026-09-27.json"
INPUTS = {
    "r6af_contract": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j7t_result": LAB / "results/j7t-candidate-prior-cost-matrix-2026-09-27.json",
    "j7x_result": LAB / "results/j7x-all-error-operator-discriminator-2026-09-27.json",
    "j7z_result": LAB / "results/j7z-higher-order-second-law-2026-09-27.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "probability_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    checks_before = {key: digest(path) == contract["pinned_inputs"][key + "_sha256"]
                     for key, path in INPUTS.items()}
    assert all(checks_before.values()), checks_before
    old = {key: json.loads(INPUTS[key].read_text()) for key in
           ("r6af_contract", "j7m_result", "j7t_result", "j7x_result", "j7z_result", "j6l_result", "j6m_result")}
    assert "IID red-X edge errors" in old["r6af_contract"]["frozen_model"]["physical_channel"]
    assert old["j7z_result"]["different_complete_law_candidate_action_cells"] == 0
    spec, budget = contract["matrix"], contract["budget"]
    assert spec["base_error_private"] == [0, 4, 3]
    assert spec["first_variable_sites_base_private"] == [1, 2]
    assert spec["alternate_charge_sites"] == [[1], [2], [1, 2]]
    assert spec["public_actions_reserved_for_followup"] == [[0], [1, 30, 32, 34, 35]]
    errors = [spec["base_error_private"]] + [row["candidate_initial_error_red_edges_private"]
            for row in old["j7t_result"]["candidate_rows"]]
    assert len(errors) == 13 == len({tuple(row) for row in errors})
    assert errors == [row["initial_error_red_edges_private"] for row in old["j7x_result"]["rows"]]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    first_flux = old["j7m_result"]["first_public"]["flux"]
    assert len(first_flux) == 24 and old["j7m_result"]["first_public"]["charge"] == [0] * 24
    usage = 0
    rows = []
    for error_index, edges in enumerate(errors):
        physical, flux = red_boundary(red, edges)
        assert flux == first_flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [i for i, bit in enumerate(flux) if bit == 0]
        assert all(mean != -1 for mean in means.values())
        variable = sorted(i for i, mean in means.items() if mean == 0)
        assert variable == old["j7x_result"]["rows"][error_index]["first_variable_sites_private"]
        assert len(variable) <= budget["max_first_variable_sites"]
        operators = [conjugated_star(sites[site], physical) for site in variable]
        cases = []
        for charge_sites in [[], *spec["alternate_charge_sites"]]:
            charge = [int(i in charge_sites) for i in range(24)]
            vacuum = [int(not (flux[i] or charge[i])) for i in range(24)]
            assert all(not (flux[i] and charge[i]) for i in range(24))
            conflict = any(means[site] == 1 for site in charge_sites)
            if conflict:
                mass = Fraction(0)
                terms = 0
                reason = "deterministic_plus_conflict"
            else:
                terms = 1 << len(variable)
                assert usage + terms <= budget["max_ordered_first_terms"]
                assert time.process_time() - started < budget["max_cpu_seconds"]
                eigenvalues = tuple(-1 if site in charge_sites else 1 for site in variable)
                mass = ordered_probability([(operators, eigenvalues)], flips)
                usage += terms
                assert 0 <= mass <= 1
                reason = "exact_projector"
            if not charge_sites:
                expected = (Fraction(old["j7m_result"]["first_public_mass"]) if error_index == 0 else
                            Fraction(old["j7t_result"]["candidate_rows"][error_index - 1]["selected_first_public_mass_given_candidate"]))
                assert mass == expected > 0
            cases.append({"first_public": {"flux": flux, "charge": charge, "vacuum": vacuum},
                          "charge_sites": charge_sites, "mass": str(mass), "positive": mass > 0,
                          "terms": terms, "reason": reason})
        if error_index == 0:
            assert [Fraction(case["mass"]) for case in cases] == [Fraction(1, 4)] * 4
            assert sum(Fraction(case["mass"]) for case in cases) == 1
        rows.append({"error_edges_private": edges, "first_variable_sites_private": variable,
                     "cases": cases})
    positive_candidate_counts = [sum(row["cases"][i]["positive"] for row in rows[1:])
                                 for i in range(1, 4)]
    assert len(rows) == 13 and len(rows[0]["cases"]) == 4
    checks_after = {key: digest(path) == contract["pinned_inputs"][key + "_sha256"]
                    for key, path in INPUTS.items()}
    assert all(checks_after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert time.process_time() - started < budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "alternate_first_record_feasibility_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": checks_before, "pinned_input_checks_after": checks_after,
            "first_public_alternative_charge_sites": spec["alternate_charge_sites"],
            "positive_candidate_counts_by_alternative": positive_candidate_counts,
            "rows": rows,
            "counters": {"ordered_first_terms": usage, "complete_second_laws": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Exact first-record feasibility only for thirteen pre-existing errors and all three other base-positive complete first records on one ideal L=2 orbit. No second-record discrimination, full-IID information, unconditional logical risk, noisy JIT or threshold inference.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
