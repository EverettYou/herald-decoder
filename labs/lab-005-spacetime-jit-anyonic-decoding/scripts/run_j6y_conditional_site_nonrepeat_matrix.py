"""Registered exact conditional-site and nonrepeat local projector matrix."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6y-conditional-site-nonrepeat-matrix-2026-09-25.json"
RESULT = LAB / "results/j6y-conditional-site-nonrepeat-matrix-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6x_result": LAB / "results/j6x-full-first-dephasing-new-third-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_first(first_ops, flips):
    rows = []
    total = Fraction()
    for bits in assignments(len(first_ops)):
        mass = ordered_probability([(first_ops, bits)], flips)
        assert mass >= 0
        total += mass
        if mass:
            rows.append((bits, mass))
    assert total == 1
    return rows


def checked_second(first_ops, first_bits, first_mass, second_op, flips):
    law = {}
    for (bit,) in assignments(1):
        joint = ordered_probability([(first_ops, first_bits), ([second_op], (bit,))], flips)
        assert joint >= 0
        law[bit] = joint / first_mass
    assert sum(law.values(), Fraction()) == 1
    return law


def branch(spec, red, sites, flips, pair_rows, started, cap, path):
    physical, flux = red_boundary(red, spec["private_physical_red_edges"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pair_rows)
    assert first_eligible == [s for s, bit in enumerate(flux) if not bit]
    first_sites = sorted(s for s, mean in first_means.items() if mean == 0)
    expected = 2 if path else 6
    if len(first_sites) != expected or any(m != 1 for m in first_means.values() if m):
        return {"status": "censored_first_structure", "first_sites_private": first_sites}
    first_ops = [conjugated_star(sites[s], physical) for s in first_sites]
    first_rows = exact_first(first_ops, flips)
    action, _ = red_boundary(red, spec["first_public_action_red_edges"])
    second_error = physical ^ action
    second_eligible, _ = sector_sites(sites, second_error, flips, pair_rows)
    second_ops = {s: conjugated_star(sites[s], second_error) for s in second_eligible}
    cases = []
    for first_bits, first_mass in first_rows:
        if time.process_time() - started >= cap:
            return {"status": "censored_cpu_cap", "partial_rows_discarded": True}
        candidates = [(s, op) for s, op in sorted(second_ops.items()) if op not in first_ops]
        if path:
            candidates = [(s, op) for s, op in candidates
                          if 0 < checked_second(first_ops, first_bits, first_mass, op, flips)[1] < 1]
        if not candidates:
            cases.append({"first_public_bits": list(first_bits), "first_mass": str(first_mass),
                          "status": "censored_no_nonrepeat_conditional_second"})
            continue
        second_site, second_op = candidates[0]
        assert all(second_op[1:] != op[1:] for op in first_ops), "phase-equivalent second repeat"
        second_law = checked_second(first_ops, first_bits, first_mass, second_op, flips)
        row = {"first_public_bits": list(first_bits), "first_mass": str(first_mass),
               "status": "exact_second_local_law", "second_site_private": second_site,
               "second_operator_nonrepeated": True,
               "second_conditional_law": {str(k): str(v) for k, v in second_law.items()}}
        if path:
            row["third_action_cases"] = []
            for name, edges in spec["second_action_branches"].items():
                second_action, _ = red_boundary(red, edges)
                third_error = second_error ^ second_action
                third_eligible, _ = sector_sites(sites, third_error, flips, pair_rows)
                new_sites = sorted(set(third_eligible) - set(second_eligible))
                candidate_third = [(s, conjugated_star(sites[s], third_error)) for s in new_sites]
                candidate_third = [(s, op) for s, op in candidate_third
                                   if op not in first_ops + [second_op]]
                if not candidate_third:
                    row["third_action_cases"].append({"action": name, "status": "censored_no_new_nonrepeat_third"})
                    continue
                third_site, third_op = candidate_third[0]
                assert all(third_op[1:] != op[1:] for op in first_ops + [second_op]), (
                    "phase-equivalent third repeat")
                third_rows = []
                for second_bit, p2 in second_law.items():
                    if not p2:
                        continue
                    joint12 = first_mass * p2
                    third_law = {}
                    for (third_bit,) in assignments(1):
                        joint123 = ordered_probability([
                            (first_ops, first_bits), ([second_op], (second_bit,)),
                            ([third_op], (third_bit,))], flips)
                        assert joint123 >= 0
                        third_law[third_bit] = joint123 / joint12
                    assert sum(third_law.values(), Fraction()) == 1
                    third_rows.append({"second_public_bit": second_bit,
                                       "third_conditional_law": {str(k): str(v) for k, v in third_law.items()}})
                row["third_action_cases"].append({"action": name, "status": "exact_new_third_local_law",
                    "third_site_private": third_site, "third_operator_nonrepeated": True, "rows": third_rows})
        cases.append(row)
    assert sum((Fraction(row["first_mass"]) for row in cases), Fraction()) == 1
    return {"status": "exact_or_explicitly_censored_prefixes", "first_random_sites_private": first_sites,
            "positive_first_records": len(first_rows), "cases": cases}


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {key: digest(path) == contract["pinned_inputs"][key + "_sha256"]
            for key, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    prior = json.loads(INPUTS["j6x_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert prior["status"] == "passed_or_censored_two_independent_ideal_diagnostics"
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"] if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(red) == len(stars) == 36 and set(sites) == set(range(24))
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    pair_rows = state["pair_rows"]
    cap = contract["budget"]["max_cpu_seconds"]
    path = branch(contract["matrix"]["three_edge_path"], red, sites, flips,
                  pair_rows, started, cap, True)
    loop = branch(contract["matrix"]["loop"], red, sites, flips,
                  pair_rows, started, cap, False)
    return {"schema_version": 1, "id": contract["id"], "status": "bounded_exact_two_branch_matrix",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "three_edge_path": path, "loop": loop,
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0}, "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Ideal selected local second/third instruments only; first block complete on variable eligible sites, later blocks not complete public rounds; not a noisy physical D4 feedback kernel."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
