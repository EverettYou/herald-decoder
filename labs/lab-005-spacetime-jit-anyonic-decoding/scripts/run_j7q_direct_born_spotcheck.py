"""Three prospectively frozen direct Born checks of J7P's next-law algebra."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7q-direct-born-spotcheck-2026-09-27.json"
RESULT = LAB / "results/j7q-direct-born-spotcheck-2026-09-27.json"
INPUTS = {
    "j7p_result": LAB / "results/j7p-next-operator-relation-matrix-2026-09-26.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j7n_result": LAB / "results/j7n-fixed-future-next-first-feasibility-2026-09-26.json",
    "j7m_contract": LAB / "manifests/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "ordered_probability_source": LAB / "scripts/run_j6w_loop_and_three_block_ideal_projector_matrix.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_mask(edges: list[int], red: dict[int, int]) -> int:
    value = 0
    for edge in edges:
        value ^= 1 << red[edge]
    return value


def prediction(site_class: dict, second_charge: list[int]) -> Fraction:
    if site_class["class"] == "fair_by_anticommutation":
        return Fraction(1, 2)
    assert site_class["class"] == "signed_repeat"
    predictions = {second_charge[row["second_site_private"]]
                   ^ int(row["charge_flipped"]) for row in site_class["relations"]}
    assert len(predictions) == 1
    return Fraction(int(predictions.pop() == 0))


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    matrix, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7p, j7m, j7n, j7m_contract, embedding, orbit = (
        json.loads(INPUTS[name].read_text()) for name in
        ("j7p_result", "j7m_result", "j7n_result", "j7m_contract",
         "j6l_result", "j6m_result"))
    assert j7p["status"] == "four_cell_operator_relation_matrix_closed"
    assert all(row["complete_next_law_reconstructed"] for row in j7p["cells"])
    assert j7n["status"] == "fixed_future_structural_cost_audit_closed"
    assert j7m["status"] == "five_site_complete_second_charge_law_closed"
    assert j7m["first_public_mass"] == "1/4"
    assert j7m_contract["matrix"]["physical_red_edges_private"] == [0, 4, 3]
    assert matrix["first_variable_sites_private"] == \
        j7m_contract["matrix"]["first_variable_sites_private"] == [1, 2]
    assert matrix["first_eigenvalues"] == j7m_contract["matrix"]["first_bits"] == [1, 1]
    assert matrix["selected_second_row_index"] == 0
    assert orbit["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    red = {q["lab004_red_edge_id"]: q["id"]
           for q in embedding["physical_qubits"] if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(name.split(":")[1]): star for name, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    flips = [sum(1 << qubit for qubit in star["outer_x_qubits"])
             for star in stars.values()]
    assert set(red) == set(range(36)) and set(sites) == set(range(24))
    assert len(flips) == 36
    physical = edge_mask([0, 4, 3], red)
    first_ops = [conjugated_star(sites[site], physical)
                 for site in matrix["first_variable_sites_private"]]
    first_block = (first_ops, tuple(matrix["first_eigenvalues"]))
    assert all(j7m["first_public"]["charge"][site] == 0
               for site in matrix["first_variable_sites_private"])
    usage = {"ordered_moment_terms": 0, "direct_born_probes": 0}
    probes = []
    for probe in matrix["probes"]:
        assert usage["direct_born_probes"] < budget["max_probes"]
        action, future = (probe[key] for key in
                          ("public_action_red_edges", "future_physical_red_edges_private"))
        prior = next(row for row in j7m["cells"]
                     if row["public_action_red_edges"] == action)
        j7n_cell = next(row for row in j7n["matrix"]
                        if row["public_action_red_edges"] == action
                        and row["future_physical_red_edges_private"] == future)
        reconstructed = next(row for row in j7p["cells"]
                             if row["public_action_red_edges"] == action
                             and row["future_physical_red_edges_private"] == future)
        assert sorted(set(j7n_cell["final_red_edges_private"]) ^ set(future)) == \
            prior["residual_red_edges_private"]
        second = prior["rows"][matrix["selected_second_row_index"]]
        public = second["public"]
        assert set(public) == {"flux", "charge", "vacuum"}
        assert public["flux"] == prior["second_public_flux"]
        assert public["vacuum"] == [1 - bit for bit in public["charge"]]
        assert all(bit == 0 for bit in public["charge"])
        second_mask = edge_mask(prior["residual_red_edges_private"], red)
        second_sites = prior["variable_second_sites_private"]
        second_ops = [conjugated_star(sites[site], second_mask)
                      for site in second_sites]
        second_bits = tuple(1 if public["charge"][site] == 0 else -1
                            for site in second_sites)
        next_site = probe["next_site_private"]
        assert j7n_cell["next_public_flux"][next_site] == 0
        next_mask = edge_mask(j7n_cell["final_red_edges_private"], red)
        next_op = conjugated_star(sites[next_site], next_mask)
        next_eigenvalue = 1 if probe["next_charge_bit"] == 0 else -1
        term_count = 1 << (2 * (len(first_ops) + len(second_ops)) + 1)
        assert term_count == probe["expected_ordered_terms"]
        usage["ordered_moment_terms"] += term_count
        assert usage["ordered_moment_terms"] <= budget["max_ordered_moment_terms"]
        assert usage["ordered_moment_terms"] <= matrix["prior_exact_term_ceiling"]
        joint = ordered_probability(
            [first_block, (second_ops, second_bits), ([next_op], (next_eigenvalue,))],
            flips)
        assert joint >= 0
        prefix_mass = Fraction(j7m["first_public_mass"]) * \
            Fraction(second["conditional_probability"])
        assert prefix_mass > 0
        conditional = joint / prefix_mass
        assert 0 <= conditional <= 1
        site_class = reconstructed["site_classes"][next_site]
        assert site_class["site_private"] == next_site
        predicted = prediction(site_class, public["charge"])
        assert predicted == Fraction(probe["expected_conditional_probability"])
        assert conditional == predicted
        usage["direct_born_probes"] += 1
        probes.append({"public_action_red_edges": action,
                       "future_physical_red_edges_private": future,
                       "selected_second_row_index": matrix["selected_second_row_index"],
                       "next_site_private": next_site,
                       "next_charge_bit": probe["next_charge_bit"],
                       "second_variable_sites_private": second_sites,
                       "selected_second_conditional_probability":
                           second["conditional_probability"],
                       "prefix_joint_mass": str(prefix_mass),
                       "direct_three_block_joint_mass": str(joint),
                       "direct_conditional_probability": str(conditional),
                       "registered_algebraic_prediction": str(predicted),
                       "ordered_moment_terms": term_count,
                       "replay": True})
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert usage["direct_born_probes"] == budget["max_probes"] == 3
    assert usage["ordered_moment_terms"] == matrix["expected_total_ordered_terms"] == 33024
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "three_direct_born_spotchecks_replayed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "probes": probes, "usage": usage,
            "prior_exact_term_ceiling": matrix["prior_exact_term_ceiling"],
            "interpretation_boundary": "Three preselected direct one-site Born probes support the algebraic route but do not exhaustively Born-verify all J7P next outcomes or imply private-error information, logical-risk or noisy JIT benefit.",
            "counters": {"full_next_joint_law_direct_born_evaluations": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
