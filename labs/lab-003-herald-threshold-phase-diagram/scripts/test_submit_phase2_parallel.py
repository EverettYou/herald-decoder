from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("submit_phase2_parallel.py")
SPEC = importlib.util.spec_from_file_location("submit_phase2_parallel", SCRIPT)
submit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(submit)


class ManifestCommandTests(unittest.TestCase):
    def test_residual80_manifest_controls_unique_command(self) -> None:
        manifest = {
            "campaign": "unit-residual80",
            "artifact_stem_template": "unit-{lattice}-{q_tag}",
            "sizes": [7, 9, 11],
            "seeds": [1, 2],
            "shots_per_seed": 3,
            "p_grid": {"honeycomb": [0.2, 0.6]},
            "decoder": {
                "max_iterations": 80,
                "update_schedule": "residual_priority",
                "residual_priority_order": "stable_sort",
                "residual_priority_buffer_reuse": False,
                "residual_priority_cached_products": False,
            },
        }
        command = submit.build_command(
            manifest=manifest,
            runtime=Path("runtime"),
            runner=Path("runner.py"),
            lattice="honeycomb",
            q=0.75,
        )
        joined = " ".join(command)
        self.assertIn("--campaign unit-residual80", joined)
        self.assertIn("--stem unit-honeycomb-q075", joined)
        self.assertIn("--sizes 7 9 11", joined)
        self.assertIn("--max-iterations 80", joined)
        self.assertIn("--update-schedule residual_priority", joined)
        self.assertIn("--residual-priority-order stable_sort", joined)
        self.assertIn("--allow-honeycomb-high-p", command)
        self.assertNotIn("--residual-priority-buffer-reuse", command)
        self.assertNotIn("--residual-priority-cached-products", command)


if __name__ == "__main__":
    unittest.main()
