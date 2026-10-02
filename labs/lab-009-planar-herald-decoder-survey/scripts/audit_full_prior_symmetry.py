"""Complete joint-record enumeration; no candidate decoder or sampled truth input."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from herald_decoder import honeycomb_graph
LAB=Path(__file__).resolve().parents[1]

def joint_risk(p,q):
    g=honeycomb_graph(2);E=len(g.edges);D=len(g.detector_vertices)
    X=((np.arange(2**E)[:,None]>>np.arange(E))&1).astype(np.uint8)
    N=X.astype(int)@g.check_matrix.toarray().T
    synd=(N%2)@(1<<np.arange(D));sector=X[:,list(g.logical_edges)].sum(1)%2
    wt=X.sum(1);prior=p**wt*(1-p)**(E-wt);Z=np.zeros((2**D,2**D,2))
    for hi in range(2**D):
        h=(hi>>np.arange(D))&1
        factors=np.where(h[None]==1,q*(N>=2),1-q*(N>=2)).prod(1)
        np.add.at(Z,(synd,np.full(len(X),hi),sector.astype(int)),prior*factors)
    assert abs(Z.sum()-1)<1e-12
    return float(Z.min(2).sum())

def run():
    rows=[]
    for q in [0,.5,1]:
        a,b=joint_risk(.2,q),joint_risk(.8,q)
        if q in [0,1]:assert abs(a-b)<1e-12
        else:assert b-a>.07
        rows.append({'q':q,'p_low':.2,'p_high':.8,'risk_low':a,'risk_high':b,'difference':b-a})
    for p in [0,1]:
        for q in [0,.5,1]:assert joint_risk(p,q)==0
    result={'status':'passed','domain':{'p':[0,1],'q':[0,1]},'L':2,'errors_enumerated':2048,'herald_records_per_error':64,'rows':rows,'interpretation':'Interior-q Bayes-risk complement symmetry disproved. Endpoint symmetries and deterministic prior risks verified. No thermodynamic boundary inferred.'}
    (LAB/'results/full-prior-symmetry-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':run()
