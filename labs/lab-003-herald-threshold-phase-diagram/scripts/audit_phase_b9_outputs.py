#!/usr/bin/env python3
"""Audit Phase B9 output pairs before inference."""
from __future__ import annotations
import argparse,gzip,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
LAB_DIR=Path(__file__).resolve().parents[1];DEFAULT_MANIFEST=LAB_DIR/"phase-b9-honeycomb-measured-endpoints-manifest-2026-08-28.json";DEFAULT_OUTPUT=LAB_DIR/"results/phase-b9-honeycomb-measured-endpoints-completion-audit-2026-08-28.json"
def load_submit():
 p=Path(__file__).with_name("submit_phase_b9_endpoints.py");s=importlib.util.spec_from_file_location("b9submit",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha256(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""):h.update(c)
 return h.hexdigest()
def audit_pair(manifest,payload,raw_path,job):
 if payload["campaign"]!=manifest["campaign"] or payload["lattice"]!="honeycomb" or float(payload["q"])!=job["q"] or list(map(float,payload["p_grid"]))!=[job["p"]] or list(map(int,payload["sizes"]))!=job["sizes"]:raise ValueError("Phase B9 output coordinate mismatch")
 if payload["seeds"]!=manifest["new_seeds"] or payload["decoder"]!=manifest["decoder"] or payload["source_hashes"]!=manifest["required_source_hashes"] or not payload["source_stability"]["start_equals_end"]:raise ValueError("Phase B9 sampling/source mismatch")
 expected=job["expected_decodes"]
 if payload["raw_records"]["records"]!=expected or payload["raw_records"]["sha256"]!=sha256(raw_path):raise ValueError("Phase B9 raw metadata mismatch")
 rows=faithful=0
 with gzip.open(raw_path,"rt",encoding="utf-8") as f:
  for line in f:
   r=json.loads(line)
   if r["campaign"]!=manifest["campaign"] or float(r["q"])!=job["q"] or float(r["p"])!=job["p"] or int(r["L"]) not in job["sizes"] or int(r["seed"]) not in manifest["new_seeds"]:raise ValueError("Phase B9 raw coordinate mismatch")
   rows+=1;faithful+=bool(r["syndrome_faithful"])
 if rows!=expected or faithful!=rows or not payload["syndrome_fidelity"]["all_faithful"]:raise ValueError("Phase B9 row/syndrome mismatch")
 return rows,faithful
def audit(manifest_path):
 submit=load_submit();manifest=json.loads(Path(manifest_path).read_text());jobs=submit.expand_jobs(manifest);submit.validate(manifest_path,manifest,jobs,reject_output_conflicts=False);records=[];rows=faithful=0
 for job in jobs:
  result,raw=Path(job["result"]),Path(job["raw"])
  if not result.is_file() or not raw.is_file():raise ValueError("missing Phase B9 output pair")
  n,f=audit_pair(manifest,json.loads(result.read_text()),raw,job);rows+=n;faithful+=f;records.append({"q":job["q"],"p":job["p"],"sizes":job["sizes"],"summary":str(result),"summary_sha256":sha256(result),"raw":str(raw),"raw_sha256":sha256(raw),"rows":n,"syndrome_faithful_rows":f})
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"data_complete_not_analyzed","manifest":{"path":str(manifest_path),"sha256":sha256(manifest_path)},"jobs_expected":4,"jobs_complete":4,"raw_rows_expected":8000,"raw_rows_observed":rows,"syndrome_faithful_rows":faithful,"records":records,"scientific_analysis_performed":False,"crossing_statistic_used":False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();o=audit(a.manifest);load_submit().atomic_json(a.output,o);print(json.dumps({k:o[k] for k in ("status","jobs_complete","raw_rows_observed")},indent=2))
if __name__=="__main__":main()
