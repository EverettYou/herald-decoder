"""Capped exact full-second loop law and frozen stateful-interface audit."""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import mask
from run_j6n_sequential_local_projector_moments import conjugated_star, moment
from run_j6o_full_binary_sequential_public_record import public_record, red_boundary
from run_j6w_loop_and_three_block_ideal_projector_matrix import ordered_probability
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j6y_conditional_site_nonrepeat_matrix import exact_first, checked_second


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6z-full-second-stateful-readiness-2026-09-25.json"
RESULT = LAB / "results/j6z-full-second-stateful-readiness-2026-09-25.json"
INPUTS = {
    "jing_pdf": ROOT / "references/jing2025-intrinsic-heralding/paper.pdf",
    "j6l_result": LAB / "results/j6l-periodic-kagome-incidence-2026-09-24.json",
    "j6m_result": LAB / "results/j6m-periodic-operator-ground-orbit-2026-09-24.json",
    "j6y_result": LAB / "results/j6y-conditional-site-nonrepeat-matrix-2026-09-25.json",
    "frozen_integrated_history": LAB / "scripts/d4_integrated_history.py",
    "j6p_adapter": LAB / "scripts/j6p_fixed_path_e2_adapter.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_fields(tree: ast.AST, class_name: str) -> list[str]:
    definition = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return [n.target.id for n in definition.body if isinstance(n, ast.AnnAssign)
            and isinstance(n.target, ast.Name)]


def interface_branch() -> dict:
    frozen = ast.parse(INPUTS["frozen_integrated_history"].read_text())
    adapter = ast.parse(INPUTS["j6p_adapter"].read_text())
    history = data_fields(frozen, "IntegratedD4HistoryV1")
    completion = data_fields(frozen, "ActionConditionedSecondRecordV1")
    provider = next(n for n in adapter.body if isinstance(n, ast.FunctionDef)
                    and n.name == "provide_fixed_path_e2")
    provider_args = [n.arg for n in provider.args.kwonlyargs]
    provider_public_keys = []
    for node in ast.walk(provider):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "public"
                                                for t in node.targets) and isinstance(node.value, ast.Dict):
            provider_public_keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
    caller = next(n for n in frozen.body if isinstance(n, ast.FunctionDef)
                  and n.name == "evaluate_schedule_arm")
    caller_calls = {n.func.id for n in ast.walk(caller) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name)}
    has_state_token = any("postselected_state" in name or "next_first_state" in name
                          for name in history + completion + provider_args + provider_public_keys)
    invokes_fixed_adapter = "provide_fixed_path_e2" in caller_calls
    return {"status": "not_integrated_stateful_next_first_interface" if not has_state_token
            or not invokes_fixed_adapter else "stateful_interface_fields_present_requires_dynamic_test",
            "history_fields": history, "completion_fields": completion,
            "fixed_adapter_arguments": provider_args,
            "fixed_adapter_public_keys": provider_public_keys,
            "has_postselected_or_next_first_state_token": has_state_token,
            "five_round_caller_invokes_fixed_adapter": invokes_fixed_adapter,
            "five_round_caller_invokes_pheno_second_provider":
                "provide_action_conditioned_second_record" in caller_calls,
            "missing_interface": "postselected state carried through action-bound completion into a later first observation" if not has_state_token else None,
            "claim_boundary": "Pinned source/API audit, not a proof that physical D4 feedback cannot exist"}


