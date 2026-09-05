#!/usr/bin/env python3
"""Pool Phase B9 endpoint counts into the Phase B8 map frontier."""
from __future__ import annotations
import argparse,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
LAB_DIR=Path(__file__).resolve().parents[1];DEFAULT_MANIFEST=LAB_DIR/"phase-b9-honeycomb-measured-endpoints-manifest-2026-08-28.json";DEFAULT_AUDIT=LAB_DIR/"results/phase-b9-honeycomb-measured-endpoints-completion-audit-2026-08-28.json";DEFAULT_OUTPUT=LAB_DIR/"results/phase-b9-honeycomb-measured-endpoints-analysis-2026-08-28.json"
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def base_cell(phase_map,q,p):
 for row in phase_map["analyses"]:
  for cell in row["cells"]:
   if abs(float(row["q"])-q)<1e-12 and abs(float(cell["p"])-p)<1e-12:
    c=dict(cell);c.setdefault("sizes",[7,9,11] if len(c["shots"])==3 else None)
    if c["sizes"] is None:raise ValueError("cannot infer Phase B9 distance window")
    return c
 raise ValueError("missing Phase B9 base cell")
def analyze_counts(cell,fresh_payload,job,seed_offset=0):
 common=load("analyze_phase_b3_frontier_reuse.py","b9common");pooled={int(L):(int(e),int(n)) for L,e,n in zip(cell["sizes"],cell["logical_errors"],cell["shots"])};fresh=common.summary_counts(fresh_payload,job["q"],job["p"],job["sizes"])
 for L,(e,n) in fresh.items():oe,on=pooled[L];pooled[L]=(oe+e,on+n)
 sizes=sorted(pooled);errors=np.asarray([pooled[L][0] for L in sizes]);shots=np.asarray([pooled[L][1] for L in sizes]);fuzzy=load("analyze_phase_b1_bayesian_fuzzy_trend.py","b9fuzzy");primary=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),seed=999128+seed_offset);uniform=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),prior_alpha=1,prior_beta=1,seed=909128+seed_offset);classification=primary["classification"] if primary["classification"]==uniform["classification"] else "unresolved"
 return {"q":job["q"],"p":job["p"],"pooling_kind":job["branch"],"sizes":sizes,"logical_errors":errors.tolist(),"shots":shots.tolist(),**primary,"jeffreys_classification":primary["classification"],"classification":classification,"uniform_prior_sensitivity":uniform,"prior_sensitivity_status":"stable" if classification==primary["classification"] else "classification_changed_conservative_gray"}
def analyze(manifest_path,audit_path):
 common=load("analyze_phase_b3_frontier_reuse.py","b9hash");manifest=json.loads(Path(manifest_path).read_text());phase_map=json.loads((LAB_DIR/manifest["source_map"]["path"]).read_text());audit=json.loads(Path(audit_path).read_text())
 if audit["status"]!="data_complete_not_analyzed" or audit["jobs_complete"]!=4 or audit["raw_rows_observed"]!=8000:raise ValueError("Phase B9 audit incomplete")
 fresh={(r["q"],r["p"]):Path(r["summary"]) for r in audit["records"]};rows=[]
 for i,job in enumerate(manifest["jobs"]):rows.append(analyze_counts(base_cell(phase_map,job["q"],job["p"]),json.loads(fresh[(job["q"],job["p"])].read_text()),job,i))
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","manifest":{"path":str(manifest_path),"sha256":common.sha256(manifest_path)},"completion_audit":{"path":str(audit_path),"sha256":common.sha256(audit_path)},"analyses":rows,"cells_updated":4,"new_decodes":8000,"crossing_statistic_used":False,"grid_expanded":False,"evidence_boundary":"Exactly four Phase B8 frontier cells; no interpolation or asymptotic claim."}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);p.add_argument("--audit",type=Path,default=DEFAULT_AUDIT);p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();o=analyze(a.manifest,a.audit);load("submit_phase_b9_endpoints.py","b9write").atomic_json(a.output,o);print(json.dumps({"status":o["status"],"cells_updated":4},indent=2))
if __name__=="__main__":main()
