#!/usr/bin/env python3
"""Verify the registered R6C fixed cycle-activation factors."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import (
    PublicD4Observation,
    build_fixed_cycle_factor_catalog,
    fixed_cycle_factor_weight,
)
from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb, periodic_honeycomb
from d4_observation import evaluate_observation
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6c-fixed-cycle-factor-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6c-fixed-cycle-factor-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6c-fixed-cycle-factor-audit.md"
R6B_RESULT = LAB_DIR / "results/r6b-paper-scope-identifiability-audit.json"


def chain(edge_count: int, mask: int) -> np.ndarray:
    return np.asarray([(mask >> edge) & 1 for edge in range(edge_count)], dtype=bool)


def exact_weight(lattice, selected, observation) -> tuple[str, float]:
    analysis = generate_loop_constraints(lattice, selected)
    if any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    ):
        return "terminal_winding", 0.0
    result = evaluate_observation(
        lattice.edge_vertices,
        selected.astype(np.uint8),
        np.asarray(observation.flux_syndrome, dtype=np.uint8),
        np.asarray(observation.charge_outcomes, dtype=np.int64),
        analysis.constraints,
    )
    return ("allowed" if result.allowed else "forbidden"), float(result.probability)


def run() -> dict:
    primitive_catalog = build_primitive_observation_catalog()
    primitive = primitive_catalog.lattice
    primitive_factors = build_fixed_cycle_factor_catalog(primitive)
    primitive_mismatches = 0
    primitive_max_error = 0.0
    primitive_active_histogram: Counter[int] = Counter()
    for key in sorted(primitive_catalog.observations):
        observation = PublicD4Observation(*key)
        for candidate in primitive_catalog.observations[key]:
            selected = chain(primitive.edge_count, candidate.mask)
            expected = 2.0 ** candidate.log2_conditional_probability
            result = fixed_cycle_factor_weight(primitive, selected, observation, primitive_factors)
            error = abs(result.probability - expected)
            primitive_max_error = max(primitive_max_error, error)
            primitive_active_histogram[result.active_cycle_count] += 1
            if error > 1e-14:
                primitive_mismatches += 1

    paper = paper_periodic_honeycomb(2)
    paper_factors = build_fixed_cycle_factor_catalog(paper)
    r6b = json.loads(R6B_RESULT.read_text())
    paper_checks = 0
    paper_mismatches = 0
    paper_max_error = 0.0
    paper_status_histogram: Counter[str] = Counter()
    example_rows = []
    for ambiguity_index, row in enumerate(r6b["ambiguous_examples"]):
        flux = tuple(int(value) for value in row["flux"])
        measured = tuple(bool(value) for value in row["measured_support"])
        base_charge = tuple(0 if value else -1 for value in measured)
        for signature_index, signature in enumerate(row["signatures"]):
            for mask in signature["example_candidate_masks"]:
                selected = chain(paper.edge_count, int(mask))
                probes = [("even", base_charge)]
                analysis = generate_loop_constraints(paper, selected)
                if analysis.constraints:
                    violated = list(base_charge)
                    violated[analysis.constraints[0].vertices[0]] = 1
                    probes.append(("parity-violation", tuple(violated)))
                for probe, charge in probes:
                    observation = PublicD4Observation(flux, charge)
                    expected_status, expected = exact_weight(paper, selected, observation)
                    actual = fixed_cycle_factor_weight(paper, selected, observation, paper_factors)
                    error = abs(actual.probability - expected)
                    paper_checks += 1
                    paper_max_error = max(paper_max_error, error)
                    paper_status_histogram[actual.status] += 1
                    if actual.status != expected_status or error > 1e-14:
                        paper_mismatches += 1
                    if len(example_rows) < 12:
                        example_rows.append({
                            "ambiguity_index": ambiguity_index,
                            "signature_index": signature_index,
                            "candidate_mask": int(mask),
                            "probe": probe,
                            "expected_status": expected_status,
                            "actual_status": actual.status,
                            "expected_probability": expected,
                            "actual_probability": actual.probability,
                            "active_cycle_count": actual.active_cycle_count,
                        })

    def catalog_summary(catalog) -> dict:
        edge_arities = [len(item.cycle_edges) + len(item.boundary_edges) for item in catalog]
        charge_arities = [max(len(item.blue_vertices), len(item.green_vertices)) for item in catalog]
        cycle_lengths = Counter(len(item.cycle_edges) for item in catalog)
        return {
            "cycle_count": len(catalog),
            "cycle_length_histogram": {str(k): v for k, v in sorted(cycle_lengths.items())},
            "minimum_edge_scope_arity": min(edge_arities),
            "maximum_edge_scope_arity": max(edge_arities),
            "maximum_per_colour_charge_arity": max(charge_arities),
        }

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "fixed_cycle_factor_exact_on_registered_matrix" if not (primitive_mismatches or paper_mismatches) else "fixed_cycle_factor_mismatch",
        "primitive_complete": {
            "candidate_observation_pair_count": primitive_catalog.candidate_observation_pair_count,
            "mismatch_count": primitive_mismatches,
            "maximum_absolute_error": primitive_max_error,
            "active_cycle_count_histogram": {str(k): v for k, v in sorted(primitive_active_histogram.items())},
            "catalog": catalog_summary(primitive_factors),
        },
        "paper_ambiguity": {
            "ambiguous_public_record_count": len(r6b["ambiguous_examples"]),
            "candidate_probe_count": paper_checks,
            "mismatch_count": paper_mismatches,
            "maximum_absolute_error": paper_max_error,
            "status_histogram": dict(sorted(paper_status_histogram.items())),
            "catalog": catalog_summary(paper_factors),
            "examples": example_rows,
        },
        "representation": {
            "decoder_visible_public_inputs": ["flux_syndrome", "charge_outcomes"],
            "latent_variables_inside_factors": ["cycle edge bits", "cycle-boundary edge bits"],
            "geometry_fixed": True,
            "candidate_component_metadata_input": False,
            "scalability_status": "unresolved; full simple-cycle catalog has no polynomial bound established",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Exact fixed finite-graph likelihood representation on the registered primitive complete matrix and stored paper-L2 ambiguity probes only. The 1068-cycle paper catalog is not a scalable decoder result; BP, logical performance, convergence, threshold, and fault tolerance remain untested.",
    }
    if primitive_mismatches or paper_mismatches:
        raise AssertionError("R6C fixed cycle factor mismatch")
    return payload


def render(payload: dict) -> str:
    p0 = payload["primitive_complete"]
    p1 = payload["paper_ambiguity"]
    return "\n".join([
        "# R6C fixed cycle-activation factor audit",
        "",
        "## Exactness",
        "",
        f"The fixed cycle-factor graph matches all {p0['candidate_observation_pair_count']} primitive compatible pairs with {p0['mismatch_count']} mismatches. "
        f"It also matches all {p1['candidate_probe_count']} even/parity-violation probes drawn from the {p1['ambiguous_public_record_count']} R6B paper-L2 ambiguity records, again with {p1['mismatch_count']} mismatches.",
        "",
        "Each factor is fixed by lattice geometry. It activates from latent cycle and boundary edge bits and then evaluates the public charge parity; no candidate component label or simulator truth is supplied as decoder input.",
        "",
        "## Scaling boundary",
        "",
        f"The primitive catalog contains {p0['catalog']['cycle_count']} trivial cycles. The paper-normalized L=2 catalog already contains {p1['catalog']['cycle_count']} cycles, with edge scopes as large as {p1['catalog']['maximum_edge_scope_arity']} plus up to {p1['catalog']['maximum_per_colour_charge_arity']} charge bits per colour. Exactness therefore supplies a finite-graph control, not a scalable BP construction. A local connectivity-auxiliary compression is the next gate.",
        "",
        "## Claim boundary",
        "",
        payload["claim_boundary"],
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    json.loads(args.manifest.read_text())
    payload = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render(payload))
    print(json.dumps({"status": payload["status"], "primitive": payload["primitive_complete"], "paper": {k: v for k, v in payload["paper_ambiguity"].items() if k != "examples"}}, indent=2))


if __name__ == "__main__":
    main()
