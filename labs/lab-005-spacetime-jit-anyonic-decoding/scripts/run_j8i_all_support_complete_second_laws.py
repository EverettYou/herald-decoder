"""Exact selected-first full second laws on all 54 eight-edge supports."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute, law
from run_j8h_signed_affine_solver_gate import affine_solutions


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8i-all-support-complete-second-laws-2026-09-27.json"
RESULT = LAB / "results/j8i-all-support-complete-second-laws-verified-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8d_result": LAB / "results/j8d-winding-class-second-law-witness-2026-09-27.json",
    "j8f_result": LAB / "results/j8f-orbit-character-reuse-audit-2026-09-27.json",
    "j8g_result": LAB / "results/j8g-binary-constraint-rank-preflight-2026-09-27.json",
    "j8h_result": LAB / "results/j8h-signed-affine-solver-gate-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "orbit_source": LAB / "scripts/run_j6m_periodic_operator_ground_orbit.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "compose_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
    "law_source": LAB / "scripts/run_j8b_alternate_first_complete_second_laws.py",
    "affine_source": LAB / "scripts/run_j8h_signed_affine_solver_gate.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8c_result", "j8d_result", "j8f_result", "j8g_result", "j8h_result", "j7m_result", "j6l_result", "j6m_result")}
    assert old["j8h_result"]["status"] == "signed_affine_solver_gate_closed"
    assert old["j8h_result"]["all_unresolved_site_gates_pass"]
    assert old["j8g_result"]["completed_supports"] == 54
    source = [branch for branch in old["j8c_result"]["new_support_branches"] if branch["cycle_length"] == 8]
    assert len(source) == 1 and len(source[0]["rows"]) == 54
    candidates = source[0]["rows"]
    assert len({tuple(row["candidate_error_red_edges_private"]) for row in candidates}) == 54
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    assert spec["first_public"] == old["j7m_result"]["first_public"]
    assert spec["actions"] == [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]]
    assert spec["base_error_private"] == old["j8d_result"]["rows"][0]["error_edges_private"]
    prior_laws = {tuple(row["error_edges_private"]): row for row in old["j8d_result"]["rows"]}
    assert len(prior_laws) == 4
    prior_sites = {tuple(row["candidate_error_red_edges_private"]): row
                   for row in old["j8f_result"]["rows"]}
    prior_sites.update({tuple(row["error_edges_private"]): row
                        for row in old["j8h_result"]["rows"] if row["kind"] == "unresolved"})
    assert len(prior_sites) == 54
    prior_rank = {tuple(row["candidate_error_red_edges_private"]): row
                  for row in old["j8g_result"]["rows"]}
    assert len(prior_rank) == 54
    counters = {"signed_affine_terms": 0, "direct_moment_checks": 0,
                "complete_candidate_law_cells": 0, "replayed_old_law_cells": 0,
                "histories": 0, "schedule_arms": 0, "bootstraps": 0}

    def signature(zmask: int) -> int:
        return sum(parity(zmask & flip) << i for i, flip in enumerate(flips))

    def signed_sum(first_ops, first_signatures, tail=()) -> int:
        product = compose(list(tail))
        choices = affine_solutions(first_signatures, signature(product[1]))
        assert len(choices) <= budget["max_affine_class_size"]
        total = 0
        for bits in choices:
            factors = [first_ops[index] for index in range(len(first_ops)) if (bits >> index) & 1]
            factors.extend(tail)
            sign, zmask, _ = compose(factors)
            assert signature(zmask) == 0
            total += sign
            counters["signed_affine_terms"] += 1
            assert counters["signed_affine_terms"] + counters["direct_moment_checks"] <= budget["max_total_terms"]
        return total

    rows = []
    for index, candidate in enumerate([None, *candidates]):
        edges = spec["base_error_private"] if candidate is None else candidate["candidate_error_red_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == spec["first_public"]["flux"]
        eligible_first, first_means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [site for site, bit in enumerate(first_flux) if bit == 0]
        assert all(mean != -1 for mean in first_means.values())
        first_variable = sorted(site for site, mean in first_means.items() if mean == 0)
        if candidate is not None:
            assert first_variable == candidate["first_variable_sites_private"]
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_signatures = [signature(op[1]) for op in first_ops]
        if candidate is not None:
            assert len(affine_solutions(first_signatures, 0)) == prior_rank[tuple(edges)]["first_signature_kernel_size"]
        first_sum = signed_sum(first_ops, first_signatures)
        first_mass = Fraction(first_sum, 1 << len(first_ops))
        expected_mass = (Fraction(old["j7m_result"]["first_public_mass"]) if candidate is None
                         else Fraction(candidate["selected_allplus_first_mass"]))
        assert first_mass == expected_mass > 0
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
                    answer = Fraction(0)
                else:
                    answer = Fraction(signed_sum(first_ops, first_signatures, (product,)), first_sum)
                assert -1 <= answer <= 1
                cache[group] = answer
                return answer

            singles = {site: conditional((site,)) for site in eligible_second}
            assert all(value in (-1, 0, 1) for value in singles.values())
            fixed = {site: int(value == -1) for site, value in singles.items() if value != 0}
            variable = sorted(site for site, value in singles.items() if value == 0)
            assert len(variable) <= budget["max_variable_second_sites_per_cell"]
            if candidate is not None:
                expected_sites = prior_sites[tuple(edges)]["cells"][action_index]["variable_second_sites_private"]
                assert variable == expected_sites
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
            assert sum((Fraction(row["conditional_probability"]) for row in reconstructed), Fraction()) == 1
            complete = law(reconstructed)
            if tuple(edges) in prior_laws:
                old_cell = prior_laws[tuple(edges)]["cells"][action_index]
                assert complete == law(old_cell["rows"])
                assert variable == old_cell["variable_second_sites_private"]
                counters["replayed_old_law_cells"] += 1
            if candidate is not None:
                counters["complete_candidate_law_cells"] += 1
            direct_checked = False
            for site in eligible_second:
                if singles[site] == 0:
                    continue
                product = compose([second_ops[site]])
                if any(not commute(product, first) for first in first_ops):
                    continue
                answers = affine_solutions(first_signatures, signature(product[1]))
                if answers:
                    bits = answers[0]
                    factors = [first_ops[i] for i in range(len(first_ops)) if (bits >> i) & 1]
                    factors.append(product)
                    assert compose(factors)[0] == moment(factors, flips)
                    counters["direct_moment_checks"] += 1
                    assert counters["direct_moment_checks"] <= budget["max_direct_moment_checks"]
                    direct_checked = True
                    break
            assert direct_checked, "no independent direct-moment check in action cell"
            cells.append({"public_action_red_edges": action, "second_public_flux": second_flux,
                          "variable_second_sites_private": variable,
                          "deterministic_second_charge_bits": {str(site): bit for site, bit in fixed.items()},
                          "positive_public_rows": len(reconstructed), "rows": reconstructed})
            assert time.process_time() - started <= budget["max_cpu_seconds"]
        rows.append({"error_edges_private": edges, "winding_class": None if candidate is None else candidate["winding_vectors"],
                     "first_public_mass": str(first_mass), "cells": cells})
    assert len(rows) == 55 and counters["complete_candidate_law_cells"] == 108
    assert counters["replayed_old_law_cells"] == 8
    assert counters["direct_moment_checks"] == 110
    assert counters["signed_affine_terms"] + counters["direct_moment_checks"] <= budget["max_total_terms"]
    different = []
    winding_counts = {}
    for candidate_index, row in enumerate(rows[1:], 1):
        winding = tuple(row["winding_class"][0])
        winding_counts[str(winding)] = winding_counts.get(str(winding), 0) + 1
        for action_index, cell in enumerate(row["cells"]):
            candidate_law = law(cell["rows"])
            base_law = law(rows[0]["cells"][action_index]["rows"])
            total_variation = sum((abs(candidate_law.get(key, Fraction()) - base_law.get(key, Fraction()))
                                   for key in candidate_law.keys() | base_law.keys()), Fraction()) / 2
            cell["total_variation_vs_base_given_first"] = str(total_variation)
            if total_variation:
                different.append({"candidate_index": candidate_index,
                                  "winding_class": row["winding_class"],
                                  "public_action_red_edges": cell["public_action_red_edges"],
                                  "total_variation": str(total_variation)})
    assert sorted(winding_counts.values()) == [18, 18, 18]
    assert counters["histories"] == counters["schedule_arms"] == counters["bootstraps"] == 0
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"], "status": "all_support_complete_second_laws_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "first_public": spec["first_public"], "actions": spec["actions"],
            "candidate_supports": 54, "candidate_action_cells": 108,
            "new_candidate_action_laws": 102, "replayed_candidate_action_laws": 6,
            "base_control_action_laws": 2, "different_candidate_action_cells": len(different),
            "different_cells": different, "winding_class_counts": winding_counts,
            "rows": rows, "counters": counters, "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "Exact conditional complete second full-binary public laws for all 54 J8C eight-edge same-first-flux supports versus base, one selected all-plus first charge record, two fixed public actions, ideal L=2 orbit. Does not cover other first records, the physical error prior, full-IID information, unconditional/logical risk, noisy JIT, L=3 or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
