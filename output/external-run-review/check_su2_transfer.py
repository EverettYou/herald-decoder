"""Small-patch test of full-SU(2)-record transfer to the external matchgate graph."""
import sys,json,itertools
from pathlib import Path
import numpy as np
sys.path.insert(0,'/Users/home/Downloads/runs/anthropic__claude-opus-5-5/run_03/src')
sys.path.insert(0,str(Path.cwd()/'labs/lab-006-sun-bp-theory/scripts'))
import heralded.decoder as module
from heralded.lattice import build_patch
from heralded.noise import gf2_nullspace
from numba_fusion_decoder import group_fusion_distribution
bank=np.zeros((4,5))
for n in range(4):
 for R,f in group_fusion_distribution('SU2',('fund',)*n).items():bank[n,int(R)]=f
# This process-local replacement supplies the repository full-irrep likelihood.
# No external or production source file is edited.
def local(n,R,q):return bank[np.asarray(n),np.asarray(R)]
module.vertex_factor=local
rng=np.random.default_rng(20261001);out={'scope':'small-patch full-SU2-record transfer, not a scaling experiment','bank':bank.tolist(),'cases':[]}
for L in [2,3]:
 P=build_patch(L);dec=module.MLDecoder(P);basis=gf2_nullspace(P.H.toarray());k=len(basis)
 coef=np.array(list(itertools.product([0,1],repeat=k)),np.uint8);Y=(coef@basis.astype(int))%2
 maxerr=0.
 for i in range(60):
  p=[.1,.3,.5][i%3];x=(rng.random(P.n_edges)<p).astype(np.uint8);n=P.counts(x);s=n&1
  R=np.array([rng.choice(5,p=bank[v]) for v in n]);c0,pf=dec.posterior(p,0,s,R)
  X=Y^c0;nv=(P.H@X.T).T;wt=X.sum(1)
  w=p**wt*(1-p)**(P.n_edges-wt)*np.prod(bank[nv,R[None]],axis=1)
  ell=(X[:,P.gamma_R].sum(1)%2);exact=w[ell!=P.logical(c0)].sum()/w.sum()
  maxerr=max(maxerr,abs(pf-exact))
 assert maxerr<1e-10
 out['cases'].append(dict(L=L,trials=60,max_posterior_error=float(maxerr)))
 print(out['cases'][-1],flush=True)
f0=group_fusion_distribution('SU2',())['1'];f2=group_fusion_distribution('SU2',('fund',)*2)['1'];f4=group_fusion_distribution('SU2',('fund',)*4)['1']
out['square_singlet_matchgate_identity']={'f0':f0,'f2':f2,'f4':f4,'f0_f4':f0*f4,'f2_squared':f2*f2,'satisfied':f0*f4==f2*f2}
Path('output/external-run-review/su2-transfer.json').write_text(json.dumps(out,indent=2)+'\n')
