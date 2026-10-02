"""Finite checks of analytic thermodynamic statements; no scaling fit."""
from collections import Counter
from fractions import Fraction as F
from itertools import product
from math import comb, log, sqrt, lcm
import hashlib
import json
import time
import numpy as np
from current_oracle import LAB, ROOT, square_graph, charge_matrix
from check_connected_current_defects import enumerate_paths, honeycomb_geometry


def mul(x,y):
    return (x[0]*y[0]+2*x[1]*y[1],x[0]*y[1]+x[1]*y[0])


def add(x,y): return (x[0]+y[0],x[1]+y[1])
def neg(x): return (-x[0],-x[1])
def scale(a,x): return (a*x[0],a*x[1])


def algebra():
    one=(F(1),F(0)); t=(F(3,2),F(-1)); mu2=(F(2),F(1))
    # Exact coefficient pairs in Q(sqrt(2)); positivity uses 17^2>2*12^2.
    margin=add(mul(add(one,t),add(one,t)),neg(scale(4,mul(mu2,t))))
    assert margin == mul(t,t) == (F(17,4),F(-3))
    assert 17**2 > 2*12**2
    assert mul(mu2,add(one,scale(2,t))) == (F(4),F(0))
    mu=sqrt(2+sqrt(2)); t0=(3-2*sqrt(2))/2
    qstar=(1+sqrt(1-4*t0*t0))/2
    checks=[]
    for q in (.993,.995,.999,1.):
        tq=sqrt(q*(1-q)); pconv=1/(1+tq)
        gcur=.5*sqrt(1+2*tq); gbin=2*sqrt(tq)/(1+tq)
        assert mu*gcur<1 and mu*gbin<1
        growth=(mu+1/max(gcur,gbin))/2
        rho=growth*max(gcur,gbin)
        assert mu<growth and rho<1
        checks.append({'q':q,'convexity_endpoint':pconv,'current_factor':mu*gcur,
                       'binary_tail_factor':mu*gbin,'chosen_walk_growth':growth,
                       'rho':rho,'asymptotic_lower_rate_per_L':-1.5*log(rho)})
    return {'mu_hex':mu,'qstar':qstar,'opposite_window_endpoint':1-qstar,
            'exact_margin_coefficients':['17/4','-3'],
            'exact_margin_positive_certificate':'17^2 > 2*12^2',
            'binary_low_endpoint_hex':(1-sqrt(1-1/mu**2))/2,
            'binary_low_endpoint_square_degree_bound':(1-sqrt(1-1/9))/2,
            'uniform_window_checks':checks}


def entropy(prob):
    return -sum(float(x)*log(float(x)) for x in prob if x>0)


