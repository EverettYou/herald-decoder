#!/usr/bin/env python3
"""Registration and fail-closed gate tests for Phase B10."""

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


REG = load("select_and_register_phase_b10_endpoints.py", "phase_b10_reg_test")
SUB = load("submit_phase_b10_endpoints.py", "phase_b10_submit_test")
ANA = load("analyze_phase_b10_frontier.py", "phase_b10_analysis_test")
REN = load("render_phase_b10_merged_map.py", "phase_b10_render_test")


class PhaseB10Tests(unittest.TestCase):
    def test_exact_matrix_and_forecast_are_frozen(self) -> None:
        selection = REG.build_selection(REG.DEFAULT_MAP, REG.DEFAULT_DESIGN)
        jobs = {(row["q"], row["p"]): (row["sizes"], row["expected_decodes"]) for row in selection["jobs"]}
        self.assertEqual(jobs[(0.30, 0.20)], ([5, 13], 2000))
        self.assertEqual(jobs[(0.35, 0.20)], ([5, 13], 2000))
        self.assertEqual(jobs[(0.55, 0.24)], ([5, 13], 2000))
        self.assertEqual(jobs[(0.65, 0.32)], ([7, 11], 2000))
        self.assertEqual(selection["expected_new_decodes"], 8000)
        self.assertAlmostEqual(selection["expected_resolved_cells"], 1.1767578125)
        self.assertAlmostEqual(selection["jobs"][0]["posterior_predictive_probability_resolved"], 0.029296875)

    def test_seed_stream_is_disjoint(self) -> None:
        self.assertEqual(REG.seed_audit()["overlaps"], [])

    def test_dispatch_budget_and_source_gate(self) -> None:
        manifest = json.loads(SUB.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            jobs = SUB.expand_jobs(manifest, project_root=Path(directory), lab_dir=Path(directory) / "lab")
        SUB.validate(SUB.DEFAULT_MANIFEST, manifest, jobs)
        self.assertEqual(sum(job["expected_decodes"] for job in jobs), 8000)
        bad = copy.deepcopy(manifest)
        bad["required_source_hashes"]["runner"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash drift"):
            SUB.validate(SUB.DEFAULT_MANIFEST, bad, jobs)

    def test_pooling_and_renderer_are_exact(self) -> None:
        cell = {"sizes": [7, 9, 11], "logical_errors": [5, 7, 9], "shots": [20, 20, 20]}
        fresh = {"summaries": [{"q": 0.65, "p": 0.32, "L": L, "logical_errors": e, "shots": 10} for L, e in [(7, 2), (11, 4)]]}
        job = {"q": 0.65, "p": 0.32, "branch": "measured_endpoints_1000", "sizes": [7, 11]}
        pooled = ANA.analyze_counts(cell, fresh, job)
        self.assertEqual(pooled["logical_errors"], [7, 7, 13])
        base = json.loads(REN.BASE.DEFAULT_BASE.read_text())
        rows = [{"q": q, "p": p, "pooling_kind": "synthetic", "sizes": [7, 9, 11],
                 "logical_errors": [1, 1, 1], "shots": [10, 10, 10], "classification": "unresolved",
                 "jeffreys_classification": "unresolved", "uniform_prior_sensitivity": {"classification": "unresolved"}}
                for q, p in sorted(REN.EXPECTED)]
        merged, changes = REN.merged_analyses(base, {"analyses": rows})
        self.assertEqual(len(changes), 4)
        self.assertEqual(sum(("phase_b10_update" in cell) for row in merged for cell in row["cells"]), 4)


if __name__ == "__main__":
    unittest.main()
