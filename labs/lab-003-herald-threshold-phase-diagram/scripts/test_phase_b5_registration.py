import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("select_and_register_phase_b5_frontier.py")
SPEC = importlib.util.spec_from_file_location("phase_b5_registration", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB5RegistrationTests(unittest.TestCase):
    def test_smallest_matrix_covers_all_five_persistent_cells(self):
        selection = module.build_selection(module.DEFAULT_MAP, module.DEFAULT_B3_SELECTION, module.DEFAULT_B3_ANALYSIS)
        jobs = {(row["q"], row["p"]): (row["branch"], row["sizes"], row["expected_decodes"]) for row in selection["new_jobs"]}
        self.assertEqual(jobs[(0.55, 0.24)], ("independent_shots", [7, 9, 11], 3000))
        for key in {(0.30, 0.20), (0.35, 0.20), (0.40, 0.20), (0.60, 0.28)}:
            self.assertEqual(jobs[key], ("distance_extension_l5", [5], 1000))
        self.assertEqual(selection["expected_new_decodes"], 7000)

    def test_no_newly_exposed_or_compatible_unused_cells(self):
        selection = module.build_selection(module.DEFAULT_MAP, module.DEFAULT_B3_SELECTION, module.DEFAULT_B3_ANALYSIS)
        self.assertEqual(selection["newly_exposed_cells"], [])
        self.assertEqual(selection["source_compatibility_audit"]["compatible_unused_count"], 0)


if __name__ == "__main__":
    unittest.main()
