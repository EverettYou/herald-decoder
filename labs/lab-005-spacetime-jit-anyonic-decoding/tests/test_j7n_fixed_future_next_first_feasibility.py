"""Zero-Born next-first structural and exact-engine cost checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7n_fixed_future_next_first_feasibility.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7n_next_first_audit", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_registered_cost_formula_and_four_cell_boundaries():
    result = json.loads(MODULE.RESULT.read_text())
    assert result["status"] == "fixed_future_structural_cost_audit_closed"
    assert all(result["pinned_input_checks_before"].values())
    assert all(result["pinned_input_checks_after"].values())
    assert len(result["matrix"]) == 4
    assert [row["positive_second_prefixes"] for row in result["matrix"]] == \
        [2, 32, 2, 32]
    assert result["matrix"][0]["next_public_flux"] == \
        result["matrix"][1]["next_public_flux"]
    assert result["matrix"][2]["next_public_flux"] == \
        result["matrix"][3]["next_public_flux"]
    assert all(row["second_next_anticommuting_pair_count"] == 1
               for row in result["matrix"])
    for row in result["matrix"]:
        expected = MODULE.current_engine_cost(2, row["second_variable_site_count"],
                                              len(row["next_eligible_sites_private"]),
                                              row["positive_second_prefixes"])
        assert row["current_engine_work_projection"] == expected
    assert result["current_engine_denominator_and_one_site_terms_total"] == 46181504
    assert not result["current_engine_stage_fits_prior_ceiling"]
    assert all(value == 0 for value in result["counters"].values())


def test_deterministic_replay():
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert stored == fresh
