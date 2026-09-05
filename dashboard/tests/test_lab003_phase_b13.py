"""Regression contracts for the active Lab 003 Phase B18 presentation."""

from __future__ import annotations

import re
import unittest

from dashboard.server import lab_payload


class Lab003PhaseB18PresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = lab_payload("lab-003-herald-threshold-phase-diagram")

    def test_phase_b18_is_the_active_collaborator_figure(self) -> None:
        matches = [
            row for row in self.payload["outputs"]
            if row["id"] == "phase-b18-symmetry-constrained-guide-figure-2026-08-28"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["presentation"], "page")
        self.assertEqual(matches[0]["format"], "image")

    def test_active_results_include_b18_and_its_core_evidence(self) -> None:
        ids = {row["id"] for row in self.payload["outputs"]}
        self.assertTrue({
            "current-evidence",
            "phase-b18-symmetry-constrained-guide-figure-2026-08-28",
        }.issubset(ids))
        self.assertNotIn("phase-b17-resolution-aware-guide-figure-2026-08-28", ids)
        self.assertNotIn("phase-b16-strong-smooth-boundary-2026-08-28", ids)
        bundle = next(row for row in self.payload["outputs"] if row["id"] == "current-evidence")
        self.assertEqual(bundle["presentation"], "result")

    def test_download_only_provenance_is_not_a_lab_result(self) -> None:
        retired = [
            row for row in self.payload["outputs"]
            if row.get("kind") == "figure"
            and re.match(r"phase-b(?:5|6|7|8|9|12)-", row["id"])
        ]
        self.assertEqual(retired, [])
        self.assertNotIn(
            "phase-b13-honeycomb-continuous-log-odds-data-2026-08-28",
            {row["id"] for row in self.payload["outputs"]},
        )
        self.assertTrue(all(row["presentation"] in {"page", "result"} for row in self.payload["outputs"]))

    def test_report_embeds_the_active_map_and_selected_ler_context(self) -> None:
        report = self.payload["report"]["content"]
        self.assertIn(
            "](results/phase-b18-symmetry-constrained-guide-2026-08-28.png)",
            report,
        )
        self.assertIn(
            "](results/final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.png)",
            report,
        )
        self.assertIsNone(re.search(
            r"!\[[^\]]*\]\((?:figures|results)/phase-b(?:5|6|7|8|9|12|13|15)-[^)]*\.png\)",
            report,
        ))


if __name__ == "__main__":
    unittest.main()
