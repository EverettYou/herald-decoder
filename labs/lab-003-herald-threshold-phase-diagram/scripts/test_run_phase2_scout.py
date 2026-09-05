from __future__ import annotations

import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("run_phase2_scout.py")
SPEC = importlib.util.spec_from_file_location("run_phase2_scout", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class SyndromeFidelityTests(unittest.TestCase):
    def test_fail_closed_helper_rejects_mismatch(self) -> None:
        graph = runner.square_graph(3)
        correction = np.zeros(len(graph.edges), dtype=np.uint8)
        syndrome = np.zeros(len(graph.detector_vertices), dtype=np.uint8)
        syndrome[0] = 1
        with self.assertRaisesRegex(RuntimeError, "correction-syndrome fidelity failure"):
            runner.require_syndrome_fidelity(
                graph=graph,
                correction=correction,
                syndrome=syndrome,
                context="unit-test",
            )

    def test_small_shard_persists_fidelity_at_all_levels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "smoke-raw.jsonl.gz"
            result = runner.run_shard(
                lattice="honeycomb",
                q=1.0,
                p_grid=(0.2,),
                sizes=(2,),
                seeds=(730001,),
                shots_per_seed=2,
                max_iterations=8,
                update_schedule="residual_priority",
                residual_priority_order="stable_sort",
                residual_priority_buffer_reuse=False,
                residual_priority_cached_products=False,
                raw_path=raw_path,
            )

            self.assertEqual(result["raw_records"]["records"], 2)
            self.assertTrue(result["source_stability"]["start_equals_end"])
            self.assertEqual(
                result["syndrome_fidelity"],
                {
                    "checked_corrections": 2,
                    "faithful_corrections": 2,
                    "failures": 0,
                    "all_faithful": True,
                    "enforcement": "raise before raw-row write and atomic shard finalization",
                },
            )
            self.assertEqual(result["summaries"][0]["syndrome_faithful_shots"], 2)
            self.assertEqual(result["summaries"][0]["syndrome_fidelity_rate"], 1.0)
            with gzip.open(raw_path, "rt", encoding="utf-8") as source:
                rows = [json.loads(line) for line in source]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["syndrome_faithful"] is True for row in rows))

    def test_high_probability_honeycomb_bp_shard_is_syndrome_faithful(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "high-p-smoke-raw.jsonl.gz"
            result = runner.run_shard(
                campaign="unit-high-p",
                lattice="honeycomb",
                q=1.0,
                p_grid=(0.9,),
                sizes=(2,),
                seeds=(730002,),
                shots_per_seed=2,
                max_iterations=8,
                update_schedule="residual_priority",
                residual_priority_order="stable_sort",
                residual_priority_buffer_reuse=False,
                residual_priority_cached_products=False,
                raw_path=raw_path,
            )
            self.assertEqual(result["raw_records"]["records"], 2)
            self.assertTrue(result["syndrome_fidelity"]["all_faithful"])

    def test_source_drift_removes_temporary_raw_and_fails_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "source-drift-raw.jsonl.gz"
            with self.assertRaisesRegex(RuntimeError, "source drift detected"):
                runner.run_shard(
                    lattice="honeycomb",
                    q=1.0,
                    p_grid=(0.2,),
                    sizes=(2,),
                    seeds=(730003,),
                    shots_per_seed=1,
                    max_iterations=8,
                    update_schedule="residual_priority",
                    residual_priority_order="stable_sort",
                    residual_priority_buffer_reuse=False,
                    residual_priority_cached_products=False,
                    raw_path=raw_path,
                    expected_source_hashes={"runner": "start"},
                    source_hash_reader=lambda: {"runner": "changed"},
                )

            self.assertFalse(raw_path.exists())
            self.assertEqual(list(Path(directory).glob(".source-drift-raw.jsonl.gz.tmp-*")), [])


if __name__ == "__main__":
    unittest.main()
