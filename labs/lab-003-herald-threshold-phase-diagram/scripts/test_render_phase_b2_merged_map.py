import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_phase_b2_merged_map.py")
SPEC = importlib.util.spec_from_file_location("phase_b2_render", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
LAB = SCRIPT.parents[1]


class PhaseB2MergedMapTests(unittest.TestCase):
    def test_changes_exactly_four_cells_and_preserves_every_other_payload(self):
        base = json.loads((LAB / "results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json").read_text())
        update = json.loads((LAB / "results/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json").read_text())
        merged, changes = module.merged_analyses(base, update)
        changed = {(row["q"], row["p"]) for row in changes}
        self.assertEqual(changed, {(0.2, 0.08), (0.45, 0.2), (0.5, 0.2), (0.75, 0.4)})
        for before_row, after_row in zip(base["analyses"], merged):
            for before, after in zip(before_row["cells"], after_row["cells"]):
                if (before_row["q"], before["p"]) not in changed:
                    self.assertEqual(before, after)

    def test_merged_classification_counts(self):
        base = json.loads((LAB / "results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json").read_text())
        update = json.loads((LAB / "results/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json").read_text())
        merged, _ = module.merged_analyses(base, update)
        counts = {label: sum(cell["classification"] == label for row in merged for cell in row["cells"]) for label in ("decodable", "undecodable", "unresolved")}
        self.assertEqual(counts, {"decodable": 85, "undecodable": 39, "unresolved": 107})
        routes = {route: sum(cell.get("gray_measurement_route") == route for row in merged for cell in row["cells"]) for route in ("more_shots_existing_L7_L9_L11_first", "add_L5_L13_distance_leverage")}
        self.assertEqual(routes, {"more_shots_existing_L7_L9_L11_first": 107, "add_L5_L13_distance_leverage": 0})


if __name__ == "__main__":
    unittest.main()
