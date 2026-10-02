"""Research-only Kac–Ward sector posterior with explicit finite support penalty.

Positive local even signatures are converted to weighted even subgraphs on a
planar boundary-rail graph. Exact zeros are replaced by exp(-penalty), so this
is an approximation to the hard-herald channel. A logarithmic derivative on
one rail edge gives sector probability, avoiding a square-root sign choice.
"""
import numpy as np
from herald_decoder.sector import SectorDecoderBase,observations,NumericalInferenceError


class KacWardHeraldDecoder(SectorDecoderBase):
    method='kac_ward_penalized'
    def __init__(self,graph,*,p,q,penalty=12):
        if graph.name!='honeycomb':raise ValueError('canonical honeycomb required')
        super().__init__(graph,p=p,q=q);self.penalty=float(penalty)
        active=[v for v in range(len(graph.vertices))if graph.incident_edges[v]]
        xy=np.array([(v.x,v.y)for v in graph.vertices]);lookup={v:i for i,v in enumerate(active)}
        left=sorted([v for v in graph.boundary_vertices if graph.vertices[v].boundary_side=='left' and graph.incident_edges[v]],key=lambda v:xy[v,1])
        right=sorted([v for v in graph.boundary_vertices if graph.vertices[v].boundary_side=='right' and graph.incident_edges[v]],key=lambda v:-xy[v,1])
        positions=list(xy[active]);r0,r1=len(positions),len(positions)+1;yt=xy[:,1].max()+1.5
        positions.extend([[xy[left[-1],0],yt],[xy[right[0],0],yt]])
        chain=[lookup[v]for v in left]+[r0,r1]+[lookup[v]for v in right]
        self.edges=np.array([(lookup[u],lookup[v])for u,v in graph.edges]+list(zip(chain[:-1],chain[1:])))
        self.flip_edge=len(graph.edges)+chain.index(r0);self.xy=np.array(positions);self.vertex_map=lookup
        nd=2*len(self.edges);tail=np.empty(nd,int);head=np.empty(nd,int);tail[::2]=self.edges[:,0];head[::2]=self.edges[:,1];tail[1::2]=head[::2];head[1::2]=tail[::2]
        angle=np.arctan2(*(self.xy[head]-self.xy[tail]).T[::-1]);arcs=[[]for _ in positions]
        for i,v in enumerate(tail):arcs[v].append(i)
        rows=[];cols=[];phase=[]
        for i,v in enumerate(head):
            for j in arcs[v]:
                if head[j]==tail[i]:continue
                turn=(angle[j]-angle[i]+np.pi)%(2*np.pi)-np.pi
                rows.append(i);cols.append(j);phase.append(np.exp(.5j*turn))
        self.rows=np.array(rows);self.cols=np.array(cols);self.phase=np.array(phase);self.nd=nd

    def posterior(self,s,h):
        s,h=observations(self.graph,s,h,self.p,self.q)
        if self.p==0:return np.array([1.,0.]),{'penalty':self.penalty,'approximate':True}
        if self.p==1:
            probs=np.zeros(2);probs[self.graph.logical_parity(np.ones(len(self.graph.edges),np.uint8))]=1.
            return probs,{'penalty':self.penalty,'deterministic_prior':True}
        c0=np.asarray(self._T@s).ravel().astype(np.uint8)&1;w=np.ones(len(self.edges));eps=np.exp(-self.penalty)
        for row,v in enumerate(self.graph.detector_vertices):
            edges=list(self.graph.incident_edges[v]);d=len(edges)
            pattern=np.array([[0,0],[1,1]])if d==2 else np.array([[0,0,0],[0,1,1],[1,0,1],[1,1,0]])
            n=(pattern^c0[edges]).sum(1)
            f=np.where(n>=2,1.,eps)if h[row]else np.where(n>=2,max(1-self.q,eps),1.)
            pair=f[1:]/f[0]
            if d==2:legs=np.repeat(np.sqrt(pair[0]),2)
            else:
                a,b,c=pair;legs=np.sqrt([b*c/a,a*c/b,a*b/c])
            w[edges]*=legs
        ratio=self.p/(1-self.p);w[:len(self.graph.edges)]*=np.where(c0==0,ratio,1/ratio)
        T=np.zeros((self.nd,self.nd),complex);T[self.rows,self.cols]=self.phase*w[self.cols//2]
        A=np.eye(self.nd)-T
        # dT / d log(weight of rail edge): precisely the two arc columns.
        dT=np.zeros_like(T);mask=self.cols//2==self.flip_edge;dT[self.rows[mask],self.cols[mask]]=T[self.rows[mask],self.cols[mask]]
        try:value=-.5*np.trace(np.linalg.solve(A,dT))
        except np.linalg.LinAlgError as exc:raise NumericalInferenceError('Kac–Ward solve failed')from exc
        if not np.isfinite(value)or abs(value.imag)>1e-7 or value.real< -1e-7 or value.real>1+1e-7:raise NumericalInferenceError(f'Kac–Ward posterior gate failed: {value}')
        pf=float(np.clip(value.real,0,1));probs=np.array([1-pf,pf])
        if self.graph.logical_parity(c0):probs=probs[::-1]
        return probs,{'penalty':self.penalty,'approximate':True,'imaginary_probability':float(value.imag),'matrix_size':self.nd}
