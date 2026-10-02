"""Fresh common-random-number comparison: repo BP, Astra MAP, Opus ML.

All candidates get coordinate-relabelled observations only. All failures kept.
"""
import sys,json,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from herald_decoder.lattice_model import honeycomb_graph
from herald_decoder.herald_bp_decoder import HeraldBeliefMatchingDecoder
sys.path.insert(0,'/tmp/scicode2-run-audit/openai__gpt-6-astra/run_03')
from honeycomb import make_patch
from decoder import WitnessDecoder
# Avoid generic module-name collision with Opus's src/decoder.py.
sys.path.insert(0,'/tmp/scicode2-run-audit/anthropic__claude-opus-5-5/run_03/src')
from heralded.lattice import build_patch
from heralded.decoder import MLDecoder

rows=[];raw=[]
for L in [7,11]:
    rg=honeycomb_graph(L);ag=make_patch(L);og=build_patch(L);od=MLDecoder(og)
    rc=[(round(2*v.x),round(2*v.y/np.sqrt(3))) for v in rg.vertices]
    re=[tuple(sorted((rc[u],rc[v]))) for u,v in rg.edges]
    rds=[rc[v] for v in rg.detector_vertices]
    ae=[tuple(sorted((tuple(ag.vertices[u]),tuple(ag.vertices[v])))) for u,v in ag.edges]
    oe=[tuple(sorted((tuple(og.coords[u]),tuple(og.coords[v])))) for u,v in og.edges]
    op=[ae.index(e) for e in oe];rp=[ae.index(e) for e in re]
    ads=[tuple(ag.vertices[v]) for v in ag.detectors]
    oidx=[ads.index(tuple(og.coords[v])) for v in og.detectors];ridx=[ads.index(v) for v in rds]
    for p,q in [(.24,.5),(.40,.8),(.49,1.),(.16,0.)]:
        bp=HeraldBeliefMatchingDecoder(rg,p=p,q=q,max_iterations=80,update_schedule='residual_priority',use_numba=True)
        ad=WitnessDecoder(ag,p,q);rng=np.random.default_rng([89326,L,int(p*1e4),int(q*1e4)])
        decoder_rng=np.random.default_rng([89327,L,int(p*1e4),int(q*1e4)])
        fails=np.zeros(3,int);invalid=np.zeros(3,int);nonconv=0;times=np.zeros(3);per=[]
        for i in range(500):
            x=(rng.random(ag.n_edges)<p).astype(np.uint8);cnt=ag.counts(x);s=cnt%2;h=((cnt>=2)&(rng.random(ag.n_detectors)<q)).astype(np.uint8)
            flags=[]
            for j in range(3):
                t=time.perf_counter()
                try:
                    if j==0:
                        ans=bp.decode(s[ridx],h[ridx]);c=ans.correction;xx=x[rp];H=rg.check_matrix;lm=np.zeros(len(re),np.uint8);lm[list(rg.logical_edges)]=1;ss=s[ridx];nonconv+=not ans.bp.converged
                    elif j==1:c=ad.decode(s,h);xx=x;H=ag.H;lm=ag.logical;ss=s
                    else:c=od.decode(p,q,s[oidx],h[oidx],rng=decoder_rng);xx=x[op];H=og.H;lm=np.zeros(len(oe),np.uint8);lm[og.gamma_R]=1;ss=s[oidx]
                    valid=c.shape==xx.shape and np.all((c==0)|(c==1)) and np.array_equal(np.asarray(H@c)%2,ss)
                    bad=not valid or bool(int((xx^c)@lm)%2)
                except Exception as e:
                    valid=False;bad=True
                    if invalid[j]==0:print('EXCEPTION',j,repr(e),flush=True)
                times[j]+=time.perf_counter()-t;invalid[j]+=not valid;fails[j]+=bad;flags.append(int(bad))
            per.append(flags)
        arr=np.array(per);diffs={}
        for j in [1,2]:
            delta=arr[:,j]-arr[:,0];diffs[['MAP','ML'][j-1]]={'candidate_minus_BP':float(delta.mean()),'paired_se':float(delta.std(ddof=1)/np.sqrt(len(delta))),'candidate_only_fails':int(np.sum(delta==1)),'BP_only_fails':int(np.sum(delta==-1))}
        row={'L':L,'p':p,'q':q,'shots':500,'decoder_order':['repo_residual80_BP','Astra03_MAP','Opus03_ML'],'fails':fails.tolist(),'invalid':invalid.tolist(),'decode_seconds':times.tolist(),'BP_nonconverged':int(nonconv),'paired_differences':diffs}
        rows.append(row);raw.append({'L':L,'p':p,'q':q,'failure_flags':per});print(row,flush=True)
        (ROOT/'output/scicode2/run_evaluation/matched_comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
(ROOT/'output/scicode2/run_evaluation/matched_failure_flags.json').write_text(json.dumps(raw)+'\n')
