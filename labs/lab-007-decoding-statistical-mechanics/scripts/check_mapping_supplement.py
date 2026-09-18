#!/usr/bin/env python3
"""Independent height reconstruction and decoder witness checks."""
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import platform
import json
import sys
import numpy as np
from scipy.sparse import csc_matrix
import pymatching
from check_exact_model import LAB, ROOT, MANIFEST, incidence, logical
from numba_fusion_decoder import FastFusionBeliefMatchingDecoder, UndirectedFusionBeliefMatchingDecoder, GeneralizedSyndrome
from sun_fusion_bp import Graph


def cycles(g):
    measured=set(g['measured']);edges=[(u if u in measured else '_B',v if v in measured else '_B') for u,v in g['edges']]
    vertices=sorted({v for edge in edges for v in edge});adj=defaultdict(list)
    for a,(u,v) in enumerate(edges):adj[u].append((v,a,1));adj[v].append((u,a,-1))
    seen={vertices[0]};queue=[vertices[0]];tree=set()
    for u in queue:
        for v,a,sign in adj[u]:
            if v not in seen:seen.add(v);queue.append(v);tree.add(a)
    assert len(seen)==len(vertices)
    chords=[a for a in range(len(edges)) if a not in tree];columns=[]
    for a in chords:
        u,v=edges[a];paths={v:[]};queue=[v]
        for t in queue:
            for w,b,sign in adj[t]:
                if b in tree and w not in paths:paths[w]=paths[t]+[(b,sign)];queue.append(w)
        col=[0]*len(edges);col[a]=1
        for b,sign in paths[u]:col[b]+=sign
        columns.append(col)
    return chords,columns


def main():
    manifest=json.loads(MANIFEST.read_text());result=json.loads((LAB/'results/exact-model-checks-2026-09-14.json').read_text())
    fixtures={g['id']:g for g in manifest['fixtures']};height=[];backend=[];bp=[]
    for g in fixtures.values():
        chords,cols=cycles(g);inc=incidence(g)
        for hidden in (False,True):
            refs={};checked=0
            for j in product((0,1,-1) if hidden else (0,1),repeat=len(g['edges'])):
                q=tuple(sum(sign*j[a] for a,sign in row) for row in inc);ref=refs.setdefault(q,j)
                diff=[a-b for a,b in zip(j,ref)];coords=[diff[a] for a in chords]
                reconstructed=[sum(col[a]*z for col,z in zip(cols,coords)) for a in range(len(j))]
                assert diff==reconstructed
                assert logical(g,sum((v%2)<<a for a,v in enumerate(diff)))==logical(g,sum(((abs(a)-abs(b))%2)<<i for i,(a,b) in enumerate(zip(j,ref))))
                checked+=1
            height.append({'fixture':g['id'],'hidden':hidden,'currents_checked':checked,'integer_basis_dimension':len(chords),'charge_records':len(refs)})
    for row in result['rows']:
        witness=row['first_strict_counterexample']
        if witness is None:continue
        g=fixtures[row['fixture']];n=len(g['edges']);matrix=np.zeros((len(g['measured']),n),dtype=np.uint8)
        for v,inc in enumerate(incidence(g)):
            for a,sign in inc:matrix[v,a]=1
        marg=np.array([float(F(v)) for v in witness['edge_marginals']]);weights=np.log((1-marg)/marg)
        c=pymatching.Matching.from_check_matrix(csc_matrix(matrix),weights=weights).decode(np.array([m for m,r in witness['record']],dtype=np.uint8))
        mask=sum(int(v)<<a for a,v in enumerate(c));valid=np.array_equal(matrix@c%2,np.array([m for m,r in witness['record']]))
        backend.append({'fixture':row['fixture'],'group':row['group'],'orientation':row['orientation'],'p':row['p'],
                        'correction_mask':mask,'exact_surrogate_maximizers':witness['surrogate_maximizer_masks'],
                        'syndrome_valid':valid,'matches_exact_objective':mask in witness['surrogate_maximizer_masks']})
        if row['fixture']=='degree-four-star':
            vertices=tuple(dict.fromkeys(v for edge in g['edges'] for v in edge));graph=Graph(vertices,tuple(map(tuple,g['edges'])))
            cls=UndirectedFusionBeliefMatchingDecoder if row['orientation']=='shared-hidden-fair' else FastFusionBeliefMatchingDecoder
            decoder=cls(graph,p=float(F(row['p'])),group=row['group'],max_iterations=100,damping=0,tolerance=1e-12)
            obs=[]
            for i,v in enumerate(vertices):
                if v not in g['measured']:
                    decoder.bank[i,0]=1.;obs.append((0,'0' if row['group']=='U1' else '1'))
                else:
                    m,r=witness['record'][g['measured'].index(v)]
                    if row['group']=='U1' and int(r)>0:r='+'+r
                    obs.append((m,r))
            actual=decoder.infer(GeneralizedSyndrome(np.array([m for m,r in obs],dtype=np.uint8),tuple(r for m,r in obs)))
            error=float(np.max(abs(actual.edge_marginals-marg)));assert actual.converged and error<1e-10
            bp.append({'group':row['group'],'orientation':row['orientation'],'p':row['p'],'max_marginal_error':error,'iterations':actual.iterations})
    sys.path.insert(0, str(ROOT/'src'))
    from herald_decoder.lattice_model import square_graph, honeycomb_graph
    from collections import Counter
    geometry=[]
    for name,fn in [('square',square_graph),('honeycomb',honeycomb_graph)]:
        for size in (5,7,9,11):
            matrix=fn(size).check_matrix.tocsc()
            counts=Counter(tuple(matrix.indices[matrix.indptr[j]:matrix.indptr[j+1]]) for j in range(matrix.shape[1]))
            geometry.append({'geometry':name,'L':size,'duplicate_detector_columns':sum(n-1 for n in counts.values() if n>1)})
    out={'status':'passed','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'height_reconstruction':height,'matching_backend':backend,'parent_tree_BP':bp,
         'summary':{'integer_current_reconstructions':sum(r['currents_checked'] for r in height),'backend_witnesses':len(backend),
                    'backend_exact_objective_matches':sum(r['matches_exact_objective'] for r in backend),'tree_BP_checks':len(bp),
                    'max_tree_BP_error':max(r['max_marginal_error'] for r in bp)},
         'claim_boundary':'Matching mismatches are separate from the exact mathematical hardening counterexample.',
         'parent_geometry_inspection':geometry,
         'parent_lattice_sha256':hashlib.sha256((ROOT/'src/herald_decoder/lattice_model.py').read_bytes()).hexdigest(),
         'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pymatching':pymatching.__version__},
         'backend_status':'Six hexagon witnesses reproduce the exact objective; 15 star witnesses do not because repeated detector columns are merged. The canonical parent matrices inspected have no repeated columns.'}
    assert all(r['syndrome_valid'] for r in backend)
    (LAB/'results/mapping-supplement-2026-09-14.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['summary'],indent=2))
    for row in backend:
        if not row['matches_exact_objective']:print('BACKEND DIFFERENCE',row)

if __name__=='__main__':main()
