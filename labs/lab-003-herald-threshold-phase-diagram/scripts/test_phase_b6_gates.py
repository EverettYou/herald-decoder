import copy,gzip,importlib.util,json,tempfile,unittest
from pathlib import Path
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
submit=load("submit_phase_b6_frontier.py","b6submit_test");audit=load("audit_phase_b6_outputs.py","b6audit_test");analyze=load("analyze_phase_b6_frontier.py","b6analyze_test");render=load("render_phase_b6_merged_map.py","b6render_test")
def fresh(q,p,rows):return {"summaries":[{"q":q,"p":p,"L":L,"logical_errors":e,"shots":n} for L,e,n in rows]}
class PhaseB6GateTests(unittest.TestCase):
 def test_dispatcher_matrix_budget_and_source_drift_gate(self):
  manifest=json.loads(submit.DEFAULT_MANIFEST.read_text())
  with tempfile.TemporaryDirectory() as t:jobs=submit.expand_jobs(manifest,project_root=Path(t),lab_dir=Path(t)/"lab")
  submit.validate(submit.DEFAULT_MANIFEST,manifest,jobs);self.assertEqual(len(jobs),4);self.assertEqual(sum(j["expected_decodes"] for j in jobs),14000);self.assertTrue(all(len(j["sizes"])>=2 for j in jobs))
  bad=copy.deepcopy(manifest);bad["required_source_hashes"]["runner"]="0"*64
  with self.assertRaisesRegex(ValueError,"source hash drift"):submit.validate(submit.DEFAULT_MANIFEST,bad,jobs)
 def test_completion_audit_checks_registered_rows(self):
  manifest=json.loads(submit.DEFAULT_MANIFEST.read_text());job=next(j for j in manifest["jobs"] if j["q"]==.55)
  with tempfile.TemporaryDirectory() as t:
   raw=Path(t)/"r.gz"
   with gzip.open(raw,"wt",encoding="utf-8") as f:
    for i in range(2000):f.write(json.dumps({"campaign":manifest["campaign"],"q":.55,"p":.24,"L":job["sizes"][i%2],"seed":manifest["new_seeds"][i%5],"syndrome_faithful":True})+"\n")
   payload={"campaign":manifest["campaign"],"lattice":"honeycomb","q":.55,"p_grid":[.24],"sizes":[5,13],"seeds":manifest["new_seeds"],"decoder":manifest["decoder"],"source_hashes":manifest["required_source_hashes"],"source_stability":{"start_equals_end":True},"raw_records":{"records":2000,"sha256":audit.sha256(raw)},"syndrome_fidelity":{"all_faithful":True}}
   self.assertEqual(audit.audit_pair(manifest,payload,raw,job),(2000,2000))
 def test_both_pooling_branches_use_map_counts_and_fresh(self):
  base={"sizes":[5,7,9,11,13],"logical_errors":[5,7,9,11,13],"shots":[20]*5};job={"q":.3,"p":.2,"branch":"rebalance_to_2000_shots","sizes":[5,7,9,13]};r=analyze.analyze_counts(base,fresh(.3,.2,[(5,1,10),(7,2,10),(9,3,10),(13,4,10)]),job);self.assertEqual(r["logical_errors"],[6,9,12,11,17]);self.assertEqual(r["shots"],[30,30,30,20,30])
  base={"sizes":[7,9,11],"logical_errors":[7,9,11],"shots":[30]*3};job={"q":.55,"p":.24,"branch":"endpoint_extension_l5_l13","sizes":[5,13]};r=analyze.analyze_counts(base,fresh(.55,.24,[(5,2,10),(13,4,10)]),job);self.assertEqual(r["sizes"],[5,7,9,11,13]);self.assertEqual(r["logical_errors"],[2,7,9,11,4])
 def test_renderer_updates_four_and_preserves_227(self):
  base=json.loads(render.DEFAULT_BASE.read_text());rows=[]
  for q,p in sorted(render.EXPECTED):rows.append({"q":q,"p":p,"pooling_kind":"synthetic","sizes":[5,7,9,11,13],"logical_errors":[1]*5,"shots":[10]*5,"classification":"unresolved","jeffreys_classification":"unresolved","uniform_prior_sensitivity":{"classification":"unresolved"}})
  merged,changes=render.merged_analyses(base,{"analyses":rows});self.assertEqual(len(changes),4);unchanged=0
  for br,ar in zip(base["analyses"],merged):
   for b,a in zip(br["cells"],ar["cells"]):
    if (br["q"],b["p"]) not in render.EXPECTED:self.assertEqual(b,a);unchanged+=1
  self.assertEqual(unchanged,227)
if __name__=="__main__":unittest.main()
