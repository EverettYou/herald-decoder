"""Rank-only exact-character quotient preflight; evaluates no projector law."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8g-binary-constraint-rank-preflight-2026-09-27.json"
RESULT = LAB / "results/j8g-binary-constraint-rank-preflight-2026-09-27.json"
INPUTS = {
    "j8c_result": LAB / "results/j8c-support-geometry-cost-matrix-2026-09-27.json",
    "j8f_result": LAB / "results/j8f-orbit-character-reuse-audit-2026-09-27.json",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "orbit_source": LAB / "scripts/run_j6m_periodic_operator_ground_orbit.py",
    "operator_source": LAB / "scripts/run_j6n_sequential_local_projector_moments.py",
    "record_source": LAB / "scripts/run_j6o_full_binary_sequential_public_record.py",
    "sector_source": LAB / "scripts/run_j6x_full_first_dephasing_new_third.py",
    "setup_source": LAB / "scripts/run_j7a_postselected_next_first_limiting_fixtures.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def basis_of(vectors: list[int]) -> list[int]:
    basis: dict[int, int] = {}
    for vector in vectors:
        value = vector
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return list(basis.values())


def in_span(vector: int, basis: list[int]) -> bool:
    return len(basis_of([*basis, vector])) == len(basis)


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    checks_before = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                     for name, path in INPUTS.items()}
    assert all(checks_before.values()), checks_before
    old = {name: json.loads(INPUTS[name].read_text()) for name in
           ("j8c_result", "j8f_result", "j6l_result", "j6m_result")}
    assert old["j8f_result"]["status"] == "orbit_character_reuse_cost_censored"
    source = [branch for branch in old["j8c_result"]["new_support_branches"]
              if branch["cycle_length"] == 8]
    assert len(source) == 1 and len(source[0]["rows"]) == 54
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24

    def signature(zmask: int) -> int:
        return sum(parity(zmask & flip) << i for i, flip in enumerate(flips))

    replay = {tuple(row["candidate_error_red_edges_private"]): row
              for row in old["j8f_result"]["rows"]}
    assert len(replay) == 45
    rows = []
    signature_tests = 0
    total_first_subsets = 0
    total_affine_terms = 0
    stop = None
    for source_row in source[0]["rows"]:
        edges = source_row["candidate_error_red_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        eligible, first_means = sector_sites(sites, physical, flips, pairs)
        assert eligible == [site for site, value in enumerate(first_flux) if value == 0]
        variable = sorted(site for site, mean in first_means.items() if mean == 0)
        assert variable == source_row["first_variable_sites_private"]
        assert all(mean != -1 for mean in first_means.values())
        first_signatures = [signature(conjugated_star(sites[site], physical)[1]) for site in variable]
        signature_tests += len(first_signatures)
        first_rank = len(basis_of(first_signatures))
        affine_size = 1 << (len(variable) - first_rank)
        total_first_subsets += 1 << len(variable)
        cells = []
        for action_index, action in enumerate(spec["actions"]):
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            check_mask, second_flux = red_boundary(red, sorted(set(edges) ^ set(action)))
            assert residual == check_mask
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert eligible_second == [site for site, bit in enumerate(second_flux) if bit == 0]
            assert len(eligible_second) == budget["eligible_second_sites_per_cell"]
            second_signatures = {site: signature(conjugated_star(sites[site], residual)[1])
                                 for site in eligible_second}
            signature_tests += len(second_signatures)
            reachable = sorted(site for site, sig in second_signatures.items()
                               if in_span(sig, basis_of(first_signatures)))
            old_row = replay.get(tuple(edges))
            if old_row is not None:
                old_cell = old_row["cells"][action_index]
                assert second_flux == old_cell["second_public_flux"]
                # Deterministic nonzero conditional means require a nonempty
                # first-subset orbit-character constraint class.
                nonzero = set(eligible_second) - set(old_cell["variable_second_sites_private"])
                assert nonzero <= set(reachable)
                max_group_sites = len(old_cell["variable_second_sites_private"])
            else:
                max_group_sites = budget["unreplayed_max_variable_sites"]
            assert max_group_sites <= budget["max_variable_second_sites_per_cell"]
            projected_terms = ((1 << max_group_sites) - 1) * affine_size
            total_affine_terms += projected_terms
            cells.append({"public_action_red_edges": action,
                          "second_public_flux": second_flux,
                          "eligible_second_sites": len(eligible_second),
                          "reachable_singleton_signatures": len(reachable),
                          "replayed_j8f_cell": old_row is not None,
                          "max_group_sites": max_group_sites,
                          "projected_affine_class_terms": projected_terms})
        rows.append({"candidate_error_red_edges_private": edges,
                     "first_variable_site_count": len(variable),
                     "first_signature_rank": first_rank,
                     "first_signature_kernel_size": affine_size,
                     "cells": cells})
        if signature_tests > budget["max_signature_tests"]:
            stop = "signature_test_cap"
            break
        if time.process_time() - started > budget["max_cpu_seconds"]:
            stop = "cpu_cap"
            break
    complete = len(rows) == 54 and stop is None
    checks_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                    for name, path in INPUTS.items()}
    assert all(checks_after.values()) and digest(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "binary_constraint_rank_closed" if complete else "binary_constraint_rank_censored",
            "contract_sha256": digest(CONTRACT), "runner_sha256": digest(Path(__file__)),
            "pinned_input_checks_before": checks_before, "pinned_input_checks_after": checks_after,
            "completed_supports": len(rows), "completed_action_cells": sum(len(row["cells"]) for row in rows),
            "j8f_replay_supports": sum(tuple(row["candidate_error_red_edges_private"]) in replay for row in rows),
            "signature_tests": signature_tests, "total_first_subsets_for_naive_preparation": total_first_subsets,
            "projected_affine_class_terms_all_cells": total_affine_terms,
            "projected_affine_class_within_legacy_orbit_term_cap": complete and total_affine_terms <= budget["max_legacy_orbit_terms"],
            "stop": stop, "rows": rows, "cpu_seconds": round(time.process_time() - started, 6),
            "orbit_expectations_evaluated": 0, "complete_second_laws": 0,
            "histories": 0, "schedule_arms": 0, "bootstraps": 0,
            "claim_boundary": "Binary rank and affine-class size are exact structural prerequisites. The projected sum is a conservative enumeration count, not a measured exact-law cost or a proof that signed quadratic cancellation can be computed within cap. No new second law, full-IID information, risk, noisy JIT, L=3 or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
