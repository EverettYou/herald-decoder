"""Exact local ideal loop and ordered three-block projector fixtures.

Only the selected flux-free stars are measured. This is not a marginal of a
complete public measurement, because omitted projector dephasing is absent.
"""

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


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25.json"
RESULT = LAB / "results/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6v_result": LAB / "results/j6v-loop-stateful-prerequisite-audit-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered_probability(blocks: list[tuple[list[tuple[int, int, int]], tuple[int, ...]]],
                        flips: list[int]) -> Fraction:
    """Exact <P1 ... Pn ... P1> for selected-star projectors only."""
    assert all(len(ops) == len(bits) for ops, bits in blocks)
    forward = [(op, bit) for ops, bits in blocks for op, bit in zip(ops, bits)]
    reverse = [(op, bit) for ops, bits in reversed(blocks[:-1])
               for op, bit in reversed(list(zip(ops, bits)))]
    factors = forward + reverse
    total = 0
    for subset in range(1 << len(factors)):
        selected = []
        sign = 1
        for index, (operator, eigenvalue) in enumerate(factors):
            if (subset >> index) & 1:
                selected.append(operator)
                sign *= eigenvalue
        total += sign * moment(selected, flips)
    return Fraction(total, 1 << len(factors))


def selected_random_sites(sites: dict, physical: int, cap: int, flips: list[int]) -> tuple[list[int], list[int]]:
    eligible_sites = [site for site in range(24) if eligible(sites[site], physical)]
    random = [site for site in eligible_sites
              if moment([conjugated_star(sites[site], physical)], flips) == 0]
    assert all(moment([conjugated_star(sites[site], physical)], flips) in (-1, 0, 1)
               for site in eligible_sites)
    return eligible_sites, random[:cap]


