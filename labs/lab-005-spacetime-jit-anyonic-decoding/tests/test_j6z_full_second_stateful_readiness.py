"""Exact full-second loop and frozen next-first interface acceptance gates."""

from fractions import Fraction
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_j6z_full_second_stateful_readiness import RESULT, run


class J6ZTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_exact_full_second_public_law(self):
        result = self.result["full_second_loop"]
        self.assertEqual(result["status"], "passed_exact_one_geometry_full_binary_second_public_law")
        self.assertEqual(result["first_positive_records"], 16)
        self.assertEqual(result["second_eligible_sites_count"], 22)
        self.assertEqual(result["second_variable_sites_private"], [])
        self.assertEqual(result["positive_public_rows"], 16)
        self.assertEqual(result["moment_terms"], 4096)
        rows = result["public_law_rows"]
        self.assertEqual(sum((Fraction(r["joint_probability"]) for r in rows), Fraction()), 1)
        self.assertEqual({r["second_conditional_probability"] for r in rows}, {"1"})
        self.assertEqual(len({tuple(r["second_public"]["charge"]) for r in rows}), 16)
        self.assertEqual([site for site in range(24)
                          if len({r["second_public"]["charge"][site] for r in rows}) > 1],
                         [17, 20, 21, 22])
        for row in rows:
            self.assertEqual(set(row["first_public"]), {"flux", "charge", "vacuum"})
            self.assertEqual(set(row["second_public"]), {"flux", "charge", "vacuum"})
            self.assertEqual({len(bits) for bits in row["second_public"].values()}, {24})

    def test_stateful_interface_absence_and_replay(self):
        interface = self.result["stateful_next_round_interface"]
        self.assertEqual(interface["status"], "not_integrated_stateful_next_first_interface")
        self.assertFalse(interface["has_postselected_or_next_first_state_token"])
        self.assertFalse(interface["five_round_caller_invokes_fixed_adapter"])
        self.assertTrue(interface["five_round_caller_invokes_pheno_second_provider"])
        self.assertTrue(all(self.result["pinned_input_checks"].values()))
        self.assertEqual(set(self.result["counters"].values()), {0})
        self.assertLess(self.result["cpu_seconds"], 60)
        saved = json.loads(RESULT.read_text())
        current = dict(self.result)
        saved.pop("cpu_seconds")
        current.pop("cpu_seconds")
        self.assertEqual(saved, current)


if __name__ == "__main__":
    unittest.main()
