"""Independent weighted oracle, cross-backend and endpoint verification."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from herald_decoder import *
from kac_ward import KacWardHeraldDecoder
LAB=Path(__file__).resolve().parents[1]

def oracle(g,p,q,s,h):
    # Independent whole-error-vector enumeration; no candidate reference,
    # nullspace construction, planar gadget or transfer code is used.
    E=len(g.edges);X=((np.arange(2**E)[:,None]>>np.arange(E))&1).astype(np.uint8)
    N=X.astype(int)@g.check_matrix.toarray().T
    logw=np.zeros(len(X))
    if p==0:logw[:]=-np.inf;logw[0]=0
    elif p==1:logw[:]=-np.inf;logw[-1]=0
    else:logw=X.sum(1)*np.log(p)+(E-X.sum(1))*np.log1p(-p)
    eligible=N>=2;factor=np.where(h[None]==1,q*eligible,1-q*eligible)
    with np.errstate(divide='ignore'):logw+=np.log(factor).sum(1)
    logw[np.any(N%2!=s,axis=1)]=-np.inf
    maximum=logw.max()
    if not np.isfinite(maximum):return None
    weights=np.exp(logw-maximum);ell=X[:,list(g.logical_edges)].sum(1)%2
    Z=np.bincount(ell.astype(int),weights=weights,minlength=2);probs=Z/Z.sum()
    maxsectors=set(ell[np.isclose(logw,maximum,atol=1e-9,rtol=0)].astype(int));return probs,maxsectors,set(np.flatnonzero(np.isclose(logw,maximum,atol=1e-9,rtol=0)))


def run():
    rng=np.random.default_rng(100912);t=time.perf_counter();records=[];g=honeycomb_graph(2)
    params=[(.2,.5),(.4,.9),(.5,0),(.5,1),(0,.5),(1e-80,.5),(.8,.5),(.7,0),(.8,1),(.95,.9),(1,0),(1,.5),(1,1)]
    for p,q in params:
        decs={k:make_decoder(g,k,p=p,q=q)for k in ['configuration_map','planar_ml','transfer_ml','mps_ml']}
        worst={k:0. for k in ['planar_ml','transfer_ml','mps_ml']};tested=0
        X=((np.arange(2**len(g.edges))[:,None]>>np.arange(len(g.edges)))&1).astype(np.uint8)
        # Test deterministic and random physically possible observations.
        samples=[np.zeros(len(g.edges),np.uint8)]+[X[i]for i in rng.choice(len(X),size=30,replace=False)] if p>0 else [X[0]]
        if p==1:samples=[X[-1]]
        for x in samples:
            s=g.true_syndrome(x);n=g.degrees(x)[list(g.detector_vertices)];h=((n>=2)&(rng.random(len(n))<q)).astype(np.uint8)
            expected=oracle(g,p,q,s,h)
            if expected is None:continue
            probs,maxsectors,maxconfigs=expected
            for method,d in decs.items():
                result=d.decode(s,h)
                assert np.array_equal(g.true_syndrome(result.correction),s)
                sector=g.logical_parity(result.correction)
                if method=='configuration_map':
                    assert sector in maxsectors
                    index=int(result.correction.astype(np.int64) @ (1<<np.arange(len(g.edges))))
                    assert index in maxconfigs,(p,q,index)
                else:
                    err=float(np.max(abs(result.sector_probabilities-probs)));worst[method]=max(worst[method],err)
                    assert err<1e-9,(p,q,method,err)
            tested+=1
        records.append({'p':p,'q':q,'cases':tested,'max_posterior_error':worst})
    # Larger independent contraction, batch paths and MPS chi sensitivity.
    larger=[];mps=[];kw=[]
    for L in [3,4,5]:
        g=honeycomb_graph(L)
        for p,q in [(.2,0),(.3,.5),(.4,.9),(.5,1),(.7,0),(.8,.5),(.9,.9),(.8,1),(1,.5)]:
            shots=[sample_observation(g,rng,p=p,q=q)for _ in range(8)]
            S=np.stack([o.syndrome for o in shots]);H=np.stack([o.herald for o in shots])
            dense=HeraldTransferMLDecoder(g,p=p,q=q);exact,_=dense.probabilities_batch(S,H)
            planar=HeraldPlanarMLDecoder(g,p=p,q=q);got=np.stack([planar.posterior(s,h)[0]for s,h in zip(S,H)])
            error=float(np.max(abs(exact-got)));assert error<1e-9
            for name in ['configuration_map','planar_ml','transfer_ml','mps_ml']:
                d=make_decoder(g,name,p=p,q=q);C=d.decode_batch(S,H)
                assert C.shape==(len(S),len(g.edges)) and np.all((C==0)|(C==1))
                assert np.array_equal((g.check_matrix@C.T)%2,S.T)
            larger.append({'L':L,'p':p,'q':q,'shots':8,'planar_vs_transfer_max_error':error})
            for chi in [4,16]:
                probs,diag=HeraldMPSDecoder(g,p=p,q=q,chi=chi).probabilities_batch(S,H)
                mps.append({'L':L,'p':p,'q':q,'chi':chi,'max_error':float(np.max(abs(probs-exact))),'decision_changes':int(np.sum(np.argmax(probs,1)!=np.argmax(exact,1))),'max_discarded_weight':max(diag['summed_discarded_weight'])})
            if L<=3:
                for penalty in [8,12,16]:
                    candidate=KacWardHeraldDecoder(g,p=p,q=q,penalty=penalty);errors=[];failed=0
                    for s,h,ex in zip(S,H,exact):
                        try:errors.append(float(np.max(abs(candidate.posterior(s,h)[0]-ex))))
                        except NumericalInferenceError:failed+=1
                    kw.append({'L':L,'p':p,'q':q,'penalty':penalty,'numerical_failures':failed,'max_error':max(errors,default=None)})
    # Endpoint/impossible input and unsupported geometry gates.
    for name in ['configuration_map','planar_ml','transfer_ml','mps_ml']:
        d=make_decoder(honeycomb_graph(2),name,p=0,q=.5)
        try:d.decode(np.ones(6,np.uint8),np.zeros(6,np.uint8))
        except ValueError:pass
        else:raise AssertionError('impossible record accepted')
    result={'status':'passed','seed':100912,'small_oracle':records,'larger':larger,'mps_sensitivity':mps,'kac_ward_research':kw,'seconds':time.perf_counter()-t,'scope':'light verification; no asymptotic or all-record floating-point stability claim'}
    (LAB/'results/validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':run()
