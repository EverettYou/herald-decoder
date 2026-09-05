#!/usr/bin/env python3
"""Run R4.5a parallel-branch winding and exact quotient gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from d4_charge import charge_chain_boundary, classify_closed_charge_chain
from d4_charge_multigraph import (
    branch_chain_sector,
    build_branch_charge_lattice,
    build_charge_branch_catalog,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN
from d4_sequential import chain_mask, closed_charge_sector
from run_r4_branch_topology_preflight import (
    DEFAULT_JSON,
    DEFAULT_MANIFEST,
    DEFAULT_REPORT,
    run_preflight,
)


def _canonical_winding(vector: np.ndarray, periods: np.ndarray) -> tuple[int, int]:
    a, b = (int(value) for value in periods[0])
    c, d = (int(value) for value in periods[1])
    determinant = a * d - b * c
    numerator = np.asarray(
        (d * int(vector[0]) - b * int(vector[1]), -c * int(vector[0]) + a * int(vector[1])),
        dtype=np.int64,
    )
    if determinant <= 0 or np.any(numerator % determinant):
        raise ValueError("parallel-branch displacement difference is not a torus winding")
    winding = numerator // determinant
    first_nonzero = next((int(value) for value in winding if value), 0)
    if first_nonzero < 0:
        winding = -winding
    return int(winding[0]), int(winding[1])


def _parallel_fixtures(lattice, color: int) -> dict:
    charge_lattice = build_branch_charge_lattice(lattice, color)
    branches = build_charge_branch_catalog(lattice, color)
    by_pair = defaultdict(list)
    for branch in branches:
        by_pair[branch.endpoints].append(branch)
    fixtures = []
    failures = 0
    for endpoints, parallel in sorted(by_pair.items()):
        if len(parallel) != 2:
            failures += 1
            continue
        first, second = parallel
        chain = np.zeros(charge_lattice.edge_count, dtype=np.uint8)
        chain[[first.branch_id, second.branch_id]] = 1
        boundary = charge_chain_boundary(charge_lattice, chain)
        expected = _canonical_winding(
            np.asarray(first.displacement, dtype=np.int64)
            - np.asarray(second.displacement, dtype=np.int64),
            charge_lattice.period_matrix,
        )
        analysis = classify_closed_charge_chain(charge_lattice, chain)
        observed = tuple(
            sorted(
                {
                    winding
                    for component in analysis.component_windings
                    for winding in component
                }
            )
        )
        expected_sector = (expected[0] & 1, expected[1] & 1)
        observed_sector = branch_chain_sector(lattice, color, chain)
        passed = (
            not np.any(boundary)
            and observed == (expected,)
            and observed_sector == expected_sector
            and analysis.logical_error
        )
        failures += int(not passed)
        fixtures.append(
            {
                "endpoints": list(endpoints),
                "branch_ids": [first.branch_id, second.branch_id],
                "displacements": [list(first.displacement), list(second.displacement)],
                "boundary_weight": int(np.sum(boundary)),
                "expected_relative_winding": list(expected),
                "observed_windings": [list(value) for value in observed],
                "expected_sector": list(expected_sector),
                "observed_sector": list(observed_sector),
                "passed": passed,
            }
        )
    return {"fixture_count": len(fixtures), "failure_count": failures, "fixtures": fixtures}


def _validate_quotient(lattice, color: int) -> dict:
    charge_lattice = build_branch_charge_lattice(lattice, color)
    check = np.zeros((charge_lattice.vertex_count, charge_lattice.edge_count), dtype=np.uint8)
    for edge, (left, right) in enumerate(charge_lattice.edge_vertices):
        check[int(left), edge] = 1
        check[int(right), edge] = 1
    closed = enumerate_affine_chains(
        check, np.zeros(charge_lattice.vertex_count, dtype=np.uint8)
    )
    closed_by_mask = {chain_mask(chain): chain for chain in closed}
    closed_sector = {
        mask: branch_chain_sector(lattice, color, chain)
        for mask, chain in closed_by_mask.items()
    }
    direct_loss = {
        mask: sector != (0, 0) for mask, sector in closed_sector.items()
    }
    legacy_component_classifier_loss_mismatches = sum(
        direct_loss[mask]
        != classify_closed_charge_chain(charge_lattice, chain).logical_error
        for mask, chain in closed_by_mask.items()
    )
    cycle_like_count = 0
    cycle_like_legacy_mismatches = 0
    for mask, chain in closed_by_mask.items():
        degree = np.zeros(charge_lattice.vertex_count, dtype=np.int64)
        for edge in np.flatnonzero(chain):
            left, right = charge_lattice.edge_vertices[edge]
            degree[int(left)] += 1
            degree[int(right)] += 1
        if np.all((degree == 0) | (degree == 2)):
            cycle_like_count += 1
            legacy = closed_charge_sector(charge_lattice, chain)
            cycle_like_legacy_mismatches += int(legacy != closed_sector[mask])
    zero_sector_histogram = defaultdict(int)
    for sector in closed_sector.values():
        zero_sector_histogram[sector] += 1

    quotient_failures = 0
    within_class_loss_failures = 0
    class_sizes = set()
    comparison_count = 0
    supported = 0
    for syndrome_mask in range(1 << charge_lattice.vertex_count):
        syndrome = np.asarray(
            [(syndrome_mask >> vertex) & 1 for vertex in range(charge_lattice.vertex_count)],
            dtype=np.uint8,
        )
        if int(np.sum(syndrome)) % 2:
            continue
        supported += 1
        actions = enumerate_affine_chains(check, syndrome)
        reference = min(actions, key=chain_mask)
        groups = defaultdict(list)
        for action in actions:
            groups[branch_chain_sector(lattice, color, action ^ reference)].append(action)
        if set(groups) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
            quotient_failures += 1
        class_sizes.update(len(group) for group in groups.values())
        for effective in actions:
            for group in groups.values():
                losses = {
                    direct_loss[chain_mask(effective ^ correction)]
                    for correction in group
                }
                comparison_count += len(group)
                if len(losses) != 1:
                    within_class_loss_failures += 1
    return {
        "vertex_count": charge_lattice.vertex_count,
        "edge_count": charge_lattice.edge_count,
        "closed_chain_count": len(closed),
        "zero_syndrome_sector_histogram": {
            str(sector): count for sector, count in sorted(zero_sector_histogram.items())
        },
        "supported_even_syndrome_count": supported,
        "affine_actions_per_syndrome": len(closed),
        "sector_count_expected": 4,
        "class_sizes": sorted(class_sizes),
        "quotient_failures": quotient_failures,
        "within_class_loss_failures": within_class_loss_failures,
        "cycle_like_closed_chain_count": cycle_like_count,
        "cycle_like_legacy_sector_mismatches": cycle_like_legacy_mismatches,
        "legacy_component_classifier_loss_mismatches": legacy_component_classifier_loss_mismatches,
        "effective_action_loss_comparisons": comparison_count,
        "public_decoder_intentionally_not_called": True,
    }


def run_audit(manifest: dict) -> dict:
    payload = run_preflight(manifest)
    if payload["status"] != "branch_provenance_preflight_passed":
        return payload
    from run_r4_distinct_observation_matrix import build_primitive_observation_catalog

    lattice = build_primitive_observation_catalog().lattice
    start = time.perf_counter()
    fixtures = {
        "blue": _parallel_fixtures(lattice, BLUE),
        "green": _parallel_fixtures(lattice, GREEN),
    }
    quotient = {
        "blue": _validate_quotient(lattice, BLUE),
        "green": _validate_quotient(lattice, GREEN),
    }
    seconds = time.perf_counter() - start
    fixture_pass = all(value["failure_count"] == 0 and value["fixture_count"] == 6 for value in fixtures.values())
    quotient_pass = all(
        value["closed_chain_count"] == 512
        and set(value["zero_syndrome_sector_histogram"].values()) == {128}
        and value["supported_even_syndrome_count"] == 8
        and value["class_sizes"] == [128]
        and value["quotient_failures"] == 0
        and value["within_class_loss_failures"] == 0
        and value["cycle_like_legacy_sector_mismatches"] == 0
        for value in quotient.values()
    )
    budget = manifest["compute_budget"]
    comparisons = sum(value["effective_action_loss_comparisons"] for value in quotient.values())
    resource_pass = comparisons <= int(budget["maximum_branch_or_action_checks"]) and payload["resource"]["wall_time_seconds"] + seconds <= 60.0 * float(budget["maximum_wall_time_minutes"])
    payload["parallel_branch_winding_fixtures"] = fixtures
    payload["charge_homology_quotient"] = quotient
    payload["resource"].update({"homology_audit_seconds": seconds, "total_preflight_seconds": payload["resource"]["wall_time_seconds"] + seconds, "branch_or_action_checks": comparisons, "branch_or_action_check_guard": int(budget["maximum_branch_or_action_checks"])})
    payload["validation"].update({
        "parallel_branch_winding_fixtures_pass": fixture_pass,
        "four_class_homology_quotient_pass": quotient_pass,
        "resource_pass": resource_pass,
        "homology_quotient_intentionally_not_run": False,
        "public_decoder_branch_fidelity_intentionally_not_run": True,
    })
    payload["status"] = "branch_homology_audit_passed" if fixture_pass and quotient_pass and resource_pass else "branch_homology_audit_failed"
    payload["claim_boundary"] = "Primitive branch representation, actual-path provenance, parallel-branch winding fixtures, and exact charge homology quotient only. Public decoder branch fidelity, sequential policy risk, LER, threshold, and scalability remain untested."
    payload["source_hashes"]["scripts/run_r4_branch_homology_audit.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload["structural_digest_sha256"] = hashlib.sha256(json.dumps({"branch_catalog": payload["branch_catalog"], "provenance": payload["provenance"], "parallel_branch_winding_fixtures": fixtures, "charge_homology_quotient": quotient, "validation": payload["validation"]}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    provenance = payload["provenance"]
    lines = [
        "# R4.5a branch-labelled charge topology audit",
        "",
        f"Status: **{payload['status']}**.",
        "",
        "## Representation and provenance",
        "",
        f"Both colours retain twelve physical branches over six endpoint pairs. All {provenance['visited_physical_action_pairs']:,} `(E,A)` pairs were classified; all {provenance['nonterminal_pairs_audited']:,} nonterminal pairs and {provenance['relation_occurrences']:,} relation occurrences have unique branch provenance, with {provenance['endpoint_projection_failures']} endpoint-projection failures.",
        "",
        "## Parallel-branch winding fixtures",
        "",
    ]
    for color in ("blue", "green"):
        result = payload["parallel_branch_winding_fixtures"][color]
        lines.append(f"- {color}: {result['fixture_count']} parallel pairs, {result['failure_count']} boundary/displacement/winding failures.")
    lines.extend(["", "## Exact charge-action quotient", ""])
    for color in ("blue", "green"):
        result = payload["charge_homology_quotient"][color]
        lines.append(f"- {color}: {result['closed_chain_count']} closed chains; four sectors of 128; {result['supported_even_syndrome_count']} even syndromes; {result['quotient_failures']} quotient and {result['within_class_loss_failures']} within-class loss failures. The period-cochain oracle agrees with the legacy lift on all {result['cycle_like_closed_chain_count']} cycle-like chains; the legacy component-level Boolean loss disagrees on {result['legacy_component_classifier_loss_mismatches']} branched/multicycle chains and is not used for the quotient.")
    lines.extend([
        "",
        "## Resource and claim boundary",
        "",
        f"The full provenance-plus-homology audit took {payload['resource']['total_preflight_seconds']:.3f} seconds and evaluated {payload['resource']['branch_or_action_checks']:,} registered action-loss comparisons, within the ten-minute and five-million-check guards.",
        "",
        "PyMatching was intentionally not called in the quotient audit. Therefore duplicate-branch fidelity of the public second-stage decoder and every sequential-policy risk remain open.",
        "",
        payload["claim_boundary"],
        "",
    ])
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
    if payload["status"] != "branch_homology_audit_passed":
        raise SystemExit("R4.5a branch homology audit failed")


if __name__ == "__main__":
    main()
