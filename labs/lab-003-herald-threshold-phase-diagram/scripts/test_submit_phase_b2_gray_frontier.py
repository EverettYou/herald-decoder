import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("submit_phase_b2_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("phase_b2_submit", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
MANIFEST = SCRIPT.parents[1] / "phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json"


class PhaseB2DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())

    def jobs(self, manifest=None):
        with tempfile.TemporaryDirectory() as temporary:
            return module.expand_jobs(manifest or self.manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")

    def test_exact_registered_matrix_and_budget(self):
        jobs = self.jobs()
        module.validate_manifest(self.manifest, jobs)
        self.assertEqual({(j["q"], j["p"], tuple(j["sizes"])) for j in jobs}, {(0.2, 0.08, (5, 13)), (0.75, 0.4, (7, 9, 11)), (0.5, 0.2, (7, 9, 11))})
        self.assertEqual(sum(j["expected_decodes"] for j in jobs), 8000)

    def test_commands_are_job_specific_and_non_overwriting(self):
        for job in self.jobs():
            command = job["command"]
            sizes = [int(value) for value in command[command.index("--sizes") + 1:command.index("--seeds")]]
            self.assertEqual(sizes, job["sizes"])
            self.assertNotIn("--skip-existing", command)
            self.assertIn(job["stem"], command)

    def test_rejects_matrix_and_budget_drift(self):
        for mutation in ("matrix", "budget"):
            manifest = json.loads(json.dumps(self.manifest))
            if mutation == "matrix":
                manifest["jobs"][0]["p"] = 0.09
            else:
                manifest["expected_new_decodes"] += 1
            with self.assertRaises(ValueError):
                module.validate_manifest(manifest, self.jobs(manifest))


if __name__ == "__main__":
    unittest.main()
