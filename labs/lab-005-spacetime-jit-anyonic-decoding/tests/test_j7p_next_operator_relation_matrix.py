"""Algebraic full-next-law reconstruction gates and deterministic replay."""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7p_next_operator_relation_matrix.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7p_relation_matrix", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_four_complete_laws_and_matched_future_contrast():
    result = json.loads(MODULE.RESULT.read_text())
    assert result["status"] == "four_cell_operator_relation_matrix_closed"
    assert all(result["pinned_input_checks_before"].values())
    assert all(result["pinned_input_checks_after"].values())
    assert result["usage"] == {"operator_pair_checks": 1936,
                               "positive_prefix_checks": 68,
                               "reconstructed_public_rows": 136}
    assert len(result["cells"]) == 4
    for cell in result["cells"]:
        assert cell["class_counts"] == {
            "ineligible_charge_zero": 2, "fair_by_anticommutation": 1,
            "signed_repeat": 21, "unresolved_commuting_other": 0}
        assert cell["fair_next_sites_private"] == [1]
        assert cell["unresolved_next_sites_private"] == []
        assert cell["complete_next_law_reconstructed"]
        assert sum((Fraction(row["conditional_probability"])
                    for row in cell["complete_next_law"]), Fraction()) == 1
        for row in cell["complete_next_law"]:
            public = row["public"]
            assert public["flux"] == cell["next_public_flux"]
            assert public["vacuum"] == [1 - bit for bit in public["charge"]]
    assert result["same_future_comparison"] == {
        "[0]": {"status": "exact_full_next_law_compared",
                "exact_total_variation": "15/16"},
        "[4]": {"status": "exact_full_next_law_compared",
                "exact_total_variation": "15/16"}}
    assert all(value == 0 for value in result["counters"].values())


def test_relation_classes_do_not_promote_commutation():
    prior = {0: (1, 0, 1)}  # X on bit 0.
    usage = {"operator_pair_checks": 0}
    assert MODULE.relation((1, 1, 0), prior, usage, 3)["class"] == \
        "fair_by_anticommutation"  # Z on bit 0.
    assert MODULE.relation((-1, 0, 1), prior, usage, 3) == {
        "class": "signed_repeat",
        "relations": [{"second_site_private": 0, "charge_flipped": True}]}
    assert MODULE.relation((1, 0, 2), prior, usage, 3)["class"] == \
        "unresolved_commuting_other"  # X on a different bit.


def test_deterministic_replay():
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert stored == fresh
