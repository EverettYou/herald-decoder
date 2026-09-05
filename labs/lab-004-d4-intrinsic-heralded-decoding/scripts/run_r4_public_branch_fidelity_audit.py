#!/usr/bin/env python3
"""Audit PyMatching's treatment of primitive parallel charge branches."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pymatching

from d4_charge import charge_chain_boundary, charge_check_matrix
from d4_charge_multigraph import (
    build_branch_charge_lattice,
    build_charge_branch_catalog,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN, periodic_honeycomb
from d4_sequential import chain_mask


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = LAB_DIR / "results/r4-branch-labelled-charge-topology-audit.json"
DEFAULT_JSON = LAB_DIR / "results/r4-public-decoder-branch-fidelity-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-public-decoder-branch-fidelity-audit.md"


def _profiles(branches) -> tuple[tuple[str, np.ndarray, int | None], ...]:
    profiles = [("unit", np.ones(len(branches), dtype=np.float64), None)]
    for target in range(len(branches)):
        weights = 16.0 + np.arange(len(branches), dtype=np.float64) / 16.0
        weights[target] = 0.125
        twin = next(
            branch.branch_id
            for branch in branches
            if branch.endpoints == branches[target].endpoints
            and branch.branch_id != target
        )
        weights[twin] = 8.125
        profiles.append((f"force_branch_{target}", weights, target))
    return tuple(profiles)


def _audit_color(honeycomb, color: int) -> dict:
    lattice = build_branch_charge_lattice(honeycomb, color)
    branches = build_charge_branch_catalog(honeycomb, color)
    check = charge_check_matrix(lattice)
    even_syndromes = []
    for mask in range(1 << lattice.vertex_count):
        syndrome = np.asarray(
            [(mask >> vertex) & 1 for vertex in range(lattice.vertex_count)],
            dtype=np.uint8,
        )
        if int(np.sum(syndrome)) % 2 == 0:
            even_syndromes.append((mask, syndrome))
    actions = {
        mask: enumerate_affine_chains(check, syndrome)
        for mask, syndrome in even_syndromes
    }
    by_pair = defaultdict(list)
    for branch in branches:
        by_pair[branch.endpoints].append(branch.branch_id)

    objective_failures = 0
    boundary_failures = 0
    minimizer_membership_failures = 0
    targeted_selection_failures = 0
    simultaneous_identity_failures = 0
    observed_edge_counts = set()
    observed_fault_counts = set()
    maximum_objective_error = 0.0
    profile_rows = []
    for name, weights, target in _profiles(branches):
        matching = pymatching.Matching.from_check_matrix(check, weights=weights)
        observed_edge_counts.add(int(matching.num_edges))
        observed_fault_counts.add(int(matching.num_fault_ids))
        retained_fault_ids = sorted(
            fault
            for _, _, attributes in matching.edges()
            for fault in attributes["fault_ids"]
        )
        pair_both_retained = 0
        for branch_ids in by_pair.values():
            if set(branch_ids) <= set(retained_fault_ids):
                pair_both_retained += 1
            else:
                simultaneous_identity_failures += 1
        row = {
            "name": name,
            "target_branch": target,
            "matching_edge_count": int(matching.num_edges),
            "matching_fault_id_count": int(matching.num_fault_ids),
            "retained_fault_ids": retained_fault_ids,
            "parallel_pairs_with_both_fault_ids_retained": pair_both_retained,
        }
        for syndrome_mask, syndrome in even_syndromes:
            correction, returned_weight = matching.decode(
                syndrome, return_weight=True
            )
            correction = np.asarray(correction, dtype=np.uint8)
            if not np.array_equal(charge_chain_boundary(lattice, correction), syndrome):
                boundary_failures += 1
            candidates = actions[syndrome_mask]
            objectives = np.asarray(
                [float(np.dot(weights, candidate)) for candidate in candidates]
            )
            exact = float(np.min(objectives))
            error = abs(float(returned_weight) - exact)
            maximum_objective_error = max(maximum_objective_error, error)
            if error > 1e-6:
                objective_failures += 1
            minimizers = {
                chain_mask(candidate)
                for candidate, objective in zip(candidates, objectives, strict=True)
                if abs(float(objective) - exact) <= 1e-12
            }
            if chain_mask(correction) not in minimizers:
                minimizer_membership_failures += 1
        if target is not None:
            target_branch = branches[target]
            target_syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
            for endpoint in target_branch.endpoints:
                target_syndrome[lattice.local_vertex(endpoint)] ^= 1
            correction = np.asarray(matching.decode(target_syndrome), dtype=np.uint8)
            twin = next(
                branch_id
                for branch_id in by_pair[target_branch.endpoints]
                if branch_id != target
            )
            if not (correction[target] == 1 and correction[twin] == 0):
                targeted_selection_failures += 1
        profile_rows.append(row)

    oracle_pass = (
        objective_failures == 0
        and boundary_failures == 0
        and minimizer_membership_failures == 0
        and targeted_selection_failures == 0
    )
    simultaneous_fidelity_pass = (
        observed_edge_counts == {len(branches)}
        and simultaneous_identity_failures == 0
    )
    return {
        "physical_branch_count": len(branches),
        "endpoint_pair_count": len(by_pair),
        "profile_count": len(profile_rows),
        "even_syndrome_count": len(even_syndromes),
        "decode_comparison_count": len(profile_rows) * len(even_syndromes),
        "observed_matching_edge_counts": sorted(observed_edge_counts),
        "observed_matching_fault_id_counts": sorted(observed_fault_counts),
        "objective_failures": objective_failures,
        "boundary_failures": boundary_failures,
        "exact_minimizer_membership_failures": minimizer_membership_failures,
        "targeted_low_weight_branch_selection_failures": targeted_selection_failures,
        "parallel_pair_simultaneous_identity_failures": simultaneous_identity_failures,
        "maximum_objective_error": maximum_objective_error,
        "exhaustive_objective_and_selected_id_pass": oracle_pass,
        "simultaneous_physical_branch_fidelity_pass": simultaneous_fidelity_pass,
        "profiles": profile_rows,
    }


def run_audit(input_payload: dict) -> dict:
    if input_payload.get("status") != "branch_homology_audit_passed":
        raise ValueError("R4.5a homology prerequisite has not passed")
    honeycomb = periodic_honeycomb(2)
    colors = {
        "blue": _audit_color(honeycomb, BLUE),
        "green": _audit_color(honeycomb, GREEN),
    }
    oracle_pass = all(
        result["exhaustive_objective_and_selected_id_pass"]
        for result in colors.values()
    )
    fidelity_pass = all(
        result["simultaneous_physical_branch_fidelity_pass"]
        for result in colors.values()
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "public_branch_fidelity_passed" if oracle_pass and fidelity_pass else "public_branch_fidelity_failed",
        "pymatching_version": pymatching.__version__,
        "input_structural_digest_sha256": input_payload["structural_digest_sha256"],
        "colors": colors,
        "validation": {
            "exhaustive_objective_and_selected_id_pass": oracle_pass,
            "simultaneous_physical_branch_fidelity_pass": fidelity_pass,
            "expanded_graph_adapter_required": not fidelity_pass,
        },
        "interpretation": "PyMatching's check-matrix constructor keeps the minimum-weight representative of each parallel endpoint pair. Rebuilding with a different weight can select either fault id and all returned objectives are exact, but one matching graph never retains both physical branches simultaneously. Therefore the primitive public second-stage graph is not topology-faithful without expansion.",
        "claim_boundary": "Deterministic primitive PyMatching representation audit only. It does not validate an expanded adapter, compute sequential policy risk, or establish LER, threshold, or scalability.",
        "new_stochastic_samples": 0,
    }
    payload["structural_digest_sha256"] = hashlib.sha256(
        json.dumps(
            {"colors": colors, "validation": payload["validation"]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    lines = [
        "# R4.5a public decoder branch-fidelity audit",
        "",
        f"Status: **{payload['status']}**.",
        "",
    ]
    for color in ("blue", "green"):
        result = payload["colors"][color]
        lines.append(
            f"- {color}: {result['physical_branch_count']} physical branches become "
            f"{result['observed_matching_edge_counts']} matching edges. Across "
            f"{result['decode_comparison_count']} profile/syndrome comparisons, objective, "
            f"boundary, minimizer-membership, and targeted-ID failures are "
            f"{result['objective_failures']}, {result['boundary_failures']}, "
            f"{result['exact_minimizer_membership_failures']}, and "
            f"{result['targeted_low_weight_branch_selection_failures']}."
        )
    lines.extend(
        [
            "",
            "The exhaustive oracle shows that reconstruction-time minimum-weight selection is numerically correct and can choose either parallel fault id when that id is made cheaper. However, a single matching graph retains only one of the two physical branches for each endpoint pair: twelve branches collapse to six edges. The public primitive graph therefore loses simultaneous branch topology and cannot yet be called reproduced.",
            "",
            "A bounded private-auxiliary-node expansion is required. Each physical branch will become a two-edge path through its own zero-syndrome auxiliary detector, with one branch fault id and split total weight. That adapter must reproduce every exhaustive objective and branch mask before sequential-risk work resumes.",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run_audit(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
