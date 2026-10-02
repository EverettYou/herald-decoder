"""Independent exact frontier contraction for the binary herald posterior."""
import numpy as np
from .sector import SectorDecoderBase,batch_observations,select_sectors,NumericalInferenceError


class HeraldTransferMLDecoder(SectorDecoderBase):
    method='transfer_ml'
    def __init__(self,graph,*,p,q,max_width=18,max_array_bytes=256*1024**2):
        super().__init__(graph,p=p,q=q);self.max_array_bytes=int(max_array_bytes)
        # Sweep pairs of vertical vertex columns, keeping the frontier narrow.
        self.order=sorted(range(len(graph.vertices)),key=lambda v:(np.floor((2*graph.vertices[v].x-1)/3),graph.vertices[v].y))
        open_edges=set();self.width=0
        for v in self.order:
            for e in graph.incident_edges[v]:
                if e in open_edges:open_edges.remove(e)
                else:open_edges.add(e)
            self.width=max(self.width,len(open_edges))
        if self.width>max_width:raise ValueError(f'exact transfer width {self.width} exceeds configured cap {max_width}')

    def probabilities_batch(self,S,H):
        S,H=batch_observations(self.graph,S,H,self.p,self.q)
        B=len(S)
        if B==0:return np.empty((0,2)),{'max_frontier_width':self.width,'algebraically_exact':True,'log_record_probability':[]}
        if B*2**(self.width+1)*8>self.max_array_bytes:raise ValueError('batch exceeds exact-contraction memory cap; split into smaller batches')
        state=np.zeros((B,2));state[:,0]=1.;frontier=[];logs=np.zeros(B);row=self.graph.detector_row
        prior=np.array([1-self.p,self.p])
        for v in self.order:
            incident=list(self.graph.incident_edges[v]);closing=[e for e in incident if e in frontier]
            for e in incident:
                if e not in frontier:state=state[...,None]*prior;frontier.append(e)
            if v in row:
                r=row[v];shape=[1]*state.ndim;shape[0]=B
                count=0
                for e in incident:
                    axis=2+frontier.index(e);sh=[1]*state.ndim;sh[axis]=2;count=count+np.arange(2).reshape(sh)
                parity=S[:,r].reshape(shape);herald=H[:,r].reshape(shape)
                factor=(count%2==parity)*np.where(herald==1,self.q*(count>=2),np.where(count>=2,1-self.q,1.))
                state=state*factor
            for e in closing:
                if e in self.graph.logical_edges:
                    idx=[slice(None)]*state.ndim;idx[2+frontier.index(e)]=1
                    slab=state[tuple(idx)];state[tuple(idx)]=slab[:,::-1].copy()
            if closing:
                axes=tuple(2+frontier.index(e)for e in closing);state=state.sum(axis=axes)
                frontier=[e for e in frontier if e not in closing]
            norm=state.reshape(B,-1).sum(1)
            if np.any(norm<=0) or not np.isfinite(norm).all():raise NumericalInferenceError('zero/underflowed record likelihood in transfer contraction')
            state=state/norm.reshape((B,)+(1,)*(state.ndim-1));logs+=np.log(norm)
        if frontier:raise RuntimeError('unclosed frontier')
        return state,{'max_frontier_width':self.width,'algebraically_exact':True,'log_record_probability':logs.tolist()}

    def posterior(self,s,h):
        probs,diag=self.probabilities_batch(np.asarray(s)[None],np.asarray(h)[None]);return probs[0],diag

    def decode_batch(self,S,H,rng=None):
        probs,_=self.probabilities_batch(S,H);sectors=select_sectors(probs,rng)
        return np.stack([self.representative(s,int(k))for s,k in zip(S,sectors)]) if len(probs) else np.empty((0,len(self.graph.edges)),np.uint8)
