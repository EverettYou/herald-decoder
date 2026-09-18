#!/usr/bin/env python3
"""Exact and matched-fixture gates for the hidden-orientation scan."""
import itertools
import json
from pathlib import Path
from time import monotonic
import numpy as np
import run_a9_hidden_orientation as a9
import run_a7_ler as a8
from numba_fusion_decoder import GROUP_IRREPS, GeneralizedSyndrome, UndirectedFusionBeliefMatchingDecoder, group_fusion_distribution
from sun_fusion_bp import Graph

LAB=Path(__file__).resolve().parents[1]

def main():
    start=monotonic();checks=[]
    (LAB/'results/a9-validation.json').write_text(json.dumps({'status':'running'})+'\n')
    for degree in range(5):
        reference=group_fusion_distribution('SU2',('fund',)*degree)
        for active in itertools.product(('fund','anti'),repeat=degree):assert group_fusion_distribution('SU2',active)==reference
    checks.append({'check':'SU2 all oriented local fusion products through degree four','status':'passed'})
    # Independently enumerate all global three-state configurations on a factor tree.
    graph=Graph(('a','b','c'),(('a','b'),('b','c')))
    rng=np.random.default_rng(601209)
    for group in ('U1','SU2','SU3'):
        errors=(rng.random((12,2))<.4).astype(np.uint8);reverse=(rng.random((12,2))<.5).astype(np.uint8)
        m,labels=a9.generate_hidden_records(errors,reverse,rng.random((12,3)),*a9.record_tables(graph,(0,2),group))
        decoder=UndirectedFusionBeliefMatchingDecoder(graph,group=group,p=.4,max_iterations=300,damping=.5,tolerance=1e-10)
        decoder.bank[[0,2],0]=1.0
        batch=a9.infer_hidden_batch(decoder,m,labels)
        maximum=0.
        for i in range(len(m)):
            observation=GeneralizedSyndrome(m[i],tuple(GROUP_IRREPS[group][v] for v in labels[i]))
            scalar=decoder.infer(observation)
            assert np.max(np.abs(batch[0][i]-scalar.edge_marginals)) <= 1e-12
            assert bool(batch[1][i])==scalar.converged and batch[2][i]==scalar.iterations
            weights=[];states=[]
            for state in itertools.product(range(3),repeat=2):
                weight=np.prod([.6 if s==0 else .2 for s in state])
                for vertex,leaves in enumerate(graph.incident):
                    if vertex in (0,2): continue
                    active=tuple('fund' if (rep=='3')==(state[edge]==1) else 'anti' for edge,rep in leaves if state[edge])
                    weight*=int((len(active)&1)==m[i,vertex])*group_fusion_distribution(group,active).get(observation.irrep[vertex],0.)
                weights.append(weight);states.append([int(x>0) for x in state])
            weights=np.array(weights);assert weights.sum()>0
            exact=weights@np.array(states)/weights.sum();maximum=max(maximum,float(np.max(abs(exact-batch[0][i]))))
        assert maximum<1e-8
        if group=='U1':
            charge={i:int(v) for i,v in enumerate(GROUP_IRREPS[group])}
            _,complete_labels=a9.generate_hidden_records(errors,reverse,rng.random((12,3)),*a9.record_tables(graph,(),group))
            assert all(sum(charge[int(v)] for v in sample)==0 for sample in complete_labels)
        checks.append({'check':'factor-tree exact enumeration and scalar/batch equality','group':group,'max_posterior_error':maximum,'status':'passed'})
    # Both lattice geometries, every representation family, real rough boundaries.
    for lattice in ('square','honeycomb'):
        for group in ('U1','SU2','SU3'):
            model,graph,detectors,boundary=a8.context(lattice,5)
            rng=np.random.default_rng(71311);errors=(rng.random((8,len(graph.edges)))<.3).astype(np.uint8)
            reverse=(rng.random(errors.shape)<.5).astype(np.uint8);uniforms=rng.random((8,len(graph.vertices)))
            m,labels=a9.generate_hidden_records(errors,reverse,uniforms,*a9.record_tables(graph,boundary,group))
            decoder=a9.decoder_for(graph,boundary,group,.3,'undirected');batch=a9.infer_hidden_batch(decoder,m,labels)
            assert np.all(decoder.bank[list(boundary),0]==1) and np.all(m[:,boundary]==0)
            scalar_posteriors=[];max_batch_difference=0.
            for i in range(8):
                scalar=decoder.infer(GeneralizedSyndrome(m[i],tuple(GROUP_IRREPS[group][v] for v in labels[i])))
                assert np.max(np.abs(batch[0][i]-scalar.edge_marginals)) <= 1e-12
                scalar_posteriors.append(scalar.edge_marginals)
                max_batch_difference=max(max_batch_difference,float(np.max(np.abs(batch[0][i]-scalar.edge_marginals))))
                assert batch[2][i]==scalar.iterations and bool(batch[1][i])==scalar.converged
            scalar_failures=a9.matching_failures(model,m,detectors,errors,np.array(scalar_posteriors))
            batch_failures=a9.matching_failures(model,m,detectors,errors,batch[0])
            assert np.array_equal(scalar_failures,batch_failures)
            result=a9.run_cell(lattice,group,5,.3,8,950514,8)
            a8.GROUPS=(group,);a8.ARMS=('representation_herald',)
            ref=a8.run_cell(lattice,5,.3,8,950514,8)[0]
            assert result['arms']['directed']['logical_failures']==ref['logical_failures']
            assert result['arms']['directed']['bp_nonconverged']==ref['bp_nonconverged']
            checks.append({'check':'lattice scalar/batch, boundary hiding and directed replay','lattice':lattice,'group':group,'status':'passed','max_scalar_batch_difference':max_batch_difference,'final_failures_match':True})
    from dispatch_a9_orientation import source_hashes
    output={'status':'passed','checks':checks,'elapsed_seconds':monotonic()-start,'source_sha256':source_hashes(),'posterior_tolerance':1e-12}
    (LAB/'results/a9-validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output),flush=True)

if __name__=='__main__':
    try: main()
    except Exception as error:
        (LAB/'results/a9-validation.json').write_text(json.dumps({'status':'failed','error':repr(error)})+'\n')
        raise