def finite_checks():
    g=square_graph(3); E=len(g.edges); D=charge_matrix(g)
    states=np.array(list(product((0,1,-1),repeat=E)),dtype=np.int8)
    charges=states@D.T
    _,qids=np.unique(charges,axis=0,return_inverse=True)
    binary=(states!=0).astype(np.int8)
    parity=(binary[:,list(g.logical_edges)].sum(axis=1)%2).astype(int)
    patterns=np.array(list(product((0,1),repeat=E)),dtype=np.int8)
    psyn=(patterns@D.T)%2
    chosen={}
    for i,sy in enumerate(psyn):
        key=tuple(sy); old=chosen.get(key)
        if old is None or (int(patterns[i].sum()),i)<(int(patterns[old].sum()),old): chosen[key]=i
    _,paths,_=enumerate_paths(g,retain=True)
    supports=[np.flatnonzero(x) for x in paths]
    nplus=(states==1).sum(axis=1); nminus=(states==-1).sum(axis=1)
    rows=[]; binary_reference={}
    for p in map(F,('0','1/20','3/10','1/2','4/5','19/20','1')):
      for q in map(F,('1/2','9/10','199/200','1')):
        raw=(1-p,p*q,p*(1-q)); den=lcm(*(x.denominator for x in raw))
        A,B,C=[int(x*den) for x in raw]
        lookup={(u,v):A**(E-u-v)*B**u*C**v for u in range(E+1) for v in range(E+1-u)}
        weights=[lookup[int(u),int(v)] for u,v in zip(nplus,nminus)]
        assert sum(weights)==den**E
        joint=[[0,0] for _ in range(int(qids.max())+1)]
        for i,w in enumerate(weights):joint[int(qids[i])][int(parity[i])]+=w
        exact=F(sum(min(x) for x in joint),den**E)
        jp=np.array([[float(F(x,den**E)) for x in row] for row in joint])
        PQ=jp.sum(axis=1); mask=PQ>0; PQ=PQ[mask]; jp=jp[mask]
        posterior=jp/PQ[:,None]; Hcond=sum(PQ[i]*entropy(r) for i,r in enumerate(posterior))
        HQ=entropy(PQ); HQH=entropy(jp.flatten())
        Fbest=sum(-pQ*log(max(pair)) for pQ,pair in zip(PQ,jp))
        R=float(exact)
        assert abs(HQH-HQ-Hcond)<2e-12
        assert -1e-12<=Fbest-HQ<=log(2)+1e-12
        assert 2*log(2)*R<=Hcond+1e-12<=entropy([R,1-R])+2e-12
        complement=p>F(1,2); residual=1-binary if complement else binary
        predicted=np.array([patterns[chosen[tuple((D@y)%2)]] for y in residual])
        wrong=((predicted[:,list(g.logical_edges)].sum(axis=1)-residual[:,list(g.logical_edges)].sum(axis=1))%2)!=0
        witnessed=np.zeros(len(states),dtype=bool)
        for support in supports:witnessed|=(2*residual[:,support].sum(axis=1)>=len(support))
        assert not np.any(wrong&~witnessed)
        rb=F(sum(w for w,bad in zip(weights,wrong) if bad),den**E)
        assert exact<=rb
        if p in binary_reference:assert rb==binary_reference[p]
        binary_reference[p]=rb
        # This complements only the parity-only baseline on binary occupancy.
        # It is not a symmetry assertion about full charge or incomplete herald records.
        r=min(p,1-p)
        pathsum=sum(sum(F(comb(len(s),k))*r**k*(1-r)**(len(s)-k)
                        for k in range((len(s)+1)//2,len(s)+1)) for s in supports)
        assert rb<=pathsum
        gaps=np.array([abs(log(row[0]/row[1])) if min(row)>0 else np.inf for row in jp])
        for K in (0.,1.,3.):
            small=float(PQ[gaps<=K+1e-14].sum())
            assert small<=(1+np.exp(K))*R+1e-12
        rows.append({'p':float(p),'q':float(q),'Bayes_LER_exact':str(exact),
                     'parity_only_risk_exact':str(rb),'parity_path_upper_exact':str(pathsum),
                     'charge_entropy':HQ,'selected_sector_free_energy':HQH,
                     'conditional_logical_entropy':Hcond,'dominant_sector_excess_free_energy':Fbest-HQ})
    return {'states':len(states),'cells':rows,'missing_binary_witnesses':0}


def main():
    start=time.monotonic(); alg=algebra(); finite=finite_checks()
    geom=[honeycomb_geometry(L) for L in (3,4,5,7,9,11)]
    elapsed=time.monotonic()-start; assert elapsed<120
    files=['scripts/check_thermodynamic_limits.py','scripts/check_connected_current_defects.py','scripts/current_oracle.py']
    hashes={str((LAB/f).relative_to(ROOT)):hashlib.sha256((LAB/f).read_bytes()).hexdigest() for f in files}
    hashes['src/herald_decoder/lattice_model.py']=hashlib.sha256((ROOT/'src/herald_decoder/lattice_model.py').read_bytes()).hexdigest()
    out={'status':'passed','scope':'Finite checks of proved thermodynamic statements; no fitted transition.',
         'algebra':alg,'finite':finite,'geometry':geom,'new_physical_record_samples':0,
         'elapsed_seconds':elapsed,'source_sha256':hashes}
    (LAB/'results/thermodynamic-limits-2026-09-20.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':'passed','algebra':alg,'finite_cells':len(finite['cells']),
                      'finite_states':finite['states'],'seconds':elapsed},indent=2))


if __name__=='__main__':main()
