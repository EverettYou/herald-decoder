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


register = load("select_and_register_phase_b4_frontier.py", "phase_b4_register_test")
submit = load("submit_phase_b4_frontier.py", "phase_b4_submit_test")


class PhaseB4RegistrationTests(unittest.TestCase):
    def test_only_newly_exposed_cell_is_selected(self):
        selection = register.build_selection(register.DEFAULT_MAP, register.DEFAULT_B3_ANALYSIS)
        self.assertEqual([(row["q"], row["p"]) for row in selection["new_jobs"]], [(0.05, 0.20)])
        self.assertEqual(selection["recently_tested_count"], 5)
        self.assertEqual(selection["expected_new_decodes"], 3000)

    def test_no_compatible_unused_measurement(self):
        active = json.loads(register.ACTIVE_BASE.read_text())
        audit = register.source_compatibility_audit(active)
        self.assertEqual(audit["compatible_unused_count"], 0)
        self.assertTrue(any(row["disposition"] == "excluded_incompatible_decoder_or_source" for row in audit["records"]))

    def test_dispatcher_is_one_job_and_closed_after_recorded_completion(self):
        manifest = json.loads(submit.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            jobs = submit.expand_jobs(manifest, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        self.assertEqual([(job["q"], job["p"], job["sizes"], job["expected_decodes"]) for job in jobs], [(0.05, 0.20, [7, 9, 11], 3000)])
        self.assertEqual(manifest["launch_gate"], "closed_data_complete")
        self.assertFalse(manifest["preflight_evidence"]["production_launched"])
        self.assertFalse(manifest["completion_evidence"]["scientific_analysis_performed"])


if __name__ == "__main__":
    unittest.main()
