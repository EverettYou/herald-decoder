from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("recover_declared_atomic_raw.py")
SPEC = importlib.util.spec_from_file_location("recover_declared_atomic_raw", SCRIPT)
recovery = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recovery)


class AtomicRecoveryTests(unittest.TestCase):
    def test_exact_declared_candidate_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lab = Path(directory)
            results = lab / "results"
            results.mkdir()
            raw = results / "unit-raw.jsonl.gz"
            candidate = results / ".unit-raw.jsonl.gz.tmp-7"
            with gzip.open(candidate, "wt", encoding="utf-8") as output:
                output.write('{"row":1}\n{"row":2}\n')
            summary = results / "unit.json"
            summary.write_text(json.dumps({
                "raw_records": {
                    "path": "results/unit-raw.jsonl.gz",
                    "records": 2,
                    "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                }
            }))
            result = recovery.recover_summary(summary, lab_dir=lab)
            self.assertEqual(result["status"], "recovered")
            self.assertTrue(raw.is_file())
            self.assertFalse(candidate.exists())

    def test_mismatched_candidate_is_left_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lab = Path(directory)
            results = lab / "results"
            results.mkdir()
            candidate = results / ".unit-raw.jsonl.gz.tmp-8"
            with gzip.open(candidate, "wt", encoding="utf-8") as output:
                output.write('{"row":1}\n')
            summary = results / "unit.json"
            summary.write_text(json.dumps({
                "raw_records": {
                    "path": "results/unit-raw.jsonl.gz",
                    "records": 1,
                    "sha256": "0" * 64,
                }
            }))
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                recovery.recover_summary(summary, lab_dir=lab)
            self.assertTrue(candidate.is_file())


if __name__ == "__main__":
    unittest.main()
