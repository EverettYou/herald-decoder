"""Deterministic error budgets for the Wiener connected-cumulant expansion."""
from pathlib import Path
import cmath
import hashlib
import json
import math

import numpy as np

from current_oracle import LAB, ROOT


ORDERS=(1,2,3,4,5,6,8,10,12,16,24,32,48,64)
PVALUES=(.05,.08,.1,.3,.46)
TARGETS=(1e-2,1e-3,1e-4)
E=32


def tail(z,N):
    return -math.log1p(-z)-sum(z**n/n for n in range(1,N+1))


def polynomial(x,N):
    return sum((-1)**(n+1)*x**n/n for n in range(1,N+1))


def main():
    rows=[]; phases=np.linspace(-math.pi,math.pi,4097)
    scalar_max=0.; product_max=0.
    for p in PVALUES:
        z=p/(1-p); budgets=[]
        for N in ORDERS:
            r=max(0.,tail(z,N)); eps=math.expm1(E*r); ler=eps/2
            # q=.37 is a non-symmetric deterministic spot check. The proof is
            # q-uniform and does not rely on this grid.
            q=.37; S=q*np.exp(1j*phases)+(1-q)*np.exp(-1j*phases); x=z*S
            exact=np.log(1+x); approx=np.array([polynomial(y,N) for y in x])
            serr=float(np.max(np.abs(exact-approx)))
            scalar_max=max(scalar_max,serr-r)
            assert serr<=r+2e-14
            # Aligned-edge product is a stringent pointwise check of the
            # Banach-algebra product estimate, not a replacement for it.
            F=(1-p)**E*(1+x)**E; FN=(1-p)**E*np.exp(E*approx)
            perr=float(np.max(np.abs(F-FN)))
            product_max=max(product_max,perr-eps)
            assert perr<=eps+2e-12
            budgets.append({'N':N,'log_remainder_bound':r,'full_Wiener_error_bound':eps,
                            'absolute_LER_error_bound':ler,'scalar_grid_max_error':serr,
                            'aligned_product_grid_max_error':perr})
        minimum={str(t):next((b['N'] for b in budgets if b['absolute_LER_error_bound']<=t),None) for t in TARGETS}
        rows.append({'p':p,'z':z,'E':E,'budgets':budgets,'minimum_N_for_LER_error':minimum,
                     'promoted_at_1e-3':minimum[str(1e-3)] is not None})
    assert next(r for r in rows if r['p']==.08)['promoted_at_1e-3']
    manifest=LAB/'manifests/wiener-cumulant-feasibility-2026-09-19.json'
    files=[Path(__file__),manifest,LAB/'scripts/current_oracle.py',ROOT/'src/herald_decoder/lattice_model.py']
    out={'status':'passed','scope':'Uniform Wiener connected-cumulant error budget; representation only, L5 coefficient contraction not yet executed.',
         'derivation':{'z':'p/(1-p)','r_N':'sum_{n>N} z^n/n','full_error':'exp(E*r_N)-1','LER_error':'[exp(E*r_N)-1]/2'},
         'cells':rows,'scalar_grid_bound_slack':scalar_max,'product_grid_bound_slack':product_max,
         'decision':'promote_finite_harmonic_evaluation',
         'next_method':'Construct a finite-harmonic approximation to exp(P_N) with its own Wiener tail, then contract the twisted charge coefficients and report LER_N plus the combined certified error.',
         'claims_prohibited':['No L5 LER value has been computed by this feasibility test.','No threshold or continuum claim.'],
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (LAB/'results/wiener-cumulant-feasibility-2026-09-19.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'decision':out['decision'],
                      'minimum_orders':{str(r['p']):r['minimum_N_for_LER_error'] for r in rows},
                      'scalar_grid_bound_slack':scalar_max,'product_grid_bound_slack':product_max},indent=2))


if __name__=='__main__': main()
