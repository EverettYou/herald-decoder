import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("select_phase_b3_frontier_reuse.py")
SPEC = importlib.util.spec_from_file_location("phase_b3_select", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB3SelectionTests(unittest.TestCase):
    def test_smallest_frontier_matrix_reuses_existing_data(self):
        result = module.select(module.DEFAULT_MAP)
        self.assertEqual(result["candidate_count"], 6)
        self.assertEqual(result["reuse_count"], 5)
        self.assertEqual(result["new_job_count"], 1)
        self.assertEqual(result["expected_new_decodes"], 3000)
        self.assertEqual([(row["q"], row["p"]) for row in result["new_jobs"]], [(0.55, 0.24)])

    def test_candidate_set_covers_every_current_red_green_pinch(self):
        result = module.select(module.DEFAULT_MAP)
        self.assertEqual({(row["q"], row["p"]) for row in result["frontier_candidates"]}, {(0.10, 0.20), (0.30, 0.20), (0.35, 0.20), (0.40, 0.20), (0.55, 0.24), (0.60, 0.28)})


if __name__ == "__main__":
    unittest.main()