def exact_two_block(physical: int, first_sites: list[int], residual: int,
                    second_sites: list[int], sites: dict, flips: list[int],
                    started: float, cpu_cap: int) -> dict:
    first_ops = [conjugated_star(sites[site], physical) for site in first_sites]
    second_ops = [conjugated_star(sites[site], residual) for site in second_sites]
    rows = []
    for first_bits in assignments(len(first_ops)):
        first_mass = ordered_probability([(first_ops, first_bits)], flips)
        assert first_mass >= 0
        if not first_mass:
            continue
        total = Fraction()
        for second_bits in assignments(len(second_ops)):
            joint = ordered_probability([(first_ops, first_bits),
                                         (second_ops, second_bits)], flips)
            assert joint >= 0
            conditional = joint / first_mass
            total += conditional
            rows.append({"first_local_charge": [int(bit == -1) for bit in first_bits],
                         "first_probability": str(first_mass),
                         "second_local_charge": [int(bit == -1) for bit in second_bits],
                         "second_conditional_probability": str(conditional)})
        assert total == 1
        assert time.process_time() - started < cpu_cap
    first_support = {tuple(row["first_local_charge"]): Fraction(row["first_probability"])
                     for row in rows}
    assert sum(first_support.values(), Fraction()) == 1
    return {"first_local_sites_private": first_sites,
            "second_local_sites_private": second_sites, "rows": rows,
            "positive_first_record_count": len(first_support)}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    prior = json.loads(INPUTS["j6v_result"].read_text())
    assert state["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert prior["status"] == "passed_two_prerequisite_diagnostics_stateful_kernel_absent"
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"]
           if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(red) == 36 and len(stars) == 36 and set(sites) == set(range(24))
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    pair_rows = state["pair_rows"]
    cpu_cap = contract["budget"]["max_cpu_seconds"]

    loop_spec = contract["matrix"]["loop"]
    loop_edges = loop_spec["private_physical_red_edges"]
    assert loop_edges == prior["simple_loop_geometry"]["canonical_red_edge_ids_private"]
    physical, first_flux = red_boundary(red, loop_edges)
    first_eligible, first_local = selected_random_sites(sites, physical, 2, flips)
    assert first_eligible == [site for site, bit in enumerate(first_flux) if bit == 0]
    assert_eligible_commute([sites[s]["center"] for s in first_local], physical, pair_rows)
    all_random_first = [site for site in first_eligible
                        if moment([conjugated_star(sites[site], physical)], flips) == 0]
    loop_cases = []
    for action, action_edges in loop_spec["actions"].items():
        action_mask, _ = red_boundary(red, action_edges)
        residual = physical ^ action_mask
        second_edges = [edge for edge in loop_edges if edge not in action_edges]
        _, second_flux = red_boundary(red, second_edges)
        second_eligible, second_local = selected_random_sites(sites, residual, 2, flips)
        assert second_eligible == [site for site, bit in enumerate(second_flux) if bit == 0]
        assert_eligible_commute([sites[s]["center"] for s in second_local], residual, pair_rows)
        case = exact_two_block(physical, first_local, residual, second_local,
                               sites, flips, started, cpu_cap)
        case.update({"action": action, "public_action_red_edge_ids": action_edges,
                     "full_public_law_status": ("censored_first_random_site_cap"
                         if len(all_random_first) > 4 else "not_computed_local_fixture_only")})
        loop_cases.append(case)

    three = contract["matrix"]["three_block"]
    pair_physical, _ = red_boundary(red, three["private_physical_red_edges"])
    first_action_mask, _ = red_boundary(red, three["first_public_action_red_edges"])
    middle_residual = pair_physical ^ first_action_mask
    first_site = three["first_local_site"]
    second_site = three["second_local_site"]
    assert eligible(sites[first_site], pair_physical)
    assert eligible(sites[second_site], middle_residual)
    first_op = [conjugated_star(sites[first_site], pair_physical)]
    second_op = [conjugated_star(sites[second_site], middle_residual)]
    three_cases = []
    for action, edges in three["third_action_branches"].items():
        second_action_mask, _ = red_boundary(red, edges)
        final_residual = middle_residual ^ second_action_mask
        third_sites = three["third_local_sites"][action]
        assert all(eligible(sites[site], final_residual) for site in third_sites)
        assert_eligible_commute([sites[site]["center"] for site in third_sites],
                                final_residual, pair_rows)
        third_ops = [conjugated_star(sites[site], final_residual) for site in third_sites]
        rows = []
        positive_first_second = 0
        for first_bits in assignments(1):
            first_mass = ordered_probability([(first_op, first_bits)], flips)
            assert first_mass >= 0
            if not first_mass:
                continue
            second_total = Fraction()
            for second_bits in assignments(1):
                joint12 = ordered_probability([(first_op, first_bits),
                                               (second_op, second_bits)], flips)
                assert joint12 >= 0
                second_total += joint12 / first_mass
                if not joint12:
                    continue
                positive_first_second += 1
                third_total = Fraction()
                for third_bits in assignments(len(third_ops)):
                    joint123 = ordered_probability([(first_op, first_bits),
                                                    (second_op, second_bits),
                                                    (third_ops, third_bits)], flips)
                    assert joint123 >= 0
                    conditional = joint123 / joint12
                    third_total += conditional
                    rows.append({"first_local_charge": int(first_bits[0] == -1),
                                 "second_local_charge": int(second_bits[0] == -1),
                                 "first_second_joint_probability": str(joint12),
                                 "third_local_charge": [int(bit == -1) for bit in third_bits],
                                 "third_conditional_probability": str(conditional)})
                assert third_total == 1
            assert second_total == 1
            assert time.process_time() - started < cpu_cap
        assert positive_first_second > 0
        three_cases.append({"action": action, "public_second_action_red_edge_ids": edges,
                            "third_local_sites_private": third_sites,
                            "second_operator_repeated_at_third_site_0":
                                second_op[0] == conjugated_star(sites[0], final_residual),
                            "positive_first_second_count": positive_first_second,
                            "rows": rows})
    assert len(loop_cases) == 2 and len(three_cases) == 2
    assert time.process_time() - started < cpu_cap
    return {"schema_version": 1, "id": contract["id"],
            "status": "passed_two_local_ideal_fixture_branches_no_general_kernel",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "loop": {"physical_edges_private": loop_edges,
                     "all_random_first_sites_private": all_random_first,
                     "selected_first_sites_private": first_local,
                     "cases": loop_cases},
            "three_block": {"physical_edges_private": three["private_physical_red_edges"],
                            "selected_first_site_private": first_site,
                            "selected_second_site_private": second_site,
                            "cases": three_cases},
            "checks": {"actual_sector_eligibility_and_commutation": True,
                       "exact_rational_normalization": True,
                       "selected_local_stars_only_not_full_public_marginal": True,
                       "five_round_caller_unchanged": True},
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "One fixed ideal J6M orbit with only selected local projectors measured. Omitted full-record dephasing, noisy rounds, logical-sector averaging and physical feedback kernel remain unresolved."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
