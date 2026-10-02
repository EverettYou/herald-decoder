"""Adapters preserving the Lab 006 observation, BP schedule and hard score."""
from pathlib import Path
import sys
import numpy as np
import pymatching
from current_oracle import ROOT, charge_matrix
sys.path.insert(0,str(ROOT/'labs/lab-006-sun-bp-theory/scripts'))
from numba_fusion_decoder import (FastFusionBeliefMatchingDecoder,
    UndirectedFusionBeliefMatchingDecoder, GeneralizedSyndrome, FastBpResult)
from sun_fusion_bp import Graph
from biased_bp_kernel import _infer_biased_inplace


class DecoderAdapter:
    def __init__(self,model,p,q,max_iterations=300):
        self.model,self.p,self.q=model,p,q
        self.observed=tuple(v for v,es in enumerate(model.incident_edges) if es)
        graph=Graph(tuple(map(str,self.observed)),tuple((str(u),str(v)) for u,v in model.edges))
        cls=FastFusionBeliefMatchingDecoder if q==1 else UndirectedFusionBeliefMatchingDecoder
        self.decoder=cls(graph,p=p,group='U1',damping=.5,max_iterations=max_iterations,tolerance=1e-10)
        for row,v in enumerate(self.observed):
            if not model.vertices[v].detector:self.decoder.bank[row,0]=1.
        self.D=charge_matrix(model)
        self.matrix=model.check_matrix
        self.detrow={v:i for i,v in enumerate(model.detector_vertices)}

    def observation(self,Q):
        labels=[];m=[]
        for v in self.observed:
            charge=int(Q[self.detrow[v]]) if v in self.detrow else 0
            labels.append('0' if charge==0 else f'{charge:+d}')
            m.append(charge%2 if v in self.detrow else 0)
        return GeneralizedSyndrome(np.array(m,dtype=np.uint8),tuple(labels))

    def infer(self,Q,force_generalized=False):
        obs=self.observation(Q);d=self.decoder
        if self.q in (.5,1.) and not force_generalized: return d.infer(obs)
        syndrome,irreps=obs.arrays('U1')
        values=_infer_biased_inplace(syndrome,irreps,d.bank,d.factor_dirs,d.factor_degrees,
            d.edge_dirs,d.edge_degrees,self.p,self.q,d.max_iterations,d.damping,d.tolerance,
            d.variable,d.factors,d.updated_variable,d.updated_factors,d.marginals)
        return FastBpResult(d.marginals.copy(),bool(values[0]),int(values[1]),float(values[2]))

    def matching(self,Q,marginals):
        clipped=np.clip(marginals,1e-12,1-1e-12)
        weights=np.log((1-clipped)/clipped)
        correction=pymatching.Matching.from_check_matrix(self.matrix,weights=weights).decode(
            np.asarray(Q,dtype=np.int64).astype(np.uint8)%2).astype(np.uint8)
        invalid=bool(np.any((self.matrix@correction)%2 != np.asarray(Q)%2))
        return self.model.logical_parity(correction),invalid,correction


def compare_record(model,oracle,decoder,j):
    Q=oracle.D@j
    exact=oracle.infer(Q,decoder.p,decoder.q)
    bp=decoder.infer(Q)
    if not np.all(np.isfinite(bp.edge_marginals)): raise ValueError('nonfinite parent BP')
    chosen=[];risks=[];failures=[]
    true=model.logical_parity((j!=0).astype(np.uint8))
    for marg in (exact['marginals'],bp.edge_marginals):
        h,invalid,corr=decoder.matching(Q,marg)
        assert not invalid,'invalid matching correction'
        chosen.append(h);risks.append(float(exact['sectors'][1-h]));failures.append(h!=true)
    return {'Q':Q.tolist(),'true_sector':true,'sector_probabilities':exact['sectors'].tolist(),
            'bayes_risk':exact['bayes_risk'],'exact_mwpm_risk':risks[0],'bp_mwpm_risk':risks[1],
            'chosen_sectors':chosen,'actual_failures':list(map(int,failures)),
            'bayes_actual_failure':int(int(np.argmax(exact['sectors']))!=true),
            'log_evidence':exact['log_evidence'],
            'signed_gap':exact['signed_gap'] if np.isfinite(exact['signed_gap']) else None,
            'gap_infinite_sign':0 if np.isfinite(exact['signed_gap']) else (1 if exact['signed_gap']>0 else -1),
            'response':exact['response'],'sector_counts':exact['sector_counts'].tolist(),
            'bp_converged':bp.converged,'bp_iterations':bp.iterations,'bp_residual':bp.max_message_delta,
            'marginal_max_error':float(np.max(abs(bp.edge_marginals-exact['marginals']))),
            'marginal_mean_error':float(np.mean(abs(bp.edge_marginals-exact['marginals'])))}
