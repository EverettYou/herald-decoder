"""Bounded geometry and low-order public-law discriminators for J8X cells."""

from collections import defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j8b_alternate_first_complete_second_laws import law


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8y-action-overlap-and-low-order-witness-2026-09-28.json"
RESULT = LAB / "results/j8y-action-overlap-and-low-order-witness-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marginal(rows: list[dict], sites: tuple[int, ...]) -> dict[tuple[int, ...], Fraction]:
    masses = defaultdict(Fraction)
    for row in rows:
        bits = tuple(row["public"]["charge"][i] for i in sites)
        masses[bits] += Fraction(row["conditional_probability"])
    assert sum(masses.values(), Fraction()) == 1
    return dict(masses)


def tv(a: dict, b: dict) -> Fraction:
    return sum((abs(a.get(key, Fraction()) - b.get(key, Fraction()))
                for key in a.keys() | b.keys()), Fraction()) / 2


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    source = json.loads((LAB / contract["source_result"]).read_text())
    assert source["status"] == "deterministic_first_collision_census_verified"
    assert len(source["rows"]) == 12
    assert contract["matrix"]["public_actions_red_edges"] == [[0], [1, 30, 32, 34, 35]]
    rows = []
    geometry_buckets = defaultdict(list)
    checks = 0
    for sector in source["rows"]:
        assert [error["first_public_mass"] for error in sector["pair_rows"]] == ["1", "1"]
        errors = [set(error["error_edges_private"]) for error in sector["pair_rows"]]
        assert len(errors) == 2 and all(len(error) == 3 for error in errors)
        for action_index, action in enumerate(contract["matrix"]["public_actions_red_edges"]):
            action_set = set(action)
            cells = [error["cells"][action_index] for error in sector["pair_rows"]]
            assert [cell["public_action_red_edges"] for cell in cells] == [action, action]
            raw = [cell["rows"] for cell in cells]
            full = tv(law(raw[0]), law(raw[1]))
            expected = Fraction(sector["paired_action_differences"][action_index]
                                ["conditional_second_total_variation"])
            assert full == expected
            singleton = [tv(marginal(raw[0], (site,)), marginal(raw[1], (site,)))
                         for site in range(24)]
            pair = [tv(marginal(raw[0], sites), marginal(raw[1], sites))
                    for sites in itertools.combinations(range(24), 2)]
            checks += len(singleton) + len(pair)
            max_single, max_pair = max(singleton), max(pair)
            assert 0 <= max_single <= max_pair <= full <= 1
            overlap = sorted(len(action_set & error) for error in errors)
            xor_overlap = len(action_set & (errors[0] ^ errors[1]))
            geometry_key = (action_index, *overlap, xor_overlap)
            geometry_buckets[geometry_key].append((sector["first_flux_mask"], full))
            rows.append({"first_flux_mask": sector["first_flux_mask"],
                         "public_action_red_edges": action,
                         "geometry_overlap_signature": {"sorted_action_error_intersections": overlap,
                                                        "action_pair_xor_intersection": xor_overlap},
                         "full_second_total_variation": str(full),
                         "maximum_single_charge_bit_total_variation": str(max_single),
                         "maximum_charge_bit_pair_total_variation": str(max_pair),
                         "full_exceeds_best_single": full > max_single,
                         "full_exceeds_best_pair": full > max_pair})
            assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert len(rows) == 24 and checks == 24 * (24 + 276)
    conflicts = []
    for key, entries in sorted(geometry_buckets.items()):
        if len({value for _, value in entries}) > 1:
            conflicts.append({"action_index": key[0], "sorted_action_error_intersections": list(key[1:3]),
                              "action_pair_xor_intersection": key[3],
                              "flux_and_full_tv": [[flux, str(value)] for flux, value in entries]})
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "action_overlap_and_low_order_witness_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "rows": rows, "geometry_signature_conflicts": conflicts,
            "summary": {"positive_full_cells": sum(Fraction(row["full_second_total_variation"]) > 0 for row in rows),
                        "full_exceeds_best_single_cells": sum(row["full_exceeds_best_single"] for row in rows),
                        "full_exceeds_best_pair_cells": sum(row["full_exceeds_best_pair"] for row in rows),
                        "geometry_signature_classes": len(geometry_buckets),
                        "geometry_signature_conflicts": len(conflicts)},
            "counters": {"marginal_comparisons": checks, "new_born_terms": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "Existing 12-sector/24-action exact public laws only. Marginal witness and action-overlap diagnostics do not establish an operator automorphism or reusable law; no other first records/sectors, full-IID information/risk, noisy JIT or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "summary": result["summary"],
                      "cpu_seconds": result["cpu_seconds"]}))
