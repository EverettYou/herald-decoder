"""Prospective bounded same-first-record two-error feasibility screen."""

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


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7s-same-first-error-pair-preflight-2026-09-27.json"
RESULT = LAB / "results/j7s-same-first-error-pair-preflight-2026-09-27.json"
INPUTS = {
    "r6af_contract": ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json",
    "j7l_result": LAB / "results/j7l-alternative-same-flux-loop-screen-2026-09-26.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "ordered_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
    "public_record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_first_mass(edges: list[int], *, red: dict, sites: dict,
                        flips: list[int], pairs: list[dict],
                        expected_flux: list[int], usage: dict,
                        budget: dict, started: float) -> tuple[Fraction | None, int, str]:
    error, flux = red_boundary(red, edges)
    assert flux == expected_flux
    eligible, means = sector_sites(sites, error, flips, pairs)
    assert eligible == [site for site, bit in enumerate(flux) if bit == 0]
    variable = sorted(site for site, mean in means.items() if mean == 0)
    if any(mean == -1 for mean in means.values()):
        return Fraction(0), len(variable), "deterministic_charge_conflict"
    if len(variable) > budget["max_first_variable_sites"]:
        return None, len(variable), "registered_variable_site_cap"
    terms = 1 << len(variable)
    if usage["ordered_moment_terms"] + terms > budget["max_ordered_moment_terms"]:
        return None, len(variable), "registered_ordered_term_cap"
    if time.process_time() - started >= budget["max_cpu_seconds"]:
        return None, len(variable), "registered_cpu_cap"
    operators = [conjugated_star(sites[site], error) for site in variable]
    mass = ordered_probability([(operators, (1,) * len(operators))], flips)
    usage["ordered_moment_terms"] += terms
    assert 0 <= mass <= 1
    return mass, len(variable), "evaluated"


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    source = json.loads(INPUTS["r6af_contract"].read_text())
    assert "IID red-X edge errors" in source["frozen_model"]["physical_channel"]
    previous = json.loads(INPUTS["j7m_result"].read_text())
    loops = json.loads(INPUTS["j7l_result"].read_text())
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    assert previous["status"] == "five_site_complete_second_charge_law_closed"
    assert loops["unique_simple_six_edge_cycle_count"] == budget["max_cycles"] == 12
    assert loops["homologically_trivial_cycle_count"] == budget["max_cycles"]
    assert spec["base_private_error_red_edges"] == [0, 4, 3]
    assert spec["public_actions"] == [[0], [1, 30, 32, 34, 35]]
    first = previous["first_public"]
    assert first["charge"] == [0] * 24 and first["vacuum"] == [1] * 24
    red, sites, flips, pairs = setup(embedding, orbit)
    assert len(red) == 36 and len(sites) == 24
    base_error, base_flux = red_boundary(red, spec["base_private_error_red_edges"])
    assert base_flux == first["flux"]
    usage = {"ordered_moment_terms": 0}
    base_mass, base_v, base_status = selected_first_mass(
        spec["base_private_error_red_edges"], red=red, sites=sites,
        flips=flips, pairs=pairs, expected_flux=base_flux, usage=usage,
        budget=budget, started=started)
    assert base_status == "evaluated" and base_mass == Fraction(1, 4)
    assert base_v == 2 and str(base_mass) == previous["first_public_mass"]
    cycles = sorted(tuple(row["loop_red_edges_private"]) for row in loops["rows"])
    assert len(cycles) == len(set(cycles)) == budget["max_cycles"]
    rows = []
    for cycle in cycles:
        row = next(row for row in loops["rows"] if tuple(row["loop_red_edges_private"]) == cycle)
        assert row["loop_homologically_trivial"] and not row["loop_winding_vectors"]
        candidate = sorted(set(spec["base_private_error_red_edges"]) ^ set(cycle))
        candidate_mask, candidate_flux = red_boundary(red, candidate)
        assert candidate_mask == base_error ^ red_boundary(red, list(cycle))[0]
        assert candidate_flux == base_flux
        mass, variable_count, status = selected_first_mass(
            candidate, red=red, sites=sites, flips=flips, pairs=pairs,
            expected_flux=base_flux, usage=usage, budget=budget, started=started)
        rows.append({"cycle_red_edges_private": list(cycle),
                     "candidate_initial_error_red_edges_private": candidate,
                     "same_complete_first_flux": True,
                     "first_variable_site_count_private": variable_count,
                     "selected_first_public_mass_given_candidate": (
                         None if mass is None else str(mass)),
                     "status": status,
                     "positive_selected_first_mass": mass is not None and mass > 0})
        if status in {"registered_ordered_term_cap", "registered_cpu_cap"}:
            break
    assert len(rows) <= budget["max_cycles"]
    positive = [row for row in rows if row["positive_selected_first_mass"]]
    selected = positive[0] if len(rows) == budget["max_cycles"] else None
    posterior = None
    if selected is not None:
        p = Fraction(spec["iid_red_x_rate"])
        def weight(edges: list[int]) -> Fraction:
            return p ** len(edges) * (1 - p) ** (len(red) - len(edges))
        base_joint = weight(spec["base_private_error_red_edges"]) * base_mass
        other_joint = weight(selected["candidate_initial_error_red_edges_private"]) * \
            Fraction(selected["selected_first_public_mass_given_candidate"])
        assert base_joint > 0 and other_joint > 0
        posterior = {"base_error_weight_given_pair_and_first": str(base_joint / (base_joint + other_joint)),
                     "candidate_error_weight_given_pair_and_first": str(other_joint / (base_joint + other_joint)),
                     "conditioning": "IID prior restricted to the two predeclared supports, then selected complete first record; not the full IID-channel posterior"}
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": ("same_first_error_pair_found" if selected else
                       "candidate_screen_censored" if len(rows) < budget["max_cycles"] or any(
                           row["status"] == "registered_variable_site_cap" for row in rows)
                       else "no_positive_shortest_cycle_pair"),
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "base_first_public_mass": str(base_mass),
            "cycles_examined": len(rows), "positive_candidate_count": len(positive),
            "candidate_rows": rows,
            "selected_candidate_initial_error_red_edges_private": (
                None if selected is None else selected["candidate_initial_error_red_edges_private"]),
            "selected_pair_posterior": posterior,
            "usage": usage,
            "counters": {"complete_second_law_evaluations": 0,
                         "stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "claim_boundary": "Only first-record positivity and a conditional two-support prior were screened. No second/next public law for the candidate, mutual information, unconditional risk, policy benefit, noisy schedule or threshold is established.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
