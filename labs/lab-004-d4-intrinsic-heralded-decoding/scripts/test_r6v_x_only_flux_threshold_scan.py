from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_r6v_x_only_flux_threshold_scan import analyze  # noqa: E402
from run_r6v_x_only_flux_threshold_scan import (  # noqa: E402
    _require_integrity_gate,
    load_stage_2_selection,
    planned_cells,
)


def _manifest() -> dict:
    return json.loads(
        (Path(__file__).resolve().parents[1] / "manifests/r6v-x-only-flux-threshold-validation-manifest-2026-08-30.json").read_text()
    )


def test_registered_stage_one_has_all_sizes_rates_and_1000_histories() -> None:
    cells = planned_cells(_manifest())
    assert len(cells) == 45
    assert {cell["size"] for cell in cells} == {5, 7, 9, 11, 13}
    assert {cell["p_X"] for cell in cells} == {0.14, 0.16, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3}
    assert sum(cell["attempted_histories"] for cell in cells) == 45_000


def test_launch_requires_an_explicit_passing_integrity_report(tmp_path: Path) -> None:
    manifest = _manifest()
    missing = tmp_path / "missing.json"
    with pytest.raises(RuntimeError, match="launch refused"):
        _require_integrity_gate(manifest, missing)
    passing = tmp_path / "passing.json"
    passing.write_text(json.dumps({"integrity_gate_passed": True}))
    assert _require_integrity_gate(manifest, passing) == passing


def test_stage_two_selection_is_explicit_and_restricted_to_registered_cells(tmp_path: Path) -> None:
    selection = tmp_path / "analysis.json"
    selection.write_text(json.dumps({"stage_2_selected_cells": [
        {"size": 5, "p_X": 0.20},
        {"size": 7, "p_X": 0.20},
    ]}))
    selected = load_stage_2_selection(selection)
    cells = planned_cells(_manifest(), histories=2_000, selected_cells=selected)
    assert [(cell["size"], cell["p_X"], cell["attempted_histories"]) for cell in cells] == [
        (5, 0.20, 2_000),
        (7, 0.20, 2_000),
    ]


def test_stage_two_selection_rejects_duplicates_and_unknown_cells(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(json.dumps({"stage_2_selected_cells": [
        {"size": 5, "p_X": 0.20},
        {"size": 5, "p_X": 0.20},
    ]}))
    with pytest.raises(ValueError, match="duplicate"):
        load_stage_2_selection(duplicate)
    with pytest.raises(ValueError, match="unregistered"):
        planned_cells(_manifest(), histories=2_000, selected_cells={(999, 0.20)})


def test_analyzer_keeps_converged_only_bp_sensitivity_separate() -> None:
    manifest = _manifest()
    design = manifest["scan_design"]
    policies = ("O0_unit_weight_MWPM", "O2_published_herald_weight_MWPM", "R6D_local_BP_posterior_LLR_MWPM")
    rows = []
    for size in design["sizes"]:
        for rate in design["p_X_grid"]:
            for index in range(2):
                entries = {policy: {"status": "decoded", "flux_union_logical_failure": bool(index)} for policy in policies}
                entries[policies[2]]["bp"] = {"converged": index == 0}
                rows.append({"size": size, "p_X": rate, "status": "nonterminal", "policies": entries})
    payload = {"scan_design": design, "rows": rows}
    result = analyze(payload, bootstrap_replicates=50)
    bp_cell = next(cell for cell in result["cells"] if cell["size"] == 5 and cell["p_X"] == 0.14)[policies[2]]
    assert bp_cell["all_final_iterates"]["decoded"] == 2
    assert bp_cell["converged_only"]["decoded"] == 1
