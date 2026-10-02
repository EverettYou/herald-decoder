"""Audit two frozen public-charge parity witnesses against the D4 orbit algebra."""

from collections import defaultdict
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
CONTRACT = LAB / "manifests/j9a-triple-parity-operator-relation-2026-09-28.json"
RESULT = LAB / "results/j9a-triple-parity-operator-relation-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walsh(rows: list[dict], group: tuple[int, ...]) -> Fraction:
    return sum((Fraction(row["conditional_probability"]) *
                (-1 if sum(row["public"]["charge"][i] for i in group) % 2 else 1)
                for row in rows), Fraction())


def parity_law(rows: list[dict], groups: tuple[tuple[int, ...], ...]) -> dict[str, Fraction]:
    masses = defaultdict(Fraction)
    for row in rows:
        bits = tuple(sum(row["public"]["charge"][i] for i in group) % 2 for group in groups)
        masses[str(bits)] += Fraction(row["conditional_probability"])
    assert sum(masses.values(), Fraction()) == 1
    return dict(sorted(masses.items()))


def tv(left: dict, right: dict) -> Fraction:
    return sum((abs(left.get(key, Fraction()) - right.get(key, Fraction()))
                for key in left.keys() | right.keys()), Fraction()) / 2


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    spec = contract["matrix"]
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    previous = json.loads((LAB / contract["selection_result"]).read_text())
    source = json.loads((LAB / contract["source_result"]).read_text())
    assert previous["status"] == "minimum_joint_charge_order_verified"
    assert source["status"] == "deterministic_first_collision_census_verified"
    groups = tuple(tuple(group) for group in spec["triple_charge_sites"])
    assert groups == ((0, 20, 22), (1, 17, 21))
    assert set(groups[0]).isdisjoint(groups[1])
    all_six = tuple(sorted(groups[0] + groups[1]))
    assert list(all_six) == previous["variable_charge_sites"]
    assert previous["first_distinguishing_parity_order"] == 3
    assert previous["full_second_total_variation"] == "3/4"
    assert all(next(row for row in previous["subset_rows"] if row["charge_sites"] == list(group))
               ["absolute_parity_expectation_difference"] == "1" for group in groups)
    assert spec["first_flux_mask"] == previous["first_flux_mask"] == 3591
    assert spec["public_action_red_edges"] == previous["public_action_red_edges"] == [1, 30, 32, 34, 35]
    assert spec["private_error_edges_analysis_only"] == previous["selected_private_error_edges"] == [
        [0, 5, 16], [2, 4, 15]]
    sector = next(row for row in source["rows"] if row["first_flux_mask"] == spec["first_flux_mask"])
    assert [row["error_edges_private"] for row in sector["pair_rows"]] == spec["private_error_edges_analysis_only"]
    red, sites, flips, pairs = setup(
        json.loads((LAB / spec["geometry_result"]).read_text()),
        json.loads((LAB / spec["orbit_result"]).read_text()))
    assert len(red) == 36 and len(sites) == 24 and len(flips) == 36
    action_mask, _ = red_boundary(red, spec["public_action_red_edges"])
    rows = []
    public_laws = []
    second_flux_reference = None
    for pair in sector["pair_rows"]:
        error = pair["error_edges_private"]
        assert pair["first_public_mass"] == "1"
        physical, first_flux = red_boundary(red, error)
        assert sum(bit << i for i, bit in enumerate(first_flux)) == spec["first_flux_mask"]
        eligible_first, first_means = sector_sites(sites, physical, flips, pairs)
        assert all(first_means[i] == 1 for i in eligible_first)
        residual = physical ^ action_mask
        check_mask, second_flux = red_boundary(red, sorted(set(error) ^ set(spec["public_action_red_edges"])))
        assert check_mask == residual
        if second_flux_reference is None:
            second_flux_reference = second_flux
        assert second_flux == second_flux_reference
        eligible_second, _ = sector_sites(sites, residual, flips, pairs)
        assert set(all_six) <= set(eligible_second)
        operators = {i: conjugated_star(sites[i], residual) for i in all_six}
        assert all(commute(a, b) for a, b in itertools.combinations(operators.values(), 2))
        cell = next(c for c in pair["cells"] if c["public_action_red_edges"] == spec["public_action_red_edges"])
        assert cell["variable_second_sites_private"] == list(all_six)
        public_rows = cell["rows"]
        assert len(law(public_rows)) == len(public_rows)
        public_laws.append(public_rows)
        operator_rows = []
        for group in (*groups, all_six):
            product = compose([operators[i] for i in group])
            assert compose([product, product]) == (1, 0, 0)
            direct = walsh(public_rows, group)
            orbit = moment([product], flips)
            assert orbit == moment([operators[i] for i in group], flips)
            assert direct == orbit
            nontrivial_character = [index for index, flip in enumerate(flips)
                                    if parity(product[1] & flip)]
            assert (orbit == 0) == bool(nontrivial_character)
            operator_rows.append({"charge_sites": list(group),
                                  "public_parity_expectation": str(direct),
                                  "orbit_operator_expectation": orbit,
                                  "operator_sign": product[0],
                                  "z_character_nonzero_flip_indices": nontrivial_character,
                                  "first_nonzero_flip_index": (nontrivial_character[0]
                                                               if nontrivial_character else None)})
        rows.append({"error_edges_private_analysis_only": error,
                     "first_public_mass": pair["first_public_mass"],
                     "first_variable_sites": 0,
                     "second_positive_rows": len(public_rows),
                     "operators": operator_rows,
                     "two_parity_law": {key: str(value) for key, value in
                                        parity_law(public_rows, groups).items()}})
        assert time.process_time() - started <= contract["budget"]["max_cpu_seconds"]
    assert [[row["public_parity_expectation"] for row in item["operators"]] for item in rows] == [
        ["1", "1", "1"], ["0", "0", "0"]]
    assert [item["second_positive_rows"] for item in rows] == [16, 64]
    assert all(Fraction(row["conditional_probability"]) == Fraction(1, 16)
               for row in public_laws[0])
    assert all(Fraction(row["conditional_probability"]) == Fraction(1, 64)
               for row in public_laws[1])
    six_assignments = set(itertools.product((0, 1), repeat=6))
    for index, public_rows in enumerate(public_laws):
        observed = {tuple(row["public"]["charge"][i] for i in all_six) for row in public_rows}
        if index == 0:
            expected = {bits for bits in six_assignments
                        if sum(bits[all_six.index(i)] for i in groups[0]) % 2 == 0
                        and sum(bits[all_six.index(i)] for i in groups[1]) % 2 == 0}
        else:
            expected = six_assignments
        assert observed == expected
    parity_a, parity_b = (parity_law(item, groups) for item in public_laws)
    full_tv = tv(law(public_laws[0]), law(public_laws[1]))
    parity_tv = tv(parity_a, parity_b)
    assert full_tv == parity_tv == Fraction(3, 4)
    assert parity_a == {"(0, 0)": Fraction(1)}
    assert parity_b == {str(bits): Fraction(1, 4) for bits in itertools.product((0, 1), repeat=2)}
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "triple_parity_operator_relation_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "first_flux_mask": spec["first_flux_mask"],
            "public_action_red_edges": spec["public_action_red_edges"],
            "triple_charge_sites": [list(group) for group in groups],
            "rows": rows, "two_parity_total_variation": str(parity_tv),
            "full_second_total_variation": str(full_tv),
            "mechanism_boundary": "In this one deterministic-first finite pair only, the two disjoint triple products are +1 orbit stabilizers for the first private error and nontrivial orbit characters with zero mean for the second. Their two parity bits exactly retain full six-site TV. This is not an operator automorphism across sectors, an action-independent law, full-IID information or risk, noisy JIT or threshold.",
            "counters": {"operator_groups": 6, "new_born_terms": 0, "histories": 0,
                         "schedule_arms": 0, "bootstraps": 0},
            "cpu_seconds": round(elapsed, 6)}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "parity_tv": result["two_parity_total_variation"],
                      "cpu_seconds": result["cpu_seconds"]}))
