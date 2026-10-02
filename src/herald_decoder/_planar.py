"""Planar parity gadgets and a face-based Pfaffian orientation.

Internal implementation: graph/embedding are built from the canonical patch.
Every active vertex has 2 or 3 ports after the rough-boundary parity rail is added.
"""
from collections import deque
import numpy as np
from ._geometry import require_canonical_honeycomb


def face_cycles(xy,edges):
    tail=np.empty(2*len(edges),int)
    head=np.empty_like(tail);tail[::2]=edges[:,0];tail[1::2]=edges[:,1];head[::2]=edges[:,1];head[1::2]=edges[:,0]
    rings=[[] for _ in xy]
    for h in range(len(tail)):rings[tail[h]].append(h)
    for v,ring in enumerate(rings):ring.sort(key=lambda h:np.arctan2(*(xy[head[h]]-xy[v])[::-1]))
    loc={h:i for ring in rings for i,h in enumerate(ring)}
    nxt=np.array([rings[head[h]][(loc[h^1]-1)%len(rings[head[h]])] for h in range(len(tail))])
    owner=np.full(len(tail),-1,int);cycles=[];areas=[]
    for start in range(len(tail)):
        if owner[start]>=0:continue
        hs=[];h=start
        while owner[h]<0:owner[h]=len(cycles);hs.append(h);h=nxt[h]
        if h!=start:raise ValueError('invalid planar rotation system')
        cyc=np.array(hs);a=xy[tail[cyc]];b=xy[head[cyc]]
        cycles.append(cyc);areas.append(.5*np.sum(a[:,0]*b[:,1]-b[:,0]*a[:,1]))
    return owner,cycles,np.array(areas)


def pfaffian_orientation(xy,edges):
    owner,cycles,areas=face_cycles(xy,edges);outer=np.flatnonzero(areas<0)
    if len(outer)!=1 or len(xy)-len(edges)+len(cycles)!=2:raise ValueError('gadget embedding must be connected and planar')
    # Build any dual spanning tree. Non-tree edge orientations start positive;
    # each leaf face fixes the remaining edge to have odd clockwise parity.
    adj=[[] for _ in cycles]
    for e in range(len(edges)):
        f,g=owner[2*e:2*e+2]
        if f!=g:adj[f].append((g,e));adj[g].append((f,e))
    parent={int(outer[0]):None};order=[int(outer[0])]
    for f in order:
        for g,e in adj[f]:
            if g not in parent:parent[g]=(f,e);order.append(g)
    if len(order)!=len(cycles):raise ValueError('dual graph disconnected')
    sign=np.ones(len(edges),int)
    for f in reversed(order[1:]):
        _,e=parent[f];cyc=cycles[f];h=int(cyc[(cyc//2)==e][0])
        others=cyc[(cyc//2)!=e]
        cw=sum(((sign[k//2]>0)!=(k%2==0)) for k in others)
        along=(cw%2==1)
        sign[e]=1 if along==(h%2==0) else -1
    for f,cyc in enumerate(cycles):
        if f==outer[0]:continue
        if sum(((sign[h//2]>0)!=(h%2==0)) for h in cyc)%2!=1:raise RuntimeError('Pfaffian face parity check failed')
    return sign


class ParityGadgets:
    def __init__(self,graph):
        require_canonical_honeycomb(graph)
        if graph.name!='honeycomb':raise ValueError('planar solver currently supports the canonical honeycomb graph')
        incident=graph.incident_edges
        if any(len(incident[v])not in(2,3) for v in graph.detector_vertices):raise ValueError('requires measured degree two or three')
        xy=np.array([(v.x,v.y)for v in graph.vertices]);detrow=graph.detector_row
        left=sorted((v for v in graph.boundary_vertices if graph.vertices[v].boundary_side=='left' and incident[v]),key=lambda v:xy[v,1])
        right=sorted((v for v in graph.boundary_vertices if graph.vertices[v].boundary_side=='right' and incident[v]),key=lambda v:-xy[v,1])
        if any(len(incident[v])>1 for v in graph.boundary_vertices):raise ValueError('unmeasured boundaries must be leaves or isolated')
        r0,r1=len(xy),len(xy)+1;ytop=xy[:,1].max()+1.5
        centers={v:xy[v] for v in graph.detector_vertices};centers.update({v:xy[v]for v in left+right});centers.update({r0:np.array([xy[left[-1],0],ytop]),r1:np.array([xy[right[0],0],ytop])})
        rail=left+[r0,r1]+right;wires=list(graph.edges)+list(zip(rail[:-1],rail[1:]));ports={v:[] for v in centers}
        for e,(u,v)in enumerate(wires):ports[u].append((e,v));ports[v].append((e,u))
        positions=[];node={};ordered={};inside={}
        for v,prts in ports.items():
            prts.sort(key=lambda ev:np.arctan2(*(centers[ev[1]]-centers[v])[::-1]));ordered[v]=prts
            for e,w in prts:
                direction=centers[w]-centers[v];node[v,e]=len(positions);positions.append(centers[v]+.25*direction/np.linalg.norm(direction))
            if len(prts)==3:
                inside[v]=len(positions)
                positions.append(np.mean([positions[node[v,e]] for e,_ in prts],axis=0))
            elif len(prts)!=2:raise ValueError('unsupported gadget port count')
        edges=[]
        def add(u,v):edges.append((u,v));return len(edges)-1
        self.wire=np.array([add(node[u,e],node[v,e]) for e,(u,v)in enumerate(wires)])
        self.logical_edge=int(self.wire[wires.index((r0,r1))]);self.constant=list(self.wire[len(graph.edges):]);self.sites=[]
        for v,prts in ordered.items():
            legs=[node[v,e]for e,_ in prts]
            if len(legs)==3:
                spokes=[add(u,inside[v])for u in legs]
                triangles=[add(legs[1],legs[2]),add(legs[2],legs[0]),add(legs[0],legs[1])]
                if v in detrow:self.sites.append((detrow[v],[e for e,_ in prts],spokes,triangles))
                else:self.constant.extend(spokes+[triangles[0]])
            else:
                link=add(*legs)
                if v in detrow:self.sites.append((detrow[v],[e for e,_ in prts],[link],[]))
                else:self.constant.append(link)
        self.edges=np.array(edges);self.xy=np.array(positions);self.sign=pfaffian_orientation(self.xy,self.edges);self.n=len(positions)
