#!/usr/bin/env python3
"""Combine R6AI dense-band cells with frozen R6AE anchors and select refinement."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_r5a_public_decoder_pilot import (
    independent_difference_bootstrap_interval,
    wilson_interval,
)


DEFAULT_MANIFEST = LAB / "manifests/r6ai-critical-band-refinement-manifest-2026-09-01.json"
DEFAULT_INPUT = LAB / "results/r6ai-critical-band-refinement-stage1-2026-09-01.json"
DEFAULT_BASELINE = LAB / "results/r6ae-signal-only-bp-threshold-stage5-analysis-2026-09-01.json"
DEFAULT_OUTPUT = LAB / "results/r6ai-critical-band-refinement-analysis-2026-09-01.json"
POLICIES = (
    "O2_published_herald_weight_MWPM",
    "R6D_local_BP_posterior_LLR_MWPM",
)


def compact_cell(rows: list[dict], policy: str) -> tuple[np.ndarray, dict]:
    values = np.asarray([bool(row["logical_failures"][policy]) for row in rows], dtype=float)
    failures = int(values.sum())
    low, high = wilson_interval(failures, len(values))
    return values, {
        "decoded": len(values),
        "failures": failures,
        "risk": float(values.mean()),
        "wilson_90": [low, high],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    refined = json.loads(args.input.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    design = manifest["scan_design"]
    sizes = [int(value) for value in design["sizes"]]
    new_grid = [float(value) for value in design["new_p_X_grid"]]
    anchors = [float(value) for value in design["retained_anchor_p_X_grid"]]
    full_grid = sorted(set(new_grid + anchors))
    baseline_cells = {
        (int(row["size"]), float(row["p_X"])): row
        for row in baseline["cells"]
        if int(row["size"]) in sizes and float(row["p_X"]) in anchors
    }
    baseline_differences = {
        (row["policy"], int(row["lower_size"]), int(row["upper_size"]), float(row["p_X"])): row
        for row in baseline["adjacent_size_differences_all_final_iterates"]
        if row["policy"] in POLICIES and float(row["p_X"]) in anchors
    }
    compact_rows = refined["rows"]
    arrays: dict[tuple[int, float, str], np.ndarray] = {}
    cells = []
    for size in sizes:
        for rate in full_grid:
            if rate in anchors:
                source = baseline_cells[(size, rate)]
                cell = {
                    "size": size,
                    "p_X": rate,
                    "attempted_histories": int(source["attempted_histories"]),
                    "terminal_physical_winding": int(source["terminal_physical_winding"]),
                    "source": "R6AE Stage 5 anchor",
                }
                for policy in POLICIES:
                    cell[policy] = source[policy]
            else:
                selected = [
                    row for row in compact_rows
                    if int(row["size"]) == size and float(row["p_X"]) == rate
                ]
                if not selected:
                    continue
                cell = {
                    "size": size,
                    "p_X": rate,
                    "attempted_histories": len(selected),
                    "terminal_physical_winding": sum(
                        row["status"] == "terminal_physical_winding" for row in selected
                    ),
                    "source": "R6AI dense-band refinement",
                }
                for policy in POLICIES:
                    values, summary = compact_cell(selected, policy)
                    arrays[(size, rate, policy)] = values
                    cell[policy] = {
                        "all_final_iterates": summary,
                        "converged_only": {
                            "decoded": 0, "failures": 0, "risk": None,
                            "wilson_90": [None, None],
                        },
                    }
            cells.append(cell)

    differences = []
    for policy_index, policy in enumerate(POLICIES):
        for lower, upper in zip(sizes, sizes[1:]):
            for rate_index, rate in enumerate(full_grid):
                if rate in anchors:
                    row = dict(baseline_differences[(policy, lower, upper, rate)])
                else:
                    left = arrays.get((lower, rate, policy))
                    right = arrays.get((upper, rate, policy))
                    if left is None or right is None:
                        continue
                    low, high = independent_difference_bootstrap_interval(
                        left, right, replicates=args.bootstrap_replicates,
                        seed=6_910_000 + 10_000 * policy_index + 100 * lower + rate_index,
                    )
                    row = {
                        "policy": policy,
                        "lower_size": lower,
                        "upper_size": upper,
                        "p_X": rate,
                        "upper_minus_lower_risk": float(right.mean() - left.mean()),
                        "bootstrap_90": [low, high],
                        "interval_contains_zero": low <= 0.0 <= high,
                    }
                differences.append(row)

    selected_cells: set[tuple[int, float]] = set()
    crossing_brackets = []
    for policy in POLICIES:
        for lower, upper in zip(sizes, sizes[1:]):
            rows = sorted(
                (row for row in differences if row["policy"] == policy
                 and row["lower_size"] == lower and row["upper_size"] == upper),
                key=lambda row: row["p_X"],
            )
            for index, row in enumerate(rows):
                if row["interval_contains_zero"]:
                    for neighbor in rows[max(0, index - 1): min(len(rows), index + 2)]:
                        if neighbor["p_X"] in new_grid:
                            selected_cells.add((lower, neighbor["p_X"]))
                            selected_cells.add((upper, neighbor["p_X"]))
            for left, right in zip(rows, rows[1:]):
                left_value = left["upper_minus_lower_risk"]
                right_value = right["upper_minus_lower_risk"]
                if left_value == 0.0 or right_value == 0.0 or left_value * right_value < 0.0:
                    crossing_brackets.append({
                        "policy": policy,
                        "lower_size": lower,
                        "upper_size": upper,
                        "p_X_bracket": [left["p_X"], right["p_X"]],
                        "endpoint_differences": [left_value, right_value],
                    })
                    for endpoint in (left["p_X"], right["p_X"]):
                        if endpoint in new_grid:
                            selected_cells.add((lower, endpoint))
                            selected_cells.add((upper, endpoint))

    result = {
        "schema_version": 1,
        "status": "r6ai_stage_1_dense_band_analysis_no_thermodynamic_fit",
        "manifest": args.manifest.name,
        "cells": sorted(cells, key=lambda row: (row["size"], row["p_X"])),
        "adjacent_size_differences_all_final_iterates": differences,
        "point_estimate_crossing_brackets": crossing_brackets,
        "stage_2_selected_cells": [
            {"size": size, "p_X": rate, "target_attempted_histories": 3000}
            for size, rate in sorted(selected_cells)
        ],
        "diagnostics": {
            "new_compact_row_count": len(compact_rows),
            "combined_cell_count": len(cells),
            "new_grid": new_grid,
            "anchor_grid": anchors,
            "stage_2_selected_cell_count": len(selected_cells),
            "all_replays_exact": all(item["exact"] for item in refined["deterministic_replays"]),
        },
        "claim_boundary": manifest["claim_boundary"],
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "combined_cells": len(cells),
        "selected_stage_2_cells": len(selected_cells),
        "crossing_brackets": len(crossing_brackets),
    }), flush=True)


if __name__ == "__main__":
    main()
