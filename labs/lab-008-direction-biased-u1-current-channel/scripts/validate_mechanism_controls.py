"""Independent matching and arrow-relabeling controls; no production samples."""
from collections import Counter
from itertools import product
import json
import numpy as np
from current_oracle import LAB,CurrentOracle,square_graph,exact_enumeration
from decoder_comparison import DecoderAdapter
from run_mechanism import make_model


def main():
    rng=np.random.default_rng(9180026);g=square_graph(3);o=CurrentOracle(g)
    table=exact_enumeration(g,.3,.75);count_error=0.
    for Q,(z,m,c) in table.items():
        a=o.infer(Q,.3,.75)
        expected=np.divide(c,z[:,None],out=np.zeros_like(c),where=z[:,None]>0)
        count_error=max(count_error,float(np.max(abs(a['sector_counts']-expected))))
    assert count_error<1e-9
    # Explicitly characterize duplicate-column merging; never use this motif for production matching.
    adapter=DecoderAdapter(g,.3,.75);matrix=g.check_matrix.toarray().astype(int)
    masks=np.array(list(product((0,1),repeat=len(g.edges))),dtype=np.uint8)
    syndromes=masks@matrix.T%2;mismatches=0;tested=0
    for Q in list(table)[::9]:
        marg=o.infer(Q,.3,.75)['marginals'];h,invalid,corr=adapter.matching(Q,marg)
        clipped=np.clip(marg,1e-12,1-1e-12);weights=np.log((1-clipped)/clipped)
        compatible=np.all(syndromes==np.array(Q)%2,axis=1)
        best=float(np.min(masks[compatible]@weights))
        mismatches+=float(corr@weights)>best+1e-9;tested+=1
        assert not invalid
    csc=g.check_matrix;columns=Counter(tuple(csc.indices[csc.indptr[e]:csc.indptr[e+1]]) for e in range(len(g.edges)))
    # On the SAME physical currents at q=.5, arrow reversal is a coordinate relabeling.
    controls=[]
    for L in (3,5):
        a=make_model('honeycomb',L,'stored');b=make_model('honeycomb',L,'bipartite')
        oa=CurrentOracle(a);ob=CurrentOracle(b)
        flip=np.array([1 if ea==eb else -1 for ea,eb in zip(a.edges,b.edges)])
        da=DecoderAdapter(a,.3,.5);db=DecoderAdapter(b,.3,.5);err=0.;bperr=0.
        for _ in range(32):
            j=(rng.random(len(a.edges))<.3)*np.where(rng.random(len(a.edges))<.5,1,-1)
            Qa=oa.D@j;Qb=ob.D@(j*flip);assert np.array_equal(Qa,Qb)
            ra=oa.infer(Qa,.3,.5);rb=ob.infer(Qb,.3,.5)
            err=max(err,float(np.max(abs(ra['sectors']-rb['sectors']))),float(np.max(abs(ra['marginals']-rb['marginals']))))
            pa=da.infer(Qa);pb=db.infer(Qb)
            bperr=max(bperr,float(np.max(abs(pa.edge_marginals-pb.edge_marginals))))
            assert abs(ra['log_evidence']-rb['log_evidence'])<1e-9
        assert err<1e-9 and bperr<1e-9
        controls.append({'L':L,'records':32,'reversed_edges':int(np.sum(flip==-1)),'max_exact_error':err,'max_bp_error':bperr})
    out={'status':'passed','sector_count_error':count_error,
         'square_L3_duplicate_columns':sum(n-1 for n in columns.values() if n>1),
         'square_L3_matching_objective_records':tested,'square_L3_matching_objective_mismatches':int(mismatches),
         'honeycomb_fair_arrow_relabeling':controls,
         'limit':'L3 square matching is not promoted as production evidence. The fair control holds physical currents fixed under a coordinate relabeling; biased arrow interventions change the physical law.'}
    (LAB/'results/mechanism-controls-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
