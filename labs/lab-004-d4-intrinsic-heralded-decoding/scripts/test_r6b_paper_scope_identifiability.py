from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import paper_periodic_honeycomb  # noqa: E402
from run_r6b_paper_scope_identifiability import enumerate_public_record  # noqa: E402


def test_paper_l2_public_record_can_have_two_exact_scope_signatures() -> None:
    lattice = paper_periodic_honeycomb(2)
    flux = (
        0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
        0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    )
    measured = (
        True, True, False, False, False, False, False, False, False, False,
        True, False, False, False, False, True, True, True, True, True, True,
        False, True, False,
    )
    result = enumerate_public_record(lattice, (flux, measured), cap=100_000)
    assert not result["capped"]
    assert result["compatible_assignment_count"] == 30
    assert result["terminal_winding_assignment_count"] == 0
    assert result["nonwinding_scope_signature_count"] == 2
    assert {len(row["parity_scopes"]) for row in result["signatures"]} == {0, 2}
