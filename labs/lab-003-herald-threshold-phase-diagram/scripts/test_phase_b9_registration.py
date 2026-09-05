#!/usr/bin/env python3
import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("select_and_register_phase_b9_endpoints.py");S=importlib.util.spec_from_file_location("b9reg",P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class PhaseB9RegistrationTests(unittest.TestCase):
 def test_exact_matrix_and_low_yield_are_frozen(self):
  s=M.build_selection(M.DEFAULT_MAP,M.DEFAULT_DESIGN);jobs={(r["q"],r["p"]):(r["sizes"],r["expected_decodes"]) for r in s["jobs"]}
  self.assertEqual(jobs[(.3,.2)],([5,13],2000));self.assertEqual(jobs[(.35,.2)],([5,13],2000));self.assertEqual(jobs[(.55,.24)],([5,13],2000));self.assertEqual(jobs[(.65,.28)],([7,11],2000));self.assertEqual(s["expected_new_decodes"],8000);self.assertAlmostEqual(s["expected_resolved_cells"],.3125)
 def test_seed_stream_is_disjoint(self):self.assertEqual(M.seed_audit()["overlaps"],[])
if __name__=="__main__":unittest.main()
