"""Independent bounded audit; candidate sources run only from /tmp copies.

Usage: python audit_run.py MODEL RUN. No campaign or downloaded shell is run.
Oracle uses literal physical law, independently of candidate likelihood code.
"""
import sys, json, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'output/scicode2/private'))
from audit_lattice_construction import construction
model, run = sys.argv[1:3]
base=Path('/tmp/scicode2-run-audit')/model/run
extra='src' if 'opus' in model or ('fable' in model and run=='run_01') else ''
sys.path.insert(0,str(base/extra))
native=True
if 'fable' in model:
    if run=='run_01':
        from honeycomb import build_lattice as build
        from decoders import HMWDecoder,MLDecoder
        def decoder(g,p,q): return lambda s,h:HMWDecoder(g,p,q).decode(s,h)
        maskattr='logical_mask'
    elif run=='run_02':
        from hexcode import build_patch as build,decode
        import hexcode.decoder as dc
        # Linux LEMON shared object cannot run on macOS. Check the unchanged
        # gadget formulation with NetworkX's exact integer blossom backend.
        import networkx as nx
        def replacement(n,eu,ev,cost):
            G=nx.Graph();G.add_nodes_from(range(n))
            for u,v,w in zip(eu,ev,cost): G.add_edge(int(u),int(v),weight=-int(w))
            matching=nx.max_weight_matching(G,maxcardinality=True)
            if 2*len(matching)!=n:return None
            mate=np.full(n,-1,int)
            for u,v in matching:mate[u]=v;mate[v]=u
            return mate
        dc.min_weight_perfect_matching=replacement;native=False
        def decoder(g,p,q):return lambda s,h:decode(g,p,q,s,h)
        maskattr='gammaR'
    else:
        from honeycomb import HoneycombPatch as build
        from decoder import decode
        def decoder(g,p,q):return lambda s,h:decode(g,p,q,s,h)
        maskattr='gamma_R'
elif 'opus' in model:
    if run=='run_01':
        from honeycomb import build_patch as build
        from decoder_api import decode
        def decoder(g,p,q):return lambda s,h:decode(g,p,q,s,h)
        maskattr='gammaR'
    elif run=='run_02':
        from lattice import build_patch as build
        from decoder import HeraldedMLDecoder
        def decoder(g,p,q):
            d=HeraldedMLDecoder(g,use_cache=False)
            return lambda s,h:d.decode(p,q,s,h)
        maskattr='logical_edges'
    else:
        from heralded.lattice import build_patch as build
        from heralded.decoder import MLDecoder
        def decoder(g,p,q):
            d=MLDecoder(g)
            return lambda s,h:d.decode(p,q,s,h)
        maskattr='gamma_R'
else:
    if run=='run_02':
        from honeycomb.geometry import make_graph as build
        from honeycomb.decoder import decode
        def decoder(g,p,q):return lambda s,h:decode(g,p,q,s,h)
    else:
        from honeycomb import make_patch as build
        from decoder import decode
        def decoder(g,p,q):return lambda s,h:decode(g,p,q,s,h)
    maskattr='logical'

def arrays(g):
    coords=np.asarray(g.coords if hasattr(g,'coords') else g.vertices)
    edges=np.asarray(g.edges)
    if edges.ndim==3: e=[tuple(sorted(map(tuple,x))) for x in edges]
    else:e=[tuple(sorted((tuple(coords[u]),tuple(coords[v])))) for u,v in edges]
    ds=np.asarray(g.detectors)
    dets=list(map(tuple,ds)) if ds.ndim==2 else [tuple(coords[v]) for v in ds]
    H=g.H.toarray() if hasattr(g.H,'toarray') else g.H
    raw=np.asarray(getattr(g,maskattr));mask=np.zeros(len(e),np.uint8)
    if maskattr in ['logical_edges'] or ('opus' in model and run=='run_03'):mask[raw]=1
    else:mask=raw.astype(np.uint8)
    return coords,e,dets,np.asarray(H,dtype=np.uint8),mask

result={'model':model,'run':run,'native_backend':native,'geometry':[],'tests':[]}
for L in [2,3,4]:
    g=build(L);coords,e,ds,H,mask=arrays(g);c=construction(L)
    checks={'vertices':set(map(tuple,coords))==c['vertices'],
      'edges':set(e)==c['edges'],'detectors':set(ds)==c['detectors'],
      'H':np.array_equal(H,np.array([[v in edge for edge in e] for v in ds],np.uint8)),
      'logical':{edge for edge,m in zip(e,mask) if m}==c['logical']}
    result['geometry'].append({'L':L,**checks});assert all(checks.values())

g=build(2);coords,edges,ds,H,mask=arrays(g)
X=((np.arange(2**len(edges))[:,None]>>np.arange(len(edges)))&1).astype(np.uint8)
N=X@H.T;S=N%2;ell=(X@mask)%2;elig=N>=2
rng=np.random.default_rng(284761)
for p,q in [(0.2,0.5),(0.4,0.9),(0.5,0),(0.5,1),(0,0.5)]:
    d=decoder(g,p,q);prior=p**X.sum(1)*(1-p)**(len(edges)-X.sum(1))
    risk=opt=0.;invalid=wrongmap=wrongml=0;max_posterr=0.;nr=0
    # Enumerate every physically possible L=2 record, with its true joint mass.
    for si in range(2**len(ds)):
        s=((si>>np.arange(len(ds)))&1).astype(np.uint8)
        ix=np.flatnonzero(np.all(S==s,axis=1));xs=X[ix];el=elig[ix]
        for hi in range(2**len(ds)):
            h=((hi>>np.arange(len(ds)))&1).astype(np.uint8)
            like=np.prod(np.where(h,np.where(el,q,0),np.where(el,1-q,1)),axis=1)
            w=prior[ix]*like;total=w.sum()
            if total<1e-300:continue
            nr+=1;mass=np.bincount(ell[ix],weights=w,minlength=2);opt+=min(mass)
            try:
                c=np.asarray(d(s,h));valid=c.shape==(len(edges),) and np.all((c==0)|(c==1)) and np.array_equal(H@c%2,s)
            except Exception as exc:
                valid=False
                if invalid==0:result.setdefault('first_exception',repr(exc))
            if not valid:invalid+=1;risk+=total;continue
            decision=int(c@mask%2);risk+=mass[1-decision]
            if mass[decision]+1e-11*total<max(mass):wrongml+=1
            # Canonical representative is allowed; assess if selected sector
            # contains a MAP configuration rather than testing c's own support.
            best=[max(w[ell[ix]==k],default=0) for k in [0,1]]
            if best[decision]+1e-10*max(best)<max(best):wrongmap+=1
    result['tests'].append({'p':p,'q':q,'records':nr,'invalid':invalid,
      'exact_L2_risk':risk,'optimal_L2_risk':opt,'nonoptimal_logical_records':wrongml,
      'nonMAP_sector_records':wrongmap})
    print(json.dumps(result['tests'][-1]),flush=True)
out=ROOT/'output/scicode2/run_evaluation'/f'{model}_{run}_audit.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print('SAVED',out,flush=True)
