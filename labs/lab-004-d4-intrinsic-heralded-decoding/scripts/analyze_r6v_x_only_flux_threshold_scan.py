#!/usr/bin/env python3
"""Analyze R6V finite-size flux curves without fitting a threshold.

The output identifies preregistered Stage-2 cells from adjacent-size interval
overlap.  It deliberately makes no thermodynamic threshold estimate.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_r5a_public_decoder_pilot import independent_difference_bootstrap_interval, wilson_interval


POLICIES = ("O0_unit_weight_MWPM", "O2_published_herald_weight_MWPM", "R6D_local_BP_posterior_LLR_MWPM")


def _eligible(rows: list[dict], policy: str, converged_only: bool) -> list[dict]:
    result = []
    for row in rows:
        if row["status"] != "nonterminal":
            continue
        decoded = row["policies"].get(policy, {})
        if decoded.get("status") != "decoded":
            continue
        if converged_only and policy == POLICIES[2] and not decoded["bp"]["converged"]:
            continue
        result.append(row)
    return result


def analyze(payload: dict, *, bootstrap_replicates: int = 10_000) -> dict:
    rows = payload["rows"]
    grid = [float(x) for x in payload["scan_design"]["p_X_grid"]]
    sizes = [int(x) for x in payload["scan_design"]["sizes"]]
    cells = {}
    for size in sizes:
        for rate in grid:
            cell_rows = [r for r in rows if r["size"] == size and r["p_X"] == rate]
            summary = {"attempted_histories": len(cell_rows), "terminal_physical_winding": sum(r["status"] != "nonterminal" for r in cell_rows)}
            for policy in POLICIES:
                accounting = {}
                for label, converged_only in (("all_final_iterates", False), ("converged_only", True)):
                    used = _eligible(cell_rows, policy, converged_only)
                    failures = sum(bool(r["policies"][policy]["flux_union_logical_failure"]) for r in used)
                    low, high = wilson_interval(failures, len(used)) if used else (None, None)
                    accounting[label] = {"decoded": len(used), "failures": failures, "risk": failures / len(used) if used else None, "wilson_90": [low, high]}
                summary[policy] = accounting
            cells[(size, rate)] = summary

    differences, stage_2 = [], set()
    for policy_index, policy in enumerate(POLICIES):
        for lower, upper in zip(sizes, sizes[1:]):
            for rate_index, rate in enumerate(grid):
                left = np.array([bool(r["policies"][policy]["flux_union_logical_failure"]) for r in _eligible([x for x in rows if x["size"] == lower and x["p_X"] == rate], policy, False)], dtype=float)
                right = np.array([bool(r["policies"][policy]["flux_union_logical_failure"]) for r in _eligible([x for x in rows if x["size"] == upper and x["p_X"] == rate], policy, False)], dtype=float)
                if not len(left) or not len(right):
                    continue
                low, high = independent_difference_bootstrap_interval(left, right, replicates=bootstrap_replicates, seed=6_100_000 + 10_000 * policy_index + 100 * lower + rate_index)
                unresolved = low <= 0.0 <= high
                differences.append({"policy": policy, "lower_size": lower, "upper_size": upper, "p_X": rate, "upper_minus_lower_risk": float(np.mean(right) - np.mean(left)), "bootstrap_90": [low, high], "interval_contains_zero": unresolved})
                if unresolved:
                    for selected in grid[max(0, rate_index - 1): min(len(grid), rate_index + 2)]:
                        stage_2.add((lower, selected)); stage_2.add((upper, selected))
    return {
        "status": "r6v_stage_1_finite_size_analysis_no_threshold_fit",
        "cells": [{"size": size, "p_X": rate, **cells[(size, rate)]} for size in sizes for rate in grid],
        "adjacent_size_differences_all_final_iterates": differences,
        "stage_2_selected_cells": [{"size": size, "p_X": rate, "next_increment_attempted_histories": payload["scan_design"]["stage_2_increment_attempted_histories"]} for size, rate in sorted(stage_2)],
        "claim_boundary": "Finite-size X-only flux curves and a preregistered allocation decision only. No crossing fit or threshold claim is made; BP converged-only sensitivity remains separately reported.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(payload, bootstrap_replicates=args.bootstrap_replicates)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
