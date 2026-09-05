from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_r6ab_o2_threshold_quick_scan import crossings_from_differences  # noqa: E402
from run_r6ab_o2_threshold_quick_scan import run  # noqa: E402


def _manifest() -> dict:
    return {
        "status": "registered",
        "phase": "R6AB",
        "scan_design": {
            "sizes": [2],
            "p_X_grid": [0.2],
            "attempted_histories_per_cell": 2,
            "seed_salt": 991,
            "paper_reference_threshold": 0.20842,
        },
        "decoder": {"id": "O2_published_herald_weight_MWPM"},
        "claim_boundary": "test only",
    }


def test_linear_crossing_interpolation() -> None:
    assert crossings_from_differences([(0.20, -0.02), (0.21, 0.01)]) == pytest.approx([0.2066666667])
    assert crossings_from_differences([(0.19, -0.01), (0.20, 0.01), (0.21, -0.01)]) == pytest.approx([0.195, 0.205])
    assert crossings_from_differences([(0.20, -0.02), (0.21, -0.01)]) == []


def test_small_scan_writes_provenanced_resumable_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    first = run(_manifest(), checkpoint, manifest_name="fixture.json")
    assert first["status"] == "completed_r6ab_o2_threshold_scan"
    assert len(first["rows"]) == 2
    assert first["source_provenance"]
    replay = run(_manifest(), checkpoint, manifest_name="fixture.json")
    assert replay["rows"] == first["rows"]
    payload = json.loads(checkpoint.read_text())
    payload["source_provenance"] = {}
    checkpoint.write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="stale R6AB checkpoint"):
        run(_manifest(), checkpoint, manifest_name="fixture.json")
