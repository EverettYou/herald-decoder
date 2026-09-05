#!/usr/bin/env python3
"""Matched paper-L D4 unit-weight-MWPM flux scan in its own threshold range."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from d4_honeycomb import paper_periodic_honeycomb
from d4_matching import syndrome_only_weights
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import decode_matching_policy, policy_summary, trajectory_seeds

LAB=Path(__file__).resolve().parents[1]; OUT=LAB/'results/l004-2-unit-weight-flux-threshold-2026-09-01.json'; CHECK=LAB/'results/l004-2-unit-weight-flux-threshold-2026-09-01.checkpoint.json'
SIZES=(5,7,9,11,13); RATES=(.14,.15,.16,.17,.18); N=1000; POLICY='O0_unit_weight_MWPM'; SALT=68432

def payload(rows,status):
 cells=[]
 for L in SIZES:
  for p in RATES:
   rs=[r for r in rows if r['size']==L and r['p_X']==p]
   if len(rs)==N: cells.append({'size':L,'p_X':p,'attempted_histories':N,'summaries':{POLICY:policy_summary(rs,POLICY)}})
 return {'schema_version':1,'status':status,'generated_at':datetime.now(timezone.utc).isoformat(),'scope':{'decoder':'Unit-weight MWPM','score':'paper-unconditional first-stage flux LER','noise':'D4 red X only; p_Z=0','sizes':SIZES,'rates':RATES,'attempts_per_cell':N},'cells':cells,'rows':rows,'claim_boundary':'Dedicated unit-weight-MWPM finite-size data around its published 0.15860 threshold; not a BP comparison.'}

def write(rows,status):
 q=CHECK.with_suffix('.tmp'); q.write_text(json.dumps(payload(rows,status),indent=2)+'\n'); q.replace(CHECK)

def main():
 rows=[]
 if CHECK.exists(): rows=json.loads(CHECK.read_text())['rows']
 for L in SIZES:
  for p in RATES:
   prior=[r for r in rows if r['size']==L and r['p_X']==p]
   for index in range(len(prior),N):
    lattice=paper_periodic_honeycomb(L); ps,os=trajectory_seeds(SALT,L,p,index); physical=(np.random.default_rng(ps).random(lattice.edge_count)<p).astype(np.uint8); obs=observation_from_error_edges(lattice,physical,seed=os)
    row={'size':L,'p_X':p,'trajectory_index':index,'physical_seed':ps,'observation_seed':os,'physical_error_edges':[int(x) for x in np.flatnonzero(physical)],'observation_status':obs.status,'policies':{}}
    if obs.status=='logical_failure': row['status']='terminal_physical_winding'
    else:
     row['status']='nonterminal'; row['policies'][POLICY]=decode_matching_policy(lattice,physical,syndrome_only_weights(lattice))
    rows.append(row)
    if (index+1)%100==0: print(json.dumps({'L':L,'p_X':p,'completed':index+1}),flush=True)
   write(rows,'running')
 OUT.write_text(json.dumps(payload(rows,'completed'),indent=2)+'\n')
 print(json.dumps({'output':str(OUT),'cells':len(payload(rows,'completed')['cells'])}))
if __name__=='__main__': main()
