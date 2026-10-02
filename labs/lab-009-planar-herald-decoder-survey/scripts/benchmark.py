"""Registered common-record pilot and warmed wall-clock efficiency measurements."""
import sys,json,time,platform,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];LAB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from herald_decoder import *

METHODS=['bp_matching','configuration_map','planar_ml','transfer_ml','mps_ml']

def wilson(k,n):
    z=1.959963984540054;a=k/n;den=1+z*z/n;center=(a+z*z/(2*n))/den;half=z*np.sqrt(a*(1-a)/n+z*z/(4*n*n))/den
    return [float(center-half),float(center+half)]

def run():
    rows=[];vectors={};shots=200;seed=100913;result={}
    checkpoint=LAB/'results/benchmark.json'
    if checkpoint.exists():
        old=json.loads(checkpoint.read_text())
        if old.get('seed')!=seed or old.get('methods')!=METHODS:raise ValueError('checkpoint contract mismatch')
        result=old;rows=old['rows'];all_batch.extend(old.get('batch_checks',[]));all_errors.extend(old.get('exceptions',[]))
        with np.load(LAB/'data/fresh-matched-vectors.npz',allow_pickle=False) as archive:
            vectors={key:archive[key] for key in archive.files}
    done={(r['L'],r['p'],r['q']) for r in rows if sum(t['L']==r['L'] and t['p']==r['p'] and t['q']==r['q'] for t in rows)==len(METHODS)}
    for L in [5,9]:
        graph=honeycomb_graph(L)
        for p,q in [(.16,0),(.24,.5),(.40,.8),(.49,1),(.60,.5),(.80,.5),(.95,.8),(.80,1)]:
            if (L,p,q) in done:continue
            rng=np.random.default_rng([seed,L,int(p*10000),int(q*10000)])
            data=[sample_observation(graph,rng,p=p,q=q)for _ in range(shots)]
            S=np.stack([o.syndrome for o in data]);H=np.stack([o.herald for o in data]);X=np.stack([o.error for o in data]);flags=np.zeros((shots,len(METHODS)),np.uint8);invalid=np.zeros_like(flags);prob=np.full((shots,len(METHODS),2),np.nan);pred=np.zeros_like(flags);times=np.zeros((shots,len(METHODS)));setup=[];nonconv=[];errors=[];batch=[]
            for j,method in enumerate(METHODS):
                t=time.perf_counter();d=make_decoder(graph,method,p=p,q=q,**({'use_numba':True}if method=='bp_matching'else{}));setup.append(time.perf_counter()-t)
                # Warm once before timing. The warm record is independent of data.
                warm=sample_observation(graph,np.random.default_rng([seed+1,L,int(p*10000),int(q*10000)]),p=p,q=q)
                t=time.perf_counter();d.decode(warm.syndrome,warm.herald);warm_seconds=time.perf_counter()-t
                count=0
                for i,(s,h,x)in enumerate(zip(S,H,X)):
                    t=time.perf_counter()
                    try:
                        result=d.decode(s,h);c=result.correction
                        if hasattr(result,'sector_probabilities')and result.sector_probabilities is not None:prob[i,j]=result.sector_probabilities
                        if hasattr(result,'bp'):count+=not result.bp.converged
                        good=c.shape==x.shape and np.all((c==0)|(c==1))and np.array_equal(graph.true_syndrome(c),s)
                        if good:pred[i,j]=graph.logical_parity(c);flags[i,j]=graph.logical_parity(x^c)
                        else:invalid[i,j]=1;flags[i,j]=1
                    except Exception as exc:invalid[i,j]=1;flags[i,j]=1;errors.append({'method':method,'shot':i,'error':str(exc)})
                    times[i,j]=time.perf_counter()-t
                nonconv.append(count)
                if hasattr(d,'decode_batch'):
                    t=time.perf_counter();C=d.decode_batch(S[:16],H[:16]);elapsed=time.perf_counter()-t
                    assert np.array_equal((graph.check_matrix@C.T)%2,S[:16].T)
                    # Ties may change the representation without changing risk.
                    sectors=np.array([graph.logical_parity(c)for c in C]);batch.append({'method':method,'shots':16,'ms_per_shot':elapsed*1000/16,'sector_disagreements':int(np.sum(sectors!=pred[:16,j]))})
                row={'L':L,'p':p,'q':q,'method':method,'shots':shots,'failures':int(flags[:,j].sum()),'invalid':int(invalid[:,j].sum()),'ler':float(flags[:,j].mean()),'ci95':wilson(int(flags[:,j].sum()),shots),'setup_ms':setup[-1]*1000,'warmup_ms':warm_seconds*1000,'median_ms':float(np.median(times[:,j])*1000),'p95_ms':float(np.quantile(times[:,j],.95)*1000),'nonconverged':count}
                rows.append(row)
            exact=prob[:,METHODS.index('planar_ml')];bayes=exact.min(1)
            for j,method in enumerate(METHODS):
                row=rows[-len(METHODS)+j];delta=flags[:,j].astype(float)-flags[:,0];conditional=1-exact[np.arange(shots),pred[:,j]];conditional[invalid[:,j].astype(bool)]=1
                row.update(paired_delta_vs_bp=float(delta.mean()),paired_se=float(delta.std(ddof=1)/np.sqrt(shots)),conditional_regret_mean=float((conditional-bayes).mean()),conditional_regret_se=float((conditional-bayes).std(ddof=1)/np.sqrt(shots)))
            all_batch.extend(batch);all_errors.extend(errors)
            key=f'L{L}_p{p}_q{q}'
            for name,value in dict(errors=X,syndrome=S,herald=H,failure_flags=flags,invalid_flags=invalid,predicted_sectors=pred,posterior=prob,timing_seconds=times).items():vectors[key+'_'+name]=value
            np.savez_compressed(LAB/'data/fresh-matched-vectors.npz',**vectors)
            result={'status':'running','seed':seed,'methods':METHODS,'rows':rows,'batch_checks':all_batch,'environment':{'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),'threads':1},'exceptions':all_errors,'scope':'200 shots/cell; independent trials shared across all methods; warmed per-shot timings exclude setup and compilation'}
            (LAB/'results/benchmark.json').write_text(json.dumps(result,indent=2)+'\n')
            print('completed',key,[round(row['ler'],3)for row in rows[-len(METHODS):]],flush=True)
    result['status']='complete';result['batch_checks']=all_batch;result['exceptions']=all_errors
    (LAB/'results/benchmark.json').write_text(json.dumps(result,indent=2)+'\n')

# Keep every cell's diagnostics, rather than only the last checkpoint.
all_batch=[];all_errors=[]
if __name__=='__main__':
    # Appending through JSON checkpoints avoids mutable scientific data globals.
    run()
