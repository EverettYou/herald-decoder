#!/usr/bin/env python3
"""Update exactly four frontier payloads and render the Phase B6 map."""

from __future__ import annotations
import argparse,copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
LAB_DIR=Path(__file__).resolve().parents[1];DEFAULT_BASE=LAB_DIR/"results/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json";DEFAULT_UPDATE=LAB_DIR/"results/phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json";DEFAULT_OUTPUT=LAB_DIR/"results/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json";DEFAULT_FIGURE=LAB_DIR/"figures/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png";EXPECTED={(.30,.20),(.35,.20),(.55,.24),(.60,.28)}
def load_b2():
 p=Path(__file__).with_name("render_phase_b2_merged_map.py");s=importlib.util.spec_from_file_location("b6renderbase",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def merged_analyses(base,update):
 rows={(float(r["q"]),float(r["p"])):r for r in update["analyses"]}
 if set(rows)!=EXPECTED or len(update["analyses"])!=4:raise ValueError("Phase B6 analysis must contain exactly four registered cells")
 merged=copy.deepcopy(base["analyses"]);changes=[]
 for qrow in merged:
  for i,cell in enumerate(qrow["cells"]):
   key=(float(qrow["q"]),float(cell["p"]));replacement=rows.get(key)
   if replacement is None:continue
   if cell["classification"]!="unresolved":raise ValueError("Phase B6 target was not gray")
   updated=copy.deepcopy(cell)
   for field,value in replacement.items():
    if field not in {"q","p"}:updated[field]=copy.deepcopy(value)
   updated["p"]=key[1]
   if updated["classification"]!="unresolved":updated["gray_measurement_route"]=None
   updated["phase_b6_update"]={"distance_window":replacement["sizes"],"pooling_kind":replacement["pooling_kind"],"shots_per_distance":replacement["shots"],"source":"phase_b6_four_cell_frontier_analysis"};qrow["cells"][i]=updated;changes.append({"q":key[0],"p":key[1],"before":cell["classification"],"after":updated["classification"],"sizes":replacement["sizes"],"logical_errors":replacement["logical_errors"],"shots":replacement["shots"]})
 if len(changes)!=4:raise ValueError("expected exactly four Phase B6 payload updates")
 return merged,sorted(changes,key=lambda r:(r["q"],r["p"]))
def build(base_path,update_path,figure_path):
 renderer=load_b2();base=json.loads(Path(base_path).read_text());update=json.loads(Path(update_path).read_text());analyses,changes=merged_analyses(base,update);counts={x:sum(c["classification"]==x for r in analyses for c in r["cells"]) for x in ("decodable","undecodable","unresolved")}
 if sum(counts.values())!=231:raise ValueError("Phase B6 count drift")
 renderer.plot_map(analyses,[float(c["p"]) for c in base["analyses"][0]["cells"]],figure_path,phase_label="Phase B6")
 return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"status":"complete","definition":base["definition"],"classification_threshold":base["classification_threshold"],"prior_sensitivity_gate":base["prior_sensitivity_gate"],"counts":counts,"analyses":analyses,"changes":changes,"unchanged_cell_count":227,"provenance":{"base_map":{"path":str(base_path),"sha256":renderer.sha256(base_path)},"phase_b6_analysis":{"path":str(update_path),"sha256":renderer.sha256(update_path)},"renderer":{"path":str(Path(__file__).resolve()),"sha256":renderer.sha256(Path(__file__).resolve())}},"figure":str(figure_path),"crossing_statistic_used":False,"grid_expanded":False,"evidence_boundary":"Phase B5 map plus exactly four Phase B6 payload updates; adaptive finite-window evidence, not an asymptotic boundary."}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--base",type=Path,default=DEFAULT_BASE);p.add_argument("--update",type=Path,default=DEFAULT_UPDATE);p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);p.add_argument("--figure",type=Path,default=DEFAULT_FIGURE);a=p.parse_args();o=build(a.base,a.update,a.figure);load_b2().atomic_json(a.output,o);print(json.dumps({"counts":o["counts"],"changes":o["changes"]},indent=2))
if __name__=="__main__":main()
