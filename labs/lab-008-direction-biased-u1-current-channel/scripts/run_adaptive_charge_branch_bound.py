"""Adaptive exact charge-prefix decision diagram with certified upper bounds."""
from itertools import product
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, CurrentOracle, square_graph


VALUES=(0,1,-1)


def risk_with_remaining_parity(weights, remaining_cut, p):
    odd=(1-(1-2*p)**remaining_cut)/2
    z0=weights[0]*(1-odd)+weights[1]*odd
    z1=weights[1]*(1-odd)+weights[0]*odd
    return min(z0,z1),z0+z1


def run_cell(L,p,q,prefix_budget,state_cap=2_000_000):
    model=square_graph(L); order=CurrentOracle(model,cap=12_000_000).profile['order']
    measured=set(model.detector_vertices);logical=set(model.logical_edges)
    assigned=set();visited=set();frontier=[];dp={((),(),0):1.0}
    finalized_upper=0.;finalized_probability=0.;peak=1;profile=[]
    for v in order:
        old=[e for e in model.incident_edges[v] if e in assigned]
        new=[e for e in model.incident_edges[v] if e not in assigned]
        keep=[e for e in frontier if e not in old]
        visited.add(v)
        future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
        old_pos=[frontier.index(e) for e in old];keep_pos=[frontier.index(e) for e in keep]
        signs=lambda edges:[1 if model.edges[e][1]==v else -1 for e in edges]
        nxt={}
        for (front_values,prefix,parity0),weight0 in dp.items():
            old_charge=sum(s*front_values[i] for s,i in zip(signs(old),old_pos));kept=tuple(front_values[i] for i in keep_pos)
            for values in product(VALUES,repeat=len(new)):
                charge=old_charge+sum(s*x for s,x in zip(signs(new),values));parity=parity0;weight=weight0
                for e,x in zip(new,values):
                    if e in logical and x!=0:parity^=1
                    weight*=1-p if x==0 else p*q if x==1 else p*(1-q)
                future_values=tuple(values[new.index(e)] for e in future)
                key=(kept+future_values,prefix+(charge,),parity)
                nxt[key]=nxt.get(key,0.)+weight
        preprune=len(nxt);peak=max(peak,preprune)
        if preprune>state_cap:raise MemoryError(f'preprune state cap {preprune}>{state_cap} at vertex {v}')
        frontier=keep+future;assigned.update(new)
        groups={}
        for (front_values,prefix,h),weight in nxt.items():
            groups.setdefault(prefix,np.zeros(2))[h]+=weight
        remaining_cut=len(logical-assigned)
        scored=[]
        for prefix,weights in groups.items():
            risk,prob=risk_with_remaining_parity(weights,remaining_cut,p)
            scored.append((risk,prefix,prob))
        scored.sort(key=lambda x:(-x[0],x[1]))
        keep_prefix={x[1] for x in scored[:prefix_budget]}
        dropped=scored[prefix_budget:]
        finalized_upper+=sum(x[0] for x in dropped);finalized_probability+=sum(x[2] for x in dropped)
        dp={key:w for key,w in nxt.items() if key[1] in keep_prefix}
        active_probability=sum(dp.values())
        assert abs(finalized_probability+active_probability-1)<1e-10
        profile.append({'vertex':int(v),'preprune_states':preprune,'active_states':len(dp),'prefixes':len(groups),
                        'kept_prefixes':len(keep_prefix),'remaining_cut_edges':remaining_cut,
                        'finalized_upper':finalized_upper,'finalized_probability':finalized_probability})
    table={}
    for (_,prefix,h),weight in dp.items():table.setdefault(prefix,np.zeros(2))[h]+=weight
    active_exact=sum(min(z) for z in table.values());upper=finalized_upper+active_exact
    assert abs(finalized_probability+sum(sum(z) for z in table.values())-1)<1e-10
    prior_odd=(1-(1-2*p)**len(logical))/2;prior_risk=min(prior_odd,1-prior_odd)
    assert upper<=prior_risk+1e-12
    return {'L':L,'p':p,'q':q,'prefix_budget':prefix_budget,'upper':upper,'prior_risk':prior_risk,
            'finalized_upper':finalized_upper,'active_exact':active_exact,'finalized_probability':finalized_probability,
            'surviving_full_records':len(table),'peak_preprune_states':peak,'profile':profile}


def main():
    manifest=LAB/'manifests/adaptive-charge-branch-bound-2026-09-19.json'
    replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json';activity_path=LAB/'results/current-activity-expansion-2026-09-18.json'
    replica=json.loads(replica_path.read_text());exact={(r['p'],r['q']):r['LER'] for r in replica['square_sector_checks']}
    gates=[]
    for p,q in ((.1,.5),(.3,.75)):
        cell=[]
        for B in (4,32,10000):
            row=run_cell(3,p,q,B);row['exact_LER']=exact[(p,q)];row['gap']=row['upper']-row['exact_LER'];assert row['gap']>=-1e-12
            if B==10000:assert row['gap']<1e-12
            cell.append(row)
        gates.append(cell)
    activity=json.loads(activity_path.read_text());base={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    studies=[];promoted=[];censored=[]
    for q in (.5,.75,.97,1.):
        rows=[]
        for B in (64,256,1024,4096):
            try:row=run_cell(5,.08,q,B)
            except MemoryError as e:censored.append({'q':q,'prefix_budget':B,'reason':str(e)});break
            b=base[(.08,q)];combined=min(b['upper'],row['upper']);base_width=b['upper']-b['lower']
            row.update({'activity_lower':b['lower'],'activity_upper':b['upper'],'combined_upper':combined,
                        'combined_width':combined-b['lower'],'relative_width_reduction':1-(combined-b['lower'])/base_width})
            row['promoted']=bool(row['relative_width_reduction']>=.10)
            if row['promoted']:promoted.append({'q':q,'prefix_budget':B,'reduction':row['relative_width_reduction']})
            rows.append(row)
        studies.append({'q':q,'runs':rows})
    decision='promote_adaptive_branch_bound' if promoted else 'reject_within_registered_budgets'
    files=[Path(__file__),manifest,replica_path,activity_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Exact adaptive charge-prefix upper bounds; no sampling, decoder or threshold.',
         'gates':gates,'studies':studies,'censored':censored,'decision':decision,'promoted':promoted,
         'next_method':('Use the smallest promoted budget per cell as the certified upper bound.' if promoted else
                        'A more structured tensor/decision-diagram merge is required; risk-only best-first pruning is insufficient.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/adaptive-charge-branch-bound-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'promoted':promoted,'censored':censored,
                      'best':[{'q':s['q'],'run':({'B':s['runs'][-1]['prefix_budget'],'upper':s['runs'][-1]['upper'],
                               'reduction':s['runs'][-1]['relative_width_reduction'],'peak':s['runs'][-1]['peak_preprune_states']} if s['runs'] else None)} for s in studies]},indent=2))


if __name__=='__main__':main()
