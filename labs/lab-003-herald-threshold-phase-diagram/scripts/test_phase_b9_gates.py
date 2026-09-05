#!/usr/bin/env python3
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
SUB=load("submit_phase_b9_endpoints.py","b9subtest");ANA=load("analyze_phase_b9_frontier.py","b9anatest");REN=load("render_phase_b9_merged_map.py","b9rentest")
class PhaseB9GateTests(unittest.TestCase):
 def test_dispatch_budget_and_source_gate(self):
  manifest=json.loads(SUB.DEFAULT_MANIFEST.read_text())
  with tempfile.TemporaryDirectory() as t:jobs=SUB.expand_jobs(manifest,project_root=Path(t),lab_dir=Path(t)/"lab")
  SUB.validate(SUB.DEFAULT_MANIFEST,manifest,jobs);self.assertEqual(sum(j["expected_decodes"] for j in jobs),8000)
  bad=copy.deepcopy(manifest);bad["required_source_hashes"]["runner"]="0"*64
  with self.assertRaisesRegex(ValueError,"source hash drift"):SUB.validate(SUB.DEFAULT_MANIFEST,bad,jobs)
 def test_pooling_updates_only_registered_endpoints(self):
  cell={"sizes":[7,9,11],"logical_errors":[5,7,9],"shots":[20]*3};fresh={"summaries":[{"q":.65,"p":.28,"L":L,"logical_errors":e,"shots":10} for L,e in [(7,2),(11,4)]]};job={"q":.65,"p":.28,"branch":"measured_endpoints_1000","sizes":[7,11]};r=ANA.analyze_counts(cell,fresh,job);self.assertEqual(r["logical_errors"],[7,7,13]);self.assertEqual(r["shots"],[30,20,30])
 def test_renderer_preserves_227(self):
  base=json.loads(REN.DEFAULT_BASE.read_text());rows=[]
  for q,p in sorted(REN.EXPECTED):rows.append({"q":q,"p":p,"pooling_kind":"synthetic","sizes":[7,9,11],"logical_errors":[1]*3,"shots":[10]*3,"classification":"unresolved","jeffreys_classification":"unresolved","uniform_prior_sensitivity":{"classification":"unresolved"}})
  merged,changes=REN.merged_analyses(base,{"analyses":rows});self.assertEqual(len(changes),4);unchanged=0
  for br,mr in zip(base["analyses"],merged):
   for b,m in zip(br["cells"],mr["cells"]):
    if (br["q"],b["p"]) not in REN.EXPECTED:self.assertEqual(b,m);unchanged+=1
  self.assertEqual(unchanged,227)
if __name__=="__main__":unittest.main()
