"""Current Lab 003 presentation must expose corrected scientific scope."""
import unittest,json
from pathlib import Path
from dashboard.server import lab_payload
class Lab003FullPriorPresentationTests(unittest.TestCase):
    def setUp(self):self.payload=lab_payload('lab-003-herald-threshold-phase-diagram')
    def test_b19_is_active_and_b18_is_not(self):
        ids={r['id']:r for r in self.payload['outputs']}
        self.assertEqual(ids['phase-b19-full-prior-evidence-coverage-2026-10-01']['presentation'],'page')
        self.assertFalse(any('b18' in key for key in ids))
        self.assertIn('current-evidence',ids)
    def test_report_embeds_corrected_coverage_and_context(self):
        text=self.payload['report']['content']
        self.assertIn('phase-b19-full-prior-evidence-coverage-2026-10-01.png',text)
        self.assertIn('final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.png',text)
        self.assertNotIn('](results/phase-b18-',text)
        self.assertIn('withdrawn',text);self.assertIn('p,q in [0,1]',text)
    def test_bundle_retains_original_measured_cells(self):
        lab=Path(__file__).resolve().parents[2]/'labs/lab-003-herald-threshold-phase-diagram/results'
        bundle=json.loads((lab/'current-evidence.json').read_text())
        original=json.loads((lab/'phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json').read_text())
        self.assertEqual(bundle['evidence']['honeycomb_finite_window_trend']['cells'],original['cells'])
        self.assertNotIn('symmetry_constrained_boundary_guide',bundle['evidence'])
if __name__=='__main__':unittest.main()
