"""Certified affine record-sector contraction for the L5 reverse response.

The default command executes only the preregistered tiny/L3 exact gates.  The
two L5 cells are unreachable unless ``--run-l5`` is passed explicitly.  This
separation lets the registration tick validate the target-preserving tangent
semiring before any production contraction is armed.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import time

import numpy as np

from check_reverse_sector_response import (
    enumerate_l3,
    joint_response,
    response_summary,
    risk,
    sector_coefficients,
    sector_switch_count,
)
from current_oracle import LAB, ROOT, CurrentOracle, charge_matrix, square_graph


VALUES = (0, 1, -1)
MANIFEST = LAB / "manifests/l5-reverse-sector-contraction-2026-09-19.json"
GATE_RESULT = LAB / "results/l5-reverse-sector-contraction-gates-2026-09-19.json"
FULL_RESULT = LAB / "results/l5-reverse-sector-contraction-2026-09-19.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["id"] == "lab008-l5-reverse-sector-contraction-2026-09-19"
    assert manifest["registered_method"]["budgets"] == [1024, 4096]
    cells = manifest["registered_matrix"]["cells"]
    assert [(x["L"], x["p"], x["epsilon"], x["q"]) for x in cells] == [
        (5, 0.08, 0.03, 0.97),
        (5, 0.3, 0.01, 0.99),
    ]
    assert manifest["compute_budget"]["new_physical_record_samples"] == 0
    assert manifest["compute_budget"]["bootstrap_replicates"] == 0
    for relative, expected in manifest["provenance_sha256"].items():
        path = (LAB / relative).resolve()
        assert path.is_file(), path
        assert sha256(path) == expected, f"provenance mismatch: {relative}"
    return manifest


def local_affine_weight(values: tuple[int, ...], p: float) -> tuple[float, float]:
    """Return the epsilon intercept and derivative for newly assigned edges."""
    occupied = sum(value != 0 for value in values)
    reverse = sum(value == -1 for value in values)
    base = (1.0 - p) ** (len(values) - occupied) * p**occupied
    if reverse == 0:
        return base, -occupied * base
    if reverse == 1:
        return 0.0, base
    return 0.0, 0.0


def multiply_affine(left: np.ndarray, right: tuple[float, float]) -> np.ndarray:
    a, b = left
    c, d = right
    return np.asarray((a * c, a * d + b * c), dtype=np.float64)


def remaining_parity_convolution(
    sector_coefficients_pair: np.ndarray, remaining_cut_edges: int, p: float
) -> np.ndarray:
    """Marginalize unassigned logical occupancy, whose tangent is exactly zero."""
    odd = (1.0 - (1.0 - 2.0 * p) ** remaining_cut_edges) / 2.0
    even = 1.0 - odd
    out = np.empty_like(sector_coefficients_pair)
    out[0] = even * sector_coefficients_pair[0] + odd * sector_coefficients_pair[1]
    out[1] = even * sector_coefficients_pair[1] + odd * sector_coefficients_pair[0]
    return out


def evaluate_pair(coefficients: np.ndarray, epsilon: float) -> np.ndarray:
    return coefficients[:, 0] + epsilon * coefficients[:, 1]


def contract(
    L: int,
    p: float,
    epsilon: float,
    *,
    prefix_budget: int | None,
    state_cap: int,
    return_table: bool = False,
) -> dict:
    """Contract J_epsilon, optionally finalizing low-risk charge prefixes."""
    model = square_graph(L)
    order = CurrentOracle(model, cap=12_000_000).profile["order"]
    measured = set(model.detector_vertices)
    logical = set(model.logical_edges)
    assigned: set[int] = set()
    visited: set[int] = set()
    frontier: list[int] = []
    # key=(frontier currents, emitted full integer-charge prefix, parity)
    # value=(affine intercept, affine derivative)
    dp: dict[tuple, np.ndarray] = {((), (), 0): np.asarray((1.0, 0.0))}
    finalized_upper = 0.0
    finalized_probability = 0.0
    peak = 1
    profile = []

    for vertex in order:
        old = [edge for edge in model.incident_edges[vertex] if edge in assigned]
        new = [edge for edge in model.incident_edges[vertex] if edge not in assigned]
        keep = [edge for edge in frontier if edge not in old]
        visited.add(vertex)
        future = [
            edge
            for edge in new
            if any(
                endpoint in measured and endpoint not in visited
                for endpoint in model.edges[edge]
            )
        ]
        old_positions = [frontier.index(edge) for edge in old]
        keep_positions = [frontier.index(edge) for edge in keep]

        def signs(edges):
            return [1 if model.edges[edge][1] == vertex else -1 for edge in edges]

        nxt: dict[tuple, np.ndarray] = {}
        for (front_values, prefix, parity0), pair0 in dp.items():
            old_charge = sum(
                sign * front_values[position]
                for sign, position in zip(signs(old), old_positions)
            )
            kept = tuple(front_values[position] for position in keep_positions)
            for values in product(VALUES, repeat=len(new)):
                local = local_affine_weight(values, p)
                if local == (0.0, 0.0):
                    continue
                charge = old_charge + sum(
                    sign * value for sign, value in zip(signs(new), values)
                )
                parity = parity0
                for edge, value in zip(new, values):
                    if edge in logical and value != 0:
                        parity ^= 1
                future_values = tuple(values[new.index(edge)] for edge in future)
                key = (kept + future_values, prefix + (charge,), parity)
                contribution = multiply_affine(pair0, local)
                if key in nxt:
                    nxt[key] += contribution
                else:
                    nxt[key] = contribution

        preprune = len(nxt)
        peak = max(peak, preprune)
        if preprune > state_cap:
            raise MemoryError(
                f"preprune state cap {preprune}>{state_cap} at vertex {vertex}"
            )
        frontier = keep + future
        assigned.update(new)

        grouped: dict[tuple[int, ...], np.ndarray] = {}
        for (_, prefix, sector), pair in nxt.items():
            if prefix not in grouped:
                grouped[prefix] = np.zeros((2, 2), dtype=np.float64)
            grouped[prefix][sector] += pair

        remaining_cut = len(logical - assigned)
        scored = []
        for prefix, pair_by_sector in grouped.items():
            completed = remaining_parity_convolution(pair_by_sector, remaining_cut, p)
            masses = evaluate_pair(completed, epsilon)
            if masses.min() < -1e-14:
                raise AssertionError(
                    f"negative prefix-sector mass {masses.min()} at {prefix}"
                )
            masses = np.maximum(masses, 0.0)
            scored.append((float(masses.min()), prefix, float(masses.sum())))
        scored.sort(key=lambda row: (-row[0], row[1]))

        if prefix_budget is None or len(scored) <= prefix_budget:
            keep_prefixes = {row[1] for row in scored}
            dropped = []
        else:
            keep_prefixes = {row[1] for row in scored[:prefix_budget]}
            dropped = scored[prefix_budget:]
        finalized_upper += sum(row[0] for row in dropped)
        finalized_probability += sum(row[2] for row in dropped)
        dp = {key: pair for key, pair in nxt.items() if key[1] in keep_prefixes}
        active_probability = sum(
            pair[0] + epsilon * pair[1] for pair in dp.values()
        )
        if abs(finalized_probability + active_probability - 1.0) > 2e-10:
            raise AssertionError("prefix probability conservation failed")
        profile.append(
            {
                "vertex": int(vertex),
                "preprune_states": preprune,
                "active_states": len(dp),
                "prefixes": len(grouped),
                "kept_prefixes": len(keep_prefixes),
                "remaining_cut_edges": remaining_cut,
                "finalized_upper": finalized_upper,
                "finalized_probability": finalized_probability,
            }
        )

    assert not frontier
    table: dict[tuple[int, ...], np.ndarray] = {}
    for (_, record, sector), pair in dp.items():
        if record not in table:
            table[record] = np.zeros((2, 2), dtype=np.float64)
        table[record][sector] += pair
    active_risk = 0.0
    active_probability = 0.0
    for pair_by_sector in table.values():
        masses = evaluate_pair(pair_by_sector, epsilon)
        if masses.min() < -1e-14:
            raise AssertionError("negative full-record sector mass")
        masses = np.maximum(masses, 0.0)
        active_risk += float(masses.min())
        active_probability += float(masses.sum())
    lower = active_risk
    upper = active_risk + finalized_upper
    if abs(finalized_probability + active_probability - 1.0) > 2e-10:
        raise AssertionError("final probability conservation failed")
    result = {
        "L": L,
        "p": p,
        "epsilon": epsilon,
        "q": 1.0 - epsilon,
        "prefix_budget": prefix_budget,
        "lower_J": lower,
        "upper_J": upper,
        "interval_width": upper - lower,
        "finalized_upper": finalized_upper,
        "finalized_probability": finalized_probability,
        "active_probability": active_probability,
        "surviving_full_records": len(table),
        "peak_preprune_states": peak,
        "profile": profile,
    }
    if return_table:
        result["table"] = table
    return result


def direct_affine_table(L: int, p: float) -> dict[tuple[int, ...], np.ndarray]:
    model = square_graph(L)
    incidence = charge_matrix(model)
    edge_count = len(model.edges)
    table: dict[tuple[int, ...], np.ndarray] = {}
    for raw in product(VALUES, repeat=edge_count):
        current = np.asarray(raw, dtype=np.int8)
        occupied = int(np.count_nonzero(current))
        reverse = int(np.count_nonzero(current == -1))
        base = (1.0 - p) ** (edge_count - occupied) * p**occupied
        if reverse == 0:
            pair = (base, -occupied * base)
        elif reverse == 1:
            pair = (0.0, base)
        else:
            continue
        record = tuple(int(x) for x in incidence @ current)
        sector = model.logical_parity((current != 0).astype(np.uint8))
        if record not in table:
            table[record] = np.zeros((2, 2), dtype=np.float64)
        table[record][sector] += pair
    return table


def compare_tables(left: dict, right: dict, tolerance: float = 1e-12) -> float:
    maximum = 0.0
    for record in set(left) | set(right):
        a = left.get(record, np.zeros((2, 2), dtype=np.float64))
        b = right.get(record, np.zeros((2, 2), dtype=np.float64))
        maximum = max(maximum, float(np.max(np.abs(a - b))))
    if maximum > tolerance:
        raise AssertionError(f"record-sector affine mismatch {maximum}>{tolerance}")
    return maximum


def fraction_table_to_float(intercept, derivative) -> dict:
    return {
        record: np.asarray(
            (
                (float(intercept[record][0]), float(derivative[record][0])),
                (float(intercept[record][1]), float(derivative[record][1])),
            ),
            dtype=np.float64,
        )
        for record in intercept
    }


def run_exact_gates(manifest: dict) -> dict:
    started = time.monotonic()
    tiny_rows = []
    for p, epsilon in ((0.08, 0.03), (0.3, 0.01)):
        # L3 is the smallest canonical open square accepted by the shared
        # lattice constructor and remains a 3^8 direct-enumeration fixture.
        direct = direct_affine_table(3, p)
        contracted = contract(
            3,
            p,
            epsilon,
            prefix_budget=None,
            state_cap=1_000_000,
            return_table=True,
        )
        maximum = compare_tables(direct, contracted.pop("table"))
        tiny_rows.append(
            {
                "p": p,
                "epsilon": epsilon,
                "records": len(direct),
                "maximum_record_sector_coefficient_error": maximum,
                "normalization_error": abs(
                    contracted["active_probability"] + contracted["finalized_probability"] - 1
                ),
            }
        )

    graph, _, groups, _ = enumerate_l3()
    predecessor = json.loads(
        (LAB / "results/reverse-sector-response-2026-09-19.json").read_text()
    )
    expected_cells = {
        (row["p"], row["epsilon"]): row
        for row in predecessor["L3_full_support_validation"]
    }
    exact_rows = []
    for p_text in (".05", ".08", ".10", ".30", ".46"):
        p_fraction = Fraction(p_text)
        p = float(p_fraction)
        intercept, derivative = sector_coefficients(groups, len(graph.edges), p_fraction)
        expected_table = fraction_table_to_float(intercept, derivative)
        # Epsilon only evaluates the affine pair; the coefficients are identical.
        contracted = contract(
            3,
            p,
            0.005,
            prefix_budget=None,
            state_cap=1_000_000,
            return_table=True,
        )
        maximum = compare_tables(expected_table, contracted.pop("table"))
        summary = response_summary(intercept, derivative)
        for epsilon_text in (".005", ".01", ".03"):
            epsilon_fraction = Fraction(epsilon_text)
            epsilon = float(epsilon_fraction)
            expected = expected_cells[(p, epsilon)]
            response = joint_response(intercept, derivative, epsilon_fraction)
            exact_risk = float(risk(response))
            switch_count = sector_switch_count(intercept, response)
            # Re-evaluate the already checked contraction coefficients at epsilon.
            affine_risk = sum(
                min(
                    float(intercept[record][0] + epsilon_fraction * derivative[record][0]),
                    float(intercept[record][1] + epsilon_fraction * derivative[record][1]),
                )
                for record in intercept
            )
            error = abs(affine_risk - exact_risk)
            if error > 1e-12:
                raise AssertionError(f"L3 affine risk mismatch {error}")
            assert abs(exact_risk - expected["joint_response_LER"]) <= 1e-12
            assert switch_count == expected["strict_sector_switches_in_response"]
            exact_rows.append(
                {
                    "p": p,
                    "epsilon": epsilon,
                    "records": len(intercept),
                    "maximum_record_sector_coefficient_error": maximum,
                    "joint_response_LER": exact_risk,
                    "LER_replay_error": error,
                    "newly_accessible_first_order_records": summary[
                        "newly_accessible_first_order_records"
                    ],
                    "new_records_with_both_sectors": summary[
                        "new_records_with_both_sectors"
                    ],
                    "strict_sector_switches": switch_count,
                }
            )

    assert len(exact_rows) == 15
    assert all(row["newly_accessible_first_order_records"] == 96 for row in exact_rows)
    assert all(row["new_records_with_both_sectors"] == 60 for row in exact_rows)
    elapsed = time.monotonic() - started
    sources = [
        Path(__file__),
        MANIFEST,
        LAB / "scripts/check_reverse_sector_response.py",
        LAB / "scripts/current_oracle.py",
        LAB / "results/reverse-sector-response-2026-09-19.json",
        ROOT / "src/herald_decoder/lattice_model.py",
    ]
    return {
        "status": "passed",
        "scope": "Implementation plus tiny and 15-cell L3 exact gates only; no L5 contraction, sampling, bootstrap, decoder, or LER inference.",
        "manifest_id": manifest["id"],
        "tiny_record_sector_gates": tiny_rows,
        "L3_exact_replay": exact_rows,
        "checks": {
            "tiny_record_sector_tuples_match": True,
            "L3_record_sector_tuples_match": True,
            "L3_cells": len(exact_rows),
            "normalization_and_positivity": True,
            "new_record_counts_replayed": True,
            "sector_switch_counts_replayed": True,
            "manifest_action_binding": True,
            "provenance_hashes_match": True,
        },
        "registration_counters": {
            "new_physical_record_samples": 0,
            "bootstrap_replicates": 0,
            "decoder_runs": 0,
            "L5_contractions": 0,
            "L5_LER_inferences": 0,
        },
        "elapsed_seconds": elapsed,
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in sources
        },
    }


def run_l5(manifest: dict, gates: dict) -> dict:
    """Execute only the frozen two-cell production matrix after exact gates pass."""
    assert gates["status"] == "passed"
    started = time.monotonic()
    cap = manifest["compute_budget"]["maximum_preprune_states"]
    total_seconds = manifest["compute_budget"]["maximum_wall_seconds_total"]
    rows = []
    censored = []
    for cell in manifest["registered_matrix"]["cells"]:
        runs = []
        for budget in manifest["registered_method"]["budgets"]:
            if time.monotonic() - started > total_seconds:
                censored.append({"cell": cell, "reason": "total wall-time cap"})
                break
            try:
                row = contract(
                    cell["L"],
                    cell["p"],
                    cell["epsilon"],
                    prefix_budget=budget,
                    state_cap=cap,
                )
            except MemoryError as error:
                censored.append({"cell": cell, "prefix_budget": budget, "reason": str(error)})
                break
            certificate = cell["exact_TV_certificate"]
            row["TV_certificate"] = certificate
            row["width_gate_passed"] = row["interval_width"] <= certificate
            envelope = [
                max(0.0, row["lower_J"] - certificate),
                min(0.5, row["upper_J"] + certificate),
            ]
            row["diagnostic_physical_envelope"] = envelope
            row["promoted_physical_LER_interval"] = (
                envelope if row["width_gate_passed"] else None
            )
            runs.append(row)
            if row["width_gate_passed"]:
                break
        rows.append({"cell": cell, "runs": runs})
    passed_cells = [
        study["cell"]
        for study in rows
        if study["runs"] and study["runs"][-1]["width_gate_passed"]
    ]
    if censored:
        status = "complete_with_censoring"
    elif len(passed_cells) == len(rows):
        status = "passed_all_width_gates"
    elif passed_cells:
        status = "completed_partial_width_gate"
    else:
        status = "completed_width_gates_failed"
    return {
        "status": status,
        "scope": "Frozen two-cell L5 affine response contraction; finite-patch intervals only.",
        "gates_result": str(GATE_RESULT.relative_to(LAB)),
        "cells": rows,
        "censored": censored,
        "passed_cells": passed_cells,
        "decision": (
            "promote_registered_physical_intervals"
            if len(passed_cells) == len(rows)
            else "reject_within_registered_budgets"
            if not passed_cells
            else "promote_only_passing_cells"
        ),
        "claim_boundary": (
            "A physical LER interval is promoted only for a cell whose final "
            "contraction width does not exceed its exact TV certificate; diagnostic "
            "envelopes for failed cells are not promoted as physical LER results."
        ),
        "new_physical_record_samples": 0,
        "bootstrap_replicates": 0,
        "decoder_runs": 0,
        "elapsed_seconds": time.monotonic() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-l5",
        action="store_true",
        help="After exact gates pass, execute the frozen two-cell L5 matrix.",
    )
    args = parser.parse_args()
    manifest = load_and_verify_manifest()
    gates = run_exact_gates(manifest)
    GATE_RESULT.write_text(json.dumps(gates, indent=2) + "\n")
    if not args.run_l5:
        print(
            json.dumps(
                {
                    "status": gates["status"],
                    "scope": gates["scope"],
                    "tiny_gates": len(gates["tiny_record_sector_gates"]),
                    "L3_cells": len(gates["L3_exact_replay"]),
                    "maximum_coefficient_error": max(
                        row["maximum_record_sector_coefficient_error"]
                        for row in gates["L3_exact_replay"]
                    ),
                    "registration_counters": gates["registration_counters"],
                    "seconds": gates["elapsed_seconds"],
                },
                indent=2,
            )
        )
        return
    result = run_l5(manifest, gates)
    result["source_sha256"] = {
        str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__)),
        str(MANIFEST.relative_to(ROOT)): sha256(MANIFEST),
        str(GATE_RESULT.relative_to(ROOT)): sha256(GATE_RESULT),
    }
    FULL_RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "cells": len(result["cells"]), "censored": result["censored"]}, indent=2))


if __name__ == "__main__":
    main()
