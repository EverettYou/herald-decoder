"""Private ideal projector-state handoff into a no-new-fault next first record."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6q_alternate_path_operator_law_matrix import assignments
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j7a-postselected-next-first-limiting-fixtures-2026-09-25.json"
RESULT = LAB / "results/j7a-postselected-next-first-limiting-fixtures-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6o_result": LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json",
    "j6z_result": LAB / "results/j6z-full-second-stateful-readiness-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical_record(value: dict) -> dict:
    if type(value) is not dict or set(value) != {"flux", "charge", "vacuum"}:
        raise ValueError("record must contain only full binary public arrays")
    if any(type(value[key]) is not list or len(value[key]) != 24
           or any(type(bit) is not int or bit not in (0, 1) for bit in value[key])
           for key in value):
        raise ValueError("invalid 24-site public array")
    if any(f and c for f, c in zip(value["flux"], value["charge"])):
        raise ValueError("flux and charge are exclusive")
    if value["vacuum"] != [1 - bit for bit in value["charge"]]:
        raise ValueError("vacuum complement drift")
    return {key: value[key].copy() for key in ("flux", "charge", "vacuum")}


@dataclass(frozen=True)
class PrivatePostselectedState:
    trial_id: str
    first_digest: str
    action_edges: tuple[int, ...]
    action_digest: str
    second_digest: str | None
    physical_mask: int
    residual_mask: int
    first_projectors: tuple[tuple[int, int, int, int], ...]
    second_projectors: tuple[tuple[int, int, int, int], ...]
    state_digest: str


def token_body(token: PrivatePostselectedState) -> dict:
    return {"trial_id": token.trial_id, "first_digest": token.first_digest,
            "action_edges": token.action_edges, "action_digest": token.action_digest,
            "second_digest": token.second_digest,
            "physical_mask": token.physical_mask, "residual_mask": token.residual_mask,
            "first_projectors": token.first_projectors,
            "second_projectors": token.second_projectors}


def make_token(*, trial_id: str, first_public: dict, second_public: dict | None,
               action_edges: tuple[int, ...], allowed_actions: tuple[tuple[int, ...], ...],
               physical_mask: int, action_mask: int,
               first_projectors: tuple[tuple[int, int, int, int], ...],
               second_projectors: tuple[tuple[int, int, int, int], ...]) -> PrivatePostselectedState:
    if not trial_id or action_edges not in allowed_actions:
        raise ValueError("unsupported action or empty trial")
    first = canonical_record(first_public)
    second = None if second_public is None else canonical_record(second_public)
    if (second is None) != (not action_edges):
        raise ValueError("defer has no second record; correction requires one")
    for site, *_, bit in first_projectors:
        if first["charge"][site] != int(bit == -1):
            raise ValueError("first projector/public record mismatch")
    for site, *_, bit in second_projectors:
        if second is None or second["charge"][site] != int(bit == -1):
            raise ValueError("second projector/public record mismatch")
    first_digest = payload_digest({"trial_id": trial_id, "first_public": first})
    action_digest = payload_digest({"trial_id": trial_id, "first_digest": first_digest,
                                    "action_edges": action_edges})
    second_digest = None if second is None else payload_digest(
        {"trial_id": trial_id, "first_digest": first_digest,
         "action_digest": action_digest, "second_public": second})
    provisional = PrivatePostselectedState(trial_id, first_digest, action_edges,
        action_digest, second_digest, physical_mask, physical_mask ^ action_mask,
        first_projectors, second_projectors, "")
    return replace(provisional, state_digest=payload_digest(token_body(provisional)))


def next_first_public(*, token: PrivatePostselectedState, trial_id: str,
                      first_public: dict, second_public: dict | None,
                      expected_action: tuple[int, ...], next_record: dict) -> dict:
    if trial_id != token.trial_id or expected_action != token.action_edges:
        raise ValueError("trial/action token mismatch")
    if payload_digest(token_body(token)) != token.state_digest:
        raise ValueError("private state token was altered")
    first = canonical_record(first_public)
    second = None if second_public is None else canonical_record(second_public)
    if payload_digest({"trial_id": trial_id, "first_public": first}) != token.first_digest:
        raise ValueError("stale first prefix")
    if payload_digest({"trial_id": trial_id, "first_digest": token.first_digest,
                       "action_edges": expected_action}) != token.action_digest:
        raise ValueError("stale action")
    second_digest = None if second is None else payload_digest(
        {"trial_id": trial_id, "first_digest": token.first_digest,
         "action_digest": token.action_digest, "second_public": second})
    if second_digest != token.second_digest:
        raise ValueError("stale second prefix")
    nxt = canonical_record(next_record)
    if nxt != (first if second is None else second):
        raise ValueError("no-new-fault next public record drift")
    public = {"trial_id": trial_id, "first_prefix_digest": token.first_digest,
              "action_digest": token.action_digest,
              "second_prefix_digest": token.second_digest,
              "next_first_public": nxt}
    return {**public, "completion_digest": payload_digest(public)}


def rejected(fn, **kwargs) -> bool:
    try:
        fn(**kwargs)
    except ValueError:
        return True
    return False


def setup(embedding: dict, state: dict):
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"]
           if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(red) == len(stars) == 36 and set(sites) == set(range(24))
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    return red, sites, flips, state["pair_rows"]


def path_branch(contract, source, red, sites, flips, pairs, started):
    spec = contract["matrix"]["two_edge_path"]
    physical, first_flux = red_boundary(red, spec["private_physical_red_edges"])
    first_eligible, _ = sector_sites(sites, physical, flips, pairs)
    assert first_eligible == [s for s, bit in enumerate(first_flux) if not bit]
    first_site = spec["first_variable_site"]
    first_op = conjugated_star(sites[first_site], physical)
    rows = []
    tokens = []
    for source_row in source["public_law_rows"]:
        action_name = source_row["action"]
        action_edges = tuple(spec["actions"][action_name])
        assert source_row["public_action_red_edge_ids"] == list(action_edges)
        first = canonical_record(source_row["first_public"])
        second = None if source_row["second_public"] is None else canonical_record(source_row["second_public"])
        first_bit = 1 if first["charge"][first_site] == 0 else -1
        action_mask, _ = red_boundary(red, list(action_edges))
        residual = physical ^ action_mask
        second_flux = red_boundary(red, [e for e in spec["private_physical_red_edges"]
                                    if e not in action_edges])[1]
        second_eligible, _ = sector_sites(sites, residual, flips, pairs)
        assert second_eligible == [s for s, bit in enumerate(second_flux) if not bit]
        if second is not None:
            assert second["flux"] == second_flux
        second_sites = spec["second_variable_sites_by_action"][action_name]
        second_ops = [conjugated_star(sites[s], residual) for s in second_sites]
        second_bits = tuple(1 if second["charge"][s] == 0 else -1 for s in second_sites)
        blocks = [([first_op], (first_bit,))]
        if second is not None:
            blocks.append((second_ops, second_bits))
        prefix_mass = Fraction(str(source_row["first_probability"])) * (
            Fraction(1) if second is None else Fraction(str(source_row["second_conditional_probability"])))
        assert ordered_probability(blocks, flips) == prefix_mass
        third_ops, expected_bits = (second_ops, second_bits) if second is not None else ([first_op], (first_bit,))
        third_law = {}
        for bits in assignments(len(third_ops)):
            joint = ordered_probability(blocks + [(third_ops, bits)], flips)
            assert joint >= 0
            third_law[bits] = joint / prefix_mass
        assert sum(third_law.values(), Fraction()) == 1
        assert third_law[expected_bits] == 1
        assert all(p == 0 for bits, p in third_law.items() if bits != expected_bits)
        next_record = first if second is None else second
        trial_id = "j7a-fixed-path"
        first_projectors = ((first_site, *first_op, first_bit),)
        second_projectors = tuple((site, *op, bit) for site, op, bit in zip(second_sites, second_ops, second_bits))
        token = make_token(trial_id=trial_id, first_public=first,
            second_public=second, action_edges=action_edges,
            allowed_actions=tuple(tuple(x) for x in spec["actions"].values()),
            physical_mask=physical, action_mask=action_mask,
            first_projectors=first_projectors, second_projectors=second_projectors)
        completed = next_first_public(token=token, trial_id=trial_id,
            first_public=first, second_public=second, expected_action=action_edges,
            next_record=next_record)
        assert set(completed) == {"trial_id", "first_prefix_digest", "action_digest",
                                  "second_prefix_digest", "next_first_public", "completion_digest"}
        assert completed == next_first_public(token=token, trial_id=trial_id,
            first_public=first, second_public=second, expected_action=action_edges,
            next_record=next_record)
        assert all("physical" not in field and "projector" not in field and "state" not in field
                   for field in completed)
        rows.append({"action": action_name, "first_public": first,
                     "second_public": second,
                     "first_probability": str(Fraction(str(source_row["first_probability"]))),
                     "second_conditional_probability": None if second is None else str(Fraction(str(source_row["second_conditional_probability"]))),
                     "next_first_conditional_probability": "1",
                     "public_completion": completed})
        tokens.append((token, first, second, next_record))
        assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    assert len(rows) == spec["positive_case_count"]
    for action in spec["actions"]:
        assert sum((Fraction(row["first_probability"]) *
                    (Fraction(1) if row["second_conditional_probability"] is None
                     else Fraction(row["second_conditional_probability"]))
                    for row in rows if row["action"] == action), Fraction()) == 1
    # Seven independently registered fail-closed controls.
    partial = next((token, first, second, nxt) for token, first, second, nxt in tokens
                   if token.action_edges == (0,))
    token, first, second, nxt = partial
    valid = dict(token=token, trial_id=token.trial_id, first_public=first,
                 second_public=second, expected_action=(0,), next_record=nxt)
    changed_first = canonical_record(first)
    changed_first["charge"][1] ^= 1
    changed_first["vacuum"][1] ^= 1
    changed_second = canonical_record(second)
    changed_second["charge"][0] ^= 1
    changed_second["vacuum"][0] ^= 1
    controls = {
        "swapped_action_token": rejected(next_first_public, **{**valid, "expected_action": (0, 4)}),
        "tampered_first_record": rejected(next_first_public, **{**valid, "first_public": changed_first}),
        "tampered_second_record": rejected(next_first_public, **{**valid, "second_public": changed_second}),
        "stale_prefix_digest": rejected(next_first_public, **{**valid,
            "token": replace(token, first_digest="0" * 64)}),
        "unsupported_action": rejected(make_token, trial_id=token.trial_id,
            first_public=first, second_public=second, action_edges=(4,),
            allowed_actions=tuple(tuple(x) for x in spec["actions"].values()),
            physical_mask=physical, action_mask=0,
            first_projectors=token.first_projectors, second_projectors=token.second_projectors),
        "private_truth_field_injection": rejected(next_first_public, **{**valid,
            "first_public": {**first, "physical_edges": [0, 4]}}),
        "cross_trial_token_reuse": rejected(next_first_public, **{**valid,
            "trial_id": "other-trial"}),
    }
    assert set(controls) == set(contract["matrix"]["binding_controls"])
    assert all(controls.values())
    return {"status": "passed_exact_action_bound_no_fault_next_first_limit",
            "positive_case_count": len(rows), "rows": rows,
            "binding_controls": controls,
            "claim_boundary": "Fixed path and zero new fault; private ideal state token prototype, not integrated five-round caller"}


def loop_branch(contract, source, red, sites, flips, pairs, started):
    spec = contract["matrix"]["six_edge_loop"]
    physical, first_flux = red_boundary(red, spec["private_physical_red_edges"])
    action_mask, _ = red_boundary(red, spec["first_public_action_red_edges"])
    residual = physical ^ action_mask
    eligible, _ = sector_sites(sites, residual, flips, pairs)
    rows = source["full_second_loop"]["public_law_rows"]
    assert len(rows) == spec["positive_case_count"]
    first_sites = source["full_second_loop"]["first_variable_sites_private"]
    first_ops = [conjugated_star(sites[s], physical) for s in first_sites]
    varying_site = 17
    second_op = conjugated_star(sites[varying_site], residual)
    assert varying_site in eligible
    checked = []
    for row in rows:
        first = canonical_record(row["first_public"])
        second = canonical_record(row["second_public"])
        assert first["flux"] == first_flux
        assert second["charge"][2] == 0
        first_bits = tuple(1 if first["charge"][s] == 0 else -1 for s in first_sites)
        second_bit = 1 if second["charge"][varying_site] == 0 else -1
        joint2 = ordered_probability([(first_ops, first_bits), ([second_op], (second_bit,))], flips)
        assert joint2 == Fraction(row["joint_probability"])
        next_law = {}
        for (third_bit,) in assignments(1):
            joint3 = ordered_probability([(first_ops, first_bits), ([second_op], (second_bit,)),
                                          ([second_op], (third_bit,))], flips)
            assert joint3 >= 0
            next_law[third_bit] = joint3 / joint2
        assert next_law[second_bit] == 1 and sum(next_law.values(), Fraction()) == 1
        # Every eligible second projector was measured; commuting-projector
        # idempotence makes the no-fault next full record equal to it.
        assert [site for site, bit in enumerate(second["flux"]) if not bit] == eligible
        checked.append({"first_public": first, "second_public": second,
                        "next_first_public": second,
                        "next_first_conditional_probability": "1",
                        "varying_site_three_block_checked": varying_site})
        assert time.process_time() - started < contract["budget"]["max_cpu_seconds"]
    return {"status": "passed_exact_loop_no_fault_repeat_limit",
            "positive_prefixes": len(checked), "rows": checked,
            "claim_boundary": "Full next-first repeat follows exact projector idempotence only with no new fault/action"}


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    path_source = json.loads(INPUTS["j6o_result"].read_text())
    loop_source = json.loads(INPUTS["j6z_result"].read_text())
    assert path_source["status"] == "passed_exact_one_geometry_full_binary_joint_record_only"
    assert loop_source["full_second_loop"]["status"] == "passed_exact_one_geometry_full_binary_second_public_law"
    red, sites, flips, pairs = setup(embedding, state)
    path = path_branch(contract, path_source, red, sites, flips, pairs, started)
    loop = loop_branch(contract, loop_source, red, sites, flips, pairs, started)
    assert all(digest(path) == contract["pinned_inputs"][name + "_sha256"]
               for name, path in INPUTS.items())
    return {"schema_version": 1, "id": contract["id"],
            "status": "passed_two_exact_no_fault_state_handoff_limits",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "two_edge_path": path, "six_edge_loop": loop,
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Private state-token prototype and no-new-fault ideal repeat limits only; not integrated with frozen five-round caller, no noisy physical D4 feedback or schedule risk."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
