from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_r5a_public_decoder_pilot import run_production  # noqa: E402


def test_production_refuses_unactivated_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"status":"registered"}\n', encoding="utf-8")
    try:
        run_production(manifest, tmp_path / "records.jsonl.gz")
    except RuntimeError as exc:
        assert "not authorized" in str(exc)
    else:
        raise AssertionError("production should fail closed before activation")


def test_tiny_activated_production_runs_both_public_modes(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "status": "preflight_passed_production_authorized",
                "source_freeze": {},
                "production_activation": {"source_freeze": {}},
                "design": {
                    "seed_salt": 91,
                    "sizes": [2],
                    "physical_error_rates": [0.0],
                    "production_histories_per_size_rate": 2,
                    "public_policies": ["syndrome_only", "heralded"],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "records.jsonl.gz"
    summary = run_production(manifest, output)
    assert summary["histories"] == 2
    assert summary["public_decoder_evaluations"] == 4
    with gzip.open(output, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    assert {row["mode"] for row in rows} == {"syndrome_only", "heralded"}
    assert all(row["stage_outcome"] == "decoded_success" for row in rows)
