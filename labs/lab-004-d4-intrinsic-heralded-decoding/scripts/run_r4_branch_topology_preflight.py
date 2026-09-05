#!/usr/bin/env python3
"""Run the registered R4.5a branch-catalog and provenance preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge_multigraph import (
    build_charge_branch_catalog,
    infer_branch_postflux_relations,
    validate_endpoint_projection,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN
from d4_matching import classify_physical_correction_union, d4_check_matrix
from d4_sequential import chain_mask
from run_r4_distinct_observation_matrix import (
    _chain,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-branch-labelled-charge-topology-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-branch-labelled-charge-topology-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-branch-labelled-charge-topology-audit.md"


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        if _sha256(LAB_DIR / relative) != expected:
            raise ValueError(f"R4.5a source hash drift: {relative}")


def _catalog_summary(branches) -> dict:
    by_pair: dict[tuple[int, int], list] = defaultdict(list)
    for branch in branches:
        by_pair[branch.endpoints].append(branch)
    return {
        "branch_count": len(branches),
        "unique_branch_id_count": len({branch.branch_id for branch in branches}),
        "unique_endpoint_pair_count": len(by_pair),
        "endpoint_multiplicities": sorted({len(values) for values in by_pair.values()}),
        "parallel_pair_count": sum(len(values) > 1 for values in by_pair.values()),
        "parallel_equal_boundary_distinct_label_failures": sum(
            len({(branch.opposite_center, branch.displacement) for branch in values})
            != len(values)
            for values in by_pair.values()
            if len(values) > 1
        ),
        "branches": [
            {
                "branch_id": branch.branch_id,
                "endpoints": list(branch.endpoints),
                "opposite_center": branch.opposite_center,
                "displacement": list(branch.displacement),
                "honeycomb_edges": list(branch.honeycomb_edges),
            }
            for branch in branches
        ],
    }


def run_preflight(manifest: dict) -> dict:
    _validate_manifest(manifest)
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    branch_catalogs = {
        BLUE: build_charge_branch_catalog(lattice, BLUE),
        GREEN: build_charge_branch_catalog(lattice, GREEN),
    }
    summaries = {
        "blue": _catalog_summary(branch_catalogs[BLUE]),
        "green": _catalog_summary(branch_catalogs[GREEN]),
    }
    supports_by_flux = defaultdict(dict)
    for (flux, _), candidates in catalog.observations.items():
        for candidate in candidates:
            supports_by_flux[flux].setdefault(candidate.mask, candidate)
    check = d4_check_matrix(lattice)
    actions_by_flux = {
        flux: tuple(
            (chain_mask(action), action)
            for action in enumerate_affine_chains(
                check, np.asarray(flux, dtype=np.uint8)
            )
        )
        for flux in sorted(supports_by_flux)
    }

    start = time.perf_counter()
    visited = 0
    terminal = 0
    audited = 0
    projection_failures = 0
    zero_provenance = 0
    multiple_provenance = 0
    relation_occurrences = 0
    distinct_branch_relations = 0
    old_pair_multiplicities = Counter()
    maximum_relations = 0
    examples = []
    for flux in sorted(supports_by_flux):
        for physical_mask in sorted(supports_by_flux[flux]):
            physical = _chain(lattice.edge_count, physical_mask)
            for action_mask, action in actions_by_flux[flux]:
                visited += 1
                union = classify_physical_correction_union(lattice, physical, action)
                if any(not component.homologically_trivial for component in union.components):
                    terminal += 1
                    continue
                audited += 1
                try:
                    enriched = infer_branch_postflux_relations(
                        lattice, physical, action, branch_catalogs
                    )
                except ValueError:
                    zero_provenance += 1
                    if len(examples) < 16:
                        examples.append({"physical_mask": physical_mask, "action_mask": action_mask, "failure": "zero_or_multiple_branch_lookup"})
                    continue
                agrees, endpoint = validate_endpoint_projection(
                    lattice, physical, action, enriched
                )
                if not agrees:
                    projection_failures += 1
                    if len(examples) < 16:
                        examples.append({"physical_mask": physical_mask, "action_mask": action_mask, "failure": "endpoint_projection"})
                relation_occurrences += len(enriched.relations)
                distinct_branch_relations += len(
                    {(relation.color, relation.branch_id) for relation in enriched.relations}
                )
                maximum_relations = max(maximum_relations, len(enriched.relations))
                branches_by_pair = defaultdict(set)
                for relation in enriched.relations:
                    branches_by_pair[(relation.color, relation.endpoints)].add(
                        relation.branch_id
                    )
                for pair in endpoint.entanglement_pairs:
                    color = int(lattice.vertex_colors[pair[0]])
                    multiplicity = len(branches_by_pair[(color, pair)])
                    old_pair_multiplicities[multiplicity] += 1
                    if multiplicity == 0:
                        zero_provenance += 1
                    elif multiplicity > 1:
                        multiple_provenance += 1
                        if len(examples) < 16:
                            examples.append({"physical_mask": physical_mask, "action_mask": action_mask, "failure": "multiple_branches_for_projected_pair", "color": color, "endpoints": list(pair), "branch_ids": sorted(branches_by_pair[(color, pair)])})
    seconds = time.perf_counter() - start

    budget = manifest["compute_budget"]
    catalog_pass = all(
        summary["branch_count"] == 12
        and summary["unique_branch_id_count"] == 12
        and summary["unique_endpoint_pair_count"] == 6
        and summary["endpoint_multiplicities"] == [2]
        and summary["parallel_pair_count"] == 6
        and summary["parallel_equal_boundary_distinct_label_failures"] == 0
        for summary in summaries.values()
    )
    provenance_pass = (
        audited > 0
        and projection_failures == 0
        and zero_provenance == 0
        and multiple_provenance == 0
    )
    resource_pass = (
        visited <= int(budget["maximum_relation_provenance_pairs"])
        and seconds <= 60.0 * float(budget["maximum_wall_time_minutes"])
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "branch_provenance_preflight_passed" if catalog_pass and provenance_pass and resource_pass else "branch_provenance_preflight_failed",
        "lattice": {"size": lattice.size, "vertex_count": lattice.vertex_count, "edge_count": lattice.edge_count, "period_matrix": lattice.period_matrix.tolist()},
        "branch_catalog": summaries,
        "provenance": {
            "visited_physical_action_pairs": visited,
            "terminal_pairs_classified_without_second_stage": terminal,
            "nonterminal_pairs_audited": audited,
            "relation_occurrences": relation_occurrences,
            "distinct_branch_relation_occurrences": distinct_branch_relations,
            "maximum_branch_relations_per_pair": maximum_relations,
            "endpoint_projection_failures": projection_failures,
            "zero_branch_provenance_failures": zero_provenance,
            "multiple_branch_provenance_failures": multiple_provenance,
            "projected_pair_branch_multiplicity_histogram": {str(key): value for key, value in sorted(old_pair_multiplicities.items())},
            "failure_examples": examples,
        },
        "resource": {
            "wall_time_seconds": seconds,
            "pair_guard": int(budget["maximum_relation_provenance_pairs"]),
            "wall_guard_seconds": 60.0 * float(budget["maximum_wall_time_minutes"]),
        },
        "validation": {
            "branch_catalog_pass": catalog_pass,
            "relation_provenance_pass": provenance_pass,
            "resource_pass": resource_pass,
            "homology_quotient_intentionally_not_run": True,
            "public_decoder_branch_fidelity_intentionally_not_run": True,
        },
        "new_stochastic_samples": 0,
        "claim_boundary": "Branch catalog and relation-provenance preflight only. Passing this gate does not establish homology quotient validity, public decoder branch fidelity, sequential policy risk, LER, threshold, or scalability.",
        "source_hashes": {
            "scripts/d4_charge_multigraph.py": _sha256(LAB_DIR / "scripts/d4_charge_multigraph.py"),
            "scripts/run_r4_branch_topology_preflight.py": _sha256(LAB_DIR / "scripts/run_r4_branch_topology_preflight.py"),
        },
    }
    payload["structural_digest_sha256"] = hashlib.sha256(json.dumps({"branch_catalog": summaries, "provenance": payload["provenance"], "validation": payload["validation"]}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    provenance = payload["provenance"]
    lines = [
        "# R4.5a branch-labelled charge topology preflight",
        "",
        f"Status: **{payload['status']}**.",
        "",
        "## Branch catalog",
        "",
    ]
    for color in ("blue", "green"):
        summary = payload["branch_catalog"][color]
        lines.append(f"- {color}: {summary['branch_count']} physical branches, {summary['unique_endpoint_pair_count']} endpoint pairs, multiplicity {summary['endpoint_multiplicities']}, and {summary['parallel_equal_boundary_distinct_label_failures']} label-uniqueness failures.")
    lines.extend([
        "",
        "## Relation provenance",
        "",
        f"The preflight classified all {provenance['visited_physical_action_pairs']:,} primitive `(E,A)` pairs. {provenance['terminal_pairs_classified_without_second_stage']:,} are terminal and emit no second-stage relation; all {provenance['nonterminal_pairs_audited']:,} surviving pairs were audited.",
        "",
        f"Endpoint-forgetting failures: `{provenance['endpoint_projection_failures']}`. Zero/multiple branch-provenance failures: `{provenance['zero_branch_provenance_failures']}` / `{provenance['multiple_branch_provenance_failures']}`. Projected-pair multiplicities: `{provenance['projected_pair_branch_multiplicity_histogram']}`.",
        "",
        "## Gate",
        "",
        f"Catalog, provenance, and resource gates: `{payload['validation']['branch_catalog_pass']}`, `{payload['validation']['relation_provenance_pass']}`, `{payload['validation']['resource_pass']}`. Runtime was `{payload['resource']['wall_time_seconds']:.3f} s` against `{payload['resource']['wall_guard_seconds']:.0f} s`.",
        "",
        "The homology quotient and public-decoder duplicate-branch test were intentionally not run in this prerequisite-first tick.",
        "",
        "## Claim boundary",
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
    payload = run_preflight(json.loads(args.manifest.read_text()))
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps(payload, indent=2))
    if payload["status"] != "branch_provenance_preflight_passed":
        raise SystemExit("R4.5a branch provenance preflight failed")


if __name__ == "__main__":
    main()
