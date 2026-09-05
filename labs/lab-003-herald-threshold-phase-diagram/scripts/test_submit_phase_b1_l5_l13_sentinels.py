import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("submit_phase_b1_l5_l13_sentinels.py")
SPEC = importlib.util.spec_from_file_location("phase_b1_submit", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
MANIFEST = SCRIPT.parents[1] / "phase-b1-honeycomb-l5-l13-sentinels-manifest-2026-08-28.json"


class PhaseB1DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())

    def test_exact_registered_matrix(self):
        with tempfile.TemporaryDirectory() as temporary:
            jobs = module.expand_jobs(self.manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        module.validate_manifest(self.manifest, jobs)
        self.assertEqual(len(jobs), 4)
        self.assertEqual(sum(job["expected_decodes"] for job in jobs), 8000)
        self.assertTrue(all(job["sizes"] == [5, 13] for job in jobs))

    def test_commands_do_not_rerun_existing_distances_or_skip_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            jobs = module.expand_jobs(self.manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        for job in jobs:
            command = job["command"]
            size_start = command.index("--sizes") + 1
            seed_start = command.index("--seeds")
            self.assertEqual([int(value) for value in command[size_start:seed_start]], [5, 13])
            self.assertNotIn("--skip-existing", command)

    def test_rejects_budget_drift(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["expected_new_decodes"] += 1
        with tempfile.TemporaryDirectory() as temporary:
            jobs = module.expand_jobs(manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        with self.assertRaises(ValueError):
            module.validate_manifest(manifest, jobs)


if __name__ == "__main__":
    unittest.main()
