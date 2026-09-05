import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("select_and_register_phase_b6_frontier.py")
SPEC = importlib.util.spec_from_file_location("phase_b6_registration", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB6RegistrationTests(unittest.TestCase):
    def test_smallest_matrix_covers_all_four_frontier_cells(self):
        selection = module.build_selection(module.DEFAULT_MAP, module.DEFAULT_B5_SELECTION, module.DEFAULT_B5_AUDIT)
        jobs = {(row["q"], row["p"]): (row["branch"], row["sizes"], row["expected_decodes"]) for row in selection["new_jobs"]}
        self.assertEqual(jobs[(0.55, 0.24)], ("endpoint_extension_l5_l13", [5, 13], 2000))
        for key in {(0.30, 0.20), (0.35, 0.20), (0.60, 0.28)}:
            self.assertEqual(jobs[key], ("rebalance_to_2000_shots", [5, 7, 9, 13], 4000))
        self.assertEqual(selection["expected_new_decodes"], 14000)

    def test_inventory_has_no_compatible_unused_source(self):
        selection = module.build_selection(module.DEFAULT_MAP, module.DEFAULT_B5_SELECTION, module.DEFAULT_B5_AUDIT)
        self.assertEqual(selection["source_compatibility_audit"]["compatible_unused_count"], 0)


if __name__ == "__main__":
    unittest.main()
