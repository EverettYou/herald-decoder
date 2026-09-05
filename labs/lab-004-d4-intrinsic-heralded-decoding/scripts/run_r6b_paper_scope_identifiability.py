#!/usr/bin/env python3
"""Exact bounded R6B test of public parity-scope identifiability."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb
from d4_r3 import geometry_trivial_loop_catalog


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6b-paper-scope-identifiability-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6b-paper-scope-identifiability-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6b-paper-scope-identifiability-audit.md"


def public_degree_record(lattice, selected: np.ndarray) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    degrees = np.bincount(
        lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
    )
    return tuple(int(value) for value in degrees % 2), tuple(bool(value) for value in degrees == 2)


def scope_signature(analysis) -> tuple[tuple[tuple[int, ...], int], ...]:
    return tuple(
        sorted((tuple(int(vertex) for vertex in item.vertices), int(item.required_parity)) for item in analysis.constraints)
    )


def has_terminal_winding(analysis) -> bool:
    return any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    )


def enumerate_public_record(lattice, record, *, cap: int) -> dict:
    flux, measured = record
    allowed = [
        ({2} if measured[vertex] else ({0} if flux[vertex] == 0 else {1, 3}))
        for vertex in range(lattice.vertex_count)
    ]
    selected_count = [0] * lattice.vertex_count
    remaining = [3] * lattice.vertex_count
    selected = np.zeros(lattice.edge_count, dtype=bool)
    signatures: dict[tuple, list[int]] = defaultdict(list)
    compatible_count = 0
    terminal_count = 0
    capped = False

    def feasible(vertex: int) -> bool:
        return any(
            selected_count[vertex] <= degree <= selected_count[vertex] + remaining[vertex]
            for degree in allowed[vertex]
        )

    def visit(edge: int) -> None:
        nonlocal compatible_count, terminal_count, capped
        if compatible_count >= cap:
            capped = True
            return
        if edge == lattice.edge_count:
            if not all(selected_count[v] in allowed[v] for v in range(lattice.vertex_count)):
                return
            compatible_count += 1
            analysis = generate_loop_constraints(lattice, selected)
            mask = sum(int(bit) << index for index, bit in enumerate(selected))
            if has_terminal_winding(analysis):
                terminal_count += 1
                return
            signature = scope_signature(analysis)
            if len(signatures[signature]) < 8:
                signatures[signature].append(mask)
            return

        left, right = (int(value) for value in lattice.edge_vertices[edge])
        remaining[left] -= 1
        remaining[right] -= 1
        if feasible(left) and feasible(right):
            visit(edge + 1)
        if compatible_count < cap:
            selected_count[left] += 1
            selected_count[right] += 1
            selected[edge] = True
            if feasible(left) and feasible(right):
                visit(edge + 1)
            selected[edge] = False
            selected_count[left] -= 1
            selected_count[right] -= 1
        remaining[left] += 1
        remaining[right] += 1

    visit(0)
    return {
        "compatible_assignment_count": compatible_count,
        "terminal_winding_assignment_count": terminal_count,
        "nonwinding_scope_signature_count": len(signatures),
        "capped": capped,
        "signatures": [
            {
                "parity_scopes": [
                    {"vertices": list(vertices), "required_parity": parity}
                    for vertices, parity in signature
                ],
                "example_candidate_masks": masks,
            }
            for signature, masks in sorted(signatures.items())
        ],
    }


def run(manifest: dict) -> dict:
    lattice = paper_periodic_honeycomb(2)
    model = manifest["model"]
    if (lattice.vertex_count, lattice.edge_count) != (model["vertex_count"], model["edge_count"]):
        raise AssertionError("paper-normalized topology drift")
    matrix = manifest["matrix"]
    cap = int(matrix["compatible_assignment_cap_per_record"])

    controls = geometry_trivial_loop_catalog(
        lattice, maximum_cycle_length=6, cycle_limit=10_000
    )
    control_rows = []
    for chain, constraints, _ in controls:
        result = enumerate_public_record(lattice, public_degree_record(lattice, chain.astype(bool)), cap=cap)
        expected = tuple(sorted((tuple(item.vertices), int(item.required_parity)) for item in constraints))
        observed = {
            tuple((tuple(scope["vertices"]), int(scope["required_parity"])) for scope in row["parity_scopes"])
            for row in result["signatures"]
        }
        control_rows.append({
            "candidate_mask": sum(int(bit) << index for index, bit in enumerate(chain)),
            "compatible_assignment_count": result["compatible_assignment_count"],
            "signature_count": result["nonwinding_scope_signature_count"],
            "capped": result["capped"],
            "expected_signature_present": expected in observed,
        })

    rng = np.random.default_rng(int(matrix["fresh_seed"]))
    rows = []
    for error_rate in (float(value) for value in matrix["bernoulli_p"]):
        records = set()
        attempts = 0
        target = int(matrix["distinct_nonwinding_public_records_per_p"])
        while len(records) < target and attempts < int(matrix["maximum_generation_attempts_per_p"]):
            attempts += 1
            selected = rng.random(lattice.edge_count) < error_rate
            analysis = generate_loop_constraints(lattice, selected)
            if has_terminal_winding(analysis):
                continue
            records.add(public_degree_record(lattice, selected))
        if len(records) != target:
            raise RuntimeError(f"could not generate {target} distinct nonwinding records at p={error_rate}")
        for record in sorted(records):
            result = enumerate_public_record(lattice, record, cap=cap)
            rows.append({
                "p": error_rate,
                "flux": list(record[0]),
                "measured_support": [int(value) for value in record[1]],
                **result,
            })

    histogram = Counter(row["nonwinding_scope_signature_count"] for row in rows if not row["capped"])
    ambiguous = [row for row in rows if not row["capped"] and row["nonwinding_scope_signature_count"] > 1]
    censored = [row for row in rows if row["capped"]]
    controls_pass = all(
        not row["capped"] and row["signature_count"] == 1 and row["expected_signature_present"]
        for row in control_rows
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "direct_public_scope_identifiability_rejected" if ambiguous else "direct_public_scope_identifiability_retained",
        "topology": {"label": "paper_periodic_honeycomb(2)", "vertex_count": 24, "edge_count": 36},
        "registration": str(DEFAULT_MANIFEST.resolve()),
        "matrix": {
            "fresh_seed": matrix["fresh_seed"],
            "p_values": matrix["bernoulli_p"],
            "record_count": len(rows),
            "records_per_p": matrix["distinct_nonwinding_public_records_per_p"],
            "assignment_cap": cap,
            "censored_record_count": len(censored),
            "signature_count_histogram": {str(key): value for key, value in sorted(histogram.items())},
            "ambiguous_record_count": len(ambiguous),
            "maximum_compatible_assignment_count": max(row["compatible_assignment_count"] for row in rows),
        },
        "positive_controls": {"count": len(control_rows), "all_pass": controls_pass, "rows": control_rows},
        "ambiguous_examples": ambiguous,
        "decision": {
            "H_unique": "rejected" if ambiguous else "retained_within_matrix",
            "H_ambiguous": "supported" if ambiguous else "not_observed",
            "reason": "At least one fully enumerated public record has multiple exact compatible nonwinding parity-scope signatures." if ambiguous else "No fully enumerated record in the registered matrix has multiple signatures.",
        },
        "new_decoder_samples": 0,
        "claim_boundary": "Finite paper-normalized L=2 structural identifiability test only. Ambiguity rejects a single observation-only charge-scope list, but does not reject a fixed factor graph with latent edge/connectivity variables and is not a BP or logical-performance result.",
    }
    if not controls_pass:
        raise AssertionError("isolated-hex positive controls failed")
    if censored:
        payload["status"] += "_with_censoring"
    return payload


def render_report(payload: dict) -> str:
    matrix = payload["matrix"]
    return "\n".join([
        "# R6B paper-normalized public parity-scope identifiability",
        "",
        "## Registered matrix",
        "",
        f"The confirmatory run uses fresh seed {matrix['fresh_seed']} on the 24-vertex, 36-edge paper-normalized L=2 graph. "
        f"It exactly enumerates every edge assignment compatible with {matrix['record_count']} public degree records across p={matrix['p_values']}; "
        f"{matrix['censored_record_count']} records hit the assignment cap.",
        "",
        f"All {payload['positive_controls']['count']} isolated-hex controls pass. The matrix contains {matrix['ambiguous_record_count']} fully enumerated public records with more than one nonwinding parity-scope signature.",
        "",
        "## Decision",
        "",
        f"H_unique is **{payload['decision']['H_unique']}**. {payload['decision']['reason']}",
        "",
        "This rejects a single parity-scope list derived only from the public flux and measured-support record. It does not reject an exact fixed graph whose factors also contain latent edge or connectivity variables; that richer construction is the next scientific gate.",
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
    manifest = json.loads(args.manifest.read_text())
    payload = run(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps({"status": payload["status"], **payload["matrix"]}, indent=2))


if __name__ == "__main__":
    main()
