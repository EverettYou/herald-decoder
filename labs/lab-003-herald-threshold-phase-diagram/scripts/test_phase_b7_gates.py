#!/usr/bin/env python3
"""Downstream fail-closed tests for Phase B7."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SUBMIT = load("submit_phase_b7_endpoints.py", "phase_b7_submit_test")
ANALYZE = load("analyze_phase_b7_endpoints.py", "phase_b7_analyze_test")
RENDER = load("render_phase_b7_merged_map.py", "phase_b7_render_test")


class PhaseB7GateTests(unittest.TestCase):
    def test_dispatch_budget_and_source_gate(self) -> None:
        manifest = json.loads(SUBMIT.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            jobs = SUBMIT.expand_jobs(manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        SUBMIT.validate(SUBMIT.DEFAULT_MANIFEST, manifest, jobs)
        self.assertEqual(sum(job["expected_decodes"] for job in jobs), 8000)
        self.assertTrue(all(job["sizes"] == [5, 13] for job in jobs))
        bad = copy.deepcopy(manifest)
        bad["required_source_hashes"]["runner"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash drift"):
            SUBMIT.validate(SUBMIT.DEFAULT_MANIFEST, bad, jobs)

    def test_pooling_updates_only_endpoint_counts(self) -> None:
        cell = {"sizes": [5, 7, 9, 11, 13], "logical_errors": [5, 7, 9, 11, 13], "shots": [20, 20, 20, 20, 20]}
        fresh = {"summaries": [{"q": 0.3, "p": 0.2, "L": 5, "logical_errors": 2, "shots": 10}, {"q": 0.3, "p": 0.2, "L": 13, "logical_errors": 4, "shots": 10}]}
        job = {"q": 0.3, "p": 0.2, "branch": "endpoint_extension_1000_each"}
        result = ANALYZE.analyze_counts(cell, fresh, job)
        self.assertEqual(result["logical_errors"], [7, 7, 9, 11, 17])
        self.assertEqual(result["shots"], [30, 20, 20, 20, 30])

    def test_renderer_updates_four_and_preserves_227(self) -> None:
        base = json.loads(RENDER.DEFAULT_BASE.read_text())
        rows = []
        for q, p in sorted(RENDER.EXPECTED):
            rows.append({"q": q, "p": p, "pooling_kind": "synthetic", "sizes": [5, 7, 9, 11, 13], "logical_errors": [1] * 5, "shots": [10] * 5, "classification": "unresolved", "jeffreys_classification": "unresolved", "uniform_prior_sensitivity": {"classification": "unresolved"}})
        merged, changes = RENDER.merged_analyses(base, {"analyses": rows})
        self.assertEqual(len(changes), 4)
        unchanged = 0
        for base_row, merged_row in zip(base["analyses"], merged):
            for before, after in zip(base_row["cells"], merged_row["cells"]):
                if (base_row["q"], before["p"]) not in RENDER.EXPECTED:
                    self.assertEqual(before, after)
                    unchanged += 1
        self.assertEqual(unchanged, 227)


if __name__ == "__main__":
    unittest.main()
