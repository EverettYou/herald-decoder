from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("run_phase3_highq_convergence_cap_diagnostic.py")
SPEC = importlib.util.spec_from_file_location("phase3_highq_cap", SCRIPT)
diagnostic = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(diagnostic)


class HighQCapDiagnosticTests(unittest.TestCase):
    def test_registered_arms_raise_only_iteration_cap(self) -> None:
        self.assertEqual(diagnostic.ARMS, (
            "residual_priority_80",
            "residual_priority_160",
            "residual_priority_320",
        ))
        self.assertEqual([diagnostic.CAPS[arm] for arm in diagnostic.ARMS], [80, 160, 320])

    def test_central_interval_is_reproducible_and_ordered(self) -> None:
        values = np.asarray([-1.0, 0.0, 1.0, 2.0])
        first = diagnostic.central_interval(values, 7)
        second = diagnostic.central_interval(values, 7)
        self.assertEqual(first, second)
        self.assertLessEqual(first[0], first[1])

    def test_l13_cli_uses_fresh_defaults_and_distinct_artifacts(self) -> None:
        args = diagnostic.parse_args(["--size", "13"])
        self.assertEqual(args.size, 13)
        self.assertEqual(args.seed_start, 60001)
        self.assertEqual(args.seed_count, 64)
        self.assertIn("l13", args.result.name)
        self.assertIn("l13", args.figure.name)
        self.assertNotEqual(args.result, diagnostic.RESULT)
        self.assertNotEqual(args.figure, diagnostic.FIGURE)

    def test_tiny_public_decode_is_syndrome_faithful(self) -> None:
        original = diagnostic.SEEDS
        diagnostic.SEEDS = (1, 2)
        try:
            cell = diagnostic.run_cell(3, 0.4, 0.9)
        finally:
            diagnostic.SEEDS = original
        self.assertEqual(set(cell["summaries"]), set(diagnostic.ARMS))
        self.assertTrue(all(item["all_syndrome_faithful"] for item in cell["summaries"].values()))


if __name__ == "__main__":
    unittest.main()
