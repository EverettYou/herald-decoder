#!/usr/bin/env python3
"""Analyze the heterogeneous five-cell Phase B5 matrix under Bayesian fuzzy trend."""

from __future__ import annotations
import argparse,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np

LAB_DIR=Path(__file__).resolve().parents[1];DEFAULT_MANIFEST=LAB_DIR/"phase-b5-honeycomb-persistent-frontier-manifest-2026-08-28.json";DEFAULT_AUDIT=LAB_DIR/"results/phase-b5-honeycomb-persistent-frontier-completion-audit-2026-08-28.json";DEFAULT_OUTPUT=LAB_DIR/"results/phase-b5-honeycomb-persistent-frontier-analysis-2026-08-28.json"
def load(filename,name):
 p=Path(__file__).with_name(filename);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def analyze_counts(base_payload,adaptive_payload,fresh_payload,branch,q,p,seed_offset=0):
 common=load("analyze_phase_b3_frontier_reuse.py","b5common")
 base=common.summary_counts(base_payload,q,p,[7,9,11])
 if branch=="distance_extension_l5":
  adaptive=common.summary_counts(adaptive_payload,q,p,[11,13]);pooled=common.pool_counts("distance_limited",base,adaptive);fresh=common.summary_counts(fresh_payload,q,p,[5]);pooled={5:fresh[5],**pooled}
 elif branch=="independent_shots":
  adaptive=common.summary_counts(adaptive_payload,q,p,[7,9,11]);pooled=common.pool_counts("new_independent_shots",base,adaptive);fresh=common.summary_counts(fresh_payload,q,p,[7,9,11]);pooled=common.pool_counts("new_independent_shots",pooled,fresh)
 else:raise ValueError("unknown Phase B5 branch")
 sizes=sorted(pooled);errors=np.asarray([pooled[x][0] for x in sizes]);shots=np.asarray([pooled[x][1] for x in sizes]);fuzzy=load("analyze_phase_b1_bayesian_fuzzy_trend.py","b5fuzzy");primary=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),seed=885128+seed_offset);uniform=fuzzy.posterior_fuzzy_linear_trend(errors,shots,np.asarray(sizes),prior_alpha=1.0,prior_beta=1.0,seed=895128+seed_offset);classification=primary["classification"] if primary["classification"]==uniform["classification"] else "unresolved"
 return {"q":q,"p":p,"pooling_kind":branch,"sizes":sizes,"logical_errors":errors.tolist(),"shots":shots.tolist(),**primary,"jeffreys_classification":primary["classification"],"classification":classification,"uniform_prior_sensitivity":uniform,"prior_sensitivity_status":"stable" if classification==primary["classification"] else "classification_changed_conservative_gray"}
def analyze(manifest_path,audit_path):
 common=load("analyze_phase_b3_frontier_reuse.py","b5hash");manifest=json.loads(Path(manifest_path).read_text());selection=json.loads((LAB_DIR/manifest["selection_evidence"]["path"]).read_text());audit=json.loads(Path(audit_path).read_text())
 if audit["status"]!="data_complete_not_analyzed" or audit["jobs_complete"]!=5:raise ValueError("Phase B5 audit incomplete")
 fresh={(r["q"],r["p"]):Path(r["summary"]) for r in audit["records"]};analyses=[]
 for offset,row in enumerate(selection["prior_adaptive_evidence"]):
  key=(row["q"],row["p"]);job=next(j for j in selection["new_jobs"] if (j["q"],j["p"])==key);analyses.append(analyze_counts(json.loads((LAB_DIR/row["base_path"]).read_text()),json.loads((LAB_DIR/row["adaptive_path"]).read_text()),json.loads(fresh[key].read_text()),job["branch"],*key,seed_offset=offset))
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","manifest":{"path":str(manifest_path),"sha256":common.sha256(manifest_path)},"completion_audit":{"path":str(audit_path),"sha256":common.sha256(audit_path)},"analyses":analyses,"cells_updated":5,"new_decodes":7000,"crossing_statistic_used":False,"grid_expanded":False,"evidence_boundary":"Exactly five persistent red/green-adjacent gray cells; no interpolation or asymptotic boundary claim."}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);p.add_argument("--audit",type=Path,default=DEFAULT_AUDIT);p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();o=analyze(a.manifest,a.audit);load("submit_phase_b5_frontier.py","b5write").atomic_json(a.output,o);print(json.dumps({"status":o["status"],"cells_updated":5},indent=2))
if __name__=="__main__":main()
