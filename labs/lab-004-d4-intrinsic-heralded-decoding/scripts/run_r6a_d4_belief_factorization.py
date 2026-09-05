#!/usr/bin/env python3
"""Run the registered R6A complete exact factorization matrix.

This runner deliberately separates two questions:

1. Does the candidate-dependent F2 diagnostic ledger reproduce the exact
   primitive-size-2 (8-vertex, 12-edge) likelihood?
2. Can those ledgers be serialized as one candidate-independent collection of
   charge-parity scopes for a public observation?

Passing (1) is not reported as passing (2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import (
    PublicD4Observation,
    f1_local_support_weight,
    f2_support_plus_parity_weight,
)
from d4_honeycomb import generate_loop_constraints
from run_r4_distinct_observation_matrix import (
    analyze_catalog,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6a-d4-belief-factorization-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6a-d4-belief-factorization-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6a-d4-belief-factorization-audit.md"
R4_RESULT = LAB_DIR / "results/r4-distinct-observation-matrix-audit.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _chain(edge_count: int, mask: int) -> np.ndarray:
    return np.asarray([(mask >> edge) & 1 for edge in range(edge_count)], dtype=bool)


def _local_signature(lattice, selected: np.ndarray) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    return tuple(int(value) for value in degrees % 2), tuple(bool(value) for value in degrees == 2)


def _observation_signature(key) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    flux, charge = key
    return flux, tuple(value != -1 for value in charge)


def _scope_signature(ledger) -> tuple[tuple[tuple[int, ...], int], ...]:
    return tuple(
        sorted(
            (tuple(int(vertex) for vertex in factor.vertices), int(factor.required_parity))
            for factor in ledger.parity_factors
        )
    )


def run_matrix(manifest: dict) -> dict:
    catalog = build_primitive_observation_catalog(candidate_observation_pair_guard=1_000_000)
    lattice = catalog.lattice
    if lattice.vertex_count != 8 or lattice.edge_count != 12:
        raise AssertionError("R6A exhaustive control must remain the primitive 8-vertex/12-edge fixture")
    priors = (0.1, 0.3, 0.5, 0.6)
    frozen_r4 = json.loads(R4_RESULT.read_text())
    replay = analyze_catalog(catalog, priors)

    masks_by_signature: dict[tuple[tuple[int, ...], tuple[bool, ...]], list[int]] = defaultdict(list)
    terminal_count = 0
    for mask in range(1 << lattice.edge_count):
        selected = _chain(lattice.edge_count, mask)
        analysis = generate_loop_constraints(lattice, selected)
        if any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        ):
            terminal_count += 1
            continue
        masks_by_signature[_local_signature(lattice, selected)].append(mask)

    f1_mismatches = 0
    f2_mismatches = 0
    f1_maximum_error = 0.0
    f2_maximum_error = 0.0
    f1_weight_mismatch_histogram: Counter[str] = Counter()
    f2_status_histogram: Counter[str] = Counter()
    local_pair_count = 0
    exact_pair_count = 0
    observations_with_multiple_scope_signatures = 0
    observations_with_candidate_dependent_exact_weight = 0
    observations_with_any_parity_scope = 0
    maximum_scope_signatures_per_observation = 0
    example_scope_conflicts: list[dict] = []
    matrix_digest = hashlib.sha256()

    for observation_index, key in enumerate(sorted(catalog.observations)):
        flux, charge = key
        observation = PublicD4Observation(flux, charge)
        exact = {
            candidate.mask: 2.0 ** candidate.log2_conditional_probability
            for candidate in catalog.observations[key]
        }
        exact_pair_count += len(exact)
        local_masks = masks_by_signature[_observation_signature(key)]
        local_pair_count += len(local_masks)
        scope_signatures: dict[tuple[tuple[tuple[int, ...], int], ...], list[int]] = defaultdict(list)
        exact_weights: set[float] = set()
        row = []
        for mask in local_masks:
            selected = _chain(lattice.edge_count, mask)
            expected = exact.get(mask, 0.0)
            f1 = f1_local_support_weight(lattice, selected, observation)
            f2 = f2_support_plus_parity_weight(lattice, selected, observation)
            f1_error = abs(f1.probability - expected)
            f2_error = abs(f2.probability - expected)
            f1_maximum_error = max(f1_maximum_error, f1_error)
            f2_maximum_error = max(f2_maximum_error, f2_error)
            if f1_error > 1e-14:
                f1_mismatches += 1
                ratio = "false-positive-support" if expected == 0.0 else f"ratio-{f1.probability / expected:g}"
                f1_weight_mismatch_histogram[ratio] += 1
            if f2_error > 1e-14:
                f2_mismatches += 1
            f2_status_histogram[f2.status] += 1
            if expected > 0.0:
                signature = _scope_signature(f2)
                scope_signatures[signature].append(mask)
                exact_weights.add(expected)
            row.append((mask, expected, f1.probability, f2.probability, _scope_signature(f2)))

        signature_count = len(scope_signatures)
        maximum_scope_signatures_per_observation = max(
            maximum_scope_signatures_per_observation, signature_count
        )
        if any(signature for signature in scope_signatures):
            observations_with_any_parity_scope += 1
        if signature_count > 1:
            observations_with_multiple_scope_signatures += 1
            if len(example_scope_conflicts) < 5:
                example_scope_conflicts.append(
                    {
                        "observation_index": observation_index,
                        "flux": list(flux),
                        "charge": list(charge),
                        "scope_signatures": [
                            {
                                "signature": [
                                    {"vertices": list(vertices), "required_parity": parity}
                                    for vertices, parity in signature
                                ],
                                "candidate_masks": masks[:8],
                                "candidate_count": len(masks),
                            }
                            for signature, masks in sorted(scope_signatures.items())
                        ],
                    }
                )
        if len(exact_weights) > 1:
            observations_with_candidate_dependent_exact_weight += 1
        matrix_digest.update(json.dumps(row, sort_keys=True, separators=(",", ":")).encode())

    f0_pass = (
        replay["observation_matrix_digest_sha256"]
        == frozen_r4["observation_matrix_digest_sha256"]
        and replay["enumeration"] == frozen_r4["enumeration"]
    )
    f1_support_exact = local_pair_count == exact_pair_count and f1_weight_mismatch_histogram.get("false-positive-support", 0) == 0
    f2_exact = f2_mismatches == 0 and local_pair_count == exact_pair_count
    fixed_direct_charge_scope_pass = observations_with_multiple_scope_signatures == 0

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_f0_f2_exact_enumeration_matrix_verified",
        "manifest": {"path": str(DEFAULT_MANIFEST.resolve()), "sha256": _sha256(DEFAULT_MANIFEST)},
        "frozen_r4": {"path": str(R4_RESULT.resolve()), "sha256": _sha256(R4_RESULT)},
        "enumeration": {
            "topology": "primitive periodic honeycomb size=2",
            "paper_normalized": False,
            "vertex_count": lattice.vertex_count,
            "edge_count": lattice.edge_count,
            "physical_mask_count": 1 << lattice.edge_count,
            "nonwinding_mask_count": catalog.nonwinding_mask_count,
            "terminal_winding_mask_count": terminal_count,
            "distinct_supported_public_observation_count": len(catalog.observations),
            "exact_candidate_observation_pair_count": exact_pair_count,
            "local_support_candidate_observation_pair_count": local_pair_count,
            "dense_global_table_cell_count": len(catalog.observations) * (1 << lattice.edge_count),
        },
        "branches": {
            "F0-exact-oracle": {
                "status": "pass" if f0_pass else "fail",
                "replayed_digest": replay["observation_matrix_digest_sha256"],
                "frozen_digest": frozen_r4["observation_matrix_digest_sha256"],
            },
            "F1-local-support": {
                "status": "support-exact-weight-inexact" if f1_support_exact and f1_mismatches else ("exact" if f1_mismatches == 0 else "fail"),
                "support_exact_on_supported_public_catalog": f1_support_exact,
                "weight_mismatch_count": f1_mismatches,
                "maximum_absolute_likelihood_error": f1_maximum_error,
                "weight_mismatch_histogram": dict(sorted(f1_weight_mismatch_histogram.items())),
            },
            "F2-candidate-dependent-ledger": {
                "status": "exact-diagnostic-only" if f2_exact else "fail",
                "candidate_likelihood_mismatch_count": f2_mismatches,
                "maximum_absolute_likelihood_error": f2_maximum_error,
                "status_histogram": dict(sorted(f2_status_histogram.items())),
                "decoder_visible": False,
            },
            "F2-fixed-direct-charge-scopes": {
                "status": "pass" if fixed_direct_charge_scope_pass else "rejected",
                "observations_with_any_parity_scope": observations_with_any_parity_scope,
                "observations_with_multiple_candidate_scope_signatures": observations_with_multiple_scope_signatures,
                "maximum_scope_signatures_per_observation": maximum_scope_signatures_per_observation,
                "observations_with_candidate_dependent_exact_weight": observations_with_candidate_dependent_exact_weight,
                "examples": example_scope_conflicts,
                "claim": "This tests one fixed list of direct observed-charge parity scopes. It does not reject richer fixed graphs with latent connectivity auxiliaries.",
            },
            "F2-global-public-table-control": {
                "status": "exact-but-global-exponential",
                "nonzero_table_entries": exact_pair_count,
                "dense_table_cells": len(catalog.observations) * (1 << lattice.edge_count),
                "claim": "A public-observation keyed factor over all twelve primitive-fixture edge bits is exact by construction and is not a scalable local factorization.",
            },
        },
        "matrix_digest_sha256": matrix_digest.hexdigest(),
        "new_stochastic_samples": 0,
        "claim_boundary": "Complete deterministic primitive-size-2 (8-vertex, 12-edge) likelihood matrix only; this is not the 24-vertex, 36-edge paper-normalized L=2 supercell. Exact candidate ledgers are not a decoder-visible scalable BP graph.",
    }
    if not f0_pass:
        raise AssertionError("F0 replay digest or enumeration drift")
    if not f2_exact:
        raise AssertionError("candidate-dependent F2 ledger does not match the exact oracle")
    return payload


def _render_report(payload: dict) -> str:
    enumeration = payload["enumeration"]
    branches = payload["branches"]
    f1 = branches["F1-local-support"]
    f2 = branches["F2-candidate-dependent-ledger"]
    fixed = branches["F2-fixed-direct-charge-scopes"]
    return "\n".join(
        [
            "# R6A complete D4 likelihood factorization matrix",
            "",
            "## Exact matrix",
            "",
            f"F0 replays the frozen R4.2 digest over {enumeration['physical_mask_count']} masks, "
            f"{enumeration['distinct_supported_public_observation_count']} supported public observations, and "
            f"{enumeration['exact_candidate_observation_pair_count']} compatible pairs.",
            "",
            f"F1 has exact support on that catalog but {f1['weight_mismatch_count']} likelihood-weight mismatches "
            f"(maximum absolute error {f1['maximum_absolute_likelihood_error']:.6g}).",
            "",
            f"The candidate-dependent F2 ledger has {f2['candidate_likelihood_mismatch_count']} mismatches and is exact as an internal evaluator. "
            "It is not decoder-visible.",
            "",
            "## Fixed-public representation test",
            "",
            f"A single candidate-independent list of direct charge-parity scopes is consistent on the complete primitive-size-2 support: "
            f"{fixed['observations_with_multiple_candidate_scope_signatures']} observations require multiple candidate-derived scope signatures "
            f"(maximum {fixed['maximum_scope_signatures_per_observation']}).",
            "",
            "This is a finite-support existence/consistency result on the 8-vertex, 12-edge primitive fixture, not the paper-normalized L=2 supercell and not a constructive scalable algorithm. "
            "The global public-observation keyed 12-edge table is exact by construction but exponential and therefore only a control.",
            "",
            "## Claim boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    payload = run_matrix(manifest)
    payload["manifest"] = {"path": str(args.manifest.resolve()), "sha256": _sha256(args.manifest)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.report.write_text(_render_report(payload))
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output),
        "f1_weight_mismatches": payload["branches"]["F1-local-support"]["weight_mismatch_count"],
        "f2_mismatches": payload["branches"]["F2-candidate-dependent-ledger"]["candidate_likelihood_mismatch_count"],
        "fixed_scope_status": payload["branches"]["F2-fixed-direct-charge-scopes"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
