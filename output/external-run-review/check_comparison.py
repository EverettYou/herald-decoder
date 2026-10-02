"""Bounded review, not a threshold campaign. External source files are read only."""
import sys, json, time, warnings
from pathlib import Path
import numpy as np
import pymatching
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,'/Users/home/Downloads/runs/anthropic__claude-opus-5-5/run_03/src')
from herald_decoder.lattice_model import honeycomb_graph
from herald_decoder.herald_bp_decoder import HeraldBeliefMatchingDecoder
from heralded.lattice import build_patch
from heralded.decoder import MLDecoder

def match_graph(L):
    g=honeycomb_graph(L); P=build_patch(L)
    coords=[(round(2*v.x),round(2*v.y/np.sqrt(3))) for v in g.vertices]
    lookup={tuple(c):i for i,c in enumerate(P.coords)}
    vm=np.array([lookup[c] for c in coords]); pe={tuple(e):i for i,e in enumerate(P.edges)}
    em=np.array([pe[tuple(sorted((vm[u],vm[v])))] for u,v in g.edges])
    dm=np.array([list(P.detectors).index(vm[v]) for v in g.detector_vertices])
    assert len(g.vertices)==P.n_vertices and len(g.edges)==P.n_edges
    assert np.array_equal(g.check_matrix.toarray(),P.H.toarray()[dm][:,em])
    # Difference between the two logical cuts must vanish on ker H.
    from heralded.noise import gf2_nullspace
    diff=np.array([int(e in g.logical_edges)^int(em[e] in P.gamma_R) for e in range(len(em))])
    # Independent row-space test, rather than exponential kernel enumeration.
    A=g.check_matrix.toarray().astype(np.uint8); y=diff.copy()
    row=0
    for c in range(A.shape[1]):
        pivot=np.flatnonzero(A[row:,c])
        if not len(pivot): continue
        rr=row+pivot[0]; A[[row,rr]]=A[[rr,row]]
        if y[c]: y^=A[row]
        for rr in range(row+1,len(A)):
            if A[rr,c]: A[rr]^=A[row]
        row+=1
        if row==len(A):break
    assert not y.any(), 'Logical cuts differ on syndrome-free residuals'
    return g,P,em,dm,dict(L=L,vertices=len(g.vertices),edges=len(g.edges),detectors=len(dm),geometry_equal=True,logical_cuts_equivalent=True)

def map_decode(g,p,q,s,h):
    H=g.check_matrix; deg=np.asarray(H.sum(axis=0)).ravel().astype(float)
    hits=np.asarray(h.astype(float)@H).ravel()
    a=np.log((1-p)/p)
    if q==1:
        soft=np.full(H.shape[1],a if a else 0.)
        M=np.sum(abs(soft))+1
        w=soft+M*(deg-2*hits)
    else:
        b=-.5*np.log1p(-q)
        soft=a+(deg-hits)*b
        M=np.sum(abs(soft))+1
        w=soft-M*hits
    c=pymatching.Matching.from_check_matrix(H,weights=w,merge_strategy='disallow').decode(s).astype(np.uint8)
    assert np.array_equal(g.true_syndrome(c),s)
    counts=g.degrees(c)[list(g.detector_vertices)]
    assert np.all(counts[h==1]>=2)
    if q==1:assert np.all(counts[h==0]<2)
    return c

out={'scope':'matched finite-size pilot, not a threshold estimate','seed':20261001,'n_per_cell':500,'geometry':[],'cells':[]}
for L in [2,3,8,16]:
    g,P,em,dm,check=match_graph(L);out['geometry'].append(check)
    print('geometry',check,flush=True)
for L,p,q in [(8,.23,.5),(16,.23,.5),(8,.4,.85),(16,.4,.85),(8,.5,1.),(16,.5,1.)]:
    g,P,em,dm,_=match_graph(L); ml=MLDecoder(P)
    decs={'bp_sync40':HeraldBeliefMatchingDecoder(g,p=p,q=q,use_numba=True),
          'bp_residual80':HeraldBeliefMatchingDecoder(g,p=p,q=q,max_iterations=80,update_schedule='residual_priority',residual_priority_order='stable_sort',use_numba=True)}
    rng=np.random.default_rng(np.random.SeedSequence([out['seed'],L,round(p*10000),round(q*10000)]))
    n=out['n_per_cell']; totals={k:0 for k in [*decs,'map','ml']}; conv={k:0 for k in decs}; rb=[]; paired={k:[] for k in [*decs,'map']}; invalid={k:0 for k in totals}; t=time.perf_counter()
    for i in range(n):
        x=(rng.random(len(g.edges))<p).astype(np.uint8)
        counts=g.degrees(x)[list(g.detector_vertices)];s=counts&1;h=((counts>=2)&(rng.random(len(counts))<q)).astype(np.uint8)
        ps=np.empty_like(s);ph=np.empty_like(h);ps[dm]=s;ph[dm]=h
        xp=np.empty_like(x);xp[em]=x
        c0,pf=ml.posterior(p,q,ps,ph);cm=c0.astype(np.uint8).copy()
        if pf>.5:cm^=P.logical_path
        mlbad=int(P.logical(xp^cm));totals['ml']+=mlbad;rb.append(min(pf,1-pf))
        invalid['ml']+=int(not np.array_equal(P.syndrome(cm),ps))
        c=map_decode(g,p,q,s,h);bad=int(g.logical_parity(x^c));totals['map']+=bad;paired['map'].append(bad-mlbad)
        for k,d in decs.items():
            result=d.decode(s,h); c=result.correction;conv[k]+=int(result.bp.converged)
            bad=int(g.logical_parity(x^c) or not np.array_equal(g.true_syndrome(c),s));totals[k]+=bad;paired[k].append(bad-mlbad);invalid[k]+=int(not np.array_equal(g.true_syndrome(c),s))
    cell=dict(L=L,p=p,q=q,n=n,failures=totals,ler={k:v/n for k,v in totals.items()},bp_converged=conv,invalid=invalid,ml_rb_mean=float(np.mean(rb)),ml_rb_se=float(np.std(rb,ddof=1)/np.sqrt(n)),paired_difference_vs_ml={k:{'mean':float(np.mean(v)),'se':float(np.std(v,ddof=1)/np.sqrt(n))} for k,v in paired.items()},seconds=time.perf_counter()-t)
    out['cells'].append(cell);print(json.dumps(cell),flush=True)
    (ROOT/'output/external-run-review/comparison.json').write_text(json.dumps(out,indent=2)+'\n')
