"""Charge-prefix branch-and-bound prioritized by frontier information value."""
from itertools import product
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, CurrentOracle, square_graph

VALUES=(0,1,-1)


def mixed_risk(weights,remaining,p):
    odd=(1-(1-2*p)**remaining)/2
    z0=weights[0]*(1-odd)+weights[1]*odd;z1=weights[1]*(1-odd)+weights[0]*odd
    return min(z0,z1),z0+z1


def run_cell(L,p,q,B,cap=2_000_000):
    model=square_graph(L);order=CurrentOracle(model,cap=12_000_000).profile['order']
    measured=set(model.detector_vertices);logical=set(model.logical_edges)
    assigned=set();visited=set();frontier=[];dp={((),(),0):1.}
    final_upper=0.;final_prob=0.;peak=1;profile=[]
    for v in order:
        old=[e for e in model.incident_edges[v] if e in assigned];new=[e for e in model.incident_edges[v] if e not in assigned]
        keep=[e for e in frontier if e not in old];visited.add(v)
        future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
        old_pos=[frontier.index(e) for e in old];keep_pos=[frontier.index(e) for e in keep]
        signs=lambda es:[1 if model.edges[e][1]==v else -1 for e in es]
        nxt={}
        for (fv,prefix,h0),w0 in dp.items():
            oldq=sum(s*fv[i] for s,i in zip(signs(old),old_pos));kept=tuple(fv[i] for i in keep_pos)
            for vals in product(VALUES,repeat=len(new)):
                charge=oldq+sum(s*x for s,x in zip(signs(new),vals));h=h0;w=w0
                for e,x in zip(new,vals):
                    if e in logical and x!=0:h^=1
                    w*=1-p if x==0 else p*q if x==1 else p*(1-q)
                fvals=tuple(vals[new.index(e)] for e in future);key=(kept+fvals,prefix+(charge,),h)
                nxt[key]=nxt.get(key,0.)+w
        peak=max(peak,len(nxt))
        if len(nxt)>cap:raise MemoryError(f'preprune state cap {len(nxt)}>{cap}')
        frontier=keep+future;assigned.update(new);remaining=len(logical-assigned)
        by_prefix={}
        for (fv,prefix,h),w in nxt.items():by_prefix.setdefault(prefix,{}).setdefault(fv,np.zeros(2))[h]+=w
        scored=[]
        for prefix,fronts in by_prefix.items():
            total=sum(fronts.values(),np.zeros(2));parent,prob=mixed_risk(total,remaining,p)
            genie=sum(mixed_risk(z,remaining,p)[0] for z in fronts.values())
            scored.append((parent-genie,parent,prefix,prob))
        scored.sort(key=lambda x:(-x[0],-x[1],x[2]));keep_prefix={x[2] for x in scored[:B]}
        dropped=scored[B:];final_upper+=sum(x[1] for x in dropped);final_prob+=sum(x[3] for x in dropped)
        dp={key:w for key,w in nxt.items() if key[1] in keep_prefix}
        assert abs(final_prob+sum(dp.values())-1)<1e-10
        profile.append({'vertex':int(v),'preprune_states':len(nxt),'active_states':len(dp),'prefixes':len(scored),
                        'kept':len(keep_prefix),'max_value_score':float(scored[0][0]) if scored else 0.,
                        'finalized_upper':final_upper})
    table={}
    for (_,prefix,h),w in dp.items():table.setdefault(prefix,np.zeros(2))[h]+=w
    upper=final_upper+sum(min(z) for z in table.values());prior=(1-(1-2*p)**len(logical))/2
    assert upper<=min(prior,1-prior)+1e-12
    return {'L':L,'p':p,'q':q,'prefix_budget':B,'upper':upper,'peak_preprune_states':peak,
            'finalized_upper':final_upper,'surviving_records':len(table),'profile':profile}


def main():
    manifest=LAB/'manifests/frontier-value-branch-bound-2026-09-19.json'
    prior_path=LAB/'results/adaptive-charge-branch-bound-2026-09-19.json';activity_path=LAB/'results/current-activity-expansion-2026-09-18.json';replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json'
    replica=json.loads(replica_path.read_text());exact={(r['p'],r['q']):r['LER'] for r in replica['square_sector_checks']}
    gates=[]
    for p,q in ((.1,.5),(.3,.75)):
        rows=[]
        for B in (4,10000):
            r=run_cell(3,p,q,B);r['exact_LER']=exact[(p,q)];r['gap']=r['upper']-r['exact_LER'];assert r['gap']>=-1e-12
            if B==10000:assert r['gap']<1e-12
            rows.append(r)
        gates.append(rows)
    prior=json.loads(prior_path.read_text());old={(s['q'],r['prefix_budget']):r for s in prior['studies'] for r in s['runs']}
    activity=json.loads(activity_path.read_text());base={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    studies=[];promoted=[]
    for q in (.5,.75):
        rows=[]
        for B in (64,256,1024):
            r=run_cell(5,.08,q,B);b=base[(.08,q)];o=old[(q,B)];combined=min(b['upper'],r['upper']);bw=b['upper']-b['lower']
            r.update({'risk_priority_upper':o['upper'],'priority_upper_improvement':o['upper']-r['upper'],
                      'activity_lower':b['lower'],'activity_upper':b['upper'],'combined_upper':combined,
                      'relative_width_reduction':1-(combined-b['lower'])/bw})
            r['promoted']=bool(r['relative_width_reduction']>=.10)
            if r['promoted']:promoted.append({'q':q,'prefix_budget':B,'reduction':r['relative_width_reduction']})
            rows.append(r)
        studies.append({'q':q,'runs':rows})
    decision='promote_frontier_value_priority' if promoted else 'close_priority_only_branch'
    files=[Path(__file__),manifest,prior_path,activity_path,replica_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Exact frontier-value priority comparison at fixed B; no sampling or decoder.',
         'gates':gates,'studies':studies,'decision':decision,'promoted':promoted,
         'next_method':('Retain the smallest promoted fair/intermediate bound.' if promoted else
                        'Priority-only refinement is closed; the remaining bounded branch is certified structured state merging.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/frontier-value-branch-bound-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'promoted':promoted,
                      'best':[{'q':s['q'],'B':s['runs'][-1]['prefix_budget'],'upper':s['runs'][-1]['upper'],
                               'old_upper':s['runs'][-1]['risk_priority_upper'],'reduction':s['runs'][-1]['relative_width_reduction'],
                               'peak':s['runs'][-1]['peak_preprune_states']} for s in studies]},indent=2))


if __name__=='__main__':main()
