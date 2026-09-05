#!/usr/bin/env python3
"""Fail-closed gate and branch-separation tests for Phase B14."""

from __future__ import annotations

import copy
import gzip
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


SUBMIT = load("submit_phase_b14_two_branch.py", "phase_b14_submit_test")
AUDIT = load("audit_phase_b14_outputs.py", "phase_b14_audit_test")
ANALYZE = load("analyze_phase_b14_two_branch.py", "phase_b14_analyze_test")


class PhaseB14GateTests(unittest.TestCase):
    def test_dispatcher_freezes_eight_noncolliding_branch_jobs(self) -> None:
        manifest = json.loads(SUBMIT.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = SUBMIT.expand_jobs(manifest, project_root=root, lab_dir=root / "lab")
        SUBMIT.validate(SUBMIT.DEFAULT_MANIFEST, manifest, jobs)
        self.assertEqual(len(jobs), 8)
        self.assertEqual(len({job["stem"] for job in jobs}), 8)
        self.assertEqual(sum(job["expected_decodes"] for job in jobs), 10000)
        self.assertEqual({tuple(job["sizes"]) for job in jobs}, {(5, 13), (7, 9, 11)})
        self.assertEqual(SUBMIT.historical_seed_overlap(SUBMIT.DEFAULT_MANIFEST, jobs), [])

    def test_source_and_output_conflicts_fail_closed(self) -> None:
        manifest = json.loads(SUBMIT.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = SUBMIT.expand_jobs(manifest, project_root=root, lab_dir=root / "lab")
            jobs[0]["output_conflict"] = True
            with self.assertRaisesRegex(ValueError, "output conflict"):
                SUBMIT.validate(SUBMIT.DEFAULT_MANIFEST, manifest, jobs)
        bad = copy.deepcopy(manifest)
        bad["required_source_hashes"]["runner"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            jobs = SUBMIT.expand_jobs(bad, project_root=Path(directory), lab_dir=Path(directory) / "lab")
        with self.assertRaisesRegex(ValueError, "source hash drift"):
            SUBMIT.validate(SUBMIT.DEFAULT_MANIFEST, bad, jobs)

    def test_branch_pooling_is_separate_before_combination(self) -> None:
        base = {"sizes": [7, 9, 11], "logical_errors": [10, 20, 30], "shots": [100, 100, 100]}
        distance = {5: (4, 50), 13: (40, 50)}
        precision = {7: (5, 50), 9: (6, 50), 11: (7, 50)}
        self.assertEqual(
            ANALYZE.pool_counts(base, [distance]),
            ([5, 7, 9, 11, 13], [4, 10, 20, 30, 40], [50, 100, 100, 100, 50]),
        )
        self.assertEqual(
            ANALYZE.pool_counts(base, [precision]),
            ([7, 9, 11], [15, 26, 37], [150, 150, 150]),
        )
        self.assertEqual(
            ANALYZE.pool_counts(base, [distance, precision]),
            ([5, 7, 9, 11, 13], [4, 15, 26, 37, 40], [50, 150, 150, 150, 50]),
        )

    def test_auditor_checks_exact_branch_rows_and_syndrome_fidelity(self) -> None:
        manifest = json.loads(SUBMIT.DEFAULT_MANIFEST.read_text())
        job = manifest["jobs"][0]
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "raw.jsonl.gz"
            with gzip.open(raw_path, "wt", encoding="utf-8") as target:
                for size in job["sizes"]:
                    for seed in job["seeds"]:
                        for shot in range(job["shots_per_seed"]):
                            target.write(json.dumps({
                                "campaign": manifest["campaign"], "lattice": "honeycomb",
                                "q": job["q"], "p": job["p"], "L": size,
                                "seed": seed, "shot": shot, "syndrome_faithful": True,
                            }) + "\n")
            payload = {
                "campaign": manifest["campaign"], "lattice": "honeycomb", "q": job["q"],
                "p_grid": [job["p"]], "sizes": job["sizes"], "seeds": job["seeds"],
                "shots_per_seed": job["shots_per_seed"], "decoder": manifest["decoder"],
                "source_hashes": manifest["required_source_hashes"],
                "source_stability": {"start_equals_end": True},
                "raw_records": {"records": job["expected_decodes"], "sha256": SUBMIT.sha256(raw_path)},
                "syndrome_fidelity": {"all_faithful": True},
            }
            self.assertEqual(AUDIT.audit_pair(manifest, payload, raw_path, job), (1000, 1000))
            payload["seeds"] = [1]
            with self.assertRaisesRegex(ValueError, "coordinate/sampling"):
                AUDIT.audit_pair(manifest, payload, raw_path, job)

    def test_continuous_summary_contains_no_phase_label(self) -> None:
        output = ANALYZE.continuous_summary([7, 9, 11], [10, 12, 14], [100, 100, 100], seed=914999)
        self.assertNotIn("classification", output)
        self.assertIn("posterior_log_odds_upward_vs_downward", output)
        self.assertIn("posterior_sign_entropy_nats", output)


if __name__ == "__main__":
    unittest.main()