def transform_coefficients(first_ops, second_ops, flips, started, cap):
    m, n = len(first_ops), len(second_ops)
    terms = 1 << (2 * m + n)
    if terms > 262144:
        return None
    first_products = [[first_ops[i] for i in range(m) if (mask_bits >> i) & 1]
                      for mask_bits in range(1 << m)]
    second_products = [[second_ops[i] for i in range(n) if (mask_bits >> i) & 1]
                       for mask_bits in range(1 << n)]
    coefficients = [0] * (1 << (m + n))
    for b, middle in enumerate(second_products):
        for d in range(1 << m):
            total = 0
            for a, left in enumerate(first_products):
                if (a & 63) == 0 and time.process_time() - started >= cap:
                    raise TimeoutError("registered CPU cap")
                total += moment(left + middle + first_products[a ^ d], flips)
            coefficients[d | (b << m)] = total
    values = coefficients.copy()
    for bit in range(m + n):
        stride = 1 << bit
        for base in range(0, len(values), stride * 2):
            for offset in range(stride):
                low = base + offset
                high = low + stride
                u, v = values[low], values[high]
                values[low], values[high] = u + v, u - v
    denominator = 1 << (2 * m + n)
    return {"values": values, "denominator": denominator, "moment_terms": terms}


def loop_branch(contract, embedding, state, started):
    cap = contract["budget"]["max_cpu_seconds"]
    spec = contract["matrix"]["full_second_loop"]
    red = {int(q["lab004_red_edge_id"]): q for q in embedding["physical_qubits"]
           if q["color"] == "red"}
    stars = {star["center"]: star for star in embedding["star_supports"]}
    sites = {int(center.split(":")[1]): star for center, star in stars.items()
             if star["center_color"] in ("blue", "green")}
    assert len(red) == len(stars) == 36 and set(sites) == set(range(24))
    flips = [mask(star["outer_x_qubits"]) for star in stars.values()]
    pair_rows = state["pair_rows"]
    physical, first_flux = red_boundary(red, spec["physical_red_edges_private"])
    first_eligible, first_means = sector_sites(sites, physical, flips, pair_rows)
    assert first_eligible == [s for s, bit in enumerate(first_flux) if not bit]
    first_sites = sorted(s for s, mean in first_means.items() if mean == 0)
    assert len(first_sites) == 6 and all(mean == 1 for mean in first_means.values() if mean)
    first_ops = [conjugated_star(sites[s], physical) for s in first_sites]
    first_rows = exact_first(first_ops, flips)
    assert len(first_rows) == 16
    action_mask, _ = red_boundary(red, spec["first_public_action_red_edges"])
    residual = physical ^ action_mask
    second_flux = red_boundary(red, [e for e in spec["physical_red_edges_private"]
                                    if e not in spec["first_public_action_red_edges"]])[1]
    second_eligible, _ = sector_sites(sites, residual, flips, pair_rows)
    assert second_eligible == [s for s, bit in enumerate(second_flux) if not bit]
    second_ops = {s: conjugated_star(sites[s], residual) for s in second_eligible}
    conditionals = {}
    variable_sites = set()
    try:
        for first_bits, first_mass in first_rows:
            if time.process_time() - started >= cap:
                raise TimeoutError("registered CPU cap")
            per_site = {}
            for site, op in second_ops.items():
                law = checked_second(first_ops, first_bits, first_mass, op, flips)
                per_site[site] = law[1]
                if 0 < law[1] < 1:
                    variable_sites.add(site)
            conditionals[first_bits] = per_site
    except TimeoutError:
        return {"status": "censored_registered_cpu_cap_during_marginals",
                "partial_rows_discarded": True}
    variable_sites = sorted(variable_sites)
    if len(variable_sites) > spec["max_variable_second_sites"]:
        return {"status": "censored_variable_second_site_cap",
                "first_positive_records": 16, "second_variable_sites_private": variable_sites,
                "second_eligible_sites_count": len(second_eligible)}
    contracted = None
    try:
        contracted = transform_coefficients(first_ops,
            [second_ops[s] for s in variable_sites], flips, started, cap)
    except TimeoutError:
        return {"status": "censored_registered_cpu_cap_during_joint",
                "first_positive_records": 16, "second_variable_sites_private": variable_sites,
                "partial_rows_discarded": True}
    if contracted is None:
        return {"status": "censored_moment_term_cap", "second_variable_sites_private": variable_sites}
    m, n = len(first_sites), len(variable_sites)
    numerator, denominator = contracted["values"], contracted["denominator"]
    assert all(value >= 0 for value in numerator)
    assert sum(numerator) == denominator
    rows = []
    for first_index in range(1 << m):
        first_bits = tuple(-1 if (first_index >> i) & 1 else 1 for i in range(m))
        first_mass = dict(first_rows).get(first_bits, Fraction())
        for second_index in range(1 << n):
            joint = Fraction(numerator[first_index | (second_index << m)], denominator)
            if not joint:
                continue
            assert first_mass > 0
            second_charge = [0] * 24
            for site, plus in conditionals[first_bits].items():
                if site not in variable_sites:
                    assert plus in (0, 1)
                    second_charge[site] = int(plus == 0)
            for bit, site in enumerate(variable_sites):
                second_charge[site] = (second_index >> bit) & 1
            first_charge = [0] * 24
            for bit, site in enumerate(first_sites):
                first_charge[site] = (first_index >> bit) & 1
            rows.append({"first_public": public_record(first_flux, first_charge),
                         "first_probability": str(first_mass),
                         "public_action_red_edge_ids": spec["first_public_action_red_edges"],
                         "second_public": public_record(second_flux, second_charge),
                         "second_conditional_probability": str(joint / first_mass),
                         "joint_probability": str(joint)})
    assert len(rows) <= spec["max_public_rows"]
    by_first = {}
    for row in rows:
        key = tuple(row["first_public"]["charge"][s] for s in first_sites)
        by_first[key] = by_first.get(key, Fraction()) + Fraction(row["joint_probability"])
    assert len(by_first) == 16
    for first_bits, first_mass in first_rows:
        key = tuple(int(bit == -1) for bit in first_bits)
        assert by_first[key] == first_mass
        for site in variable_sites:
            plus = sum((Fraction(row["joint_probability"]) for row in rows
                        if tuple(row["first_public"]["charge"][s] for s in first_sites) == key
                        and row["second_public"]["charge"][site] == 0), Fraction())
            assert plus / first_mass == conditionals[first_bits][site]
    return {"status": "passed_exact_one_geometry_full_binary_second_public_law",
            "first_variable_sites_private": first_sites,
            "second_variable_sites_private": variable_sites,
            "first_positive_records": len(first_rows),
            "second_eligible_sites_count": len(second_eligible),
            "moment_terms": contracted["moment_terms"],
            "positive_public_rows": len(rows),
            "public_law_rows": rows,
            "claim_boundary": "One ideal fixed loop/action and one vacuum orbit; no physical noisy history or stateful next first observation"}


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    pins = {name: digest(path) == contract["pinned_inputs"][name + "_sha256"]
            for name, path in INPUTS.items()}
    assert all(pins.values()), pins
    embedding = json.loads(INPUTS["j6l_result"].read_text())
    state = json.loads(INPUTS["j6m_result"].read_text())
    prior = json.loads(INPUTS["j6y_result"].read_text())
    assert prior["status"] == "bounded_exact_two_branch_matrix"
    exact = loop_branch(contract, embedding, state, started)
    interface = interface_branch()
    assert all(digest(path) == contract["pinned_inputs"][name + "_sha256"]
               for name, path in INPUTS.items())
    return {"schema_version": 1, "id": contract["id"],
            "status": "bounded_two_prerequisite_matrix",
            "contract_sha256": digest(CONTRACT), "pinned_input_checks": pins,
            "full_second_loop": exact, "stateful_next_round_interface": interface,
            "counters": {"stochastic_histories": 0, "schedule_arm_evaluations": 0,
                         "bootstrap_replicates": 0},
            "cpu_seconds": time.process_time() - started,
            "inference_boundary": "Complete second public law only if exact branch passes; frozen caller audit separately tests integration. No general D4 transition or noisy schedule inference."}


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2) + "\n")
