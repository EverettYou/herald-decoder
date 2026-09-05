#!/usr/bin/env python3
"""Register the Phase B8 raise-minimum four-cell frontier matrix."""

from __future__ import annotations
import argparse,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path

LAB_DIR=Path(__file__).resolve().parents[1]
DEFAULT_MAP=LAB_DIR/"results/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_DESIGN=LAB_DIR/"results/phase-b7-honeycomb-frontier-posterior-predictive-design-2026-08-28.json"
DEFAULT_SELECTION=LAB_DIR/"results/phase-b8-honeycomb-raise-minimum-selection-2026-08-28.json"
DEFAULT_MANIFEST=LAB_DIR/"phase-b8-honeycomb-raise-minimum-manifest-2026-08-28.json"
EXPECTED={(.30,.20),(.35,.20),(.55,.24),(.65,.28)};NEW_SEEDS=[878001,878002,878003,878004,878005];CAMPAIGN="phase-b8-honeycomb-raise-minimum-2026-08-28"
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic_json(path,payload):
 path=Path(path);tmp=path.with_name(f".{path.name}.tmp-{os.getpid()}");tmp.write_text(json.dumps(payload,indent=2)+"\n");os.replace(tmp,path)
def seed_audit():
 records=[];overlaps=[]
 for path in sorted((LAB_DIR/"results").glob("*.json")):
  try:payload=json.loads(path.read_text())
  except (json.JSONDecodeError,UnicodeDecodeError):continue
  seeds=payload.get("seeds")
  if not isinstance(seeds,list) or payload.get("campaign")==CAMPAIGN:continue
  hit=sorted(set(map(int,seeds))&set(NEW_SEEDS));records.append({"path":str(path.relative_to(LAB_DIR)),"sha256":sha256(path)})
  if hit:overlaps.append({"path":str(path.relative_to(LAB_DIR)),"seeds":hit})
 if overlaps:raise ValueError(f"Phase B8 seed overlap: {overlaps}")
 return {"planned_seeds":NEW_SEEDS,"summaries_checked":len(records),"records":records,"overlaps":[]}
def build_selection(map_path,design_path):
 design=json.loads(Path(design_path).read_text());frontier={(r["q"],r["p"]) for r in design["frontier_candidates"]}
 if frontier!=EXPECTED:raise ValueError("Phase B8 frontier drift")
 chosen=next(r for r in design["designs"] if r["name"]=="raise_minimum_by_1000")
 if chosen["total_additional_decodes"]!=11000:raise ValueError("Phase B8 design budget drift")
 jobs=[]
 for cell in chosen["cells"]:
  sizes=[int(L) for L,m in zip(cell["sizes"],cell["additional_shots"]) if int(m)>0];shots={int(m) for m in cell["additional_shots"] if int(m)>0}
  if shots!={1000}:raise ValueError("Phase B8 additions drift")
  jobs.append({"branch":"raise_minimum_by_1000","q":cell["q"],"p":cell["p"],"sizes":sizes,"expected_decodes":1000*len(sizes),"current_sizes":cell["sizes"],"current_shots":cell["current_shots"],"posterior_predictive_probability_resolved":cell["posterior_predictive_probability_resolved"],"posterior_predictive_probability_false_direction_resolution":cell["posterior_predictive_probability_false_direction_resolution"]})
 if {(j["q"],j["p"]) for j in jobs}!=EXPECTED or sum(j["expected_decodes"] for j in jobs)!=11000:raise ValueError("Phase B8 job matrix drift")
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","source_map":{"path":str(Path(map_path).relative_to(LAB_DIR)),"sha256":sha256(map_path)},"design_evidence":{"path":str(Path(design_path).relative_to(LAB_DIR)),"sha256":sha256(design_path)},"design_rule":"Cover every exact Phase B7 frontier branch with the descriptive-efficiency-leading raise_minimum_by_1000 design; preserve the low predicted yield.","jobs":sorted(jobs,key=lambda r:(r["q"],r["p"])),"job_count":4,"expected_new_decodes":11000,"expected_resolved_cells":chosen["expected_resolved_cells"],"expected_false_direction_resolutions":chosen["expected_false_direction_resolutions"],"seed_overlap_audit":seed_audit(),"claim_boundary":"Registration only; exact four-cell frontier, currently least-sampled distances only, fixed 0.90 gate, no adaptive expansion or asymptotic claim."}
def build_manifest(selection_path,selection):
 base=json.loads((LAB_DIR/"results/phase2-residual80-honeycomb-q030-discovery-1000-2026-08-28.json").read_text())
 return {"schema_version":1,"status":"registered","campaign":CAMPAIGN,"purpose":"Run the smallest fixed design covering every exact Phase B7 frontier branch.","selection_evidence":{"path":str(Path(selection_path).relative_to(LAB_DIR)),"sha256":sha256(selection_path)},"source_map":selection["source_map"],"design_evidence":selection["design_evidence"],"lattice":"honeycomb","new_seeds":NEW_SEEDS,"shots_per_seed":200,"jobs":[{k:r[k] for k in ("branch","q","p","sizes","expected_decodes")} for r in selection["jobs"]],"job_count":4,"workers_cap":4,"expected_new_decodes":11000,"forecast":{"expected_resolved_cells":selection["expected_resolved_cells"],"expected_false_direction_resolutions":selection["expected_false_direction_resolutions"]},"decoder":base["decoder"],"required_source_hashes":base["source_hashes"],"analysis":{"primary":"Bayesian posterior OLS linear-projection slope against code distance","classification_threshold":.9,"prior_sensitivity":"Jeffreys primary and uniform sensitivity","pooling":"Pool fresh counts only with the corresponding Phase B7 map-count vector."},"preflight_gate":"Implement/test non-overwriting dispatch, exact completion, pooled analysis and four-payload rendering before launch.","stop_rule":"Stop after four jobs and 11000 decodes; no outcome-adaptive branch, size, cell, coordinate, lattice or gate change.","launch_gate":"closed_implementation"}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--phase-map",type=Path,default=DEFAULT_MAP);p.add_argument("--design",type=Path,default=DEFAULT_DESIGN);p.add_argument("--selection",type=Path,default=DEFAULT_SELECTION);p.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST);a=p.parse_args();s=build_selection(a.phase_map,a.design);atomic_json(a.selection,s);atomic_json(a.manifest,build_manifest(a.selection,s));print(json.dumps({k:s[k] for k in ("job_count","expected_new_decodes","expected_resolved_cells")},indent=2))
if __name__=="__main__":main()
