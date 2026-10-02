"""Exact frontier contraction of bounded U(1) currents on the canonical graph.

Sectors are absolute logical-cut activity parities; conditioning fixes the
syndrome, so these are a record-dependent relabeling of relative sectors.
Each physical edge prior is inserted once, at its first measured endpoint.
Unmeasured rough-endpoint charges are summed without an observation factor.
"""
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import sys
import time
import numpy as np
from numba import njit

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(ROOT/'src'))
from herald_decoder.lattice_model import square_graph, honeycomb_graph


@njit(cache=True)
def make_transitions(before_size, base, alphabet, old_positions, old_signs,
                     keep_positions, new_signs, future_new, cut_new):
    nnew = len(new_signs)
    choices = base**nnew
    n = before_size * choices
    # before, after, charge, logical delta, nplus, nminus, new-config
    out = np.empty((n, 7), dtype=np.int32)
    row = 0
    for i in range(before_size):
        oldQ = 0
        for k in range(len(old_positions)):
            oldQ += old_signs[k] * alphabet[(i//(base**old_positions[k]))%base]
        keep = 0
        for k in range(len(keep_positions)):
            keep += ((i//(base**keep_positions[k]))%base)*base**k
        for conf in range(choices):
            after = keep
            Q, parity, plus, minus = oldQ, 0, 0, 0
            for k in range(nnew):
                digit = (conf//base**k)%base
                val = alphabet[digit]
                Q += new_signs[k]*val
                plus += val == 1
                minus += val == -1
                if cut_new[k] and val != 0: parity ^= 1
            for k in range(len(future_new)):
                digit = (conf//base**future_new[k])%base
                after += digit*base**(len(keep_positions)+k)
            out[row] = (i, after, Q, parity, plus, minus, conf)
            row += 1
    return out


@njit(cache=True)
def forward_step(previous, transitions, weights, after_size):
    out = np.zeros((after_size,2))
    for t in range(len(transitions)):
        a,b,_,h,_,_,_ = transitions[t]
        w = weights[t]
        out[b,h] += previous[a,0]*w
        out[b,1^h] += previous[a,1]*w
    scale = out.sum()
    if scale > 0: out /= scale
    return out, scale


@njit(cache=True)
def backward_step(fwd, later, transitions, weights, scale, before_size,
                  nnew, base, alphabet):
    back = np.zeros((before_size,2))
    # Per-sector joint moments for positive/negative new currents.
    joint = np.zeros((2,nnew,2))
    for t in range(len(transitions)):
        a,b,_,h,_,_,conf = transitions[t]
        w = weights[t]/scale
        for k in range(2):
            back[a,k] += w*later[b,k^h]
            contribution = w*(fwd[a,0]*later[b,k^h] + fwd[a,1]*later[b,k^1^h])
            for e in range(nnew):
                value = alphabet[(conf//base**e)%base]
                if value == 1: joint[k,e,0] += contribution
                if value == -1: joint[k,e,1] += contribution
    return back, joint


def charge_matrix(model, measured=None):
    measured = model.detector_vertices if measured is None else tuple(measured)
    D = np.zeros((len(measured),len(model.edges)),dtype=np.int8)
    index = {v:i for i,v in enumerate(measured)}
    for a,(u,v) in enumerate(model.edges):
        if u in index: D[index[u],a] = -1
        if v in index: D[index[v],a] = 1
    return D


class CurrentOracle:
    def __init__(self, model, *, directed=False, measured=None, cap=12_000_000, order=None):
        start=time.monotonic()
        self.model=model
        self.measured=tuple(model.detector_vertices if measured is None else measured)
        self.D=charge_matrix(model,self.measured)
        self.alphabet=np.array([0,1] if directed else [0,1,-1],dtype=np.int64)
        self.base=len(self.alphabet)
        self.row={v:i for i,v in enumerate(self.measured)}
        candidates=[list(self.measured),
                    sorted(self.measured,key=lambda v:(round(model.vertices[v].y,6),model.vertices[v].x)),
                    sorted(self.measured,key=lambda v:(round(model.vertices[v].x,6),model.vertices[v].y))]
        if order is not None: candidates=[order]
        sketches=[self._sketch(o) for o in candidates]
        steps,cost,width=min(sketches,key=lambda x:x[1])
        if cost>cap: raise MemoryError(f'candidate cap: {cost}>{cap}, width={width}')
        self.steps=[]
        for step in steps:
            before,new,old,keep,future,v=step
            signs=lambda es:np.array([1 if model.edges[a][1]==v else -1 for a in es],dtype=np.int64)
            a=make_transitions(self.base**len(before),self.base,self.alphabet,
                np.array([before.index(e) for e in old],dtype=np.int64),signs(old),
                np.array([before.index(e) for e in keep],dtype=np.int64),signs(new),
                np.array([new.index(e) for e in future],dtype=np.int64),
                np.array([e in model.logical_edges for e in new],dtype=np.bool_))
            grouped={int(Q):np.ascontiguousarray(a[a[:,2]==Q]) for Q in np.unique(a[:,2])}
            self.steps.append((self.row[v],new,self.base**len(before),
                               self.base**(len(keep)+len(future)),grouped))
        self.profile={'candidate_transitions':cost,'maximum_frontier':width,
                      'construction_seconds':time.monotonic()-start,
                      'order':[step[-1] for step in steps],'base':self.base}

    def _sketch(self, order):
        visited=set(); assigned=set(); frontier=[]; steps=[]; cost=0; width=0
        inc=self.model.incident_edges; measured=set(self.measured)
        for v in order:
            old=[a for a in inc[v] if a in assigned]
            new=[a for a in inc[v] if a not in assigned]
            keep=[a for a in frontier if a not in old]
            visited.add(v)
            future=[a for a in new if any(u in measured and u not in visited for u in self.model.edges[a])]
            steps.append((list(frontier),new,old,keep,future,v))
            cost+=self.base**(len(frontier)+len(new))
            width=max(width,len(frontier),len(keep)+len(future))
            assigned.update(new);frontier=keep+future
        assert not frontier and len(assigned)==len(self.model.edges)
        return steps,cost,width

    def infer(self, charges, p, q):
        if self.base==2 and q!=1: raise ValueError('binary oracle requires q=1')
        charges=np.asarray(charges,dtype=int)
        fwd=[np.array([[1.,0.]])];scales=[];trans=[];weights=[]
        for row,new,before_size,after_size,grouped in self.steps:
            t=grouped.get(int(charges[row]))
            if t is None: raise ValueError('impossible charge record')
            w=(1-p)**(len(new)-t[:,4]-t[:,5])*(p*q)**t[:,4]*(p*(1-q))**t[:,5]
            out,scale=forward_step(fwd[-1],t,w,after_size)
            if scale<=0: raise ValueError('zero record evidence')
            fwd.append(out);scales.append(scale);trans.append(t);weights.append(w)
        sectors=fwd[-1][0].copy()
        joint=np.zeros((2,len(self.model.edges),2))
        back=np.array([[1.,0.]])
        for k in reversed(range(len(self.steps))):
            _,new,before_size,_,_=self.steps[k]
            back,local=backward_step(fwd[k],back,trans[k],weights[k],scales[k],
                                     before_size,len(new),self.base,self.alphabet)
            joint[:,new,:]=local
        assert np.max(abs(back[0]-sectors))<1e-9
        marginals=joint.sum(axis=(0,2))
        counts=np.divide(joint.sum(axis=1),sectors[:,None],
                         out=np.zeros((2,2)),where=sectors[:,None]>0)
        derivative=None
        if 0<q<1 and np.all(sectors>0):
            derivative=float((counts[0,0]-counts[1,0])/q-(counts[0,1]-counts[1,1])/(1-q))
        return {'sectors':sectors,'marginals':marginals,'sector_counts':counts,
                'log_evidence':float(np.log(scales).sum()),'response':derivative,
                'bayes_risk':float(min(sectors)),
                'signed_gap':float(np.log(sectors[0]/sectors[1])) if np.all(sectors>0) else (float('inf') if sectors[0]>0 else -float('inf'))}


def exact_enumeration(model,p,q,measured=None):
    D=charge_matrix(model,measured);table={}
    for current in product((0,1,-1),repeat=len(model.edges)):
        j=np.array(current)
        w=float(np.prod(np.where(j==0,1-p,np.where(j==1,p*q,p*(1-q)))))
        if w==0: continue
        Q=tuple(D@j)
        if Q not in table: table[Q]=[np.zeros(2),np.zeros(len(j)),np.zeros((2,2))]
        h=model.logical_parity((j!=0).astype(np.uint8))
        z,m,c=table[Q]
        z[h]+=w;m+=(j!=0)*w;c[h]+=w*np.array([(j==1).sum(),(j==-1).sum()])
    return table
