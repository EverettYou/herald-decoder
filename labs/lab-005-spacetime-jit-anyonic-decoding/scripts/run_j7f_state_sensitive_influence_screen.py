"""Bounded exact first-postselected state-sensitive influence screen."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star, eligible, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j7d_cross_round_commutation_screen import cross_vacuum_anticommutes


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7f-state-sensitive-influence-screen-2026-09-25.json"
RESULT = LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7d_result": LAB / "results/j7d-cross-round-commutation-screen-2026-09-25.json",
    "j7e_result": LAB / "results/j7e-two-edge-complete-next-law-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget = contract["budget"]
    pins_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                   for name, path in INPUTS.items()}
    assert all(pins_before.values()), pins_before
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    screen = json.loads(INPUTS["j7d_result"].read_text())
    prior = json.loads(INPUTS["j7e_result"].read_text())
    assert orbit["operator_counts"]["outer_x_flip_rank"] == 33
    assert screen["status"] == "finite_structural_opening_found"
    assert prior["status"] == "exact_two_edge_complete_public_discriminator_closed"
    assert set(prior["matrix"]["exact_total_variation_by_first_charge"].values()) == {"0"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"]
           if q["color"] == "red"}
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    assert len(stars) == 36 and set(sites) == set(range(24)) and len(red) == 36
    fixtures = tuple(contract["matrix"][name] | {"fixture": name} for name in (
        "two_edge_path", "three_edge_chain", "four_edge_path",
        "four_edge_branch", "six_edge_loop"))
    assert len(fixtures) == budget["max_fixtures"]
    usage = {"ordered_moment_terms": 0}

    def exact(blocks):
        terms = 1 << (2 * sum(len(ops) for ops, _ in blocks[:-1]) +
                      len(blocks[-1][0]))
        if usage["ordered_moment_terms"] + terms > budget["max_ordered_moment_terms"]:
            raise RuntimeError("registered_ordered_moment_cap")
        if time.process_time() - started >= budget["max_cpu_seconds"]:
            raise RuntimeError("registered_cpu_cap")
        usage["ordered_moment_terms"] += terms
        return ordered_probability(blocks, flips)

    rows = []
    for spec in fixtures:
        name, edges, action, future = (spec[k] for k in
            ("fixture", "physical", "action", "future"))
        source_rows = [row for row in screen["branch_rows"]
                       if row["fixture"] == name and
                       row["public_action_edges"] == action and
                       row["future_fault_edge_private"] == future]
        assert len(source_rows) == 1
        source = source_rows[0]
        second_site, next_site = spec["expected_witness"]
        assert source["first_witness_sites_private"] == [second_site, next_site]
        physical, first_flux = red_boundary(red, edges)
        action_mask, _ = red_boundary(red, action)
        future_mask, _ = red_boundary(red, [future])
        residual, final = physical ^ action_mask, physical ^ action_mask ^ future_mask
        final_edges = sorted(set(edges) ^ set(action) ^ {future})
        assert sorted(source["final_edges_private"]) == final_edges
        _, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
        _, next_flux = red_boundary(red, final_edges)
        first_eligible = [s for s in range(24) if eligible(sites[s], physical)]
        second_eligible = [s for s in range(24) if eligible(sites[s], residual)]
        next_eligible = [s for s in range(24) if eligible(sites[s], final)]
        assert first_eligible == [s for s, b in enumerate(first_flux) if b == 0]
        assert second_eligible == source["second_eligible_sites_private"]
        assert next_eligible == source["next_eligible_sites_private"]
        assert second_eligible == [s for s, b in enumerate(second_flux) if b == 0]
        assert next_eligible == [s for s, b in enumerate(next_flux) if b == 0]
        second_ops = {s: conjugated_star(sites[s], residual) for s in second_eligible}
        next_op = conjugated_star(sites[next_site], final)
        anti_sites = [s for s, op in second_ops.items()
                      if cross_vacuum_anticommutes(op, next_op)]
        assert second_site in anti_sites and anti_sites
        first_random, first_ops, charge = [], [], [0] * 24
        for s in first_eligible:
            op = conjugated_star(sites[s], physical)
            mean = moment([op], flips)
            assert mean in (-1, 0, 1)
            if mean == 0:
                first_random.append(s)
                first_ops.append(op)
            else:
                charge[s] = int(mean == -1)
        first_public = public_record(first_flux, charge)
        first_block = (first_ops, (1,) * len(first_ops))
        first_mass = exact([first_block])
        if first_mass <= 0:
            raise RuntimeError("selected_complete_first_record_zero_mass:" + name)
        plus_mass = exact([first_block, ([next_op], (1,))])
        baseline_mean = 2 * plus_mass / first_mass - 1
        assert -1 <= baseline_mean <= 1
        # A full commuting second block contains an anticommuting member,
        # so its nonselective dephasing sends this next operator to zero.
        after_second_mean = Fraction(0)
        direct_sum = None
        if name == "two_edge_path":
            op = second_ops[second_site]
            direct_sum = sum((exact([first_block, ([op], (bit,)),
                                      ([next_op], (1,))]) for bit in (1, -1)),
                             Fraction())
            assert direct_sum / first_mass == Fraction(1, 2)
        rows.append({"fixture": name, "physical_edges_private": edges,
                     "public_action_edges": action, "future_fault_edge_private": future,
                     "final_edges_private": final_edges,
                     "first_public": first_public,
                     "first_random_sites_private": first_random,
                     "first_mass": str(first_mass),
                     "full_second_eligible_sites_private": second_eligible,
                     "anticommuting_second_sites_private": anti_sites,
                     "next_witness_site_private": next_site,
                     "baseline_next_mean": str(baseline_mean),
                     "after_full_second_marginal_next_mean": str(after_second_mean),
                     "one_site_influence": str(abs(baseline_mean)),
                     "direct_two_edge_plus_joint_sum": (
                         None if direct_sum is None else str(direct_sum))})
    pins_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                  for name, path in INPUTS.items()}
    assert all(pins_after.values()), pins_after
    return {"schema_version": 1, "id": contract["id"],
            "status": ("selected_record_state_sensitive_opening" if any(
                Fraction(row["one_site_influence"]) > 0 for row in rows)
                else "selected_record_one_site_null"),
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": pins_before,
            "pinned_input_checks_after": pins_after,
            "rows": rows, "usage": usage,
            "j7e_exact_complete_public_tv_control": "0 at both first records",
            "inference_boundary": "Exact one-selected-first-record and one-next-site ideal marginal screen on five finite topologies. This is neither a matched-history full-public law nor a general state-sufficiency or noisy schedule claim.",
            "stochastic_histories": 0, "schedule_arm_evaluations": 0,
            "bootstrap_replicates": 0,
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
