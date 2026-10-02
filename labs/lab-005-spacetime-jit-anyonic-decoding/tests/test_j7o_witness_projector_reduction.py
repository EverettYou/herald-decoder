"""Four-cell symbolic next-witness reduction and deterministic replay."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7o_witness_projector_reduction.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7o_witness_reduction", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_four_cell_identity_and_zero_born_budget():
    result = json.loads(MODULE.RESULT.read_text())
    assert result["status"] == "witness_one_site_projector_identity_closed"
    assert all(result["pinned_input_checks_before"].values())
    assert all(result["pinned_input_checks_after"].values())
    assert result["operator_pair_checks"] == 2860
    assert result["positive_prefix_checks"] == 68
    assert [(row["future_physical_red_edges_private"],
             row["second_next_witness_private"],
             row["positive_complete_second_prefixes"])
            for row in result["cells"]] == [([0], [0, 1], 2),
                                           ([0], [0, 1], 32),
                                           ([4], [2, 1], 2),
                                           ([4], [2, 1], 32)]
    assert all(row["conditional_next_charge_probabilities_for_every_prefix"]
               == {"0": "1/2", "1": "1/2"} for row in result["cells"])
    assert all(value == 0 for value in result["counters"].values())


def test_operator_involution_guard_and_deterministic_replay():
    assert MODULE.hermitian_involution((1, 0b11, 0b11))
    assert not MODULE.hermitian_involution((1, 0b01, 0b01))
    assert not MODULE.hermitian_involution((0, 0, 0))
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert stored == fresh
