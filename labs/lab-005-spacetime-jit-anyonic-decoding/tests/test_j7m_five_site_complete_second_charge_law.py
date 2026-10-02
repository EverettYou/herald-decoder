"""Exact equal-flux complete-second charge-law controls."""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7m_five_site_complete_second_charge_law.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7m_charge_law", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_full_public_laws_and_charge_only_overlap():
    result = json.loads(MODULE.RESULT.read_text())
    assert result["status"] == "five_site_complete_second_charge_law_closed"
    assert result["same_second_public_flux"]
    assert all(result["pinned_input_checks_before"].values())
    assert all(result["pinned_input_checks_after"].values())
    baseline, toggled = result["cells"]
    assert baseline["second_public_flux"] == toggled["second_public_flux"]
    assert baseline["variable_second_sites_private"] == [0]
    assert toggled["variable_second_sites_private"] == [0, 17, 20, 21, 22]
    left, right = MODULE.law(baseline["rows"]), MODULE.law(toggled["rows"])
    assert len(left) == 2 and set(left.values()) == {Fraction(1, 2)}
    assert len(right) == 32 and set(right.values()) == {Fraction(1, 32)}
    assert set(left) <= set(right)
    tv = sum((abs(left.get(key, Fraction()) - right.get(key, Fraction()))
              for key in set(left) | set(right)), Fraction()) / 2
    assert tv == Fraction(result["exact_complete_second_public_total_variation"])
    assert tv == Fraction(15, 16)
    assert result["usage"]["ordered_moment_terms"] <= 32768
    assert all(value == 0 for value in result["counters"].values())


def test_deterministic_replay():
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert stored == fresh
