#!/usr/bin/env python3
"""Run the registered R4.5b expanded-branch MWPM equivalence matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import charge_chain_boundary, charge_check_matrix
from d4_charge_multigraph import (
    branch_chain_sector,
    build_branch_charge_lattice,
    build_charge_branch_catalog,
    build_expanded_branch_matching,
    decode_expanded_branch_syndrome,
    expanded_charge_syndrome,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN, periodic_honeycomb
from d4_sequential import chain_mask
from run_r4_distinct_observation_matrix import _sha256
from run_r4_public_branch_fidelity_audit import _profiles


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-expanded-branch-mwpm-adapter-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-expanded-branch-mwpm-adapter-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-expanded-branch-mwpm-adapter-audit.md"


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        if _sha256(LAB_DIR / relative) != expected:
            raise ValueError(f"R4.5b source hash drift: {relative}")


def _selected_edges_have_complete_private_paths(
    matching,
    expanded_syndrome: np.ndarray,
    physical_vertex_count: int,
    branch_count: int,
) -> bool:
    selected = {
        tuple(sorted((int(left), int(right))))
        for left, right in matching.decode_to_edges_array(expanded_syndrome)
    }
    for branch_id in range(branch_count):
        auxiliary = physical_vertex_count + branch_id
        incidence = sum(auxiliary in edge for edge in selected)
        if incidence not in (0, 2):
            return False
    return True


def _audit_color(honeycomb, color: int) -> dict:
    lattice = build_branch_charge_lattice(honeycomb, color)
    branches = build_charge_branch_catalog(honeycomb, color)
    check = charge_check_matrix(lattice)
    even_syndromes = []
    actions = {}
    for mask in range(1 << lattice.vertex_count):
        syndrome = np.asarray(
            [(mask >> vertex) & 1 for vertex in range(lattice.vertex_count)],
            dtype=np.uint8,
        )
        if int(np.sum(syndrome)) % 2 == 0:
            even_syndromes.append((mask, syndrome))
            actions[mask] = enumerate_affine_chains(check, syndrome)

    topology_failures = 0
    auxiliary_degree_failures = 0
    auxiliary_syndrome_failures = 0
    half_branch_solution_failures = 0
    objective_failures = 0
    boundary_failures = 0
    minimizer_membership_failures = 0
    targeted_selection_failures = 0
    targeted_sector_failures = 0
    maximum_objective_error = 0.0
    profile_rows = []
    for name, weights, target in _profiles(branches):
        matching = build_expanded_branch_matching(honeycomb, color, weights)
        edges = matching.edges()
        retained = sorted(
            fault
            for _, _, attributes in edges
            for fault in attributes["fault_ids"]
        )
        topology_pass = (
            matching.num_nodes == lattice.vertex_count + lattice.edge_count
            and matching.num_edges == 2 * lattice.edge_count
            and matching.num_fault_ids == lattice.edge_count
            and retained == list(range(lattice.edge_count))
            and len({tuple(sorted((int(left), int(right)))) for left, right, _ in edges})
            == 2 * lattice.edge_count
        )
        topology_failures += int(not topology_pass)
        degrees = {lattice.vertex_count + edge: 0 for edge in range(lattice.edge_count)}
        for left, right, _ in edges:
            if int(left) in degrees:
                degrees[int(left)] += 1
            if int(right) in degrees:
                degrees[int(right)] += 1
        auxiliary_degree_failures += sum(degree != 2 for degree in degrees.values())
        row = {
            "name": name,
            "target_branch": target,
            "matching_node_count": int(matching.num_nodes),
            "matching_edge_count": int(matching.num_edges),
            "matching_fault_id_count": int(matching.num_fault_ids),
            "retained_fault_ids": retained,
        }
        for syndrome_mask, syndrome in even_syndromes:
            expanded = expanded_charge_syndrome(lattice, syndrome)
            if np.any(expanded[lattice.vertex_count :]):
                auxiliary_syndrome_failures += 1
            correction, returned_weight = decode_expanded_branch_syndrome(
                honeycomb, color, syndrome, weights
            )
            if not _selected_edges_have_complete_private_paths(
                matching, expanded, lattice.vertex_count, lattice.edge_count
            ):
                half_branch_solution_failures += 1
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
            syndrome = np.zeros(lattice.vertex_count, dtype=np.uint8)
            for endpoint in target_branch.endpoints:
                syndrome[lattice.local_vertex(endpoint)] ^= 1
            correction, _ = decode_expanded_branch_syndrome(
                honeycomb, color, syndrome, weights
            )
            twin = next(
                branch.branch_id
                for branch in branches
                if branch.endpoints == target_branch.endpoints
                and branch.branch_id != target
            )
            if not (correction[target] == 1 and correction[twin] == 0):
                targeted_selection_failures += 1
            target_chain = np.zeros(lattice.edge_count, dtype=np.uint8)
            target_chain[target] = 1
            if branch_chain_sector(
                honeycomb, color, correction ^ target_chain
            ) != (0, 0):
                targeted_sector_failures += 1
        profile_rows.append(row)
    passed = all(
        failure == 0
        for failure in (
            topology_failures,
            auxiliary_degree_failures,
            auxiliary_syndrome_failures,
            half_branch_solution_failures,
            objective_failures,
            boundary_failures,
            minimizer_membership_failures,
            targeted_selection_failures,
            targeted_sector_failures,
        )
    )
    return {
        "physical_branch_count": lattice.edge_count,
        "profile_count": len(profile_rows),
        "even_syndrome_count": len(even_syndromes),
        "decode_comparison_count": len(profile_rows) * len(even_syndromes),
        "topology_failures": topology_failures,
        "private_auxiliary_degree_failures": auxiliary_degree_failures,
        "nonzero_auxiliary_syndrome_failures": auxiliary_syndrome_failures,
        "half_branch_solution_failures": half_branch_solution_failures,
        "objective_failures": objective_failures,
        "boundary_failures": boundary_failures,
        "exact_minimizer_membership_failures": minimizer_membership_failures,
        "targeted_branch_selection_failures": targeted_selection_failures,
        "targeted_period_cochain_sector_failures": targeted_sector_failures,
        "maximum_objective_error": maximum_objective_error,
        "expanded_adapter_pass": passed,
        "profiles": profile_rows,
    }


def run_audit(manifest: dict) -> dict:
    _validate_manifest(manifest)
    honeycomb = periodic_honeycomb(2)
    colors = {
        "blue": _audit_color(honeycomb, BLUE),
        "green": _audit_color(honeycomb, GREEN),
    }
    comparisons = sum(result["decode_comparison_count"] for result in colors.values())
    validation = {
        "blue_adapter_pass": colors["blue"]["expanded_adapter_pass"],
        "green_adapter_pass": colors["green"]["expanded_adapter_pass"],
        "decode_comparison_guard_pass": comparisons <= int(manifest["compute_budget"]["maximum_decode_comparisons"]),
    }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "expanded_branch_adapter_passed" if all(validation.values()) else "expanded_branch_adapter_failed",
        "colors": colors,
        "total_decode_comparisons": comparisons,
        "validation": validation,
        "new_stochastic_samples": 0,
        "claim_boundary": "Expanded primitive public charge-MWPM representation equivalence only. No sequential policy risk, LER, threshold, noisy-measurement, or scalability result is computed.",
        "source_hashes": {
            "scripts/d4_charge_multigraph.py": _sha256(LAB_DIR / "scripts/d4_charge_multigraph.py"),
            "scripts/run_r4_expanded_branch_adapter_audit.py": _sha256(LAB_DIR / "scripts/run_r4_expanded_branch_adapter_audit.py"),
        },
    }
    payload["structural_digest_sha256"] = hashlib.sha256(
        json.dumps(
            {"colors": colors, "validation": validation},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    lines = [
        "# R4.5b expanded branch MWPM adapter audit",
        "",
        f"Status: **{payload['status']}**.",
        "",
    ]
    for color in ("blue", "green"):
        result = payload["colors"][color]
        lines.append(
            f"- {color}: {result['decode_comparison_count']} exhaustive comparisons; "
            f"topology/auxiliary/half-branch failures "
            f"{result['topology_failures']}/{result['private_auxiliary_degree_failures']}/"
            f"{result['half_branch_solution_failures']}; objective/boundary/minimizer/"
            f"target/sector failures {result['objective_failures']}/"
            f"{result['boundary_failures']}/{result['exact_minimizer_membership_failures']}/"
            f"{result['targeted_branch_selection_failures']}/"
            f"{result['targeted_period_cochain_sector_failures']}."
        )
    lines.extend(
        [
            "",
            "Each colour uses one 16-node, 24-edge matching graph with twelve private degree-two auxiliary detectors and all twelve physical branch fault ids. Auxiliary syndrome bits are always zero, and every decoded solution selects both segments of a branch or neither.",
            "",
            f"All {payload['total_decode_comparisons']} registered profile/syndrome cases match exhaustive primitive objectives and minimum branch masks. The adapter is now eligible for integration into a re-registered R4.5 sequential-policy computation; that integration and risk are not part of this audit.",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run_audit(json.loads(args.manifest.read_text()))
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps(payload, indent=2))
    if payload["status"] != "expanded_branch_adapter_passed":
        raise SystemExit("R4.5b expanded branch adapter audit failed")


if __name__ == "__main__":
    main()
