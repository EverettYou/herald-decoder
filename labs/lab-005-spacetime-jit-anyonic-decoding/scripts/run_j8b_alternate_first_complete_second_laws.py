"""All-positive-first-record exact second laws with shared signed projector moments."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8b-alternate-first-complete-second-laws-2026-09-27.json"
RESULT = LAB / "results/j8b-alternate-first-complete-second-laws-2026-09-27.json"
INPUTS = {
    "j8a_contract": LAB / "manifests/j8a-alternate-first-record-mass-matrix-2026-09-27.json",
    "j8a_result": LAB / "results/j8a-alternate-first-record-mass-matrix-2026-09-27.json",
    "j7z_result": LAB / "results/j7z-higher-order-second-law-2026-09-27.json",
    "j7m_result": LAB / "results/j7m-five-site-complete-second-charge-law-2026-09-26.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
    "compose_source": LAB / "scripts/run_j7v_joint_second_walsh_reduction.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def law(rows: list[dict]) -> dict[str, Fraction]:
    values = {key(row["public"]): Fraction(row["conditional_probability"]) for row in rows}
    assert len(values) == len(rows)
    assert all(value > 0 for value in values.values())
    assert sum(values.values(), Fraction()) == 1
    return values


def signs(eigenvalues: tuple[int, ...]) -> list[int]:
    return [math.prod(eigenvalues[i] for i in range(len(eigenvalues)) if (subset >> i) & 1)
            for subset in range(1 << len(eigenvalues))]


def commute(left, right) -> bool:
    return compose([left, right]) == compose([right, left])


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
              for name, path in INPUTS.items()}
    assert all(before.values()), before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8a_contract", "j8a_result", "j7z_result", "j7m_result", "j6l_result", "j6m_result")}
    prior, replay = old["j8a_result"], old["j7z_result"]
    assert prior["status"] == "alternate_first_record_feasibility_closed"
    assert prior["positive_candidate_counts_by_alternative"] == [11, 11, 10]
    assert replay["different_complete_law_candidate_action_cells"] == 0
    assert spec["base_error_private"] == [0, 4, 3]
    assert spec["first_charge_sites"] == [[], [1], [2], [1, 2]]
    assert spec["actions"] == [[0], [1, 30, 32, 34, 35]]
    assert len(prior["rows"]) == len(replay["rows"]) == 13
    assert [row["error_edges_private"] for row in prior["rows"]] == [
        row["initial_error_red_edges_private"] for row in replay["rows"]]
    assert [cell["public_action_red_edges"] for cell in old["j7m_result"]["cells"]] == spec["actions"]
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    usage = {"first_orbit_moments": 0, "second_orbit_moments": 0,
             "algebraic_relation_probes": 0, "ordered_projector_terms": 0}
    rows = []
    allplus_replays = 0
    for error_index, source in enumerate(prior["rows"]):
        edges = source["error_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == old["j7m_result"]["first_public"]["flux"]
        eligible_first, means = sector_sites(sites, physical, flips, pairs)
        assert eligible_first == [i for i, bit in enumerate(first_flux) if bit == 0]
        assert all(value != -1 for value in means.values())
        first_variable = sorted(site for site, value in means.items() if value == 0)
        assert first_variable == source["first_variable_sites_private"]
        assert len(first_variable) <= budget["max_first_variable_sites"]
        first_ops = [conjugated_star(sites[site], physical) for site in first_variable]
        assert all(commute(a, b) for a in first_ops for b in first_ops)
        first_subsets = [[first_ops[i] for i in range(len(first_ops)) if (mask >> i) & 1]
                         for mask in range(1 << len(first_ops))]
        raw_first = [moment(subset, flips) for subset in first_subsets]
        usage["first_orbit_moments"] += len(raw_first)
        assert usage["first_orbit_moments"] + usage["second_orbit_moments"] <= budget["max_orbit_moment_terms"]
        positive = {}
        for first_index, (charge_sites, case) in enumerate(zip(spec["first_charge_sites"], source["cases"])):
            assert case["charge_sites"] == charge_sites
            assert case["first_public"]["flux"] == first_flux
            conflict = any(means[site] == 1 for site in charge_sites)
            if conflict:
                assert not case["positive"] and Fraction(case["mass"]) == 0
                continue
            eigenvalues = tuple(-1 if site in charge_sites else 1 for site in first_variable)
            sign_vector = signs(eigenvalues)
            first_sum = sum(sign * raw for sign, raw in zip(sign_vector, raw_first))
            mass = Fraction(first_sum, 1 << len(first_variable))
            assert mass == Fraction(case["mass"]) and mass > 0 and case["positive"]
            positive[first_index] = (sign_vector, first_sum)
        assert 0 in positive
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            assert second_flux == old["j7m_result"]["cells"][action_index]["second_public_flux"]
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(eligible_second) == budget["eligible_second_sites_per_cell"] == 22
            second_ops = {site: conjugated_star(sites[site], residual) for site in eligible_second}
            assert all(commute(a, b) for a in second_ops.values() for b in second_ops.values())
            moment_cache = {}

            def conditional(group: tuple[int, ...]) -> dict[int, Fraction]:
                if group in moment_cache:
                    return moment_cache[group]
                product = compose([second_ops[site] for site in group])
                assert compose([product, product]) == (1, 0, 0)
                if any(not commute(product, first) for first in first_ops):
                    values = {index: Fraction(0) for index in positive}
                else:
                    relation = None
                    for subset_mask, subset in enumerate(first_subsets):
                        usage["algebraic_relation_probes"] += 1
                        assert usage["algebraic_relation_probes"] <= budget["max_algebraic_relation_probes"]
                        observed = moment([product, *subset], flips)
                        if observed in (-1, 1):
                            relation = (subset_mask, observed)
                            break
                    if relation is not None:
                        subset_mask, observed = relation
                        values = {index: Fraction(observed * signed[0][subset_mask])
                                  for index, signed in positive.items()}
                    else:
                        raw = [moment([*subset, product], flips) for subset in first_subsets]
                        usage["second_orbit_moments"] += len(raw)
                        assert usage["first_orbit_moments"] + usage["second_orbit_moments"] <= budget["max_orbit_moment_terms"]
                        values = {index: Fraction(sum(sign * value for sign, value in zip(signed[0], raw)),
                                                  signed[1]) for index, signed in positive.items()}
                assert all(-1 <= value <= 1 for value in values.values())
                moment_cache[group] = values
                return values

            single = {site: conditional((site,)) for site in eligible_second}
            for first_index in range(4):
                if first_index not in positive:
                    cells.append({"first_index": first_index, "public_action_red_edges": action,
                                  "status": "zero_first_mass_excluded", "rows": []})
                    continue
                fixed = {site: int(single[site][first_index] == -1)
                         for site in eligible_second if single[site][first_index] in (-1, 1)}
                variable = sorted(site for site in eligible_second if site not in fixed)
                assert all(single[site][first_index] == 0 for site in variable)
                assert len(variable) <= budget["max_variable_second_sites_per_cell"]
                moments = {(): Fraction(1)}
                for order in range(1, len(variable) + 1):
                    for group in itertools.combinations(variable, order):
                        moments[group] = conditional(group)[first_index]
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
                this_law = law(reconstructed)
                if first_index == 0:
                    assert this_law == law(replay["rows"][error_index]["cells"][action_index]["rows"])
                    allplus_replays += 1
                cells.append({"first_index": first_index, "public_action_red_edges": action,
                              "status": "exact_complete_second_law", "second_public_flux": second_flux,
                              "variable_second_sites_private": variable,
                              "deterministic_second_charge_bits": {str(site): bit for site, bit in fixed.items()},
                              "positive_public_rows": len(reconstructed), "rows": reconstructed})
            assert time.process_time() - started < budget["max_cpu_seconds"]
        assert len(cells) == 8
        rows.append({"error_edges_private": edges, "first_public_cases": source["cases"], "cells": cells})
    assert allplus_replays == 26
    base_laws = {(cell["first_index"], tuple(cell["public_action_red_edges"])): law(cell["rows"])
                 for cell in rows[0]["cells"] if cell["status"] == "exact_complete_second_law"}
    different = []
    for error_index, row in enumerate(rows[1:], 1):
        for cell in row["cells"]:
            if cell["first_index"] == 0 or cell["status"] != "exact_complete_second_law":
                continue
            pair_key = (cell["first_index"], tuple(cell["public_action_red_edges"]))
            candidate_law = law(cell["rows"])
            base_law = base_laws[pair_key]
            tv = sum((abs(candidate_law.get(outcome, Fraction()) - base_law.get(outcome, Fraction()))
                      for outcome in set(candidate_law) | set(base_law)), Fraction()) / 2
            cell["total_variation_vs_base_given_first"] = str(tv)
            if tv:
                different.append({"error_index": error_index, "first_index": cell["first_index"],
                                  "public_action_red_edges": cell["public_action_red_edges"],
                                  "total_variation": str(tv)})
    expected_positive = 13 + sum(1 + count for count in prior["positive_candidate_counts_by_alternative"])
    assert expected_positive == 48
    assert sum(cell["status"] == "exact_complete_second_law" for row in rows for cell in row["cells"]) == 96
    assert sum(cell["status"] == "zero_first_mass_excluded" for row in rows for cell in row["cells"]) == 8
    after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
             for name, path in INPUTS.items()}
    assert all(after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert time.process_time() - started < budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "alternate_first_complete_second_laws_closed",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": before, "pinned_input_checks_after": after,
            "first_record_charge_sites": spec["first_charge_sites"],
            "actions": spec["actions"], "errors": 13, "allplus_complete_law_replays": allplus_replays,
            "positive_first_error_cells": expected_positive, "complete_second_law_cells": 96,
            "zero_first_mass_exclusions": 4, "different_alternate_candidate_action_cells": len(different),
            "different_cells": different, "rows": rows,
            "counters": {**usage, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Exact complete second public laws only for the thirteen pre-existing private errors, four selected complete first records, two fixed relation-free actions, and one ideal L=2 orbit. Zero-mass first cells are excluded, not inferred. A TV contrast is only a restricted error-conditioned law witness, not full-IID information, unconditional logical risk, noisy JIT benefit or a threshold.",
            "cpu_seconds": round(time.process_time() - started, 6)}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
