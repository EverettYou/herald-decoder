"""Matched-input method promotion before the full-domain experiment."""
import sys,time,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];LAB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from herald_decoder import honeycomb_graph,make_decoder,sample_observation
from phase_runtime import phase_graph,SweepPlanar

def main():
    cells=[(.16,0),(.24,.5),(.5,.85),(.7,.5),(.95,.8),(.5,1),(.8,1)]
    rows=[];record=0
    for L in [4,8,12,16,24,32]:
        plain=honeycomb_graph(L);g=phase_graph(L)
        assert plain.vertices==g.vertices and plain.edges==g.edges and plain.logical_edges==g.logical_edges
        assert np.array_equal(plain.check_matrix.toarray(),g.check_matrix.toarray())
        for p,q in cells:
            rng=np.random.default_rng([20261002,L,int(1e4*p),int(1e4*q)])
            ref=make_decoder(g,'planar_ml',p=p,q=q);fast=SweepPlanar(g,p=p,q=q)
            transfer=make_decoder(g,'transfer_ml',p=p,q=q)if L<=12 else None
            times={k:[]for k in ['source_cached','sweep','transfer']};errors=[];deltas=[];res=[]
            for _ in range(12):
                o=sample_observation(g,rng,p=p,q=q);out={}
                for k,d in [('source_cached',ref),('sweep',fast),('transfer',transfer)]:
                    if d is None:continue
                    t=time.perf_counter();probs,diag=d.posterior(o.syndrome,o.herald);times[k].append(time.perf_counter()-t);out[k]=probs
                    if k=='sweep':res.append(diag.get('solve_residual',0))
                for k in out:
                    delta=float(np.max(abs(out[k]-out['sweep'])));deltas.append(delta);assert delta<1e-9,(L,p,q,k,delta)
                record+=1
            rows.append({'L':L,'p':p,'q':q,'records':12,'max_posterior_error':max(deltas),'max_solve_residual':max(res),'median_seconds':{k:float(np.median(v))for k,v in times.items()if v}})
            print(L,p,q,rows[-1]['median_seconds'],flush=True)
    receipt={'status':'passed','records':record,'rows':rows,'selected_method':'exact planar sector inference with cached geometry and vectorized identical site weights','max_posterior_error':max(r['max_posterior_error']for r in rows),'max_solve_residual':max(r['max_solve_residual']for r in rows),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in list((ROOT/'src/herald_decoder').glob('*.py'))+[LAB/'scripts/phase_runtime.py']}}
    (LAB/'results/phase-method-validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
