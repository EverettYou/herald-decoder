"""Regression: an invalid physical guide cannot be regenerated/promoted."""
import importlib.util,json,unittest
from pathlib import Path
PATH=Path(__file__).with_name('analyze_phase_b18_symmetry_constrained_guide.py')
SPEC=importlib.util.spec_from_file_location('phase_b18',PATH);MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)
class WithdrawnGuideTests(unittest.TestCase):
    def test_analysis_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'withdrawn'):
            MODULE.analyze(MODULE.DEFAULT_EVIDENCE,MODULE.DEFAULT_B17,MODULE.DEFAULT_MANIFEST)
    def test_current_bundle_has_no_symmetry_guide(self):
        data=json.loads((PATH.parents[1]/'results/current-evidence.json').read_text())
        self.assertNotIn('symmetry_constrained_boundary_guide',data['evidence'])
        x=data['evidence']['full_prior_coverage']
        self.assertEqual(x['domain']['p'],[0,1]);self.assertIsNone(x['boundary_curve'])
        self.assertEqual(x['fabricated_or_mirrored_cells'],0)
if __name__=='__main__':unittest.main()
