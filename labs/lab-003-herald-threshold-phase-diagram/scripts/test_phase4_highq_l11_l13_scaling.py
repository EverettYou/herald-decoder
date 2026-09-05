from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LAB_DIR = SCRIPT_DIR.parent
MANIFEST = LAB_DIR / "phase4-residual80-honeycomb-highq-l11-l13-scaling-manifest-2026-08-28.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


analysis = load_module("phase4_scaling_analysis", SCRIPT_DIR / "analyze_phase2_scout.py")
submit = load_module("phase4_scaling_submit", SCRIPT_DIR / "submit_phase2_parallel.py")


class Phase4ScalingManifestTests(unittest.TestCase):
    def test_registered_matrix_is_bounded_and_fresh(self) -> None:
        manifest = analysis.load_manifest(MANIFEST)
        self.assertIn(manifest["status"], {"registered", "ready", "production_validated", "analyzed_unresolved", "analyzed"})
        self.assertEqual(manifest["lattices"], ["honeycomb"])
        self.assertEqual(manifest["q_values"], [0.85, 0.9, 0.95])
        self.assertEqual(manifest["sizes"], [11, 13])
        self.assertEqual(len(manifest["seeds"]), 20)
        self.assertEqual(manifest["shots_per_cell"], 4000)
        self.assertEqual(manifest["expected_raw_records"], 168000)
        self.assertEqual(manifest["inference"]["confidence_level"], 0.9)

    def test_dispatch_commands_preserve_primary_decoder(self) -> None:
        manifest = analysis.load_manifest(MANIFEST)
        runtime = Path("run_research_python.sh")
        runner = SCRIPT_DIR / "run_phase2_scout.py"
        commands = [
            submit.build_command(
                manifest=manifest,
                runtime=runtime,
                runner=runner,
                lattice="honeycomb",
                q=q,
            )
            for q in manifest["q_values"]
        ]
        self.assertEqual(len({tuple(command) for command in commands}), 3)
        for command in commands:
            joined = " ".join(command)
            self.assertIn("--sizes 11 13", joined)
            self.assertIn("--shots-per-seed 200", joined)
            self.assertIn("--max-iterations 80", joined)
            self.assertIn("--update-schedule residual_priority", joined)
            self.assertIn("--residual-priority-order stable_sort", joined)
            self.assertNotIn("--allow-honeycomb-high-p", command)


if __name__ == "__main__":
    unittest.main()
