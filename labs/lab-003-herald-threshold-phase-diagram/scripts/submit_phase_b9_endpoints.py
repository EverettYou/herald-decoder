#!/usr/bin/env python3
"""Fail-closed dispatcher and preflight for Phase B9."""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,importlib.util,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
LAB_DIR=Path(__file__).resolve().parents[1];PROJECT_ROOT=LAB_DIR.parents[1];DEFAULT_MANIFEST=LAB_DIR/"phase-b9-honeycomb-measured-endpoints-manifest-2026-08-28.json";DEFAULT_PREFLIGHT=LAB_DIR/"results/phase-b9-honeycomb-measured-endpoints-preflight-2026-08-28.json";EXPECTED={(.30,.20,(5,13),2000),(.35,.20,(5,13),2000),(.55,.24,(5,13),2000),(.65,.28,(7,11),2000)}
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic_json(path,payload):path=Path(path);tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(payload,indent=2)+"\n");tmp.replace(path)
def load_runner():
 p=Path(__file__).with_name("run_phase2_scout.py");s=importlib.util.spec_from_file_location("b9runner",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def stem(job):return f"phase-b9-honeycomb-l{'-'.join(map(str,job['sizes']))}-q{int(round(100*job['q'])):03d}-p{int(round(100*job['p'])):03d}-2026-08-28"
def expand_jobs(manifest,project_root=PROJECT_ROOT,lab_dir=LAB_DIR):
 jobs=[]
 for row in manifest["jobs"]:
  artifact=stem(row);result=lab_dir/"results"/f"{artifact}.json";raw=lab_dir/"results"/f"{artifact}-raw.jsonl.gz";d=manifest["decoder"]
  command=[str(project_root/"run_research_python.sh"),str(lab_dir/"scripts/run_phase2_scout.py"),"--lattice","honeycomb","--q",str(row["q"]),"--p",str(row["p"]),"--campaign",manifest["campaign"],"--stem",artifact,"--shots-per-seed",str(manifest["shots_per_seed"]),"--sizes",*[str(x) for x in row["sizes"]],"--seeds",*[str(x) for x in manifest["new_seeds"]],"--max-iterations",str(d["max_iterations"]),"--update-schedule",d["update_schedule"],"--residual-priority-order",d["residual_priority_order"]]
  jobs.append({**row,"stem":artifact,"result":str(result),"raw":str(raw),"output_conflict":result.exists() or raw.exists(),"command":command})
 return jobs
def validate(manifest_path,manifest,jobs,reject_output_conflicts=True):
 if manifest["status"] not in {"registered","ready","data_complete","analyzed"} or manifest["launch_gate"] not in {"closed_implementation","ready","closed_data_complete"}:raise ValueError("invalid Phase B9 lifecycle")
 if {(j["q"],j["p"],tuple(j["sizes"]),j["expected_decodes"]) for j in jobs}!=EXPECTED or sum(j["expected_decodes"] for j in jobs)!=8000:raise ValueError("Phase B9 matrix/budget drift")
 if manifest["new_seeds"]!=[889001,889002,889003,889004,889005] or manifest["shots_per_seed"]!=200:raise ValueError("Phase B9 sampling drift")
 for field in ("selection_evidence","source_map","design_evidence"):
  path=LAB_DIR/manifest[field]["path"]
  if sha256(path)!=manifest[field]["sha256"]:raise ValueError(f"Phase B9 {field} hash drift")
 selection=json.loads((LAB_DIR/manifest["selection_evidence"]["path"]).read_text())
 for record in selection["seed_overlap_audit"]["records"]:
  if sha256(LAB_DIR/record["path"])!=record["sha256"]:raise ValueError("Phase B9 seed-inventory hash drift")
 if selection["seed_overlap_audit"]["overlaps"]:raise ValueError("Phase B9 seed overlap")
 if load_runner().source_hashes()!=manifest["required_source_hashes"]:raise ValueError("Phase B9 source hash drift")
 if reject_output_conflicts and any(j["output_conflict"] for j in jobs):raise ValueError("refusing Phase B9 output conflict")
def cli_shape_smoke(jobs):
 passed=[]
 for job in jobs:
  cmd=list(job["command"]);i=cmd.index("--shots-per-seed");cmd[i+1]="0";run=subprocess.run(cmd,cwd=PROJECT_ROOT,text=True,capture_output=True);transcript=run.stdout+run.stderr
  if run.returncode==0 or "seeds and shots-per-seed must be positive" not in transcript:raise ValueError(f"Phase B9 CLI smoke failed: {job['stem']}")
  passed.append({"stem":job["stem"],"sizes":job["sizes"],"reached_post_size_validation":True,"no_output_written":not Path(job["result"]).exists() and not Path(job["raw"]).exists()})
 return passed
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);p.add_argument("--preflight",type=Path,default=DEFAULT_PREFLIGHT);p.add_argument("--dry-run",action="store_true");a=p.parse_args();manifest=json.loads(a.manifest.read_text());jobs=expand_jobs(manifest);validate(a.manifest,manifest,jobs);gates={}
 for filename in ("audit_phase_b9_outputs.py","analyze_phase_b9_frontier.py","render_phase_b9_merged_map.py"):
  path=Path(__file__).with_name(filename)
  if not path.is_file():raise ValueError(f"missing Phase B9 gate: {filename}")
  gates[filename]=sha256(path)
 if a.dry_run:
  payload={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"preflight_passed_not_launched","manifest":{"path":str(a.manifest),"sha256":sha256(a.manifest)},"jobs":jobs,"job_count":4,"expected_new_decodes":8000,"workers_cap":4,"cli_shape_smoke":cli_shape_smoke(jobs),"gate_scripts":gates,"production_launched":False,"crossing_statistic_used":False,"grid_expanded":False};atomic_json(a.preflight,payload);print(json.dumps(payload,indent=2));return
 if manifest["status"]!="ready" or manifest["launch_gate"]!="ready":raise SystemExit("Phase B9 is not production-ready; use --dry-run")
 with concurrent.futures.ThreadPoolExecutor(max_workers=manifest["workers_cap"]) as pool:codes=list(pool.map(lambda j:subprocess.run(j["command"],cwd=PROJECT_ROOT).returncode,jobs))
 if any(codes):raise SystemExit(f"Phase B9 failures: {codes}")
if __name__=="__main__":main()
