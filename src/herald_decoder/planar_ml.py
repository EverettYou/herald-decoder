"""Logical-sector Bayes decoding of binary parity factors on the honeycomb patch."""
import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu
from ._planar import ParityGadgets
from .sector import SectorDecoderBase,observations,NumericalInferenceError
from .configuration_map import HeraldConfigurationMAPDecoder


class PlanarParitySolver(SectorDecoderBase):
    """Generic binary local-factor sector solver.

    Each factor is an array of shape (2,)*degree in graph.incident_edges order.
    Exact parity is imposed by s; rough vertices have no factor. Factors may
    encode full-irrep likelihoods. Edge prior is IID Bernoulli(p). The graph
    is the canonical honeycomb patch with the package logical cut.
    """
    method='planar_ml'
    def __init__(self,graph,*,p,q=0):
        super().__init__(graph,p=p,q=q);self.gadgets=ParityGadgets(graph)
        self._matrix_rows=np.r_[self.gadgets.edges[:,0],self.gadgets.edges[:,1]]
        self._matrix_cols=np.r_[self.gadgets.edges[:,1],self.gadgets.edges[:,0]]

    def posterior_from_factors(self,s,factors,reference=None):
        s=np.asarray(s)
        if s.shape!=(len(self.graph.detector_vertices),) or not np.all((s==0)|(s==1)):
            raise ValueError('s must be binary in detector order')
        if len(factors)!=len(s):raise ValueError('one local factor per detector is required')
        for v,f in zip(self.graph.detector_vertices,factors):
            if np.shape(f)!=(2,)*len(self.graph.incident_edges[v]) or not np.all(np.isfinite(f)) or np.any(np.asarray(f)<0):
                raise ValueError('local factors must have nonnegative finite binary tensor entries')
        if reference is not None and not np.all((np.asarray(reference)==0)|(np.asarray(reference)==1)):
            raise ValueError('reference must be a binary edge configuration')
        c0=np.asarray(self._T @ s).ravel().astype(np.uint8)&1 if reference is None else np.asarray(reference,np.uint8)
        if c0.shape!=(len(self.graph.edges),) or not np.array_equal(self.graph.true_syndrome(c0),s):raise ValueError('invalid reference correction')
        if self.p==0:
            if s.any() or any(np.asarray(f)[(0,)*np.asarray(f).ndim]<=0 for f in factors):raise ValueError('impossible record at p=0')
            return np.array([1.,0.]),{'matrix_size':self.gadgets.n,'algebraically_exact':True}
        if self.p==1:
            x=np.ones(len(self.graph.edges),np.uint8)
            if not np.array_equal(self.graph.true_syndrome(x),s) or any(np.asarray(f)[(1,)*np.asarray(f).ndim]<=0 for f in factors):raise ValueError('impossible record at p=1')
            probs=np.zeros(2);probs[self.graph.logical_parity(x)]=1.
            return probs,{'matrix_size':self.gadgets.n,'algebraically_exact':True}
        g=self.gadgets;w=np.zeros(len(g.edges));w[g.constant]=1.;forced=np.zeros(len(self.graph.edges),bool)
        for row,edges,spokes,tri in g.sites:
            d=len(edges);patterns=np.array([[0,0],[1,1]]) if d==2 else np.array([[0,0,0],[0,1,1],[1,0,1],[1,1,0]])
            X=patterns^c0[edges]
            original=list(self.graph.incident_edges[self.graph.detector_vertices[row]])
            perm=[edges.index(e)for e in original]
            vals=np.asarray(factors[row])[tuple(X[:,perm].T)]
            scale=vals.max(initial=0)
            if scale<=0:raise ValueError('record has zero local likelihood in its parity class')
            vals=vals/scale
            if d==2:
                if vals[1]>0:w[spokes[0]]=vals[0]/vals[1]
                elif vals[0]>0:w[spokes[0]]=1.;forced[edges]=True
                else:raise ValueError('zero local support')
            else:
                w[spokes]=vals[1:]
                nz=np.flatnonzero(vals[1:]>0)
                if len(nz):j=int(nz[0]);w[tri[j]]=vals[0]/vals[j+1]
                else:w[spokes]=1.;w[tri[0]]=1.;forced[edges]=True
        odds=self.p/(1-self.p)
        edge_ratio=np.where(c0==0,odds,1/odds);edge_ratio[forced]=0.
        w[g.wire[:len(self.graph.edges)]]=edge_ratio
        # Diagonal congruence leaves all matching relative weights and edge
        # occupancies unchanged; it reduces dynamic range before sparse LU.
        u,v=g.edges.T
        norm=np.zeros(g.n);np.maximum.at(norm,u,np.abs(w));np.maximum.at(norm,v,np.abs(w))
        balance=1/np.sqrt(np.maximum(norm,np.finfo(float).tiny));w=w*balance[u]*balance[v]
        val=w*g.sign
        K=csc_matrix((np.r_[val,-val],(self._matrix_rows,self._matrix_cols)),shape=(g.n,g.n))
        i,j=g.edges[g.logical_edge];e=np.zeros(g.n);e[i]=1.
        try:lu=splu(K);z=lu.solve(e)
        except RuntimeError as exc:raise NumericalInferenceError('singular partition-function matrix; record impossible or numerical conditioning failed') from exc
        pf=float(K[i,j]*z[j]);res=float(np.max(np.abs(K@z-e)))
        if not np.isfinite(pf) or pf < -1e-8 or pf > 1+1e-8 or not np.isfinite(res) or res>1e-7:
            raise NumericalInferenceError(f'posterior numerical gate failed: probability={pf}, solve residual={res}')
        pf=float(np.clip(pf,0,1));probs=np.array([1-pf,pf])
        if self.graph.logical_parity(c0):probs=probs[::-1]
        return probs,{'matrix_size':g.n,'solve_residual':res,'algebraically_exact':True,'roundoff_clip':pf in(0.,1.)}


class HeraldPlanarMLDecoder(PlanarParitySolver):
    def __init__(self,graph,*,p,q):
        super().__init__(graph,p=p,q=q);self._map=HeraldConfigurationMAPDecoder(graph,p=p,q=q)
        self._counts=[np.indices((2,)*len(graph.incident_edges[v])).sum(0)for v in graph.detector_vertices]

    def posterior(self,s,h):
        s,h=observations(self.graph,s,h,self.p,self.q)
        if 0 < self.p < 1e-12 or 1-1e-12 < self.p < 1:
            from .transfer_ml import HeraldTransferMLDecoder
            probs,diag=HeraldTransferMLDecoder(self.graph,p=self.p,q=self.q).posterior(s,h)
            diag['fallback']='exact transfer for extreme prior (subject to width cap)'
            return probs,diag
        if self.p==.5 and self.q==0:return np.array([.5,.5]),{'algebraically_exact':True,'uniform_sector_limit':True}
        factors=[(self.q*(n>=2) if hv else np.where(n>=2,1-self.q,1.))for n,hv in zip(self._counts,h)]
        # A visible-record MAP reference improves conditioning without giving
        # this solver any sampled truth or hidden coin.
        reference=self._map.decode(s,h).correction
        return self.posterior_from_factors(s,factors,reference)
