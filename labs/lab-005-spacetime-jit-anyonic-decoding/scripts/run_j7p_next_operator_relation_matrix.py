"""Bounded exact operator-relation map for every next charge on J7O fixture."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j7d_cross_round_commutation_screen import cross_vacuum_anticommutes


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7p-next-operator-relation-matrix-2026-09-26.json"
RESULT = LAB / "results/j7p-next-operator-relation-matrix-2026-09-26.json"
INPUTS = {
    "j7o_result": LAB / "results/j7o-witness-projector-reduction-2026-09-26.json",
    "j7n_result": LAB / "results/j7n-fixed-future-next-first-feasibility-2026-09-26.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "commutation_source": LAB / "scripts/run_j7d_cross_round_commutation_screen.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_mask(edges: list[int], red: dict[int, int]) -> int:
    result = 0
    for edge in edges:
        result ^= 1 << red[edge]
    return result


def is_involution(op: tuple[int, int, int]) -> bool:
    sign, zmask, xmask = op
    return sign in (-1, 1) and ((zmask & xmask).bit_count() & 1) == 0


def relation(next_op: tuple[int, int, int], second_ops: dict[int, tuple[int, int, int]],
             usage: dict, max_pairs: int) -> dict:
    anti, repeats = [], []
    assert is_involution(next_op)
    for site, prior_op in second_ops.items():
        usage["operator_pair_checks"] += 1
        assert usage["operator_pair_checks"] <= max_pairs
        assert is_involution(prior_op)
        if cross_vacuum_anticommutes(prior_op, next_op):
            anti.append(site)
        if prior_op[1:] == next_op[1:]:
            repeats.append({"second_site_private": site,
                            "charge_flipped": prior_op[0] != next_op[0]})
    assert not (anti and repeats)
    if anti:
        return {"class": "fair_by_anticommutation", "second_sites_private": anti}
    if repeats:
        return {"class": "signed_repeat", "relations": repeats}
    return {"class": "unresolved_commuting_other"}


def public_record(flux: list[int], charge: list[int]) -> dict:
    assert len(flux) == len(charge) == 24
    assert not any(f and c for f, c in zip(flux, charge))
    return {"flux": flux.copy(), "charge": charge.copy(),
            "vacuum": [1 - bit for bit in charge]}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    j7o, j7n, j7m, embedding, orbit = (
        json.loads(INPUTS[name].read_text()) for name in
        ("j7o_result", "j7n_result", "j7m_result", "j6l_result", "j6m_result"))
    assert j7o["status"] == "witness_one_site_projector_identity_closed"
    assert j7n["status"] == "fixed_future_structural_cost_audit_closed"
    assert j7m["status"] == "five_site_complete_second_charge_law_closed"
    assert Fraction(j7m["first_public_mass"]) == Fraction(1, 4)
    assert orbit["status"] == "passed_symbolic_vacuum_orbit_existence_only"
    assert spec["public_actions"] == [row["public_action_red_edges"]
                                      for row in j7m["cells"]]
    assert spec["public_actions"] == [[0], [1, 30, 32, 34, 35]]
    assert spec["matched_later_fault_keys_private"] == [[0], [4]]
    red = {qubit["lab004_red_edge_id"]: qubit["id"]
           for qubit in embedding["physical_qubits"] if qubit["color"] == "red"}
    sites = {int(star["center"].split(":")[1]): star
             for star in embedding["star_supports"]
             if star["center_color"] in ("blue", "green")}
    assert set(red) == set(range(36)) and set(sites) == set(range(24))
    usage = {"operator_pair_checks": 0, "positive_prefix_checks": 0,
             "reconstructed_public_rows": 0}
    cells = []
    for future in spec["matched_later_fault_keys_private"]:
        for action, prior in zip(spec["public_actions"], j7m["cells"]):
            cell = next(row for row in j7n["matrix"]
                        if row["public_action_red_edges"] == action
                        and row["future_physical_red_edges_private"] == future)
            j7o_cell = next(row for row in j7o["cells"]
                            if row["public_action_red_edges"] == action
                            and row["future_physical_red_edges_private"] == future)
            assert len(prior["rows"]) == cell["positive_second_prefixes"]
            assert sorted(set(cell["final_red_edges_private"]) ^ set(future)) == \
                prior["residual_red_edges_private"]
            second_mask = edge_mask(prior["residual_red_edges_private"], red)
            next_mask = edge_mask(cell["final_red_edges_private"], red)
            second_ops = {s: conjugated_star(sites[s], second_mask)
                          for s in cell["second_eligible_sites_private"]}
            classes = []
            for site, flux_bit in enumerate(cell["next_public_flux"]):
                if flux_bit:
                    assert site not in cell["next_eligible_sites_private"]
                    classes.append({"site_private": site, "class": "ineligible_charge_zero"})
                    continue
                assert site in cell["next_eligible_sites_private"]
                next_op = conjugated_star(sites[site], next_mask)
                classes.append({"site_private": site,
                                **relation(next_op, second_ops, usage,
                                           budget["max_operator_pair_checks"])})
            assert len(classes) == spec["next_sites_per_cell"] == 24
            assert classes[1]["class"] == "fair_by_anticommutation"
            assert classes[1]["second_sites_private"] == \
                [j7o_cell["second_next_witness_private"][0]]
            fair = [row["site_private"] for row in classes
                    if row["class"] == "fair_by_anticommutation"]
            unresolved = [row["site_private"] for row in classes
                          if row["class"] == "unresolved_commuting_other"]
            reconstruct = not unresolved and len(fair) <= 1
            law: dict[tuple[int, ...], Fraction] = {}
            prior_mass = Fraction()
            for second_row in prior["rows"]:
                usage["positive_prefix_checks"] += 1
                assert usage["positive_prefix_checks"] <= \
                    budget["max_positive_prefix_checks"]
                second = second_row["public"]
                assert set(second) == {"flux", "charge", "vacuum"}
                assert all(len(second[key]) == 24 for key in second)
                assert second["flux"] == prior["second_public_flux"]
                assert second["vacuum"] == [1 - bit for bit in second["charge"]]
                prior_probability = Fraction(second_row["conditional_probability"])
                assert prior_probability > 0
                prior_mass += prior_probability
                deterministic = [0] * 24
                for cls in classes:
                    site = cls["site_private"]
                    if cls["class"] == "signed_repeat":
                        predictions = {second["charge"][match["second_site_private"]]
                                       ^ int(match["charge_flipped"])
                                       for match in cls["relations"]}
                        assert len(predictions) == 1
                        deterministic[site] = predictions.pop()
                    elif cls["class"] == "ineligible_charge_zero":
                        assert cell["next_public_flux"][site] == 1
                if reconstruct:
                    for fair_bit in (0, 1) if fair else (0,):
                        charge = deterministic.copy()
                        if fair:
                            charge[fair[0]] = fair_bit
                        record = public_record(cell["next_public_flux"], charge)
                        key = tuple(record["charge"])
                        weight = prior_probability / (2 if fair else 1)
                        law[key] = law.get(key, Fraction()) + weight
                        usage["reconstructed_public_rows"] += 1
                        assert usage["reconstructed_public_rows"] <= \
                            budget["max_reconstructed_public_rows"]
            assert prior_mass == 1
            if reconstruct:
                assert sum(law.values(), Fraction()) == 1
            cells.append({"public_action_red_edges": action,
                          "future_physical_red_edges_private": future,
                          "next_public_flux": cell["next_public_flux"],
                          "site_classes": classes,
                          "class_counts": {name: sum(row["class"] == name for row in classes)
                                           for name in ("ineligible_charge_zero",
                                                        "fair_by_anticommutation",
                                                        "signed_repeat",
                                                        "unresolved_commuting_other")},
                          "fair_next_sites_private": fair,
                          "unresolved_next_sites_private": unresolved,
                          "complete_next_law_reconstructed": reconstruct,
                          "complete_next_law": [
                              {"public": public_record(cell["next_public_flux"], list(key)),
                               "conditional_probability": str(mass)}
                              for key, mass in sorted(law.items())] if reconstruct else None})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert len(cells) == budget["max_action_future_cells"] == 4
    assert usage["positive_prefix_checks"] == budget["max_positive_prefix_checks"] == 68
    assert usage["operator_pair_checks"] <= budget["max_operator_pair_checks"]
    comparison = {}
    for future in spec["matched_later_fault_keys_private"]:
        pair = [row for row in cells if row["future_physical_red_edges_private"] == future]
        assert len(pair) == 2 and pair[0]["next_public_flux"] == pair[1]["next_public_flux"]
        if all(row["complete_next_law_reconstructed"] for row in pair):
            left, right = ({tuple(row["public"]["charge"]): Fraction(
                row["conditional_probability"]) for row in cell["complete_next_law"]}
                           for cell in pair)
            tv = sum((abs(left.get(key, Fraction()) - right.get(key, Fraction()))
                      for key in set(left) | set(right)), Fraction()) / 2
            comparison[str(future)] = {"status": "exact_full_next_law_compared",
                                       "exact_total_variation": str(tv)}
        else:
            comparison[str(future)] = {
                "status": "censored_unresolved_next_operator_classes",
                "unresolved_by_action": [row["unresolved_next_sites_private"] for row in pair],
                "exact_total_variation": None}
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()), after
    return {"schema_version": 1, "id": contract["id"],
            "status": "four_cell_operator_relation_matrix_closed",
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": before,
            "pinned_input_checks_after": after,
            "cells": cells, "same_future_comparison": comparison,
            "usage": usage,
            "counters": {"ordered_moment_terms_evaluated": 0,
                         "next_first_born_laws_evaluated": 0,
                         "stochastic_histories": 0,
                         "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "interpretation_boundary": "Exact anti/repeat classes only; unresolved commuting sites are not assigned a law. Complete next-law TV is absent unless all next sites and correlation structure resolve algebraically. No information/risk/policy/noisy-schedule claim.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
