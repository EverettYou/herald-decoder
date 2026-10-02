"""Controlled column-MPS approximation of sector sums on the canonical honeycomb.

Finite chi is an approximation. Diagnostics report discarded singular-value
weight, not an all-record bound on logical error. Compare chi and an exact
backend before drawing scientific conclusions.
"""
import numpy as np
from ._geometry import require_canonical_honeycomb
from .sector import SectorDecoderBase,batch_observations,select_sectors,NumericalInferenceError


class HeraldMPSDecoder(SectorDecoderBase):
    method='mps_ml'
    def __init__(self,graph,*,p,q,chi=16):
        require_canonical_honeycomb(graph)
        if graph.name!='honeycomb':raise ValueError('column MPS supports the canonical honeycomb patch')
        if int(chi)!=chi or chi<1:raise ValueError('chi must be a positive integer')
        super().__init__(graph,p=p,q=q);self.chi=int(chi);self.steps=[]
        coords={(round(2*v.x),round(2*v.y/np.sqrt(3))):i for i,v in enumerate(graph.vertices)}
        ei={tuple(sorted(edge)):e for e,edge in enumerate(graph.edges)}
        def edge(c,d):return ei[tuple(sorted((coords[c],coords[d])))]
        L=graph.size;coverage=np.zeros(len(graph.edges),int)
        for a in range(L-1):
            rowsA=[];rowsB=[]
            for i in range(L+1):
                ca=(3*a+1,(a%2)-1+2*i);cb=(3*a+2,((a+1)%2)-1+2*i)
                rowsA.append(graph.detector_row[coords[ca]]);rowsB.append(graph.detector_row[coords[cb]])
                coverage[edge((3*a-1,ca[1]),ca)]+=1;coverage[edge(ca,cb)]+=1
                if i<L:
                    far=(3*a+1,ca[1]+2) if a%2==0 else (3*a+2,cb[1]+2)
                    coverage[edge(cb if a%2==0 else ca,far)]+=1
            self.steps.append((np.array(rowsA),np.array(rowsB)))
        self.right_edges=np.array([edge((3*(L-1)-1,(L-1)%2-1+2*i),(3*(L-1)+1,(L-1)%2-1+2*i))for i in range(L+1)])
        coverage[self.right_edges]+=1
        if not np.all(coverage==1):raise ValueError('MPS construction must cover every edge exactly once')

    def _local(self,S,H,rows,degree):
        n=np.indices((2,)*degree).sum(0);shape=(len(S),)+(1,)*degree
        s=S[:,rows].reshape(shape);h=H[:,rows].reshape(shape)
        return (n[None]%2==s)*np.where(h==1,self.q*(n[None]>=2),np.where(n[None]>=2,1-self.q,1.))

    def _mpo(self,S,H,a):
        A,B=self.steps[a];L=self.graph.size;prior=np.array([1-self.p,self.p]);ops=[]
        for i in range(L+1):
            da=3 if (i>0 if a%2==0 else i<L)else 2
            db=3 if (i<L if a%2==0 else i>0)else 2
            ta=self._local(S,H,A[i],da);tb=self._local(S,H,B[i],db)
            if da==2:ta=ta[:,:,None,:]
            if db==2:tb=tb[:,:,None,:]
            ta=ta*prior[None,:,None,None]*prior[None,None,None,:]
            if a%2==0:op=np.einsum('bilm,bmro->blior',ta,tb)
            else:op=np.einsum('birm,bmlo->blior',ta,tb)
            if i<L:op=op*prior[None,None,None,None,:]
            ops.append(op)
        return ops

    def probabilities_batch(self,S,H):
        S,H=batch_observations(self.graph,S,H,self.p,self.q)
        if len(S)==0:return np.empty((0,2)),{'chi':self.chi,'algebraically_exact':False,'summed_discarded_weight':[]}
        if 0 < self.p < 1e-12 or 1-1e-12 < self.p < 1:
            from .transfer_ml import HeraldTransferMLDecoder
            probs,diag=HeraldTransferMLDecoder(self.graph,p=self.p,q=self.q).probabilities_batch(S,H)
            diag['fallback']='exact transfer for extreme prior (subject to width cap)'
            return probs,diag
        B=len(S);n=self.graph.size+1
        M=[np.ones((B,1,2,1))for _ in range(n)];logs=np.zeros(B);discarded=np.zeros(B)
        for a in range(self.graph.size-1):
            for i,W in enumerate(self._mpo(S,H,a)):
                tensor=np.einsum('bLxyR,blxr->bLlyRr',W,M[i],optimize=True)
                M[i]=tensor.reshape(B,tensor.shape[1]*tensor.shape[2],2,tensor.shape[4]*tensor.shape[5])
            for i in range(n-1):
                ml,mr=M[i].shape[1],M[i].shape[3]
                Q,R=np.linalg.qr(M[i].reshape(B,2*ml,mr));k=Q.shape[-1]
                M[i]=Q.reshape(B,ml,2,k);M[i+1]=np.einsum('bkc,bcxr->bkxr',R,M[i+1])
            for i in range(n-1,0,-1):
                ml,mr=M[i].shape[1],M[i].shape[3]
                try:U,s,V=np.linalg.svd(M[i].reshape(B,ml,2*mr),full_matrices=False)
                except np.linalg.LinAlgError as exc:raise NumericalInferenceError('MPS SVD failed')from exc
                k=min(self.chi,len(s[0]));den=np.sum(s*s,axis=1)
                discarded+=np.sum(s[:,k:]**2,axis=1)/np.maximum(den,np.finfo(float).tiny)
                M[i]=V[:,:k].reshape(B,k,2,mr)
                M[i-1]=np.einsum('blxc,bck->blxk',M[i-1],U[:,:,:k]*s[:,None,:k])
            norm=np.sqrt(np.sum(M[0]**2,axis=(1,2,3)))
            if np.any(norm<=0)or not np.isfinite(norm).all():raise NumericalInferenceError('MPS zero norm / impossible record')
            M[0]/=norm[:,None,None,None];logs+=np.log(norm)
        parity=np.zeros((2,2,2));prior=[1-self.p,self.p]
        for c in range(2):
            for x in range(2):parity[c,x,c^x]=prior[x]
        E=np.zeros((B,1,2));E[:,0,0]=1.
        for tensor in M:E=np.einsum('bkc,bkxl,cxd->bld',E,tensor,parity,optimize=True)
        raw=E[:,0,:]
        tolerance=1e-10*np.maximum(np.max(np.abs(raw),axis=1),np.finfo(float).tiny)
        if np.any(raw < -tolerance[:,None])or not np.isfinite(raw).all():raise NumericalInferenceError('truncation produced negative/nonfinite sector weights; increase chi')
        raw=np.maximum(raw,0);norm=raw.sum(1)
        if np.any(norm<=0):raise NumericalInferenceError('zero sector sum')
        probs=raw/norm[:,None]
        for j,s in enumerate(S):
            ref=self.representative(s,0)
            if int(ref[self.right_edges].sum())%2:probs[j]=probs[j,::-1]
        return probs,{'chi':self.chi,'algebraically_exact':False,'summed_discarded_weight':discarded.tolist(),'log_normalization':logs.tolist()}

    def posterior(self,s,h):
        probs,diag=self.probabilities_batch(np.asarray(s)[None],np.asarray(h)[None]);return probs[0],diag

    def decode_batch(self,S,H,rng=None):
        probs,_=self.probabilities_batch(S,H)
        return np.stack([self.representative(s,int(k))for s,k in zip(S,select_sectors(probs,rng))]) if len(probs) else np.empty((0,len(self.graph.edges)),np.uint8)
