"""Exact marginal and Walsh-order contraction of one frozen joint-charge witness."""

from collections import defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j8b_alternate_first_complete_second_laws import law


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8z-minimum-joint-charge-order-2026-09-28.json"
RESULT = LAB / "results/j8z-minimum-joint-charge-order-2026-09-28.json"


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


def walsh(rows: list[dict], sites: tuple[int, ...]) -> Fraction:
    return sum((Fraction(row["conditional_probability"])
                * (-1 if sum(row["public"]["charge"][i] for i in sites) % 2 else 1)
                for row in rows), Fraction())


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    source = json.loads((LAB / contract["source_result"]).read_text())
    prior = json.loads((LAB / contract["selection_result"]).read_text())
    assert source["status"] == "deterministic_first_collision_census_verified"
    assert prior["status"] == "action_overlap_and_low_order_witness_verified"
    spec = contract["matrix"]
    assert spec["first_flux_mask"] == 3591
    assert spec["public_action_red_edges"] == [1, 30, 32, 34, 35]
    assert spec["variable_charge_sites"] == [0, 1, 17, 20, 21, 22]
    selected = [row for row in prior["rows"] if row["first_flux_mask"] == spec["first_flux_mask"]
                and row["public_action_red_edges"] == spec["public_action_red_edges"]]
    assert len(selected) == 1
    assert selected[0]["full_second_total_variation"] == "3/4"
    assert selected[0]["maximum_single_charge_bit_total_variation"] == "0"
    assert selected[0]["maximum_charge_bit_pair_total_variation"] == "0"
    sectors = [row for row in source["rows"] if row["first_flux_mask"] == spec["first_flux_mask"]]
    assert len(sectors) == 1
    sector = sectors[0]
    assert [row["first_public_mass"] for row in sector["pair_rows"]] == ["1", "1"]
    assert [row["error_edges_private"] for row in sector["pair_rows"]] == [[0, 5, 16], [2, 4, 15]]
    cells = [next(cell for cell in row["cells"] if cell["public_action_red_edges"] == spec["public_action_red_edges"])
             for row in sector["pair_rows"]]
    assert [cell["variable_second_sites_private"] for cell in cells] == [spec["variable_charge_sites"]] * 2
    public_rows = [cell["rows"] for cell in cells]
    full_tv = tv(law(public_rows[0]), law(public_rows[1]))
    assert full_tv == Fraction(3, 4)
    # All charge coordinates outside the frozen six-site union are identical
    # and deterministic under both errors, so these 64 subsets cover every
    # possible public-charge subset up to redundant fixed coordinates.
    for site in set(range(24)) - set(spec["variable_charge_sites"]):
        values = {row["public"]["charge"][site] for rows in public_rows for row in rows}
        assert len(values) == 1
    by_order = []
    all_rows = []
    for order in range(7):
        cases = []
        for sites in itertools.combinations(spec["variable_charge_sites"], order):
            value = tv(marginal(public_rows[0], sites), marginal(public_rows[1], sites))
            parity_difference = abs(walsh(public_rows[0], sites) - walsh(public_rows[1], sites))
            assert 0 <= value <= full_tv and 0 <= parity_difference <= 2
            cases.append({"charge_sites": list(sites), "marginal_total_variation": str(value),
                          "absolute_parity_expectation_difference": str(parity_difference)})
            all_rows.append(cases[-1])
            assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
        maximum_tv = max(Fraction(row["marginal_total_variation"]) for row in cases)
        maximum_parity = max(Fraction(row["absolute_parity_expectation_difference"]) for row in cases)
        by_order.append({"order": order, "subsets": len(cases), "maximum_marginal_total_variation": str(maximum_tv),
                         "maximum_absolute_parity_expectation_difference": str(maximum_parity),
                         "first_maximum_tv_sites": next(row["charge_sites"] for row in cases
                                                        if Fraction(row["marginal_total_variation"]) == maximum_tv),
                         "positive_marginal_subsets": sum(Fraction(row["marginal_total_variation"]) > 0
                                                          for row in cases)})
    assert len(all_rows) == 64
    assert by_order[0]["maximum_marginal_total_variation"] == "0"
    assert by_order[1]["maximum_marginal_total_variation"] == "0"
    assert by_order[2]["maximum_marginal_total_variation"] == "0"
    assert Fraction(by_order[-1]["maximum_marginal_total_variation"]) == full_tv
    first_distinguishing_order = next(row["order"] for row in by_order
                                      if Fraction(row["maximum_marginal_total_variation"]) > 0)
    first_parity_order = next(row["order"] for row in by_order
                              if Fraction(row["maximum_absolute_parity_expectation_difference"]) > 0)
    assert first_distinguishing_order >= 3 and first_parity_order >= 3
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "minimum_joint_charge_order_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "first_flux_mask": spec["first_flux_mask"], "public_action_red_edges": spec["public_action_red_edges"],
            "selected_private_error_edges": [row["error_edges_private"] for row in sector["pair_rows"]],
            "variable_charge_sites": spec["variable_charge_sites"],
            "full_second_total_variation": str(full_tv),
            "first_distinguishing_marginal_order": first_distinguishing_order,
            "first_distinguishing_parity_order": first_parity_order,
            "by_order": by_order, "subset_rows": all_rows,
            "counters": {"exact_subset_contractions": len(all_rows), "new_born_terms": 0,
                         "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6),
            "claim_boundary": "One frozen selected equal-prior same-first-record private-error pair under one fixed public action. Exact six-variable-charge marginal and parity contractions; not a full-channel information/risk, logical benefit, noisy JIT, scaling or threshold result."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "first_marginal_order": result["first_distinguishing_marginal_order"],
                      "first_parity_order": result["first_distinguishing_parity_order"],
                      "cpu_seconds": result["cpu_seconds"]}))
