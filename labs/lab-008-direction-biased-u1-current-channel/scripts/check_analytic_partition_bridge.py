"""Independent finite checks of analytic partition-function predictions."""
from itertools import product, combinations
from math import comb, ceil
from pathlib import Path
import hashlib
import json
import numpy as np
from current_oracle import LAB, ROOT, square_graph, charge_matrix, exact_enumeration


def path_formula(d,p,q):
    a,b,c=1-p,p*q,p*(1-q)
    return min(a**d,b**d+c**d)+sum(comb(d,k)*min(a**(d-k)*b**k,a**k*c**(d-k)) for k in range(1,d))


def path_enumeration(d,p,q):
    table={}
    for values in product((0,1,-1),repeat=d):
        j=np.array(values);weight=np.prod(np.where(j==0,1-p,np.where(j==1,p*q,p*(1-q))))
        Q=tuple(j[:-1]-j[1:]);h=abs(int(j[0]))%2
        table.setdefault(Q,np.zeros(2))[h]+=weight
    return sum(min(z) for z in table.values())


def leading_square(L,q):
    directed=q==1
    g=square_graph(L);D=charge_matrix(g);E=len(g.edges);distance=L-1
    limit=distance if directed else ceil(distance/2);table={};states=0
    for k in range(limit+1):
        for support in combinations(range(E),k):
            h=sum(e in g.logical_edges for e in support)%2
            for signs in product((1,) if directed else (1,-1),repeat=k):
                j=np.zeros(E,dtype=np.int8);j[list(support)]=signs;Q=(D@j).tobytes()
                row=table.setdefault(Q,[[E+1,0.],[E+1,0.]])
                if row[h][0]>k:row[h]=[k,0.]
                if row[h][0]==k:row[h][1]+=q**sum(s==1 for s in signs)*(1-q)**sum(s==-1 for s in signs)
                states+=1
    exponent=E+1;coefficient=0.;ambiguous=0
    for row in table.values():
        k0,c0=row[0];k1,c1=row[1];order=max(k0,k1)
        if order>limit:continue
        ambiguous+=1
        c=c0 if k0>k1 else c1 if k1>k0 else min(c0,c1)
        if order<exponent:exponent=order;coefficient=0.
        if order==exponent:coefficient+=c
    assert exponent==limit and coefficient>0
    predicted=comb(2*distance,distance) if directed else (L*comb(distance,distance//2)*min(q,1-q)**(distance//2) if distance%2==0 else None)
    if predicted is not None:assert abs(coefficient-predicted)<1e-10
    return {'L':L,'distance':distance,'q':q,'enumerated_low_activity_states':states,
            'leading_power':exponent,'leading_coefficient':coefficient,'ambiguous_records_within_order':ambiguous}


def main():
    checks=[]
    for d in range(1,7):
        for p in (.1,.3,.46):
            for q in (.5,.75,.97,1.):
                x=path_formula(d,p,q);y=path_enumeration(d,p,q);assert abs(x-y)<1e-10
                checks.append({'d':d,'p':p,'q':q,'analytic':x,'enumerated':y,'error':abs(x-y)})
    g=square_graph(3);D=charge_matrix(g);n=9;M=D.shape[0];p=.3;q=.75
    mesh=np.indices((n,)*M).reshape(M,-1).T*(2*np.pi/n);phi=mesh@D
    table=exact_enumeration(g,p,q);errors=[];coefficients=[]
    cut=np.array([e in g.logical_edges for e in range(len(g.edges))])
    for twist in (0,1):
        x=phi+np.pi*twist*cut
        K=1-p+p*q*np.exp(1j*x)+p*(1-q)*np.exp(-1j*x)
        A=np.fft.fftn(np.prod(K,axis=1).reshape((n,)*M))/(n**M)
        err=max(abs(A[tuple(int(x)%n for x in Q)]-(z[0]+(-1)**twist*z[1])) for Q,(z,_,_) in table.items())
        assert err<1e-10;errors.append(float(err));coefficients.append(A)
    from_K=float((1-np.abs(coefficients[1]).sum())/2)
    enumerated=sum(min(z) for z,_,_ in table.values());assert abs(from_K-enumerated)<1e-10
    leading=[leading_square(L,q) for L in (3,4,5) for q in (.5,.75,.97,1.)]
    files=[Path(__file__),ROOT/'src/herald_decoder/lattice_model.py',LAB/'scripts/current_oracle.py',
           LAB/'manifests/analytic-partition-bridge-2026-09-18.json']
    out={'status':'passed','path_cases':len(checks),'path_max_error':max(c['error'] for c in checks),'path_checks':checks,
         'K_fourier':{'L':3,'p':p,'q':q,'grid_per_vertex':n,'quadrature_points':n**M,'sector_record_cases':len(table),
                      'twist_max_errors':errors,'LER_from_K':from_K,'LER_from_enumeration':enumerated},
         'square_low_activity_expansion':leading,
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files if 'manifests' not in str(f)},
         'scope':'Independent finite checks accompany analytic proofs; no moderate-p full 2D formula or phase claim.'}
    (LAB/'results/analytic-partition-bridge-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('path_checks','source_sha256')},indent=2))


if __name__=='__main__':main()
