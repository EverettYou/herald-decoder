import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_phase_b3_merged_map.py")
SPEC = importlib.util.spec_from_file_location("phase_b3_render", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
LAB = SCRIPT.parents[1]


class PhaseB3MergedMapTests(unittest.TestCase):
    def inputs(self):
        base = json.loads((LAB / "results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json").read_text())
        update = json.loads((LAB / "results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json").read_text())
        return base, update

    def test_changes_exactly_one_cell_and_preserves_every_other_payload(self):
        base, update = self.inputs()
        merged, changes = module.merged_analyses(base, update)
        changed = {(row["q"], row["p"]) for row in changes}
        self.assertEqual(changed, {(0.1, 0.2)})
        unchanged = 0
        for before_row, after_row in zip(base["analyses"], merged):
            for before, after in zip(before_row["cells"], after_row["cells"]):
                if (before_row["q"], before["p"]) not in changed:
                    self.assertEqual(before, after)
                    unchanged += 1
        self.assertEqual(unchanged, 230)

    def test_merged_classification_counts_and_gray_routes(self):
        base, update = self.inputs()
        merged, _ = module.merged_analyses(base, update)
        counts = {
            label: sum(cell["classification"] == label for row in merged for cell in row["cells"])
            for label in ("decodable", "undecodable", "unresolved")
        }
        self.assertEqual(counts, {"decodable": 85, "undecodable": 40, "unresolved": 106})
        routes = {
            route: sum(cell.get("gray_measurement_route") == route for row in merged for cell in row["cells"])
            for route in ("more_shots_existing_L7_L9_L11_first", "add_L5_L13_distance_leverage")
        }
        self.assertEqual(routes, {"more_shots_existing_L7_L9_L11_first": 106, "add_L5_L13_distance_leverage": 0})


if __name__ == "__main__":
    unittest.main()
