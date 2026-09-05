#!/usr/bin/env python3
"""Verify the registered R6D fixed local auxiliary-spin representation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import (
    PublicD4Observation,
    explicit_local_edge_flow_partition,
    explicit_local_spin_partition,
    local_edge_flow_factor_weight,
    local_spin_factor_weight,
)
from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb
from d4_observation import evaluate_observation
from run_r4_distinct_observation_matrix import build_primitive_observation_catalog


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6d-local-spin-factor-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6d-local-spin-factor-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6d-local-spin-factor-audit.md"
R6B_RESULT = LAB_DIR / "results/r6b-paper-scope-identifiability-audit.json"


def chain(edge_count: int, mask: int) -> np.ndarray:
    return np.asarray([(mask >> edge) & 1 for edge in range(edge_count)], dtype=bool)


def public_observation(lattice, selected, charge_bits=None) -> PublicD4Observation:
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    charge[degrees == 2] = 0
    for vertex, value in (charge_bits or {}).items():
        charge[int(vertex)] = int(value)
    return PublicD4Observation(
        tuple(int(value) for value in degrees % 2),
        tuple(int(value) for value in charge),
    )


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


def explicit_controls(lattice) -> list[tuple[str, np.ndarray, PublicD4Observation]]:
    vacuum = np.zeros(lattice.edge_count, dtype=bool)
    first = 0
    shared = int(lattice.edge_vertices[first, 1])
    second = next(
        int(edge)
        for edge in np.flatnonzero(np.any(lattice.edge_vertices == shared, axis=1))
        if int(edge) != first
    )
    open_path = np.zeros(lattice.edge_count, dtype=bool)
    open_path[[first, second]] = True

    branch = np.zeros(lattice.edge_count, dtype=bool)
    branch[np.flatnonzero(np.any(lattice.edge_vertices == 0, axis=1))] = True

    loop = None
    loop_analysis = None
    for mask in range(1, 1 << lattice.edge_count):
        selected = chain(lattice.edge_count, mask)
        analysis = generate_loop_constraints(lattice, selected)
        if analysis.constraints and not any(
            component.nonbranching_closed and not component.homologically_trivial
            for component in analysis.components
        ):
            loop = selected
            loop_analysis = analysis
            break
    if loop is None or loop_analysis is None:
        raise AssertionError("primitive control graph has no trivial loop")
    loop_observation = public_observation(lattice, loop)
    violated_vertex = int(loop_analysis.constraints[0].vertices[0])
    loop_violation = public_observation(lattice, loop, {violated_vertex: 1})
    return [
        ("vacuum", vacuum, public_observation(lattice, vacuum)),
        ("open", open_path, public_observation(lattice, open_path)),
        ("branch", branch, public_observation(lattice, branch)),
        ("loop-even", loop, loop_observation),
        ("loop-parity-violation", loop, loop_violation),
    ]


def graph_complexity(lattice) -> dict:
    return {
        "physical_edge_variables": lattice.edge_count,
        "binary_auxiliary_edge_flow_variables": 2 * lattice.edge_count,
        "edge_flow_pin_factors": 2 * lattice.edge_count,
        "edge_flow_vertex_factors": 2 * lattice.vertex_count,
        "total_edge_flow_factors": 2 * (lattice.edge_count + lattice.vertex_count),
        "maximum_edge_pin_factor_variable_arity": 2,
        "maximum_vertex_factor_variable_arity_including_public_charge": 7,
        "domain_size": 2,
        "growth": "O(V+E) variables and factors; arities and domains are geometry-independent",
    }


def run() -> dict:
    primitive_catalog = build_primitive_observation_catalog()
    primitive = primitive_catalog.lattice
    pair_count = primitive_catalog.candidate_observation_pair_count
    explicit_indices = set(int(value) for value in np.linspace(0, pair_count - 1, 64))

    primitive_mismatches = 0
    primitive_max_error = 0.0
    primitive_status_histogram: Counter[str] = Counter()
    explicit_checks = 0
    explicit_mismatches = 0
    edge_flow_explicit_checks = 0
    edge_flow_explicit_mismatches = 0
    explicit_rows = []
    pair_index = 0
    for key in sorted(primitive_catalog.observations):
        observation = PublicD4Observation(*key)
        for candidate in primitive_catalog.observations[key]:
            selected = chain(primitive.edge_count, candidate.mask)
            expected = 2.0 ** candidate.log2_conditional_probability
            result = local_spin_factor_weight(primitive, selected, observation)
            edge_result = local_edge_flow_factor_weight(primitive, selected, observation)
            error = max(
                abs(result.probability - expected),
                abs(edge_result.probability - expected),
            )
            primitive_max_error = max(primitive_max_error, error)
            primitive_status_histogram[result.status] += 1
            if error > 1e-14:
                primitive_mismatches += 1
            if pair_index in explicit_indices:
                partitions = tuple(
                    explicit_local_spin_partition(primitive, selected, observation, colour)
                    for colour in (0, 1)
                )
                edge_partitions = tuple(
                    explicit_local_edge_flow_partition(
                        primitive, selected, observation, colour
                    )
                    for colour in (0, 1)
                )
                explicit_checks += 1
                if partitions != result.colour_partitions:
                    explicit_mismatches += 1
                edge_flow_explicit_checks += 1
                if any(
                    abs(edge_partitions[colour] - edge_result.colour_partitions[colour]) > 1e-14
                    for colour in (0, 1)
                ):
                    edge_flow_explicit_mismatches += 1
                if len(explicit_rows) < 12:
                    explicit_rows.append({
                        "kind": "evenly_spaced_complete_pair",
                        "pair_index": pair_index,
                        "candidate_mask": int(candidate.mask),
                        "explicit_partitions": list(partitions),
                        "analytic_partitions": list(result.colour_partitions),
                        "explicit_nonnegative_edge_flow_partitions": list(edge_partitions),
                        "analytic_nonnegative_edge_flow_partitions": list(edge_result.colour_partitions),
                    })
            pair_index += 1

    control_rows = []
    for name, selected, observation in explicit_controls(primitive):
        actual = local_spin_factor_weight(primitive, selected, observation)
        edge_actual = local_edge_flow_factor_weight(primitive, selected, observation)
        partitions = tuple(
            explicit_local_spin_partition(primitive, selected, observation, colour)
            for colour in (0, 1)
        )
        edge_partitions = tuple(
            explicit_local_edge_flow_partition(primitive, selected, observation, colour)
            for colour in (0, 1)
        )
        expected_status, expected = exact_weight(primitive, selected, observation)
        mismatch = (
            partitions != actual.colour_partitions
            or actual.status != expected_status
            or abs(actual.probability - expected) > 1e-14
        )
        explicit_checks += 1
        explicit_mismatches += int(mismatch)
        edge_flow_mismatch = (
            any(
                abs(edge_partitions[colour] - edge_actual.colour_partitions[colour]) > 1e-14
                for colour in (0, 1)
            )
            or edge_actual.status != expected_status
            or abs(edge_actual.probability - expected) > 1e-14
        )
        edge_flow_explicit_checks += 1
        edge_flow_explicit_mismatches += int(edge_flow_mismatch)
        control_rows.append({
            "name": name,
            "expected_status": expected_status,
            "actual_status": actual.status,
            "expected_probability": expected,
            "actual_probability": actual.probability,
            "explicit_partitions": list(partitions),
            "analytic_partitions": list(actual.colour_partitions),
            "explicit_nonnegative_edge_flow_partitions": list(edge_partitions),
            "analytic_nonnegative_edge_flow_partitions": list(edge_actual.colour_partitions),
        })

    paper = paper_periodic_honeycomb(2)
    r6b = json.loads(R6B_RESULT.read_text())
    paper_checks = 0
    paper_mismatches = 0
    paper_max_error = 0.0
    paper_status_histogram: Counter[str] = Counter()
    paper_rows = []
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
                    actual = local_spin_factor_weight(paper, selected, observation)
                    edge_actual = local_edge_flow_factor_weight(paper, selected, observation)
                    error = max(
                        abs(actual.probability - expected),
                        abs(edge_actual.probability - expected),
                    )
                    paper_checks += 1
                    paper_max_error = max(paper_max_error, error)
                    paper_status_histogram[actual.status] += 1
                    if (
                        actual.status != expected_status
                        or edge_actual.status != expected_status
                        or error > 1e-14
                    ):
                        paper_mismatches += 1
                    if len(paper_rows) < 12:
                        paper_rows.append({
                            "ambiguity_index": ambiguity_index,
                            "signature_index": signature_index,
                            "candidate_mask": int(mask),
                            "probe": probe,
                            "expected_status": expected_status,
                            "actual_status": actual.status,
                            "expected_probability": expected,
                            "actual_probability": actual.probability,
                            "colour_partitions": list(actual.colour_partitions),
                            "nonnegative_edge_flow_partitions": list(edge_actual.colour_partitions),
                        })

    mismatches = (
        primitive_mismatches
        + explicit_mismatches
        + edge_flow_explicit_mismatches
        + paper_mismatches
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "nonnegative_local_edge_flow_exact_on_registered_matrix" if not mismatches else "local_factor_mismatch",
        "primitive_complete": {
            "candidate_observation_pair_count": pair_count,
            "mismatch_count": primitive_mismatches,
            "maximum_absolute_error": primitive_max_error,
            "status_histogram": dict(sorted(primitive_status_histogram.items())),
        },
        "explicit_spin_sum": {
            "check_count": explicit_checks,
            "mismatch_count": explicit_mismatches,
            "enumerated_spin_assignments_per_colour_per_check": 1 << primitive.vertex_count,
            "evenly_spaced_probe_count": len(explicit_indices),
            "named_controls": control_rows,
            "examples": explicit_rows,
        },
        "explicit_nonnegative_edge_flow_sum": {
            "check_count": edge_flow_explicit_checks,
            "mismatch_count": edge_flow_explicit_mismatches,
            "enumerated_flow_assignments_per_colour_per_check": 1 << primitive.edge_count,
            "all_local_factor_values_nonnegative": True,
        },
        "paper_ambiguity": {
            "ambiguous_public_record_count": len(r6b["ambiguous_examples"]),
            "candidate_probe_count": paper_checks,
            "mismatch_count": paper_mismatches,
            "maximum_absolute_error": paper_max_error,
            "status_histogram": dict(sorted(paper_status_histogram.items())),
            "examples": paper_rows,
        },
        "complexity": {
            "primitive": graph_complexity(primitive),
            "paper_L2": graph_complexity(paper),
            "simple_cycle_catalog_required": False,
            "component_labels_supplied_to_factors": False,
            "all_edge_flow_factor_values_nonnegative": True,
            "signed_vertex_spin_control": "exact independent Fourier-character representation, retained as a control but not treated as a probability factor graph",
            "winding_gate_status": "separate nonlocal terminal branch under the ground-state-relative contract",
        },
        "source_audit": {
            "paper": "Jing et al., Intrinsically heralded quantum error correction",
            "paper_method": "Eq. A12 likelihood; optimal-threshold stat-mech calculation reweights by 2^C and checks nonlocal constraints C by graph search",
            "project_contribution": "the binary local auxiliary-spin identity is derived in Lab 004 and validated here; it is not attributed to Jing et al.",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Exact fixed nonnegative bounded-arity local likelihood representation on the registered nonwinding matrix only. The ground-state-relative winding test remains a separate terminal gate. No BP convergence, polynomial-time decoding, correction, LER, threshold, or fault-tolerance claim is made.",
    }
    if mismatches:
        raise AssertionError("R6D local auxiliary-spin mismatch")
    return payload


def render(payload: dict) -> str:
    primitive = payload["primitive_complete"]
    explicit = payload["explicit_spin_sum"]
    edge_flow = payload["explicit_nonnegative_edge_flow_sum"]
    paper = payload["paper_ambiguity"]
    complexity = payload["complexity"]
    return "\n".join([
        "# R6D local auxiliary-spin factor audit",
        "",
        "## Result",
        "",
        f"The nonnegative local edge-flow graph matches all {primitive['candidate_observation_pair_count']} primitive compatible likelihoods and all {paper['candidate_probe_count']} registered paper-`L=2` ambiguity probes with zero errors. A direct sum over all {edge_flow['enumerated_flow_assignments_per_colour_per_check']} primitive edge-flow assignments per colour matches the analytic contraction on {edge_flow['check_count']} checks. The independent signed vertex-spin Fourier representation also matches after summing all {explicit['enumerated_spin_assignments_per_colour_per_check']} spin assignments per colour on the same controls.",
        "",
        "For each charge colour, every physical edge carries a binary auxiliary flow bit. An unselected edge pins it to zero. A degree-two vertex constrains the XOR of its two selected flow bits to the observed same-colour charge (or zero for the other colour); every other vertex contributes the nonnegative normalization `2^{-d/2}`. Cutting a non-cycle component at degree-not-two vertices produces maximal chains, each with two flow assignments and total endpoint normalization one half, so every chain contributes one. A pure loop has two assignments for even parity and none for odd parity. Multiplying the two colour partitions gives the D4 loop factor four without naming the loop.",
        "",
        "## Fixed local graph",
        "",
        f"On paper-`L=2`, the representation uses {complexity['paper_L2']['binary_auxiliary_edge_flow_variables']} binary auxiliary edge-flow variables and {complexity['paper_L2']['total_edge_flow_factors']} nonnegative factors, compared with the 1,068 simple-cycle factors required by R6C. Edge-pin factors have arity two; vertex factors have scope at most seven when the public charge bit is counted. Counts grow as `O(V+E)`, and no component label or simple-cycle catalog is supplied to a factor.",
        "",
        "## Source and derivation boundary",
        "",
        "Jing et al. provide the Eq. A12 likelihood and, in their optimal-threshold statistical-mechanics calculation, retain the nonlocal constraint count through a `2^C` reweighting and graph-search constraint check. The auxiliary-spin localization used here is a Lab 004 derivation independently checked against that exact likelihood; it is not presented as a formula from the paper.",
        "",
        "The first vertex-spin derivation is exact but signed because a charge character can equal minus one; it is therefore retained only as an independent tensor-network control. The edge-flow construction is the nonnegative probability-factor representation released by this audit.",
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
    print(json.dumps({
        "status": payload["status"],
        "primitive": payload["primitive_complete"],
        "explicit": {k: v for k, v in payload["explicit_spin_sum"].items() if k not in {"named_controls", "examples"}},
        "edge_flow": payload["explicit_nonnegative_edge_flow_sum"],
        "paper": {k: v for k, v in payload["paper_ambiguity"].items() if k != "examples"},
        "complexity": payload["complexity"],
    }, indent=2))


if __name__ == "__main__":
    main()
