"""Signed T-join MAP on the honeycomb: low-prior integers, high-prior literal weights."""
import numpy as np
import pymatching
from ._geometry import require_canonical_honeycomb
from .sector import SectorDecoderBase,SectorResult,observations


class HeraldConfigurationMAPDecoder(SectorDecoderBase):
    method='configuration_map'
    def __init__(self,graph,*,p,q):
        require_canonical_honeycomb(graph)
        if graph.name!='honeycomb' or any(len(graph.incident_edges[v])>3 for v in graph.detector_vertices):
            raise ValueError('integer MAP reduction is validated for the canonical trivalent honeycomb patch')
        super().__init__(graph,p=p,q=q)
        self.H=graph.check_matrix
        self._d=np.asarray(self.H.sum(axis=0)).ravel().astype(np.int64)

    def edge_weights(self,h):
        hits=np.asarray(np.asarray(h,dtype=np.int64) @ self.H).ravel()
        # On this bipartite boundary geometry, 4*N-T has exactly the same
        # minima as (A+2B)*N-B*T for 0<p<1/2,0<q<1. Endpoints are separate.
        if self.p > .5 and self.p < 1:
            # Literal negative log posterior. A is negative above half;
            # the low-prior integer objective is not equivalent here.
            A=np.log1p(-self.p)-np.log(self.p)
            if self.q==0:return np.full(len(self.graph.edges),A)
            if self.q==1:
                soft=np.full(len(self.graph.edges),A)
                penalty=float(np.abs(soft).sum())+1
                weights=soft+penalty*(self._d-2*hits)
            else:
                B=-.5*np.log1p(-self.q)
                soft=A+B*(self._d-hits)
                penalty=float(np.abs(soft).sum())+1
                weights=soft-penalty*hits
            # Common positive scaling preserves the minimizer and backend range.
            return weights/max(1.,float(np.max(np.abs(weights))))
        if self.q==0:return np.full(len(self.graph.edges),0 if self.p==.5 else 1,dtype=np.int64)
        if self.q==1:
            soft=np.full(len(self.graph.edges),0 if self.p==.5 else 1,dtype=np.int64)
            penalty=int(soft.sum())+1
            return soft+penalty*(self._d-2*hits)
        soft=self._d-hits if self.p==.5 else 2+self._d
        penalty=int(soft.sum())+1
        return soft-penalty*hits

    def decode(self,s,h,rng=None):
        s,h=observations(self.graph,s,h,self.p,self.q)
        if self.p==0:c=np.zeros(len(self.graph.edges),np.uint8);w=np.zeros(len(c))
        elif self.p==1:c=np.ones(len(self.graph.edges),np.uint8);w=np.zeros(len(c))
        else:
            w=self.edge_weights(h)
            if np.max(np.abs(w),initial=0)>2**24-1:
                raise ValueError('graph exceeds the exact integer range of the matching backend')
            c=pymatching.Matching.from_check_matrix(self.H,weights=w,merge_strategy='disallow').decode(s).astype(np.uint8)
        counts=self.graph.degrees(c)[list(self.graph.detector_vertices)]
        if not np.array_equal(counts&1,s) or np.any(counts[h==1]<2) or (self.q==1 and np.any(counts[h==0]>=2)):
            raise RuntimeError('MAP correction failed syndrome or hard likelihood support')
        return SectorResult(c,None,self.method,{'objective':'configuration MAP','cost':float(w @ c),'exact_integer_objective':self.p<=.5 or self.p==1})
