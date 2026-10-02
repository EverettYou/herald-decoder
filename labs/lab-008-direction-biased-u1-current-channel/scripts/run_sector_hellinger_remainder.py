"""Sector-level Hellinger upper bound with exact omitted parity masses."""
from itertools import combinations, product
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, square_graph, charge_matrix


def truncated_table(L, cells, kmax):
    model=square_graph(L); D=charge_matrix(model); E=len(model.edges)
    logical=set(model.logical_edges); table={}; states=0
    for k in range(kmax+1):
        for support in combinations(range(E),k):
            h=sum(e in logical for e in support)%2
            columns=D[:,support]
            for signs in product((1,-1),repeat=k):
                key=(columns@np.asarray(signs,dtype=np.int8)).tobytes()
                row=table.setdefault(key,np.zeros((len(cells),2)))
                plus=sum(s==1 for s in signs); minus=k-plus
                row[:,h] += [(1-p)**(E-k)*(p*q)**plus*(p*(1-q))**minus for p,q in cells]
                states += 1
    z=np.stack(list(table.values()))
    outputs=[]
    for i,(p,q) in enumerate(cells):
        sector_mass=z[:,i,:].sum(axis=0)
        lower=float(np.minimum(z[:,i,0],z[:,i,1]).sum())
        H=float(np.sqrt(z[:,i,0]*z[:,i,1]).sum())
        odd=(1-(1-2*p)**len(logical))/2
        total=np.array([1-odd,odd]); residual=total-sector_mass
        assert np.min(residual)>-1e-10
        residual=np.maximum(residual,0)
        upper_H=H+np.sqrt(sector_mass[0]*residual[1])+np.sqrt(sector_mass[1]*residual[0])+np.sqrt(residual.prod())
        outputs.append({'p':p,'q':q,'records':len(table),'states':states,
                        'truncated_sector_mass':sector_mass.tolist(),'exact_sector_mass':total.tolist(),
                        'residual_sector_mass':residual.tolist(),'activity_lower':lower,
                        'truncated_Hellinger':H,'Hellinger_remainder_upper':float(min(.5,upper_H))})
    return {'L':L,'edges':E,'logical_cut_edges':len(logical),'kmax':kmax,'cells':outputs}


def main():
    manifest=LAB/'manifests/sector-hellinger-remainder-2026-09-18.json'
    activity_path=LAB/'results/current-activity-expansion-2026-09-18.json'
    replica_path=LAB/'results/replica-boundary-theory-2026-09-18.json'
    exact_data=json.loads(replica_path.read_text())
    exact={(r['p'],r['q']):r['LER'] for r in exact_data['square_sector_checks']}
    gate_cells=[(.1,.5),(.1,1.),(.3,.75),(.46,.97)]
    gate=truncated_table(3,gate_cells,8)
    for row in gate['cells']:
        row['exact_LER']=exact[(row['p'],row['q'])]
        row['gate_margin']=row['Hellinger_remainder_upper']-row['exact_LER']
        assert row['gate_margin']>=-1e-12
        assert max(row['residual_sector_mass'])<1e-12

    study_cells=[(p,q) for p in (.05,.08) for q in (.5,.75,.97,1.)]
    study=truncated_table(5,study_cells,4)
    activity=json.loads(activity_path.read_text())
    baseline={(r['p'],r['q']):r for r in activity['pilot']['checkpoints'][-1]['cells']}
    improved_p008=0
    for row in study['cells']:
        base=baseline[(row['p'],row['q'])]
        combined=min(base['upper'],row['Hellinger_remainder_upper'])
        base_width=base['upper']-base['lower']; width=max(0.,combined-base['lower'])
        row.update({'activity_upper':base['upper'],'combined_upper':combined,
                    'baseline_width':base_width,'combined_width':width,
                    'relative_width_reduction':0. if base_width==0 else 1-width/base_width})
        row['promoted']=row['relative_width_reduction']>=.10
        if row['p']==.08 and row['promoted']: improved_p008+=1
    decision='promote_sector_hellinger_remainder' if improved_p008 else 'reject_sector_hellinger_remainder'
    files=[Path(__file__),manifest,activity_path,replica_path,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Deterministic sector Hellinger remainder; no sampling or fitted curve.',
         'gate':gate,'study':study,'decision':decision,'improved_p008_cells':improved_p008,
         'next_method':('Use the promoted bound in the certified LER interval.' if improved_p008 else
                        'Proceed to a registered connected-cluster feasibility test; do not enlarge this failed global remainder.'),
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/sector-hellinger-remainder-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':decision,'improved_p008_cells':improved_p008,
                      'study':[{'p':r['p'],'q':r['q'],'H_upper':r['Hellinger_remainder_upper'],
                                'activity_upper':r['activity_upper'],'relative_reduction':r['relative_width_reduction']} for r in study['cells']]},indent=2))


if __name__=='__main__': main()
