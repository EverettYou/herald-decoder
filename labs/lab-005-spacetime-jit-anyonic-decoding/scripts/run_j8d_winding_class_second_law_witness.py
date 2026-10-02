"""Exact selected-first complete second laws for cost-selected winding witnesses."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute, law


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8d-winding-class-second-law-witness-2026-09-27.json"
RESULT = LAB / "results/j8d-winding-class-second-law-witness-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j7z_result": LAB / "results/j7z-higher-order-second-law-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "compose_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
    "j8b_source": LAB / "scripts/run_j8b_alternate_first_complete_second_laws.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_rows(j8c: dict, spec: dict) -> list[dict]:
    branches = [branch for branch in j8c["new_support_branches"] if branch["cycle_length"] == 8]
    assert len(branches) == 1 and len(branches[0]["rows"]) == 54
    chosen = []
    for winding in spec["winding_classes"]:
        members = [row for row in branches[0]["rows"] if row["winding_vectors"] == [winding]]
        assert len(members) == 18
        members.sort(key=lambda row: (row["projected_exact_first_terms"],
                                      row["loop_red_edges_private"]))
        assert Fraction(members[0]["selected_allplus_first_mass"]) > 0
        chosen.append(members[0])
    assert [row["loop_red_edges_private"] for row in chosen] == spec["selected_loop_red_edges_private"]
    assert [row["candidate_error_red_edges_private"] for row in chosen] == spec["selected_error_red_edges_private"]
    return chosen


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8c_result", "j7z_result", "j7m_result", "j6l_result", "j6m_result")}
    assert old["j8c_result"]["status"] == "support_geometry_cost_matrix_closed"
    assert old["j8c_result"]["new_support_exact_mass_gate_pass"]
    assert spec["base_error_private"] == [0, 4, 3]
    assert spec["winding_classes"] == [[1, -1], [1, 0], [0, 1]]
    assert spec["first_charge_sites"] == []
    assert spec["actions"] == [[0], [1, 30, 32, 34, 35]]
    chosen = selected_rows(old["j8c_result"], spec)
    errors = [spec["base_error_private"]] + [row["candidate_error_red_edges_private"] for row in chosen]
    assert [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]] == spec["actions"]
    assert old["j7m_result"]["first_public"]["charge"] == [0] * 24
    assert old["j7z_result"]["rows"][0]["initial_error_red_edges_private"] == errors[0]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    usage = {"first_orbit_moments": 0, "second_orbit_moments": 0,
             "algebraic_relation_probes": 0, "ordered_projector_terms": 0}
    rows = []
    for error_index, edges in enumerate(errors):
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [i for i, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in means.values())
        first_variable = sorted(site for site, value in means.items() if value == 0)
        assert len(first_variable) <= budget["max_first_variable_sites"]
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_subsets = [[first_ops[i] for i in range(len(first_ops)) if (mask >> i) & 1]
                         for mask in range(1 << len(first_ops))]
        first_sum = sum(moment(subset, flips) for subset in first_subsets)
        usage["first_orbit_moments"] += len(first_subsets)
        first_mass = Fraction(first_sum, 1 << len(first_ops))
        expected_mass = (Fraction(old["j7m_result"]["first_public_mass"]) if error_index == 0
                         else Fraction(chosen[error_index - 1]["selected_allplus_first_mass"]))
        assert first_mass == expected_mass > 0
        if error_index:
            assert first_variable == chosen[error_index - 1]["first_variable_sites_private"]
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(eligible_second) == budget["eligible_second_sites_per_cell"]
            second_ops = {site: conjugated_star(sites[site], residual) for site in eligible_second}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
            cache = {}

            def conditional(group: tuple[int, ...]) -> Fraction:
                if group in cache:
                    return cache[group]
                product = compose([second_ops[site] for site in group])
                assert compose([product, product]) == (1, 0, 0)
                if any(not commute(product, first) for first in first_ops):
                    value = Fraction(0)
                else:
                    relation = None
                    for subset in first_subsets:
                        usage["algebraic_relation_probes"] += 1
                        assert usage["algebraic_relation_probes"] <= budget["max_algebraic_relation_probes"]
                        observed = moment([product, *subset], flips)
                        if observed in (-1, 1):
                            relation = observed
                            break
                    if relation is not None:
                        value = Fraction(relation)
                    else:
                        total = sum(moment([*subset, product], flips) for subset in first_subsets)
                        usage["second_orbit_moments"] += len(first_subsets)
                        value = Fraction(total, first_sum)
                assert -1 <= value <= 1
                assert usage["first_orbit_moments"] + usage["second_orbit_moments"] <= budget["max_orbit_moment_terms"]
                cache[group] = value
                return value

            single = {site: conditional((site,)) for site in eligible_second}
            assert all(value in (-1, 0, 1) for value in single.values())
            fixed = {site: int(value == -1) for site, value in single.items() if value != 0}
            variable = sorted(site for site, value in single.items() if value == 0)
            assert len(variable) <= budget["max_variable_second_sites_per_cell"]
            moments = {(): Fraction(1)}
            for order in range(1, len(variable) + 1):
                for group in itertools.combinations(variable, order):
                    moments[group] = conditional(group)
            assert len(moments) == 1 << len(variable)
            reconstructed = []
            for bits in itertools.product((0, 1), repeat=len(variable)):
                probability = sum((value * (-1 if sum(bits[variable.index(site)] for site in group) % 2 else 1)
                                   for group, value in moments.items()), Fraction()) / (1 << len(variable))
                assert 0 <= probability <= 1
                if probability:
                    charge = [0] * 24
                    for site, bit in fixed.items():
                        charge[site] = bit
                    for site, bit in zip(variable, bits):
                        charge[site] = bit
                    reconstructed.append({"public": public_record(second_flux, charge),
                                          "conditional_probability": str(probability)})
            complete = law(reconstructed)
            if error_index == 0:
                assert complete == law(old["j7z_result"]["rows"][0]["cells"][action_index]["rows"])
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "variable_second_sites_private": variable,
                          "deterministic_second_charge_bits": {str(site): bit for site, bit in fixed.items()},
                          "positive_public_rows": len(reconstructed), "rows": reconstructed})
            assert time.process_time() - started < budget["max_cpu_seconds"]
        rows.append({"error_edges_private": edges, "winding_class": None if error_index == 0 else spec["winding_classes"][error_index - 1],
                     "first_public_mass": str(first_mass), "cells": cells})
    different = []
    for index, row in enumerate(rows[1:], 1):
        for action_index, cell in enumerate(row["cells"]):
            candidate = law(cell["rows"])
            base = law(rows[0]["cells"][action_index]["rows"])
            tv = sum((abs(candidate.get(key, Fraction()) - base.get(key, Fraction()))
                      for key in set(candidate) | set(base)), Fraction()) / 2
            cell["total_variation_vs_base_given_first"] = str(tv)
            if tv:
                different.append({"candidate_index": index, "winding_class": row["winding_class"],
                                  "public_action_red_edges": cell["public_action_red_edges"],
                                  "total_variation": str(tv)})
    assert len(rows) == 4 and sum(len(row["cells"]) for row in rows) == 8
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert time.process_time() - started < budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"], "status": "winding_class_second_law_witness_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "selected_loop_red_edges_private": spec["selected_loop_red_edges_private"],
            "winding_classes": spec["winding_classes"], "actions": spec["actions"],
            "complete_second_law_cells": 8, "different_candidate_action_cells": len(different),
            "different_cells": different, "rows": rows,
            "counters": {**usage, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Exact complete second public laws for one pre-cost-selected error per winding class plus base, one selected complete first record, both fixed actions, and one ideal L=2 orbit only. No class-wide null from representative equality, full-IID information, unconditional logical risk, noisy JIT, or threshold claim.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
