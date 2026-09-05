#!/usr/bin/env python3
"""Bounded R6AC audit of the D4 A/B sublattice herald record.

This is deliberately an event-table audit, not a decoder benchmark.  It
enumerates a fixed non-winding hexagon and a two-edge open path on the
paper-normalized honeycomb.  For each physical error set it checks the
implemented sampler's support and likelihood against the stated local model:
at a degree-two blue (green) vertex the only non-vacuum outcome is e_blue
(e_green), and its local marginal probability is one half.  Closed components
add their colour-separated parity constraints.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import PublicD4Observation, f2_support_plus_parity_weight
from d4_honeycomb import BLUE, GREEN, generate_loop_constraints, paper_periodic_honeycomb
from d4_observation import evaluate_observation
from d4_sampler import observation_from_error_edges

OUTPUT = LAB_DIR / "results/r6ac-d4-sublattice-herald-model-audit-2026-08-31.json"
REPORT = LAB_DIR / "wiki/records/r6ac-d4-sublattice-herald-model-audit-2026-08-31.md"


def local_hexagon(lattice):
    # Search graphically rather than importing a primitive-fixture cycle.
    for start in range(lattice.vertex_count):
        stack = [(start, [start])]
        while stack:
            vertex, path = stack.pop()
            if len(path) == 6:
                closing = np.flatnonzero(
                    np.any(lattice.edge_vertices == vertex, axis=1)
                    & np.any(lattice.edge_vertices == start, axis=1)
                )
                if len(closing) == 1:
                    selected = np.zeros(lattice.edge_count, dtype=bool)
                    for left, right in zip(path, path[1:] + [start]):
                        selected[lattice.edge_between(left, right)] = True
                    analysis = generate_loop_constraints(lattice, selected)
                    if analysis.constraints and not any(
                        c.nonbranching_closed and not c.homologically_trivial
                        for c in analysis.components
                    ):
                        return selected
                continue
            for edge in np.flatnonzero(np.any(lattice.edge_vertices == vertex, axis=1)):
                left, right = (int(x) for x in lattice.edge_vertices[edge])
                neighbor = right if left == vertex else left
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor]))
    raise AssertionError("could not locate a trivial six-edge hexagon")


def open_two_edge_path(lattice):
    selected = np.zeros(lattice.edge_count, dtype=bool)
    selected[0] = True
    shared = int(lattice.edge_vertices[0, 1])
    second = next(int(e) for e in np.flatnonzero(np.any(lattice.edge_vertices == shared, axis=1)) if e != 0)
    selected[second] = True
    return selected


def enumerate_allowed(lattice, selected):
    degrees = np.bincount(lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count)
    internal = np.flatnonzero(degrees == 2)
    analysis = generate_loop_constraints(lattice, selected)
    allowed = []
    for mask in range(1 << len(internal)):
        # Signal-only public record: zero does not reveal internal support.
        charge = np.zeros(lattice.vertex_count, dtype=int)
        for index, vertex in enumerate(internal):
            charge[vertex] = (mask >> index) & 1
        evaluation = evaluate_observation(lattice.edge_vertices, selected, degrees % 2, charge, analysis.constraints)
        if evaluation.allowed:
            public = PublicD4Observation(tuple(int(x) for x in degrees % 2), tuple(int(x) for x in charge))
            f2 = f2_support_plus_parity_weight(lattice, selected, public)
            if f2.probability != evaluation.probability:
                raise AssertionError("factorized likelihood disagrees with direct likelihood")
            allowed.append((charge, evaluation.probability))
    if not allowed or not np.isclose(sum(weight for _, weight in allowed), 1.0):
        raise AssertionError("conditional herald outcome table is not normalized")
    return internal, analysis, allowed


def summarize_case(name, lattice, selected):
    internal, analysis, allowed = enumerate_allowed(lattice, selected)
    colors = np.asarray(lattice.vertex_colors)
    rows = []
    for vertex in internal:
        probability_one = sum(weight for charge, weight in allowed if charge[vertex] == 1)
        probability_zero = sum(weight for charge, weight in allowed if charge[vertex] == 0)
        rows.append({"vertex": int(vertex), "sublattice": "blue/A" if colors[vertex] == BLUE else "green/B",
                     "P_vacuum": probability_zero, "P_matching_colour_e": probability_one,
                     "P_wrong_colour_e": 0.0})
        if not (np.isclose(probability_zero, 0.5) and np.isclose(probability_one, 0.5)):
            raise AssertionError("implemented per-sublattice marginal is not q=1/2")
    observed = Counter()
    for seed in range(4096):
        record = observation_from_error_edges(lattice, selected, seed=seed)
        if record.status != "sampled" or record.charge_outcomes is None:
            raise AssertionError("fixed nonwinding record did not sample")
        observed[tuple(record.charge_outcomes)] += 1
    if set(observed) != {tuple(int(x) for x in charge) for charge, _ in allowed}:
        raise AssertionError("sampler support differs from exact event table")
    return {"case": name, "selected_edge_count": int(selected.sum()), "internal_vertex_count": len(internal),
            "allowed_outcome_count": len(allowed), "probability_sum": sum(weight for _, weight in allowed),
            "constraints": [{"vertices": list(c.vertices), "required_parity": c.required_parity, "label": c.label} for c in analysis.constraints],
            "per_vertex_event_table": rows, "sampled_support_count": len(observed),
            "sampled_histogram_min": min(observed.values()), "sampled_histogram_max": max(observed.values())}


def main():
    lattice = paper_periodic_honeycomb(2)
    cases = [summarize_case("open_two_edge_path", lattice, open_two_edge_path(lattice)),
             summarize_case("trivial_hexagon", lattice, local_hexagon(lattice))]
    payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
               "status": "implemented_q_half_sublattice_event_table_passed",
               "scope": {"lattice": "paper_periodic_honeycomb(L=2)", "decoder": "none; source-to-event likelihood audit only"},
               "intended_model_checked": {"internal_degree_two_vertex": "vacuum with probability 1/2; matching-colour Abelian e with probability 1/2",
                                           "wrong_colour_outcome": "zero probability at a given sublattice vertex",
                                           "closed_component_constraint": "separate parity relations for blue/A and green/B internal vertices"},
               "signal_only_event_table_gate_passed": True,
               "acceptance": {"all_event_tables_normalized": True, "all_per_vertex_marginals_q_half": True,
                              "factorized_weight_matches_direct_likelihood": True, "sampler_support_matches_event_table": True},
               "cases": cases,
               "claim_boundary": "This verifies the current abstract implementation realizes a q=1/2 coloured-vertex record. It does not by itself prove the abstract red-edge-to-source geometry or p_X convention matches Jing et al.; those remain required before reinterpreting the suspended BP curve."}
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT.write_text("\n".join(["# R6AC D4 A/B sublattice herald event-table audit", "", "## Result", "", "The signal-only implementation passes the bounded q=1/2 coloured-sublattice gate: every degree-two blue/A or green/B vertex has `P(vacuum)=P(e_matching-colour)=1/2`, never a wrong-colour e outcome. The direct Appendix-A likelihood, factorized likelihood, and sampler support agree exactly on both controls. The public record is binary: vacuum does not reveal hidden degree-two support.", "", "## Controls", "", *[f"- `{row['case']}`: {row['internal_vertex_count']} internal vertices, {row['allowed_outcome_count']} allowed outcomes, probability sum {row['probability_sum']:.1f}, sampled support {row['sampled_support_count']}." for row in cases], "", "## Interpretation boundary", "", "This clears only the claim that the current abstract record accidentally uses q=3/4 or gives both colours independently at one vertex. It does not yet establish source-faithful red-edge geometry, the paper's p_X convention, or a valid BP threshold. The prior BP curve remains withheld while those remaining compatibility gates are tested.", ""]) )
    print(json.dumps({"output": str(OUTPUT), "report": str(REPORT), "status": payload["status"]}))


if __name__ == "__main__":
    main()
