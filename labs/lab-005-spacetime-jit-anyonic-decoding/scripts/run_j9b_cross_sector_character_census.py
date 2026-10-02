"""Exact parity-character census on the frozen deterministic-first collision class."""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute, law


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9b-cross-sector-character-census-2026-09-28.json"
RESULT = LAB / "results/j9b-cross-sector-character-census-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tv(a: dict, b: dict) -> Fraction:
    return sum((abs(a.get(key, Fraction()) - b.get(key, Fraction()))
                for key in a.keys() | b.keys()), Fraction()) / 2


def add_constraint(basis: dict[int, tuple[int, int]], mask: int, sign: int) -> None:
    while mask:
        pivot = mask.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (mask, sign)
            return
        prior_mask, prior_sign = basis[pivot]
        mask ^= prior_mask
        sign *= prior_sign
    assert sign == 1, "Inconsistent deterministic parity character"


def run() -> dict:
    start = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec, budget = contract["matrix"], contract["budget"]
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    source = json.loads((LAB / contract["source_result"]).read_text())
    control = json.loads((LAB / contract["control_result"]).read_text())
    assert source["status"] == "deterministic_first_collision_census_verified"
    assert control["status"] == "triple_parity_operator_relation_verified"
    assert len(source["rows"]) == 12
    actions = spec["public_actions_red_edges"]
    assert actions == [[0], [1, 30, 32, 34, 35]]
    red, sites, flips, pairs = setup(
        json.loads((LAB / spec["geometry_result"]).read_text()),
        json.loads((LAB / spec["orbit_result"]).read_text()))
    assert len(red) == 36 and len(sites) == 24 and len(flips) == 36
    rows = []
    moment_checks = 0
    for sector in source["rows"]:
        assert [error["first_public_mass"] for error in sector["pair_rows"]] == ["1", "1"]
        assert len(sector["pair_rows"]) == 2
        for action_index, action in enumerate(actions):
            action_mask, _ = red_boundary(red, action)
            cells = [error["cells"][action_index] for error in sector["pair_rows"]]
            assert all(cell["public_action_red_edges"] == action for cell in cells)
            public_rows = [cell["rows"] for cell in cells]
            full_laws = [law(case) for case in public_rows]
            full_tv = tv(*full_laws)
            assert full_tv == Fraction(sector["paired_action_differences"][action_index]
                                       ["conditional_second_total_variation"])
            active = sorted(set().union(*(set(cell["variable_second_sites_private"]) for cell in cells)))
            assert len(active) <= budget["max_active_charge_sites_per_cell"]
            outside = set(range(24)) - set(active)
            for site in outside:
                assert len({row["public"]["charge"][site]
                            for case in public_rows for row in case}) == 1
            second_flux = None
            law_rows = []
            all_moments = []
            for error, cell, case in zip(sector["pair_rows"], cells, public_rows):
                physical, first_flux = red_boundary(red, error["error_edges_private"])
                assert sum(bit << i for i, bit in enumerate(first_flux)) == sector["first_flux_mask"]
                eligible_first, first_means = sector_sites(sites, physical, flips, pairs)
                assert all(first_means[site] == 1 for site in eligible_first)
                residual = physical ^ action_mask
                check_mask, this_flux = red_boundary(
                    red, sorted(set(error["error_edges_private"]) ^ set(action)))
                assert check_mask == residual
                if second_flux is None:
                    second_flux = this_flux
                assert this_flux == second_flux
                eligible_second, _ = sector_sites(sites, residual, flips, pairs)
                assert set(active) <= set(eligible_second)
                operators = [conjugated_star(sites[site], residual) for site in active]
                assert all(commute(a, b) for a, b in itertools.combinations(operators, 2))
                projected = defaultdict(Fraction)
                for row in case:
                    assert row["public"]["flux"] == second_flux
                    bits = tuple(row["public"]["charge"][site] for site in active)
                    projected[bits] += Fraction(row["conditional_probability"])
                assert sum(projected.values(), Fraction()) == 1
                basis = {}
                moments = {}
                for mask in range(1 << len(active)):
                    selected = [operators[index] for index in range(len(active)) if mask >> index & 1]
                    product = compose(selected)
                    assert compose([product, product]) == (1, 0, 0)
                    orbit = moment([product], flips)
                    direct = sum((mass * (-1 if parity(sum(bit << i for i, bit in enumerate(bits)) & mask)
                                                  else 1)
                                  for bits, mass in projected.items()), Fraction())
                    assert direct == orbit
                    moment_checks += 1
                    moments[mask] = orbit
                    if abs(orbit) == 1 and mask:
                        add_constraint(basis, mask, orbit)
                rank = len(basis)
                predicted = {}
                for bits in itertools.product((0, 1), repeat=len(active)):
                    bit_mask = sum(bit << i for i, bit in enumerate(bits))
                    if all((-1 if parity(bit_mask & relation) else 1) == sign
                           for relation, sign in basis.values()):
                        predicted[bits] = Fraction(1, 1 << (len(active) - rank))
                assert predicted == dict(projected)
                law_rows.append({"error_edges_private_analysis_only": error["error_edges_private"],
                                 "affine_parity_rank": rank,
                                 "independent_parity_constraints": [
                                     {"charge_sites": [active[i] for i in range(len(active)) if mask >> i & 1],
                                      "eigenvalue": sign}
                                     for mask, sign in sorted(basis.values())],
                                 "positive_active_assignments": len(projected),
                                 "uniform_active_probability": str(Fraction(1, len(projected)))})
                all_moments.append(moments)
                assert time.process_time() - start <= budget["max_cpu_seconds"]
            projected_laws = []
            for case in public_rows:
                projected = defaultdict(Fraction)
                for row in case:
                    projected[tuple(row["public"]["charge"][site] for site in active)] += Fraction(
                        row["conditional_probability"])
                projected_laws.append(dict(projected))
            assert tv(*projected_laws) == full_tv
            differing = [sum((mask >> i) & 1 for i in range(len(active)))
                         for mask in all_moments[0] if all_moments[0][mask] != all_moments[1][mask]]
            assert bool(differing) == bool(full_tv)
            rows.append({"first_flux_mask": sector["first_flux_mask"],
                         "public_action_red_edges": action,
                         "active_charge_sites": active,
                         "private_error_laws": law_rows,
                         "first_distinguishing_parity_order": min(differing) if differing else None,
                         "full_second_total_variation": str(full_tv),
                         "affine_support_intersection_assignments": len(set(projected_laws[0]) &
                                                                         set(projected_laws[1]))})
    assert len(rows) == 24 and moment_checks <= budget["max_operator_character_checks"]
    witness = next(row for row in rows if row["first_flux_mask"] == control["first_flux_mask"]
                   and row["public_action_red_edges"] == control["public_action_red_edges"])
    assert witness["first_distinguishing_parity_order"] == 3
    assert witness["full_second_total_variation"] == control["full_second_total_variation"] == "3/4"
    by_tv = Counter(row["full_second_total_variation"] for row in rows)
    by_order = Counter(str(row["first_distinguishing_parity_order"])
                       for row in rows if row["first_distinguishing_parity_order"] is not None)
    rank_buckets = defaultdict(set)
    for row in rows:
        key = tuple(law["affine_parity_rank"] for law in row["private_error_laws"])
        rank_buckets[key].add(row["full_second_total_variation"])
    conflicting_rank_pairs = [{"rank_pair": list(key), "observed_tvs": sorted(values)}
                              for key, values in sorted(rank_buckets.items()) if len(values) > 1]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - start
    assert elapsed <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "cross_sector_character_census_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "rows": rows,
            "summary": {"cells": len(rows), "complete_laws": 2 * len(rows),
                        "tv_cell_counts": dict(sorted(by_tv.items())),
                        "positive_minimum_parity_order_counts": dict(sorted(by_order.items())),
                        "rank_pair_tv_conflicts": conflicting_rank_pairs},
            "counters": {"operator_character_checks": moment_checks, "new_born_terms": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Exact deterministic-first 12-sector/two-action class only. Public-law moments and affine parity supports replay all 48 stored direct laws, but ranks and characters are not an operator automorphism or a license to reuse laws outside this class. No full-IID information/risk, noisy JIT, scaling or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "summary": result["summary"],
                      "cpu_seconds": result["cpu_seconds"]}))
