"""Exact positive transfer for a two-current relative-defect upper bound."""
from itertools import product
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, square_graph


VALUES = (0, 1, -1)


def local_options(cells, cut):
    grouped = {}
    for a, b in product(VALUES, repeat=2):
        delta = a-b
        parity = int(cut and ((a != 0) ^ (b != 0)))
        weights = []
        for p, q in cells:
            prob = {0: 1-p, 1: p*q, -1: p*(1-q)}
            weights.append(np.sqrt(prob[a]*prob[b]))
        grouped.setdefault((delta, parity), np.zeros(len(cells)))
        grouped[(delta, parity)] += weights
    return [(d, h, w) for (d, h), w in sorted(grouped.items())]


def best_order(model):
    measured = tuple(model.detector_vertices)
    candidates = [list(measured),
                  sorted(measured,key=lambda v:(round(model.vertices[v].y,6),model.vertices[v].x)),
                  sorted(measured,key=lambda v:(round(model.vertices[v].x,6),model.vertices[v].y))]
    def width(order):
        assigned=set(); frontier=[]; visited=set(); peak=0
        for v in order:
            old=[e for e in model.incident_edges[v] if e in assigned]
            new=[e for e in model.incident_edges[v] if e not in assigned]
            keep=[e for e in frontier if e not in old]
            visited.add(v)
            future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
            frontier=keep+future; assigned.update(new); peak=max(peak,len(frontier))
        return peak
    return min(candidates,key=width)


def transfer(L, cells, cap=2_000_000):
    model = square_graph(L)
    measured = set(model.detector_vertices)
    order = best_order(model)
    cut = set(model.logical_edges)
    normal = local_options(cells, False)
    twisted = local_options(cells, True)
    assigned=set(); visited=set(); frontier=[]
    dp={((),0):np.ones(len(cells))}
    profile=[]
    for v in order:
        old=[e for e in model.incident_edges[v] if e in assigned]
        new=[e for e in model.incident_edges[v] if e not in assigned]
        keep=[e for e in frontier if e not in old]
        visited.add(v)
        future=[e for e in new if any(u in measured and u not in visited for u in model.edges[e])]
        old_pos=[frontier.index(e) for e in old]
        keep_pos=[frontier.index(e) for e in keep]
        signs=lambda edges:[1 if model.edges[e][1]==v else -1 for e in edges]
        choices=[twisted if e in cut else normal for e in new]
        nxt={}; transitions=0
        for (front_values, parity0), weight0 in dp.items():
            old_charge=sum(s*front_values[i] for s,i in zip(signs(old),old_pos))
            kept=tuple(front_values[i] for i in keep_pos)
            for option_tuple in product(*choices):
                deltas=tuple(x[0] for x in option_tuple)
                if old_charge+sum(s*d for s,d in zip(signs(new),deltas)) != 0:
                    continue
                parity=parity0
                weight=weight0.copy()
                for _,h,w in option_tuple:
                    parity ^= h; weight *= w
                future_values=tuple(deltas[new.index(e)] for e in future)
                key=(kept+future_values,parity)
                nxt[key]=nxt.get(key,np.zeros(len(cells)))+weight
                transitions += 1
        frontier=keep+future; assigned.update(new); dp=nxt
        if len(dp)>cap: raise MemoryError(f'frontier state cap {len(dp)}>{cap}')
        profile.append({'vertex':int(v),'frontier':len(frontier),'states':len(dp),'accepted_transitions':transitions})
    assert frontier==[] and all(key[0]==() for key in dp)
    even=dp.get(((),0),np.zeros(len(cells)))
    odd=dp.get(((),1),np.zeros(len(cells)))
    assert np.all(even>=0) and np.all(odd>=0)
    return {'L':L,'cells':[{'p':p,'q':q,'pair_even':float(even[i]),'pair_odd_upper':float(odd[i])} for i,(p,q) in enumerate(cells)],
            'profile':profile,'peak_states':max(x['states'] for x in profile)}


def main():
    manifest=LAB/'manifests/positive-defect-transfer-2026-09-18.json'
    replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json'
    activity_path=LAB/'results/current-activity-expansion-2026-09-18.json'
    replica=json.loads(replica_path.read_text())
    exact={(r['p'],r['q']):r['LER'] for r in replica['square_sector_checks']}
    gate_cells=[(0.1,0.5),(0.1,1.0),(0.3,0.75),(0.46,0.97)]
    gate=transfer(3,gate_cells)
    for row in gate['cells']:
        row['exact_LER']=exact[(row['p'],row['q'])]
        row['capped_pair_upper']=min(.5,row['pair_odd_upper'])
        row['gate_margin']=row['capped_pair_upper']-row['exact_LER']
        assert row['gate_margin']>=-1e-12

    cells=[(p,q) for p in (0.05,0.08) for q in (0.5,0.75,0.97,1.0)]
    study=transfer(5,cells)
    activity=json.loads(activity_path.read_text())
    baseline={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    improved_at_008=0
    for row in study['cells']:
        base=baseline[(row['p'],row['q'])]
        pair=min(.5,row['pair_odd_upper'])
        combined=min(base['upper'],pair)
        row.update({'activity_lower':base['lower'],'activity_upper':base['upper'],
                    'capped_pair_upper':pair,'combined_upper':combined,
                    'baseline_width':base['upper']-base['lower'],
                    'combined_width':max(0.,combined-base['lower'])})
        row['relative_width_reduction']=0. if row['baseline_width']==0 else 1-row['combined_width']/row['baseline_width']
        row['promoted']=row['relative_width_reduction']>=.10
        if row['p']==.08 and row['promoted']: improved_at_008+=1
    decision=('promote_positive_pair_bound' if improved_at_008 else 'reject_positive_pair_relaxation')
    files=[Path(__file__),manifest,replica_path,activity_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Positive two-current defect transfer; deterministic upper-bound comparison only.',
         'gate':gate,'study':study,'decision':decision,'improved_p008_cells':improved_at_008,
         'next_method':('Use promoted pair bound in a certified interval.' if improved_at_008 else
                        'The configuration-level pair relaxation is too loose; next require sector-level Hellinger/TV contraction or a controlled connected-cluster expansion.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/positive-defect-transfer-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'improved_p008_cells':improved_at_008,
                      'L3_peak_states':gate['peak_states'],'L5_peak_states':study['peak_states'],
                      'study':[{'p':r['p'],'q':r['q'],'pair_upper':r['capped_pair_upper'],'activity_upper':r['activity_upper'],'relative_reduction':r['relative_width_reduction']} for r in study['cells']]},indent=2))


if __name__=='__main__': main()
