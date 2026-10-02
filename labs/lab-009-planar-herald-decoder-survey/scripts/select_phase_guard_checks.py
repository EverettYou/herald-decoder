"""Extend clipped crossing windows instead of forcing an absent root."""
from pathlib import Path
import json,sys
import numpy as np
from analyze_phase_sweep import read_rows,crossings,crossing_risk
LAB=Path(__file__).resolve().parents[1]

def main():
    rows=read_rows();table={(r['L'],r['p'],r['q']):r for r in rows};pilot=json.loads((LAB/'results/phase-broad-grid.json').read_text())['rows'];roots=crossings(pilot,8,16)+crossings(pilot,16,24);jobs={};reasons=[]
    for root in roots:
        q=root['q'];lo,hi=root['p_bracket'];direction=1 if root['orientation']=='low-p entry'else -1
        for p,side in [(lo,-1),(hi,1)]:
            if (24,p,q)not in table or(32,p,q)not in table:continue
            a,b=table[24,p,q],table[32,p,q];delta=crossing_risk(b)-crossing_risk(a)
            if direction*side*delta>0:continue
            # Wrong sign at a proposed window edge calls for a guard, not a
            # fabricated threshold. New guard cells use independent streams.
            guard=round(p+side*.025,6)
            if not 0<guard<1:continue
            for L in [16,24,32]:
                if table.get((L,guard,q),{}).get('n',0)<768:jobs[L,guard,q]=768
            reasons.append({'q':q,'pilot_bracket':[lo,hi],'orientation':root['orientation'],'edge':p,'edge_difference':delta,'new_guard':guard})
    # Resolve the narrow closing region without pinning its peak at p=1/2.
    for q in [.85,.86,.875]:
        for p in [.475,.525,.575]:
            for L in [16,24,32]:
                if table.get((L,p,q),{}).get('n',0)<768:jobs[L,p,q]=768
    for q in [.85,.86,.875]:
        for p in [.5,.525,.55]:
            for L in [16,24,32]:
                if table.get((L,p,q),{}).get('n',0)<1536:jobs[L,p,q]=1536
    result={'status':'registered','jobs':[[L,p,q,n]for (L,p,q),n in sorted(jobs.items())],'reasons':reasons,'closing_checks':'Independent half-step p cells on both sides of half; no forced closure position','selection_scope':'Largest-pair wrong-sign bracket guards, half-step closing checks and 1536-record checks at p=.5,.525,.55 near closure. Stop after this bounded extension and report residual uncertainty; no new decoder, forced root or extrapolation model.'}
    (LAB/'manifests/phase-guard-checks.json').write_text(json.dumps(result,indent=2)+'\n');(LAB/'manifests/phase-guard-jobs.json').write_text(json.dumps(result['jobs'],indent=2)+'\n');print('registered guard/closing jobs',len(result['jobs']))
if __name__=='__main__':main()
