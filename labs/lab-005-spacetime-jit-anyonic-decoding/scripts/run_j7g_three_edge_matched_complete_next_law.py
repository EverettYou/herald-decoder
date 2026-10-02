"""Exact complete-public three-edge matched-support history discriminator."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import (
    canonical_record, make_token, payload_digest, setup,
)
from run_j7b_future_fault_next_first_and_caller_gate import Censor
from run_j7c_three_edge_history_memory_discriminator import completion, rejected
from run_j7e_two_edge_complete_next_law import checked_exact, full_law


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7g-three-edge-matched-complete-next-law-2026-09-25.json"
RESULT = LAB / "results/j7g-three-edge-matched-complete-next-law-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j7c_result": LAB / "results/j7c-three-edge-history-memory-discriminator-2026-09-25.json",
    "j7d_result": LAB / "results/j7d-cross-round-commutation-screen-2026-09-25.json",
    "j7e_result": LAB / "results/j7e-two-edge-complete-next-law-2026-09-25.json",
    "j7f_result": LAB / "results/j7f-state-sensitive-influence-screen-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}
TRIAL_ID = "j7g-three-edge-one-first-exact"
FUTURE_KEYS = {"A": "j7g-future-physical-red-0", "B": "j7g-future-physical-red-4"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_matrix(contract, frozen_first, red, sites, flips, pairs, started):
    spec, budget = contract["matrix"], contract["budget"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [s for s, bit in enumerate(first_flux) if bit == 0]
    assert [s for s, mean in first_means.items() if mean == 0] == spec["first_variable_sites_private"]
    first = canonical_record(frozen_first["first_public"])
    assert first["flux"] == first_flux
    assert first["charge"] == [0] * 24
    first_sites = spec["first_variable_sites_private"]
    first_ops = [conjugated_star(sites[s], physical) for s in first_sites]
    first_bits = tuple(spec["first_bits"])
    assert first_bits == (1, 1)
    first_block = (first_ops, first_bits)
    usage = {"ordered_moment_terms": 0, "second_rows": 0, "next_rows": 0}
    try:
        first_mass = checked_exact([first_block], flips, usage, budget, started)
        assert first_mass == Fraction(spec["first_probability"])
        assert first_mass == Fraction(frozen_first["first_mass"])
        branches = {}
        example = None
        for label in ("A", "B"):
            branch = spec["branch_" + label.lower()]
            action = tuple(branch["public_action_red_edges"])
            future_edge = branch["future_physical_red_edge_private"]
            action_mask, _ = red_boundary(red, list(action))
            future_mask, _ = red_boundary(red, [future_edge])
            residual = physical ^ action_mask
            final = residual ^ future_mask
            assert final == physical
            residual_edges = branch["residual_red_edges_private"]
            _, second_flux = red_boundary(red, residual_edges)
            second_eligible, _ = sector_sites(sites, residual, flips, pairs)
            assert second_eligible == [s for s, bit in enumerate(second_flux) if bit == 0]
            next_eligible, _ = sector_sites(sites, final, flips, pairs)
            assert next_eligible == first_eligible
            second_variable, second_rows = full_law(
                blocks=[first_block], candidate_sites=second_eligible,
                error_mask=residual, flux=second_flux, sites=sites,
                flips=flips, usage=usage, budget=budget, started=started,
                variable_cap="max_variable_second_sites", row_key="second_rows")
            rows = []
            for second_row in second_rows:
                second = canonical_record(second_row["public"])
                second_ops = [conjugated_star(sites[s], residual)
                              for s in second_variable]
                second_bits = tuple(1 if second["charge"][s] == 0 else -1
                                    for s in second_variable)
                blocks = [first_block, (second_ops, second_bits)]
                prefix_mass = checked_exact(blocks, flips, usage, budget, started)
                assert prefix_mass == first_mass * Fraction(
                    second_row["conditional_probability"])
                for op, bit in zip(second_ops, second_bits):
                    assert checked_exact(blocks + [([op], (bit,))], flips,
                                         usage, budget, started) == prefix_mass
                    assert checked_exact(blocks + [([op], (-bit,))], flips,
                                         usage, budget, started) == 0
                next_variable, next_rows = full_law(
                    blocks=blocks, candidate_sites=next_eligible,
                    error_mask=final, flux=first_flux, sites=sites,
                    flips=flips, usage=usage, budget=budget, started=started,
                    variable_cap="max_variable_next_sites", row_key="next_rows")
                token = make_token(
                    trial_id=TRIAL_ID, first_public=first,
                    second_public=second, action_edges=action,
                    allowed_actions=((0,), (4,)), physical_mask=physical,
                    action_mask=action_mask,
                    first_projectors=tuple((s, *op, bit) for s, op, bit
                        in zip(first_sites, first_ops, first_bits)),
                    second_projectors=tuple((s, *op, bit) for s, op, bit
                        in zip(second_variable, second_ops, second_bits)))
                support = {payload_digest(row["public"]) for row in next_rows}
                for next_row in next_rows:
                    nxt = next_row.pop("public")
                    next_row["next_first_public"] = nxt
                    args = dict(token=token, first_public=first,
                        second_public=second, action_edges=action,
                        future_key=FUTURE_KEYS[label],
                        expected_future_key=FUTURE_KEYS[label],
                        next_public=nxt, support=support)
                    next_row["public_completion"] = completion(**args)
                    assert completion(**args) == next_row["public_completion"]
                    if example is None:
                        example = args
                rows.append({"first_public": first, "second_public": second,
                             "public_action_red_edge_ids": list(action),
                             "second_variable_sites_private": second_variable,
                             "next_variable_sites_private": next_variable,
                             "prefix_mass": str(prefix_mass),
                             "next_rows": next_rows})
            assert sum((Fraction(row["prefix_mass"]) for row in rows),
                       Fraction()) == first_mass
            branches[label] = {"public_action_red_edge_ids": list(action),
                "future_physical_red_edge_private": future_edge,
                "residual_red_edges_private": residual_edges,
                "positive_prefixes": len(rows), "rows": rows}
        assert example is not None
        changed_first = canonical_record(first)
        changed_first["charge"][1] ^= 1
        changed_first["vacuum"][1] ^= 1
        changed_second = canonical_record(example["second_public"])
        second_site = branches["A"]["rows"][0]["second_variable_sites_private"][0]
        changed_second["charge"][second_site] ^= 1
        changed_second["vacuum"][second_site] ^= 1
        controls = {
            "swapped_action": rejected(completion, **{**example,
                "action_edges": (4,)}),
            "tampered_first": rejected(completion, **{**example,
                "first_public": changed_first}),
            "tampered_second": rejected(completion, **{**example,
                "second_public": changed_second}),
            "wrong_future_key": rejected(completion, **{**example,
                "future_key": "wrong"}),
            "private_field_injection": rejected(completion, **{**example,
                "next_public": {**example["next_public"],
                                "physical_edges": [0, 4, 3]}}),
        }
        assert all(controls.values())
        laws = {}
        for label in ("A", "B"):
            law = {}
            for row in branches[label]["rows"]:
                for next_row in row["next_rows"]:
                    key = payload_digest(next_row["next_first_public"])
                    mass = Fraction(row["prefix_mass"]) * Fraction(
                        next_row["conditional_probability"]) / first_mass
                    law[key] = law.get(key, Fraction()) + mass
            assert sum(law.values(), Fraction()) == 1
            laws[label] = law
        tv = sum((abs(laws["A"].get(key, Fraction()) -
                      laws["B"].get(key, Fraction()))
                  for key in set(laws["A"]) | set(laws["B"])), Fraction()) / 2
        site_one_minus = {}
        for label in ("A", "B"):
            site_one_minus[label] = sum((Fraction(row["prefix_mass"]) *
                Fraction(next_row["conditional_probability"]) / first_mass
                for row in branches[label]["rows"] for next_row in row["next_rows"]
                if next_row["next_first_public"]["charge"][1] == 1), Fraction())
        assert site_one_minus == {"A": Fraction(1, 2), "B": Fraction(0)}
        assert tv >= Fraction(1, 2)
        return {"status": "passed_two_branch_complete_public_law",
                "first_public": first, "first_mass": str(first_mass),
                "branch_a": branches["A"], "branch_b": branches["B"],
                "exact_total_variation": str(tv),
                "next_site_one_charge_probability": {key: str(value)
                    for key, value in site_one_minus.items()},
                "binding_controls": controls, "usage": usage,
                "claim_boundary": "One selected first record on one ideal three-edge orbit; later fault differs by branch, so not isolated action causality"}
    except Censor as error:
        return {"status": "censored_at_registered_cap", "reason": str(error),
                "usage": usage}


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    j7c = json.loads(INPUTS["j7c_result"].read_text())
    j7d = json.loads(INPUTS["j7d_result"].read_text())
    j7e = json.loads(INPUTS["j7e_result"].read_text())
    j7f = json.loads(INPUTS["j7f_result"].read_text())
    assert set(j7c["matrix"]["exact_total_variation_by_first_charge"].values()) == {"0"}
    assert set(j7e["matrix"]["exact_total_variation_by_first_charge"].values()) == {"0"}
    frozen = next(row for row in j7f["rows"] if row["fixture"] == "three_edge_chain")
    assert frozen["first_mass"] == "1/4" and frozen["baseline_next_mean"] == "1"
    specs = contract["matrix"]
    for label in ("a", "b"):
        branch = specs["branch_" + label]
        rows = [row for row in j7d["branch_rows"]
                if row["fixture"] == "three_edge_chain" and
                row["public_action_edges"] == branch["public_action_red_edges"] and
                row["future_fault_edge_private"] == branch["future_physical_red_edge_private"]]
        assert len(rows) == 1
        assert set(rows[0]["final_edges_private"]) == set(specs["physical_red_edges_private"])
        assert (rows[0]["second_next_anticommuting_pairs"] > 0) == (label == "a")
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    orbit = json.loads(INPUTS["j6m_result"].read_text())
    red, sites, flips, pairs = setup(embedding, orbit)
    matrix = run_matrix(contract, frozen, red, sites, flips, pairs, started)
    pins_after = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
                  for name, path in INPUTS.items()}
    assert all(pins_after.values())
    return {"schema_version": 1, "id": contract["id"],
            "status": ("exact_three_edge_one_first_complete_public_contrast_closed"
                if matrix["status"].startswith("passed") else
                "exact_three_edge_one_first_complete_public_contrast_censored"),
            "contract_sha256": digest(CONTRACT),
            "pinned_input_checks_before": pins,
            "pinned_input_checks_after": pins_after,
            "matrix": matrix,
            "j7c_j7e_exact_null_controls": True,
            "frozen_caller_gate": "unchanged_not_integrated_stateful_future_first_callback",
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": round(time.process_time() - started, 6),
            "inference_boundary": "One ideal fixed three-edge selected-first-record complete-public history contrast; no physical five-round integration, isolated action effect, noisy JIT risk, scaling, general D4 kernel or threshold."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
