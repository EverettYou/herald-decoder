#!/usr/bin/env python3
"""Pool Phase B6 counts with Phase B5 map payloads and run fuzzy trend."""

from __future__ import annotations
import argparse,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
LAB_DIR=Path(__file__).resolve().parents[1];DEFAULT_MANIFEST=LAB_DIR/"phase-b6-honeycomb-four-cell-frontier-manifest-2026-08-28.json";DEFAULT_AUDIT=LAB_DIR/"results/phase-b6-honeycomb-four-cell-frontier-completion-audit-2026-08-28.json";DEFAULT_OUTPUT=LAB_DIR/"results/phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json"
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def base_cell(phase_map,q,p):
 for row in phase_map["analyses"]:
  for cell in row["cells"]:
   if abs(float(row["q"])-q)<1e-12 and abs(float(cell["p"])-p)<1e-12:return cell
 raise ValueError("missing Phase B6 base cell")
def analyze_counts(cell,fresh_payload,job,seed_offset=0):
 common=load("analyze_phase_b3_frontier_reuse.py","b6common");q,p=job["q"],job["p"];pooled={int(L):(int(e),int(n)) for L,e,n in zip(cell["sizes"],cell["logical_errors"],cell["shots"])};fresh=common.summary_counts(fresh_payload,q,p,job["sizes"])
 for size,(new_errors,new_shots) in fresh.items():
  old_errors,old_shots=pooled.get(size,(0,0));pooled[size]=(old_errors+new_errors,old_shots+new_shots)
 sizes=sorted(pooled);errors=np.asarray([pooled[x][0] for x in sizes]);shots=np.asarray([pooled[x][1] for x in sizes]);fuzzy=load("analyze_phase_b1_bayesian_fuzzy_trend.py","b6fuzzy");primary=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),seed=886128+seed_offset);uniform=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),prior_alpha=1.0,prior_beta=1.0,seed=896128+seed_offset);classification=primary["classification"] if primary["classification"]==uniform["classification"] else "unresolved"
 return {"q":q,"p":p,"pooling_kind":job["branch"],"sizes":sizes,"logical_errors":errors.tolist(),"shots":shots.tolist(),**primary,"jeffreys_classification":primary["classification"],"classification":classification,"uniform_prior_sensitivity":uniform,"prior_sensitivity_status":"stable" if classification==primary["classification"] else "classification_changed_conservative_gray"}
def analyze(manifest_path,audit_path):
 common=load("analyze_phase_b3_frontier_reuse.py","b6hash");manifest=json.loads(Path(manifest_path).read_text());phase_map=json.loads((LAB_DIR/manifest["source_map"]["path"]).read_text());audit=json.loads(Path(audit_path).read_text())
 if audit["status"]!="data_complete_not_analyzed" or audit["jobs_complete"]!=4 or audit["raw_rows_observed"]!=14000:raise ValueError("Phase B6 audit incomplete")
 fresh={(r["q"],r["p"]):Path(r["summary"]) for r in audit["records"]};analyses=[]
 for offset,job in enumerate(manifest["jobs"]):analyses.append(analyze_counts(base_cell(phase_map,job["q"],job["p"]),json.loads(fresh[(job["q"],job["p"])].read_text()),job,offset))
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","manifest":{"path":str(manifest_path),"sha256":common.sha256(manifest_path)},"completion_audit":{"path":str(audit_path),"sha256":common.sha256(audit_path)},"analyses":analyses,"cells_updated":4,"new_decodes":14000,"crossing_statistic_used":False,"grid_expanded":False,"evidence_boundary":"Exactly four persistent red/green-adjacent gray cells; no interpolation or asymptotic boundary claim."}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);p.add_argument("--audit",type=Path,default=DEFAULT_AUDIT);p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();o=analyze(a.manifest,a.audit);load("submit_phase_b6_frontier.py","b6write").atomic_json(a.output,o);print(json.dumps({"status":o["status"],"cells_updated":4},indent=2))
if __name__=="__main__":main()
