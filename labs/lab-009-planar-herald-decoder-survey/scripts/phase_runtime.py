"""Immutable geometry cache for the registered exact planar sweep.

No factor, reference rule, posterior solver or noise law is changed. The
cached values are the canonical graph's derived incidence and detector sets.
"""
from functools import cached_property
from herald_decoder.lattice_model import LatticeGraph,honeycomb_graph

class CachedGeometry(LatticeGraph):
    detector_vertices=cached_property(LatticeGraph.detector_vertices.fget)
    boundary_vertices=cached_property(LatticeGraph.boundary_vertices.fget)
    detector_row=cached_property(LatticeGraph.detector_row.fget)
    check_matrix=cached_property(LatticeGraph.check_matrix.fget)
    incident_edges=cached_property(LatticeGraph.incident_edges.fget)


def phase_graph(L):
    g=honeycomb_graph(L)
    return CachedGeometry(g.name,g.size,g.vertices,g.edges,g.logical_edges,g.logical_line)

import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu
from herald_decoder.planar_ml import HeraldPlanarMLDecoder
from herald_decoder.sector import observations,NumericalInferenceError

class SweepPlanar(HeraldPlanarMLDecoder):
    """Same exact planar algebra with vectorized count-dependent site weights.

    Restricted to the declared binary herald channel. No truth is accepted.
    Numerical probability and solve-residual gates match the source solver.
    """
    def __init__(self,graph,*,p,q):
        super().__init__(graph,p=p,q=q)
        self.groups={}
        for degree in [2,3]:
            sites=[s for s in self.gadgets.sites if len(s[1])==degree]
            self.groups[degree]=tuple(np.asarray([s[j]for s in sites],int)for j in range(4))
        self.patterns={2:np.array([[0,0],[1,1]],np.uint8),3:np.array([[0,0,0],[0,1,1],[1,0,1],[1,1,0]],np.uint8)}
        self.u,self.v=self.gadgets.edges.T
        self.logical_i,self.logical_j=self.gadgets.edges[self.gadgets.logical_edge]
        self.unit=np.zeros(self.gadgets.n);self.unit[self.logical_i]=1.

    def posterior(self,s,h):
        s,h=observations(self.graph,s,h,self.p,self.q)
        if self.p in [0,1] or (self.p==.5 and self.q==0):
            return super().posterior(s,h)
        c0=self._map.decode(s,h).correction
        g=self.gadgets;w=np.zeros(len(g.edges));w[g.constant]=1.;forced=np.zeros(len(self.graph.edges),bool)
        for degree,(rows,edges,spokes,tri)in self.groups.items():
            counts=(self.patterns[degree][None,:,:]^c0[edges][:,None,:]).sum(2)
            eligible=counts>=2
            vals=np.where(h[rows,None],self.q*eligible,np.where(eligible,1-self.q,1.))
            scale=vals.max(1)
            if np.any(scale<=0):raise NumericalInferenceError('zero local likelihood')
            vals=vals/scale[:,None]
            if degree==2:
                nonzero=vals[:,1]>0
                w[spokes[:,0]]=np.divide(vals[:,0],vals[:,1],out=np.ones(len(rows)),where=nonzero)
                forced[edges[~nonzero].ravel()]=True
            else:
                w[spokes]=vals[:,1:]
                nz=vals[:,1:]>0;has=nz.any(1);j=nz.argmax(1)
                rr=np.flatnonzero(has)
                w[tri[rr,j[rr]]]=vals[rr,0]/vals[rr,j[rr]+1]
                rr=np.flatnonzero(~has)
                w[spokes[rr]]=1.;w[tri[rr,0]]=1.;forced[edges[rr].ravel()]=True
        odds=self.p/(1-self.p)
        ratio=np.where(c0==0,odds,1/odds);ratio[forced]=0.
        w[g.wire[:len(self.graph.edges)]]=ratio
        norm=np.zeros(g.n);np.maximum.at(norm,self.u,abs(w));np.maximum.at(norm,self.v,abs(w))
        balance=1/np.sqrt(np.maximum(norm,np.finfo(float).tiny));w*=balance[self.u]*balance[self.v]
        val=w*g.sign
        K=csc_matrix((np.r_[val,-val],(self._matrix_rows,self._matrix_cols)),shape=(g.n,g.n))
        try:z=splu(K).solve(self.unit)
        except RuntimeError as e:raise NumericalInferenceError('singular planar matrix')from e
        pf=float(K[self.logical_i,self.logical_j]*z[self.logical_j]);res=float(np.max(abs(K@z-self.unit)))
        if not np.isfinite(pf) or pf < -1e-8 or pf > 1+1e-8 or not np.isfinite(res) or res>1e-7:
            raise NumericalInferenceError(f'posterior numerical gate: probability={pf}, residual={res}')
        pf=float(np.clip(pf,0,1));probs=np.array([1-pf,pf])
        if self.graph.logical_parity(c0):probs=probs[::-1]
        return probs,{'algebraically_exact':True,'solve_residual':res,'matrix_size':g.n}
