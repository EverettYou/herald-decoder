import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("submit_slope_flow_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("gray_frontier", SCRIPT)
gray_frontier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gray_frontier)


MANIFEST = SCRIPT.parents[1] / "phase-s1-honeycomb-slope-flow-gray-frontier-manifest-2026-08-28.json"


class GrayFrontierDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())

    def test_expands_exact_registered_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            lab_dir = Path(temporary) / "lab"
            jobs = gray_frontier.expand_jobs(self.manifest, project_root=Path(temporary), lab_dir=lab_dir)
        gray_frontier.validate_manifest(self.manifest, jobs)
        self.assertEqual(len(jobs), 10)
        self.assertEqual(sum(job["expected_decodes"] for job in jobs), 24000)
        self.assertEqual(sum(job["branch"] == "seed-limited-pinch" for job in jobs), 4)
        self.assertEqual(sum(job["branch"] == "distance-limited-pinch" for job in jobs), 6)

    def test_commands_preserve_branch_specific_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            jobs = gray_frontier.expand_jobs(self.manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        for job in jobs:
            command = job["command"]
            size_offset = command.index("--sizes") + 1
            seed_offset = command.index("--seeds")
            sizes = [int(value) for value in command[size_offset:seed_offset]]
            expected = [7, 9, 11] if job["branch"] == "seed-limited-pinch" else [11, 13]
            self.assertEqual(sizes, expected)
            self.assertIn("--skip-existing", command)

    def test_rejects_budget_drift(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["expected_new_decodes"] += 1
        with tempfile.TemporaryDirectory() as temporary:
            jobs = gray_frontier.expand_jobs(manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        with self.assertRaises(ValueError):
            gray_frontier.validate_manifest(manifest, jobs)


if __name__ == "__main__":
    unittest.main()
