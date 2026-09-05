import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load(filename, name):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


submit = load("submit_phase_b3_frontier_reuse.py", "phase_b3_submit_test")
reuse = load("audit_phase_b3_reuse_sources.py", "phase_b3_reuse_test")
analyze = load("analyze_phase_b3_frontier_reuse.py", "phase_b3_analyze_test")


class PhaseB3PreflightTests(unittest.TestCase):
    def test_one_job_matrix_and_budget(self):
        manifest = json.loads(submit.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            jobs = submit.expand_jobs(manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        submit.validate_manifest(manifest, jobs)
        self.assertEqual([(j["q"], j["p"], j["sizes"], j["expected_decodes"]) for j in jobs], [(0.55, 0.24, [7, 9, 11], 3000)])

    def test_five_reuse_sources_are_audited(self):
        result = reuse.audit(reuse.DEFAULT_MANIFEST)
        self.assertEqual(result["status"], "reuse_sources_verified")
        self.assertEqual(result["reuse_sources_verified"], 5)
        self.assertEqual(result["reused_raw_rows"], 11000)
        self.assertFalse(result["withdrawn_interpretation_reused"])

    def test_heterogeneous_pooling_rules(self):
        base = {7: (1, 1000), 9: (2, 1000), 11: (3, 1000)}
        self.assertEqual(analyze.pool_counts("seed_limited", base, {7: (4, 1000), 9: (5, 1000), 11: (6, 1000)}), {7: (5, 2000), 9: (7, 2000), 11: (9, 2000)})
        self.assertEqual(analyze.pool_counts("distance_limited", base, {11: (6, 1000), 13: (7, 1000)}), {7: (1, 1000), 9: (2, 1000), 11: (9, 2000), 13: (7, 1000)})


if __name__ == "__main__":
    unittest.main()
