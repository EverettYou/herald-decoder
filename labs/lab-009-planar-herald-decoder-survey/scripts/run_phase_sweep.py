"""Checkpointed independent full-domain exact-sector risk measurements."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,time,hashlib,argparse,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];LAB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from phase_runtime import phase_graph,SweepPlanar
GRAPHS={};DIRECTORY=LAB/'data/phase-sweep';SEED=202610021

def key(L,p,q):return f'L{L}_p{p:.6f}_q{q:.6f}'
def atomic_json(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def measure(job):
    L,p,q,target=job;k=key(L,p,q);jpath=DIRECTORY/(k+'.json');npath=DIRECTORY/(k+'.npz')
    if jpath.exists():
        old=json.loads(jpath.read_text())
        if old['n']>=target:return old
    if p in [0.,1.]:
        result={'L':L,'p':p,'q':q,'n':0,'risk':0.,'se':0.,'failures':0,'status':'analytic_deterministic_prior','source':'known noiseless/all-one prior; no inferred complement symmetry'};atomic_json(jpath,result);return result
    g=GRAPHS.setdefault(L,phase_graph(L)) if L not in GRAPHS else GRAPHS[L]
    rng=np.random.default_rng([SEED,L,int(round(p*1e6)),int(round(q*1e6))])
    previous={}
    start=0
    if npath.exists():
        with np.load(npath,allow_pickle=False)as z:previous={k:z[k]for k in z.files}
        start=len(previous['risk'])
        # RNG streams are record-indexed below, so resume never repeats trials.
    decoder=SweepPlanar(g,p=p,q=q)
    matrix=g.check_matrix;edges=len(g.edges);detectors=len(g.detector_vertices);logical=list(g.logical_edges)
    values={name:[]for name in ['risk','probability_one','failure','seconds','residual','errors_packed','syndrome_packed','herald_packed']};failures=[]
    begin=time.perf_counter()
    for i in range(start,target):
        rng=np.random.default_rng([SEED,L,int(round(p*1e6)),int(round(q*1e6)),i])
        x=(rng.random(edges)<p).astype(np.uint8);counts=np.asarray(matrix@x).ravel();s=(counts&1).astype(np.uint8);h=((counts>=2)&(rng.random(detectors)<q)).astype(np.uint8)
        t=time.perf_counter()
        try:
            probs,diag=decoder.posterior(s,h);r=float(probs.min());prob=float(probs[1]);res=diag.get('solve_residual',0.);f=int((int(probs[1]>probs[0])^(int(x[logical].sum())&1)))
        except Exception as e:
            failures.append({'record':i,'error':type(e).__name__+': '+str(e)});r=prob=res=float('nan');f=1
        for name,val in [('risk',r),('probability_one',prob),('failure',f),('seconds',time.perf_counter()-t),('residual',res),('errors_packed',np.packbits(x)),('syndrome_packed',np.packbits(s)),('herald_packed',np.packbits(h))]:values[name].append(val)
    arrays={}
    for name,vals in values.items():
        a=np.asarray(vals,dtype=np.uint8 if name in ['failure','errors_packed','syndrome_packed','herald_packed']else float)
        arrays[name]=np.concatenate([previous[name],a])if name in previous else a
    tmp=npath.with_suffix('.tmp.npz');np.savez_compressed(tmp,**arrays);tmp.replace(npath)
    risk=arrays['risk'];valid=np.isfinite(risk);missing=int((~valid).sum());n=len(risk)
    goodrisk=risk[valid]
    result={'L':L,'p':p,'q':q,'n':n,'risk':float(goodrisk.mean())if len(goodrisk)else None,'se':float(goodrisk.std(ddof=1)/np.sqrt(n))if len(goodrisk)>1 else None,'missing_records':missing,'missing_risk_mean_bounds':[float(np.nansum(risk)/n),float((np.nansum(risk)+missing*.5)/n)],'direct_failures':int(arrays['failure'].sum()),'max_solve_residual':float(np.nanmax(arrays['residual'])),'median_seconds':float(np.median(arrays['seconds'])),'elapsed_extension_seconds':time.perf_counter()-begin,'status':'passed'if missing==0 else'numerical_gate_failed','errors':failures,'seed':SEED,'rng':'record-indexed SeedSequence(base,L,p*1e6,q*1e6,index)','vector':str(npath.relative_to(LAB)),'sha256':hashlib.sha256(npath.read_bytes()).hexdigest()}
    contract=json.loads((LAB/'manifests/phase-diagram.json').read_text())
    is_pilot_cell=L in contract['sizes'] and p in contract['p_grid'] and q in contract['q_grid']
    cutoff=contract['initial_shots_per_cell'] if is_pilot_cell and n>contract['initial_shots_per_cell'] else 0
    confirm=risk[cutoff:]
    result.update(confirmation_start=cutoff,confirmation_n=len(confirm),risk_confirmation=float(confirm.mean())if np.isfinite(confirm).all()else None,se_confirmation=float(confirm.std(ddof=1)/np.sqrt(len(confirm)))if len(confirm)>1 and np.isfinite(confirm).all()else None)
    atomic_json(jpath,result);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--jobs');ap.add_argument('--workers',type=int,default=6);args=ap.parse_args()
    contract=json.loads((LAB/'manifests/phase-diagram.json').read_text())
    assert json.loads((LAB/'results/phase-method-validation.json').read_text())['status']=='passed'
    jobs=json.loads(Path(args.jobs).read_text())if args.jobs else [[L,p,q,contract['initial_shots_per_cell']]for L in contract['sizes']for q in contract['q_grid']for p in contract['p_grid']]
    DIRECTORY.mkdir(exist_ok=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers)as pool:
        futures={pool.submit(measure,job):job for job in jobs}
        for i,future in enumerate(concurrent.futures.as_completed(futures),1):
            row=future.result();print(json.dumps({'completed':i,'total':len(jobs),'L':row['L'],'p':row['p'],'q':row['q'],'n':row['n'],'risk':row['risk'],'status':row['status']}),flush=True)
    rows=[json.loads(p.read_text())for p in sorted(DIRECTORY.glob('*.json'))]
    result={'status':'passed'if all(r['status']in ['passed','analytic_deterministic_prior']for r in rows)else'numerical_gate_failed','method':'exact planar logical-sector Bayes risk','rows':rows,'shots':sum(r['n']for r in rows),'cells':len(rows),'failed_records':sum(r.get('missing_records',0)for r in rows),'domain':{'p':[0,1],'q':[0,1]},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),LAB/'scripts/phase_runtime.py']}}
    atomic_json(LAB/'results/phase-sweep.json',result)
if __name__=='__main__':main()
