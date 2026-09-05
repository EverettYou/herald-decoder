import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("select_phase_b2_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("phase_b2_select", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class PhaseB2SelectionTests(unittest.TestCase):
    def test_current_selection_is_bounded_and_covers_both_arms(self):
        phase_map = json.loads(module.DEFAULT_MAP.read_text())
        b1 = json.loads(module.DEFAULT_B1.read_text())
        selection = module.select_cells(phase_map, b1)
        self.assertEqual([(row["q"], row["p"]) for row in selection["distance_leverage_new"]], [(0.2, 0.08)])
        self.assertEqual([(row["q"], row["p"]) for row in selection["distance_leverage_reused"]], [(0.45, 0.2)])
        self.assertEqual({row["branch"] for row in selection["shot_limited_selected"]}, {"shot_limited_upward_frontier", "shot_limited_downward_frontier"})
        self.assertEqual(len(selection["shot_limited_selected"]), 2)


if __name__ == "__main__":
    unittest.main()
