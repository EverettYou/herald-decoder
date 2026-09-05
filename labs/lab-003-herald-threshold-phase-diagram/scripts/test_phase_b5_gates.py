import copy,gzip,importlib.util,json,tempfile,unittest
from pathlib import Path
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
submit=load("submit_phase_b5_frontier.py","b5submit_test");audit=load("audit_phase_b5_outputs.py","b5audit_test");analyze=load("analyze_phase_b5_frontier.py","b5analyze_test");render=load("render_phase_b5_merged_map.py","b5render_test")
def summary(q,p,rows):return {"summaries":[{"q":q,"p":p,"L":L,"logical_errors":e,"shots":n} for L,e,n in rows]}
class PhaseB5GateTests(unittest.TestCase):
 def test_dispatcher_matrix_budget_and_source_drift_gate(self):
  manifest=json.loads(submit.DEFAULT_MANIFEST.read_text())
  with tempfile.TemporaryDirectory() as t:jobs=submit.expand_jobs(manifest,project_root=Path(t),lab_dir=Path(t)/"lab")
  submit.validate(submit.DEFAULT_MANIFEST,manifest,jobs);self.assertEqual(len(jobs),5);self.assertEqual(sum(j["expected_decodes"] for j in jobs),7000)
  self.assertTrue(all("run_phase_b5_single_size.py" in j["command"][1] for j in jobs if j["sizes"]==[5]))
  self.assertIn("run_phase2_scout.py",next(j for j in jobs if j["sizes"]==[7,9,11])["command"][1])
  bad=copy.deepcopy(manifest);bad["required_source_hashes"]["runner"]="0"*64
  with self.assertRaisesRegex(ValueError,"source hash drift"):submit.validate(submit.DEFAULT_MANIFEST,bad,jobs)
 def test_completion_audit_checks_registered_rows(self):
  manifest=json.loads(submit.DEFAULT_MANIFEST.read_text());job=next(j for j in manifest["jobs"] if j["q"]==0.3)
  with tempfile.TemporaryDirectory() as t:
   raw=Path(t)/"r.gz"
   with gzip.open(raw,"wt",encoding="utf-8") as f:
    for i in range(1000):f.write(json.dumps({"campaign":manifest["campaign"],"q":0.3,"p":0.2,"L":5,"seed":manifest["new_seeds"][i%5],"syndrome_faithful":True})+"\n")
   payload={"campaign":manifest["campaign"],"lattice":"honeycomb","q":0.3,"p_grid":[0.2],"sizes":[5],"seeds":manifest["new_seeds"],"decoder":manifest["decoder"],"source_hashes":manifest["required_source_hashes"],"source_stability":{"start_equals_end":True},"execution_wrapper":{"sha256":manifest["required_execution_hashes"]["single_size_wrapper"],"source_stable":True},"raw_records":{"records":1000,"sha256":audit.sha256(raw)},"syndrome_fidelity":{"all_faithful":True}}
   self.assertEqual(audit.audit_pair(manifest,payload,raw,job),(1000,1000))
 def test_both_pooling_branches_use_every_registered_source(self):
  distance=analyze.analyze_counts(summary(.3,.2,[(7,10,100),(9,20,100),(11,30,100)]),summary(.3,.2,[(11,3,10),(13,4,10)]),summary(.3,.2,[(5,5,10)]),"distance_extension_l5",.3,.2)
  self.assertEqual(distance["sizes"],[5,7,9,11,13]);self.assertEqual(distance["logical_errors"],[5,10,20,33,4]);self.assertEqual(distance["shots"],[10,100,100,110,10])
  shots=analyze.analyze_counts(summary(.55,.24,[(7,10,100),(9,20,100),(11,30,100)]),summary(.55,.24,[(7,1,10),(9,2,10),(11,3,10)]),summary(.55,.24,[(7,4,20),(9,5,20),(11,6,20)]),"independent_shots",.55,.24)
  self.assertEqual(shots["logical_errors"],[15,27,39]);self.assertEqual(shots["shots"],[130,130,130])
 def test_renderer_updates_five_and_preserves_226(self):
  base=json.loads(render.DEFAULT_BASE.read_text());rows=[]
  for q,p in sorted(render.EXPECTED):rows.append({"q":q,"p":p,"pooling_kind":"synthetic","sizes":[7,9,11],"logical_errors":[1,2,3],"shots":[10,10,10],"classification":"unresolved","jeffreys_classification":"unresolved","uniform_prior_sensitivity":{"classification":"unresolved"}})
  merged,changes=render.merged_analyses(base,{"analyses":rows});self.assertEqual(len(changes),5);unchanged=0
  for br,ar in zip(base["analyses"],merged):
   for b,a in zip(br["cells"],ar["cells"]):
    if (br["q"],b["p"]) not in render.EXPECTED:self.assertEqual(b,a);unchanged+=1
  self.assertEqual(unchanged,226)
if __name__=="__main__":unittest.main()
