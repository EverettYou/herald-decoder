"""Capped full-first loop dephasing and new-third-site exact diagnostics."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star, eligible, moment
from run_j6o_full_binary_sequential_public_record import assert_eligible_commute, red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6x-full-first-dephasing-new-third-2026-09-25.json"
RESULT = LAB / "results/j6x-full-first-dephasing-new-third-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6w_result": LAB / "results/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sector_sites(sites: dict, error: int, flips: list[int], pair_rows: list[dict]):
    eligible_sites = [site for site in range(24) if eligible(sites[site], error)]
    assert_eligible_commute([sites[s]["center"] for s in eligible_sites], error, pair_rows)
    means = {site: moment([conjugated_star(sites[site], error)], flips)
             for site in eligible_sites}
    assert set(means.values()) <= {-1, 0, 1}
    return eligible_sites, means


def path_branch(contract: dict, red: dict, sites: dict, flips: list[int],
                pair_rows: list[dict], started: float) -> dict:
    spec = contract["matrix"]["three_edge_new_third"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pair_rows)
    assert first_eligible == [site for site, bit in enumerate(first_flux) if not bit]
    first_random = sorted(site for site, mean in first_means.items() if mean == 0)
    if len(first_random) > 2 or any(mean != 1 for mean in first_means.values() if mean):
        return {"status": "censored_first_structure", "first_random_sites_private": first_random}
    first_ops = [conjugated_star(sites[s], physical) for s in first_random]
    first_action, _ = red_boundary(red, spec["first_public_action"])
    middle = physical ^ first_action
    middle_eligible, middle_means = sector_sites(sites, middle, flips, pair_rows)
    second_sites = sorted(site for site, mean in middle_means.items() if mean == 0)[:2]
    if len(second_sites) != 2:
        return {"status": "censored_second_structure", "second_random_sites_private": second_sites}
    second_ops = [conjugated_star(sites[s], middle) for s in second_sites]
    cases = []
    for action, action_edges in spec["second_action_branches"].items():
        correction, _ = red_boundary(red, action_edges)
        final = middle ^ correction
        final_eligible, _ = sector_sites(sites, final, flips, pair_rows)
        new_sites = sorted(set(final_eligible) - set(middle_eligible))
        if not new_sites:
            cases.append({"action": action, "status": "censored_no_new_third_site"})
            continue
        third_site = new_sites[0]
        third_op = conjugated_star(sites[third_site], final)
        if third_op in first_ops + second_ops:
            cases.append({"action": action, "status": "censored_repeated_third_operator",
                          "third_site_private": third_site})
            continue
        rows = []
        first_mass_total = Fraction()
        for first_bits in assignments(len(first_ops)):
            first_mass = ordered_probability([(first_ops, first_bits)], flips)
            assert first_mass >= 0
            first_mass_total += first_mass
            if not first_mass:
                continue
            second_total = Fraction()
            for second_bits in assignments(len(second_ops)):
                joint12 = ordered_probability([(first_ops, first_bits),
                                               (second_ops, second_bits)], flips)
                assert joint12 >= 0
                second_total += joint12 / first_mass
                if not joint12:
                    continue
                third_total = Fraction()
                for third_bits in assignments(1):
                    joint123 = ordered_probability([(first_ops, first_bits),
                                                    (second_ops, second_bits),
                                                    ([third_op], third_bits)], flips)
                    assert joint123 >= 0
                    conditional = joint123 / joint12
                    third_total += conditional
                    rows.append({"first_bits_private": list(first_bits),
                                 "second_bits_private": list(second_bits),
                                 "joint_first_second": str(joint12),
                                 "third_bit_private": third_bits[0],
                                 "third_conditional_probability": str(conditional)})
                assert third_total == 1
            assert second_total == 1
            assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
        assert first_mass_total == 1
        by_second = {}
        for row in rows:
            key = tuple(row["second_bits_private"])
            first = tuple(row["first_bits_private"])
            dist = by_second.setdefault(key, {}).setdefault(first, {})
            dist[row["third_bit_private"]] = Fraction(row["third_conditional_probability"])
        comparable = [group for group in by_second.values() if len(group) > 1]
        comparison = ("no_comparable_first_records" if not comparable else
                      "dependent_at_fixed_second" if any(
                          len({tuple(sorted(dist.items())) for dist in group.values()}) > 1
                          for group in comparable) else "independent_at_fixed_second")
        cases.append({"action": action, "status": "exact_new_third_local_law",
                      "public_second_action_red_edge_ids": action_edges,
                      "third_site_private": third_site,
                      "third_new_relative_to_second": True,
                      "third_operator_nonrepeated": True,
                      "first_dependence_given_second": comparison,
                      "rows": rows})
    return {"status": "passed_or_explicitly_censored_action_branches",
            "first_random_sites_private": first_random,
            "second_random_sites_private": second_sites,
            "cases": cases}


def loop_branch(contract: dict, red: dict, sites: dict, flips: list[int],
                pair_rows: list[dict], previous: dict, started: float) -> dict:
    spec = contract["matrix"]["loop_full_first_dephasing"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pair_rows)
    assert first_eligible == [site for site, bit in enumerate(first_flux) if not bit]
    first_random = sorted(site for site, mean in first_means.items() if mean == 0)
    if len(first_random) != 6 or any(mean != 1 for mean in first_means.values() if mean):
        return {"status": "censored_first_structure", "first_random_sites_private": first_random}
    assert first_random == previous["loop"]["all_random_first_sites_private"]
    first_ops = [conjugated_star(sites[s], physical) for s in first_random]
    correction, _ = red_boundary(red, spec["first_public_action"])
    residual = physical ^ correction
    second_eligible, _ = sector_sites(sites, residual, flips, pair_rows)
    second_site = spec["second_local_site"]
    assert second_site in second_eligible
    second_op = [conjugated_star(sites[second_site], residual)]
    repeated_first_site = second_site in first_random and (
        second_op[0] == first_ops[first_random.index(second_site)])
    rows = []
    first_total = Fraction()
    try:
        for first_bits in assignments(len(first_ops)):
            if time.process_time() - started >= contract["budget"]["max_cpu_seconds"]:
                raise TimeoutError("registered CPU cap")
            first_mass = ordered_probability([(first_ops, first_bits)], flips)
            assert first_mass >= 0
            first_total += first_mass
            if not first_mass:
                continue
            second_total = Fraction()
            for second_bits in assignments(1):
                joint = ordered_probability([(first_ops, first_bits),
                                             (second_op, second_bits)], flips)
                assert joint >= 0
                conditional = joint / first_mass
                second_total += conditional
                rows.append({"full_first_variable_bits_private": list(first_bits),
                             "full_first_probability": str(first_mass),
                             "second_local_bit_private": second_bits[0],
                             "second_conditional_probability": str(conditional)})
            assert second_total == 1
        assert first_total == 1
    except TimeoutError:
        return {"status": "censored_registered_cpu_cap", "first_random_sites_private": first_random,
                "partial_rows_discarded": True}
    coarse = {}
    for row in rows:
        bits = tuple(row["full_first_variable_bits_private"])
        first_key = bits[:2]
        first_mass = Fraction(row["full_first_probability"])
        joint = first_mass * Fraction(row["second_conditional_probability"])
        masses = coarse.setdefault(first_key, {1: Fraction(), -1: Fraction()})
        masses[row["second_local_bit_private"]] += joint
    coarse_rows = []
    for first_key, masses in sorted(coarse.items()):
        denominator = sum(masses.values(), Fraction())
        assert denominator > 0
        coarse_rows.append({"selected_first_bits_private": list(first_key),
                            "full_first_dephased_second_plus": str(masses[1] / denominator)})
    local_case = next(case for case in previous["loop"]["cases"]
                      if case["action"] == "correct_edge_0")
    assert local_case["first_local_sites_private"] == first_random[:2]
    assert local_case["second_local_sites_private"][0] == second_site
    local_plus = {}
    for row in local_case["rows"]:
        if row["second_local_charge"][0] != 0:
            continue
        key = tuple(1 if bit == 0 else -1 for bit in row["first_local_charge"])
        local_plus[key] = local_plus.get(key, Fraction()) + Fraction(
            row["second_conditional_probability"])
    assert set(local_plus) == {tuple(row["selected_first_bits_private"]) for row in coarse_rows}
    for row in coarse_rows:
        row["selected_only_second_plus"] = str(local_plus[tuple(row["selected_first_bits_private"])])
        row["difference_full_minus_selected"] = str(
            Fraction(row["full_first_dephased_second_plus"]) -
            Fraction(row["selected_only_second_plus"]))
    return {"status": "exact_full_first_one_site_second_law",
            "first_random_sites_private": first_random,
            "positive_full_first_records": len({tuple(row["full_first_variable_bits_private"])
                                                for row in rows}),
            "second_operator_repeats_first_site": repeated_first_site,
            "full_second_public_record_status": "not_computed_one_site_only",
            "rows": rows, "coarse_contrast": coarse_rows}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    previous = json.loads(INPUTS["j6w_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert previous["status"] == "passed_two_local_ideal_fixture_branches_no_general_kernel"
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"]
           if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(red) == len(stars) == 36 and set(sites) == set(range(24))
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    pair_rows = state["pair_rows"]
    path = path_branch(contract, red, sites, flips, pair_rows, started)
    loop = loop_branch(contract, red, sites, flips, pair_rows, previous, started)
    return {"schema_version": 1, "id": contract["id"],
            "status": "passed_or_censored_two_independent_ideal_diagnostics",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "three_edge_new_third": path, "loop_full_first_dephasing": loop,
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "First six-site loop record is complete only for initial ideal eligible stars; the next record measures one selected star. Three-edge third record measures one newly eligible star, not a full public round. Neither is a noisy general D4 feedback kernel."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
