"""Direct Born spot-check, term cap, and algebraic prediction controls."""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7q_direct_born_spotcheck.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7q_direct_born", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_registered_three_probe_result_and_budget():
    result = json.loads(MODULE.RESULT.read_text())
    assert result["status"] == "three_direct_born_spotchecks_replayed"
    assert all(result["pinned_input_checks_before"].values())
    assert all(result["pinned_input_checks_after"].values())
    assert result["usage"] == {"direct_born_probes": 3,
                               "ordered_moment_terms": 33024}
    assert result["usage"]["ordered_moment_terms"] <= \
        result["prior_exact_term_ceiling"] == 65536
    assert [row["direct_conditional_probability"] for row in result["probes"]] == \
        ["1/2", "1", "1/2"]
    assert [row["direct_three_block_joint_mass"] for row in result["probes"]] == \
        ["1/16", "1/8", "1/256"]
    assert all(Fraction(row["direct_three_block_joint_mass"]) /
               Fraction(row["prefix_joint_mass"]) ==
               Fraction(row["registered_algebraic_prediction"])
               for row in result["probes"])
    assert all(value == 0 for value in result["counters"].values())


def test_prediction_guard_and_deterministic_replay():
    assert MODULE.prediction({"class": "fair_by_anticommutation"},
                             [0]) == Fraction(1, 2)
    cls = {"class": "signed_repeat",
           "relations": [{"second_site_private": 0, "charge_flipped": True}]}
    assert MODULE.prediction(cls, [0]) == 0
    assert MODULE.prediction(cls, [1]) == 1
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert stored == fresh
