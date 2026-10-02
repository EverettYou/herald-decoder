"""Certified finite-state coarsening of charge histories by posterior buckets."""
from itertools import product
from pathlib import Path
import hashlib
import json
import math

import numpy as np

from current_oracle import LAB, ROOT, CurrentOracle, square_graph

VALUES=(0,1,-1)


def mixed(weights,remaining,p):
    odd=(1-(1-2*p)**remaining)/2
    z0=weights[0]*(1-odd)+weights[1]*odd;z1=weights[1]*(1-odd)+weights[0]*odd
    return z0,z1


def signature(charge,z0,z1,bins,cap):
    if z0==z1:sign=0;mag=0.
    elif z0==0 or z1==0:sign=1 if z0>z1 else -1;mag=cap
    else:sign=1 if z0>z1 else -1;mag=min(cap,abs(math.log(z0/z1)))
    index=min(bins-1,int(mag/cap*bins))
    return (int(charge),sign,index)


def run_cell(L,p,q,bins=None,cap_log=16.,state_cap=2_000_000):
    model=square_graph(L);order=CurrentOracle(model,cap=12_000_000).profile['order']
    measured=set(model.detector_vertices);logical=set(model.logical_edges)
    assigned=set();visited=set();frontier=[];dp={((),(),0):1.};peak=1;profile=[]
    for v in order:
        old=[e for e in model.incident_edges[v] if e in assigned];new=[e for e in model.incident_edges[v] if e not in assigned]
        keep=[e for e in frontier if e not in old];visited.add(v)
        future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
        old_pos=[frontier.index(e) for e in old];keep_pos=[frontier.index(e) for e in keep]
        signs=lambda es:[1 if model.edges[e][1]==v else -1 for e in es]
        temp={}
        for (fv,label,h0),w0 in dp.items():
            oldq=sum(s*fv[i] for s,i in zip(signs(old),old_pos));kept=tuple(fv[i] for i in keep_pos)
            for vals in product(VALUES,repeat=len(new)):
                charge=oldq+sum(s*x for s,x in zip(signs(new),vals));h=h0;w=w0
                for e,x in zip(new,vals):
                    if e in logical and x!=0:h^=1
                    w*=1-p if x==0 else p*q if x==1 else p*(1-q)
                fvals=tuple(vals[new.index(e)] for e in future);child=label+(charge,) if bins is None else (label,charge)
                key=(kept+fvals,child,h);temp[key]=temp.get(key,0.)+w
        frontier=keep+future;assigned.update(new);remaining=len(logical-assigned)
        if bins is None:dp=temp;labels={k[1] for k in dp}
        else:
            child_totals={}
            for (fv,child,h),w in temp.items():child_totals.setdefault(child,np.zeros(2))[h]+=w
            mapping={}
            for child,z in child_totals.items():
                z0,z1=mixed(z,remaining,p);mapping[child]=signature(child[1],z0,z1,bins,cap_log)
            dp={}
            for (fv,child,h),w in temp.items():
                key=(fv,mapping[child],h);dp[key]=dp.get(key,0.)+w
            labels=set(mapping.values())
        peak=max(peak,len(dp))
        if len(labels)>1024:raise MemoryError(f'label cap {len(labels)}>1024')
        if len(dp)>state_cap:raise MemoryError(f'state cap {len(dp)}>{state_cap}')
        assert abs(sum(dp.values())-1)<1e-10
        profile.append({'vertex':int(v),'states':len(dp),'labels':len(labels),'remaining_cut_edges':remaining})
    table={}
    for (_,label,h),w in dp.items():table.setdefault(label,np.zeros(2))[h]+=w
    upper=sum(min(z) for z in table.values())
    return {'L':L,'p':p,'q':q,'bins':bins,'upper':upper,'labels':len(table),'peak_states':peak,'profile':profile}


def main():
    manifest=LAB/'manifests/posterior-bucket-merge-2026-09-19.json';replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json';activity_path=LAB/'results/current-activity-expansion-2026-09-18.json';risk_path=LAB/'results/adaptive-charge-branch-bound-2026-09-19.json';value_path=LAB/'results/frontier-value-branch-bound-2026-09-19.json'
    replica=json.loads(replica_path.read_text());exact={(r['p'],r['q']):r['LER'] for r in replica['square_sector_checks']}
    gates=[]
    for p,q in ((.1,.5),(.3,.75)):
        rows=[]
        for bins in (None,16,64):
            r=run_cell(3,p,q,bins);r['exact_LER']=exact[(p,q)];r['gap']=r['upper']-r['exact_LER'];assert r['gap']>=-1e-12
            if bins is None:assert r['gap']<1e-12
            rows.append(r)
        gates.append(rows)
    activity=json.loads(activity_path.read_text());base={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    risk=json.loads(risk_path.read_text());oldrisk={s['q']:s['runs'][-1] for s in risk['studies'] if s['q'] in (.5,.75)}
    value=json.loads(value_path.read_text());oldvalue={s['q']:s['runs'][-1] for s in value['studies']}
    studies=[];promoted=[];censored=[]
    for q in (.5,.75):
        rows=[]
        for bins in (16,32,64):
            try:r=run_cell(5,.08,q,bins)
            except MemoryError as e:censored.append({'q':q,'bins':bins,'reason':str(e)});break
            b=base[(.08,q)];combined=min(b['upper'],r['upper']);bw=b['upper']-b['lower']
            r.update({'activity_lower':b['lower'],'activity_upper':b['upper'],'risk_priority_upper':oldrisk[q]['upper'],
                      'value_priority_upper':oldvalue[q]['upper'],'combined_upper':combined,
                      'relative_width_reduction':1-(combined-b['lower'])/bw})
            r['promoted']=bool(r['relative_width_reduction']>=.10)
            if r['promoted']:promoted.append({'q':q,'bins':bins,'reduction':r['relative_width_reduction']})
            rows.append(r)
        studies.append({'q':q,'runs':rows})
    decision='promote_posterior_bucket_merge' if promoted else 'close_structured_merge_branch'
    files=[Path(__file__),manifest,replica_path,activity_path,risk_path,value_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Certified coarsened observation labels at fixed <=1024 state budget; no sampling or decoder.',
         'gates':gates,'studies':studies,'censored':censored,'decision':decision,'promoted':promoted,
         'next_method':('Retain the smallest promoted merge per cell.' if promoted else
                        'Registered contraction refinements are exhausted for fair/intermediate cells; retain the activity intervals and stop this numerical branch.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/posterior-bucket-merge-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'promoted':promoted,'censored':censored,
                      'best':[{'q':s['q'],'run':({'bins':s['runs'][-1]['bins'],'upper':s['runs'][-1]['upper'],
                               'reduction':s['runs'][-1]['relative_width_reduction'],'labels':s['runs'][-1]['labels'],
                               'peak':s['runs'][-1]['peak_states']} if s['runs'] else None)} for s in studies]},indent=2))


if __name__=='__main__':main()
