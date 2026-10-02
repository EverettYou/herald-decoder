"""Exact physical-sector asymptotics in the singular directional boundary layer."""
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
from math import comb, lcm
import hashlib
import json
import time
import numpy as np
from current_oracle import LAB, ROOT, square_graph, charge_matrix


def leading_table(L, alpha):
    g = square_graph(L); E = len(g.edges); d = L-1
    scale = alpha.denominator
    beta = scale+alpha.numerator
    families = [(u,v) for v in range(d*scale//beta+1)
                for u in range((d*scale-beta*v)//scale+1)]
    total = sum(comb(E,v)*comb(E-v,u) for u,v in families)
    assert total <= 100000
    D = charge_matrix(g); cut = set(g.logical_edges)
    records = {}
    for u,v in families:
        cost = u*scale+v*beta
        for neg in combinations(range(E),v):
            rest = tuple(e for e in range(E) if e not in neg)
            negQ = D[:,neg].sum(axis=1) if neg else np.zeros(D.shape[0],dtype=int)
            negpar = sum(e in cut for e in neg)
            for pos in combinations(rest,u):
                Q = (D[:,pos].sum(axis=1) if pos else 0)-negQ
                key = tuple(int(x) for x in Q)
                parity = (sum(e in cut for e in pos)+negpar)%2
                pair = records.setdefault(key, [None,None]); old = pair[parity]
                if old is None or cost < old[0]: pair[parity] = [cost,Counter({v:1})]
                elif cost == old[0]: old[1][v] += 1
    finite = [(Q,a,b) for Q,(a,b) in records.items() if a is not None and b is not None]
    nu_scaled = min(max(a[0],b[0]) for _,a,b in finite)
    leading = [(Q,a,b) for Q,a,b in finite if max(a[0],b[0]) == nu_scaled]
    theory = min(max(Fraction(k),(1+alpha)*(d-k)) for k in range(d+1))
    assert Fraction(nu_scaled,scale) == theory
    def coefficient(lam):
        out = Fraction(0)
        for _,a,b in leading:
            ca = sum(n*lam**v for v,n in a[1].items())
            cb = sum(n*lam**v for v,n in b[1].items())
            out += ca if a[0]>b[0] else cb if b[0]>a[0] else min(ca,cb)
        return out
    rows = []
    if alpha == d-1:
        for lam in map(Fraction,('1/4','1/2','1','2','4')):
            measured = coefficient(lam)
            predicted = comb(2*d,d)+L*d*lam+(L-2)*d*min(lam,1)
            assert measured == predicted, (L,lam,measured,predicted)
            rows.append({'lambda':float(lam),'coefficient_exact':str(measured),'predicted_exact':str(predicted)})
    return {'L':L,'alpha':str(alpha),'states':total,'charge_records':len(records),
            'exponent_exact':str(Fraction(nu_scaled,scale)), 'predicted_exponent':str(theory),
            'leading_records':len(leading), 'critical_coefficients':rows}


def full_L3():
    g=square_graph(3); E=len(g.edges); D=charge_matrix(g)
    groups={}
    for raw in product((0,1,-1),repeat=E):
        j=np.array(raw,dtype=np.int8)
        Q=tuple(int(x) for x in D@j)
        parity=int(j[list(g.logical_edges)].sum())%2
        pair=groups.setdefault(Q,[Counter(),Counter()])
        pair[parity][int((j==1).sum()),int((j==-1).sum())] += 1
    rows=[]
    for p in map(Fraction,('1/200','1/100','1/50')):
        for lam in map(Fraction,('1/4','1','4')):
            q=1-lam*p
            raw=(1-p,p*q,p*(1-q)); den=lcm(*(x.denominator for x in raw))
            A,B,C=[int(x*den) for x in raw]
            weights={(u,v):A**(E-u-v)*B**u*C**v for u in range(E+1) for v in range(E+1-u)}
            numerator=0; normalization=0
            for pair in groups.values():
                joint=[sum(n*weights[key] for key,n in sector.items()) for sector in pair]
                numerator+=min(joint); normalization+=sum(joint)
            assert normalization == den**E
            risk=Fraction(numerator,den**E)
            coefficient=6+6*lam+2*min(lam,1)
            rows.append({'p':float(p),'q':float(q),'lambda':float(lam),
                         'Bayes_LER_exact':str(risk),'Bayes_LER':float(risk),
                         'risk_over_p2':float(risk/p**2),'limiting_coefficient':float(coefficient),
                         'relative_asymptotic_error':float(abs(risk/p**2-coefficient)/coefficient)})
    return {'states':3**E,'records':len(groups),'cells':rows}


def main():
    start=time.monotonic()
    rows=[leading_table(L,Fraction(str(a))) for L in (3,4,5) for a in (.5,1,2,3)]
    exact=full_L3()
    elapsed=time.monotonic()-start
    assert elapsed < 120
    files=['scripts/check_directional_crossover.py','scripts/current_oracle.py',
           'wiki/partition-function-ler.md']
    hashes={str((LAB/f).relative_to(ROOT)):hashlib.sha256((LAB/f).read_bytes()).hexdigest() for f in files}
    hashes['src/herald_decoder/lattice_model.py']=hashlib.sha256((ROOT/'src/herald_decoder/lattice_model.py').read_bytes()).hexdigest()
    out={'status':'passed','scope':'Fixed-size p->0 asymptotics for 1-q=lambda*p^alpha; no finite-p fit or threshold.',
         'exponent_checks':rows,'critical_coefficient_checks':sum(len(x['critical_coefficients']) for x in rows),
         'finite_L3_control':exact,'new_physical_record_samples':0,'elapsed_seconds':elapsed,'source_sha256':hashes}
    (LAB/'results/directional-crossover-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exponents':[{k:v for k,v in r.items() if k!='critical_coefficients'} for r in rows],
                      'coefficient_checks':out['critical_coefficient_checks'],'finite_L3':exact['cells'],'seconds':elapsed},indent=2))


if __name__=='__main__': main()
