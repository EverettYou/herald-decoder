"""Independent weighted-oracle and saved-observation gates for the phase sweep."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];LAB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from herald_decoder import sample_observation,make_decoder
from phase_runtime import phase_graph,SweepPlanar
from validate_decoders import oracle

def main():
    g=phase_graph(2);rng=np.random.default_rng(821003);cases=0;max_error=0.
    for p in [0,.05,.16,.5,.8,.95,1]:
        for q in [0,.5,.9,1]:
            d=SweepPlanar(g,p=p,q=q)
            for i in range(8):
                o=sample_observation(g,rng,p=p,q=q);expected=oracle(g,p,q,o.syndrome,o.herald)[0];actual,_=d.posterior(o.syndrome,o.herald);error=float(np.max(abs(expected-actual)));assert error<1e-9;max_error=max(max_error,error);cases+=1
    rows=[json.loads(p.read_text())for p in sorted((LAB/'data/phase-sweep').glob('*.json'))]
    checks=[];records=0;graphs={}
    for r in rows:
        if r['n']==0:continue
        g=graphs.setdefault(r['L'],phase_graph(r['L'])) if r['L']not in graphs else graphs[r['L']];E=len(g.edges);D=len(g.detector_vertices);H=g.check_matrix;logical=list(g.logical_edges)
        path=LAB/r['vector'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
        with np.load(path,allow_pickle=False)as z:
            X=np.unpackbits(z['errors_packed'],axis=1)[:,:E];S=np.unpackbits(z['syndrome_packed'],axis=1)[:,:D];herald=np.unpackbits(z['herald_packed'],axis=1)[:,:D]
            N=np.asarray(H@X.T).T
            assert np.array_equal(N%2,S)and np.all(N[herald==1]>=2)
            if r['q']==0:assert not herald.any()
            if r['q']==1:assert np.array_equal(herald,N>=2)
            prob=z['probability_one'];risk=z['risk'];assert np.isfinite(risk).all()and np.all((risk>=0)&(risk<=.5))
            assert np.max(abs(risk-np.minimum(prob,1-prob)))<1e-12
            truth=X[:,logical].sum(1)%2;assert np.array_equal(z['failure'],(prob>.5)^truth)
            assert abs(float(risk.mean())-r['risk'])<1e-12 and len(risk)==r['n'];records+=len(risk)
            # One production-solver replay per sampled L,q at the worst-risk p
            # is appended below, rather than redoing the whole campaign.
    for L,q in sorted({(r['L'],r['q'])for r in rows if r['n']>0}):
        r=max([r for r in rows if r['L']==L and r['q']==q and r['n']>0],key=lambda r:r['risk']);g=graphs.setdefault(L,phase_graph(L)) if L not in graphs else graphs[L];source=make_decoder(g,'planar_ml',p=r['p'],q=q)
        with np.load(LAB/r['vector'],allow_pickle=False)as z:
            S=np.unpackbits(z['syndrome_packed'],axis=1)[:,:len(g.detector_vertices)];H=np.unpackbits(z['herald_packed'],axis=1)[:,:len(g.detector_vertices)]
            probs,_=source.posterior(S[0],H[0]);delta=abs(float(probs[1])-float(z['probability_one'][0]));assert delta<1e-9
            checks.append({'L':L,'p':r['p'],'q':q,'record':0,'posterior_error':delta})
    result={'status':'passed','whole_error_oracle_cases':cases,'max_oracle_posterior_error':max_error,'saved_trial_vectors_checked':records,'saved_cells_checked':len(rows),'source_replay':checks,'max_source_replay_error':max(c['posterior_error']for c in checks),'scope':'All retained sampled vectors checked against geometry/channel/score; one production replay per size,q at maximum measured risk; independent complete-error enumeration at L2.'}
    (LAB/'results/phase-vector-audit.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='source_replay'})
if __name__=='__main__':main()
