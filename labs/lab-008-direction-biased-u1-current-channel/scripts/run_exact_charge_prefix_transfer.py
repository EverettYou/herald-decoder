"""Exact coarse-charge transfer bounds for all-record Bayes LER."""
from itertools import product
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, CurrentOracle, square_graph


VALUES=(0,1,-1)


def contraction(L,cells,selected_count,cap=2_000_000):
    model=square_graph(L)
    order=CurrentOracle(model,cap=12_000_000).profile['order']
    selected=set(order[-selected_count:]) if selected_count else set()
    measured=set(model.detector_vertices); logical=set(model.logical_edges)
    assigned=set(); visited=set(); frontier=[]
    dp={((),(),0):np.ones(len(cells))}; peak=1; profile=[]
    for v in order:
        old=[e for e in model.incident_edges[v] if e in assigned]
        new=[e for e in model.incident_edges[v] if e not in assigned]
        keep=[e for e in frontier if e not in old]
        visited.add(v)
        future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
        old_pos=[frontier.index(e) for e in old]; keep_pos=[frontier.index(e) for e in keep]
        signs=lambda edges:[1 if model.edges[e][1]==v else -1 for e in edges]
        nxt={}; transitions=0
        for (front_values,charges,parity0),weight0 in dp.items():
            old_charge=sum(s*front_values[i] for s,i in zip(signs(old),old_pos))
            kept=tuple(front_values[i] for i in keep_pos)
            for values in product(VALUES,repeat=len(new)):
                charge=old_charge+sum(s*x for s,x in zip(signs(new),values))
                parity=parity0
                weight=weight0.copy()
                for e,x in zip(new,values):
                    if e in logical and x!=0: parity^=1
                    weight *= np.array([1-p if x==0 else p*q if x==1 else p*(1-q) for p,q in cells])
                future_values=tuple(values[new.index(e)] for e in future)
                out_charges=charges+(charge,) if v in selected else charges
                key=(kept+future_values,out_charges,parity)
                nxt[key]=nxt.get(key,np.zeros(len(cells)))+weight
                transitions+=1
        frontier=keep+future;assigned.update(new);dp=nxt;peak=max(peak,len(dp))
        profile.append({'vertex':int(v),'selected':v in selected,'frontier':len(frontier),'states':len(dp),'transitions':transitions})
        if len(dp)>cap: raise MemoryError(f'state cap {len(dp)}>{cap} at selected_count={selected_count}')
    assert frontier==[]
    table={}
    for (_,charges,h),weight in dp.items():
        table.setdefault(charges,np.zeros((len(cells),2)))[:,h]+=weight
    z=np.stack(list(table.values())); total=z.sum(axis=(0,2)); assert np.max(abs(total-1))<1e-10
    risk=np.minimum(z[:,:,0],z[:,:,1]).sum(axis=0)
    return {'selected_count':selected_count,'selected_vertices':order[-selected_count:] if selected_count else [],
            'records':len(table),'peak_states':peak,'profile':profile,
            'cells':[{'p':p,'q':q,'coarse_LER_upper':float(risk[i])} for i,(p,q) in enumerate(cells)]}


def run_nested(L,cells,counts,cap):
    runs=[];censored=None
    for count in counts:
        try:r=contraction(L,cells,count,cap)
        except MemoryError as e:
            censored={'selected_count':count,'reason':str(e)};break
        runs.append(r)
    for i in range(len(cells)):
        risks=[r['cells'][i]['coarse_LER_upper'] for r in runs]
        assert all(a+1e-12>=b for a,b in zip(risks,risks[1:]))
    return {'L':L,'runs':runs,'censored':censored}


def main():
    manifest=LAB/'manifests/exact-charge-prefix-transfer-2026-09-19.json'
    replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json'
    activity_path=LAB/'results/current-activity-expansion-2026-09-18.json'
    replica=json.loads(replica_path.read_text()); exact={(r['p'],r['q']):r['LER'] for r in replica['square_sector_checks']}
    gate_cells=[(.1,.5),(.1,1.),(.3,.75),(.46,.97)]
    gate=run_nested(3,gate_cells,(0,1,3),2_000_000)
    assert gate['censored'] is None
    for row in gate['runs'][-1]['cells']:
        row['exact_LER']=exact[(row['p'],row['q'])]
        row['error']=abs(row['coarse_LER_upper']-row['exact_LER']);assert row['error']<1e-12

    cells=[(p,q) for p in (.05,.08) for q in (.5,.75,.97,1.)]
    study=run_nested(5,cells,(0,1,3,5,7,9,12,15),2_000_000)
    activity=json.loads(activity_path.read_text()); base={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    promoted=[]
    for run in study['runs']:
        for row in run['cells']:
            b=base[(row['p'],row['q'])];combined=min(b['upper'],row['coarse_LER_upper'])
            width=combined-b['lower'];base_width=b['upper']-b['lower']
            row.update({'activity_lower':b['lower'],'activity_upper':b['upper'],'combined_upper':combined,
                        'combined_width':width,'relative_width_reduction':1-width/base_width})
            row['promoted']=row['relative_width_reduction']>=.10
            if row['promoted']:promoted.append({'selected_count':run['selected_count'],'p':row['p'],'q':row['q'],'reduction':row['relative_width_reduction']})
    decision='promote_exact_charge_prefix' if any(x['p']==.08 for x in promoted) else 'no_p008_improvement_within_cap'
    files=[Path(__file__),manifest,replica_path,activity_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Exact physical-kernel coarse-charge upper bounds; no sampling, decoder or threshold.',
         'correction':'Exact K is already finite harmonic; charge-record l1 contraction, not edge-kernel approximation, is the active difficulty.',
         'gate':gate,'study':study,'decision':decision,'promoted_cells':promoted,
         'next_method':('Use the promoted nested charge set and refine only if the registered cap permits.' if decision.startswith('promote') else
                        'A scalable l1/tensor contraction is still required; do not approximate the already exact edge kernel.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/exact-charge-prefix-transfer-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'censored':study['censored'],
                      'runs':[{'selected_count':r['selected_count'],'records':r['records'],'peak_states':r['peak_states'],
                               'p008':[{'q':x['q'],'upper':x['coarse_LER_upper'],'reduction':x['relative_width_reduction']} for x in r['cells'] if x['p']==.08]} for r in study['runs']]},indent=2))


if __name__=='__main__':main()
