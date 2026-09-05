#!/usr/bin/env python3
"""Run bounded matched X-only D4 O0/O2/BP flux pilot."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_honeycomb import paper_periodic_honeycomb
from d4_matching import edge_chain_boundary, published_herald_weights, syndrome_only_weights
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import decode_bp_policy, decode_matching_policy, trajectory_seeds, policy_summary, paired_summary

manifest_path = LAB_DIR / "r6u-d4-native-three-policy-curve-manifest-2026-08-30.json"
output_path = LAB_DIR / "results/r6u-d4-native-three-policy-curve-2026-08-30.json"
manifest = json.loads(manifest_path.read_text())
if manifest["status"] != "registered": raise RuntimeError("R6U not registered")
scope = manifest["scope"]; rows=[]
for size in scope["sizes"]:
  lattice=paper_periodic_honeycomb(int(size))
  for p in scope["physical_error_rates"]:
    for index in range(int(scope["histories_per_cell"])):
      ps, os = trajectory_seeds(int(scope["seed_salt"]),int(size),float(p),index)
      physical=(np.random.default_rng(ps).random(lattice.edge_count)<float(p)).astype(np.uint8)
      obs=observation_from_error_edges(lattice,physical,seed=os)
      row={"size":int(size),"p_X":float(p),"trajectory_index":index,"status":"nonterminal","policies":{}}
      if obs.status != "sampled" or obs.charge_outcomes is None:
        row["status"]="terminal_physical_winding"; rows.append(row); continue
      row["policies"]["O0_unit_weight_MWPM"]=decode_matching_policy(lattice,physical,syndrome_only_weights(lattice))
      row["policies"]["O2_published_herald_weight_MWPM"]=decode_matching_policy(lattice,physical,published_herald_weights(lattice,np.asarray(obs.charge_outcomes,dtype=np.int64)))
      row["policies"]["R6D_local_BP_posterior_LLR_MWPM"]=decode_bp_policy(lattice,physical,obs,float(p),scope["bp_defaults"])
      rows.append(row)
policies=scope["flux_policies"]
cells=[]
for size in scope["sizes"]:
  for p in scope["physical_error_rates"]:
    cell=[r for r in rows if r["size"]==size and r["p_X"]==p]
    cells.append({"size":size,"p_X":p,"summaries":{x:policy_summary(cell,x) for x in policies},"pairings":[paired_summary(cell,"O0_unit_weight_MWPM","O2_published_herald_weight_MWPM"),paired_summary(cell,"O0_unit_weight_MWPM","R6D_local_BP_posterior_LLR_MWPM"),paired_summary(cell,"O2_published_herald_weight_MWPM","R6D_local_BP_posterior_LLR_MWPM")]})
payload={"schema_version":1,"status":"completed_x_only_flux_pilot","generated_at":datetime.now(timezone.utc).isoformat(),"manifest":manifest_path.name,"scope":scope,"cells":cells,"rows":rows,"claim_boundary":manifest["claim_boundary"]}
output_path.write_text(json.dumps(payload,indent=2)+"\n")
print(json.dumps({"output":str(output_path),"cells":len(cells),"rows":len(rows)}))
