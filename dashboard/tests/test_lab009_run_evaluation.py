"""The complete assessment must be reachable through the actual Lab result card."""
import json,re,unittest
from pathlib import Path
from dashboard.server import lab_payload
ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'labs/lab-009-planar-herald-decoder-survey'
class RunEvaluationDeliveryTests(unittest.TestCase):
    def test_wiki_result_uses_supported_reader(self):
        payload=lab_payload(LAB.name)
        output=next(r for r in payload['outputs']if r['id']=='scicode2-run-evaluation')
        self.assertEqual(output['href'],f'/lab-wiki?lab={LAB.name}&page=scicode2-run-evaluation')
        figure=next(r for r in payload['outputs']if r['id']=='scicode2-run-boundary-comparison')
        self.assertEqual(figure['format'],'image');self.assertEqual(figure['presentation'],'page')
    def test_main_report_and_complete_assessment_are_present(self):
        report=(LAB/'REPORT.md').read_text();page=(LAB/'wiki/scicode2-run-evaluation.md').read_text()
        self.assertIn('figures/scicode2-run-boundary-comparison.png',report)
        self.assertIn('wiki/scicode2-run-evaluation.md',report)
        for family in ['Fable','Opus','Astra']:
            for run in range(1,4):self.assertIn(f'{family} {run}',report);self.assertIn(f'{family} {run}',page)
        self.assertIn('Lessons for SciCode 2 evaluation',page)
        self.assertIn('p≤1/2',page);self.assertIn('p,q in [0,1]',page)
    def test_original_assets_and_snapshot_are_exact(self):
        source=ROOT/'output/scicode2/run_evaluation'
        self.assertEqual((source/'REPORT.md').read_bytes(),(LAB/'data/inherited/audit_REPORT.md').read_bytes())
        for ext in ['png','pdf']:
            self.assertEqual((source/f'boundary_comparison.{ext}').read_bytes(),(LAB/f'figures/scicode2-run-boundary-comparison.{ext}').read_bytes())
        receipts=json.loads((LAB/'results/figure-provenance.json').read_text())
        self.assertEqual(sum(f['id']=='scicode2-run-boundary-comparison'for f in receipts['figures']),1)
if __name__=='__main__':unittest.main()
