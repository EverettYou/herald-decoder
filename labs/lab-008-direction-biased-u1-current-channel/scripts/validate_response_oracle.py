"""Registered exhaustive oracle validation, parent replay and runtime profile."""
from collections import Counter
from pathlib import Path
from time import monotonic
import hashlib
import json
import platform
import numpy as np
import pymatching
from current_oracle import CurrentOracle, exact_enumeration, square_graph, honeycomb_graph, LAB, ROOT
from decoder_comparison import DecoderAdapter, compare_record


def main():
    start=monotonic();g=square_graph(3);rng=np.random.default_rng(18092026)
    checks=[];responses=[];endpoint=[];profiles=[]
    for p in (.10,.30,.46):
        for q in (.5,.75,1.):
            table=exact_enumeration(g,p,q);oracle=CurrentOracle(g,directed=q==1)
            assert abs(sum(sum(x[0]) for x in table.values())-1)<1e-12
            errors=np.zeros(3);record_count=0
            for Q,(z,m,c) in table.items():
                actual=oracle.infer(Q,p,q);total=sum(z)
                errors=np.maximum(errors,[abs(np.exp(actual['log_evidence'])-total),
                    np.max(abs(actual['sectors']-z/total)),np.max(abs(actual['marginals']-m/total))])
                assert errors.max()<1e-9
                if q<1 and np.all(z>0) and record_count%7==0:
                    eps=1e-6
                    fd=(oracle.infer(Q,p,q+eps)['signed_gap']-oracle.infer(Q,p,q-eps)['signed_gap'])/(2*eps)
                    err=abs(fd-actual['response']);assert err<2e-5
                    responses.append(err)
                record_count+=1
            checks.append({'p':p,'q':q,'records':len(table),'max_errors':errors.tolist()})
            print('exhaustive',p,q,len(table),errors.tolist(),flush=True)
    # Independent endpoint parent record generator + production BP objects.
    import run_a7_ler as parent
    import run_a9_hidden_orientation as parent_hidden
    for q in (.5,1.):
        g=square_graph(5);adapter=DecoderAdapter(g,.3,q)
        model,graph,detrows,boundary=parent.context('square',5)
        errors=(rng.random((16,len(g.edges)))<.3).astype(np.uint8)
        reverse=(rng.random(errors.shape)<.5).astype(np.uint8) if q==.5 else np.zeros_like(errors)
        currents=errors.astype(int)*(1-2*reverse.astype(int))
        uniforms=rng.random((16,len(graph.vertices)))
        if q==.5:
            m,labels=parent_hidden.generate_hidden_records(errors,reverse,uniforms,
                *parent_hidden.record_tables(graph,boundary,'U1'))
        else:m,labels=parent._generate_records_numba(errors,uniforms,*parent._record_tables(graph,boundary,'U1'))
        dec=parent_hidden.decoder_for(graph,boundary,'U1',.3,'undirected' if q==.5 else 'directed')
        expected=parent_hidden.infer_hidden_batch(dec,m,labels) if q==.5 else dec.infer_batch(m,labels)
        maximum=0.;generalized_max=0.
        for i,j in enumerate(currents):
            Q=adapter.D@j;obs=adapter.observation(Q);ma,la=obs.arrays('U1')
            assert np.array_equal(ma,m[i]) and np.array_equal(la,labels[i])
            actual=adapter.infer(Q);maximum=max(maximum,float(np.max(abs(actual.edge_marginals-expected[0][i]))))
            assert actual.converged==bool(expected[1][i]) and actual.iterations==expected[2][i]
            if q==.5:
                other=adapter.infer(Q,True);generalized_max=max(generalized_max,float(np.max(abs(actual.edge_marginals-other.edge_marginals))))
                assert actual.converged==other.converged and actual.iterations==other.iterations
        assert maximum<1e-12 and generalized_max<1e-12
        endpoint.append({'q':q,'records':16,'max_parent_error':maximum,'max_generalized_error':generalized_max})
    # Frontier order independence on a different topology.
    hg=honeycomb_graph(2)
    ho=CurrentOracle(hg);rev=CurrentOracle(hg,order=list(reversed(hg.detector_vertices)))
    order_error=0.
    for k in range(16):
        j=(rng.random(len(hg.edges))<.3)*(np.where(rng.random(len(hg.edges))<.75,1,-1))
        Q=ho.D@j;a=ho.infer(Q,.3,.75);b=rev.infer(Q,.3,.75)
        order_error=max(order_error,float(np.max(abs(a['sectors']-b['sectors']))),float(np.max(abs(a['marginals']-b['marginals']))))
    assert order_error<1e-9
    # Profile all registered sizes, respecting candidate caps.
    for name,factory,sizes in [('square',square_graph,[4,5,7,9]),('honeycomb',honeycomb_graph,[3,5])]:
        for L in sizes:
            g=factory(L);matrix=g.check_matrix.tocsc()
            columns=Counter(tuple(matrix.indices[matrix.indptr[a]:matrix.indptr[a+1]]) for a in range(len(g.edges)))
            duplicates=sum(n-1 for n in columns.values() if n>1)
            try:o=CurrentOracle(g)
            except MemoryError as exc:
                profiles.append({'lattice':name,'L':L,'status':'candidate_cap','reason':str(exc)});print(profiles[-1],flush=True);continue
            dec=DecoderAdapter(g,.3,.75);times=[];risks=[]
            for k in range(4):
                j=(rng.random(len(g.edges))<.3)*np.where(rng.random(len(g.edges))<.75,1,-1)
                t=monotonic();row=compare_record(g,o,dec,j);times.append(monotonic()-t);risks.append(row['bayes_risk'])
                if sum(times)>90:break
            profile={'lattice':name,'L':L,'status':'profiled','edges':len(g.edges),'duplicate_detector_columns':duplicates,
                     **o.profile,'record_seconds':times,'pilot_risks_not_production':risks}
            profiles.append(profile);print('PROFILE',json.dumps(profile),flush=True)
    files=[Path(__file__),LAB/'scripts/current_oracle.py',LAB/'scripts/decoder_comparison.py',
           LAB/'scripts/biased_bp_kernel.py',ROOT/'src/herald_decoder/lattice_model.py',
           ROOT/'labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py']
    out={'status':'passed','exhaustive':checks,'response_checks':len(responses),'max_response_error':max(responses),
         'parent_endpoints':endpoint,'honeycomb_order_error':order_error,'profiles':profiles,
         'wall_seconds':monotonic()-start,
         'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
         'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pymatching':pymatching.__version__},
         'limits':['L3 square is oracle validation only, not matching evidence.','Pilot samples excluded from production.']}
    (LAB/'results/response-oracle-validation-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASSED',len(checks),len(responses),out['wall_seconds'],flush=True)


if __name__=='__main__':main()
