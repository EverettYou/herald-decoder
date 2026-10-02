"""Checkpointed, registered matched-record mechanism experiments."""
from dataclasses import replace
from collections import deque
from pathlib import Path
from time import monotonic
import argparse
import hashlib
import json
import platform
import numpy as np
import pymatching
from current_oracle import CurrentOracle, square_graph, honeycomb_graph, LAB, ROOT
from decoder_comparison import DecoderAdapter, compare_record


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def make_model(lattice,L,pattern='stored'):
    g=(square_graph if lattice=='square' else honeycomb_graph)(L)
    if pattern=='stored':return g
    assert pattern=='bipartite'
    adj=[[] for _ in g.vertices]
    for u,v in g.edges:adj[u].append(v);adj[v].append(u)
    color={}
    for root in range(len(g.vertices)):
        if root in color or not adj[root]:continue
        color[root]=0;queue=deque([root])
        while queue:
            u=queue.popleft()
            for v in adj[u]:
                if v not in color:color[v]=1-color[u];queue.append(v)
                else:assert color[v]!=color[u]
    edges=tuple((u,v) if color[u]==0 else (v,u) for u,v in g.edges)
    return replace(g,edges=edges)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest');args=parser.parse_args()
    manifest_path=LAB/args.manifest;manifest=json.loads(manifest_path.read_text())
    result_dir=LAB/manifest['result_directory'];result_dir.mkdir(parents=True,exist_ok=True)
    source_files=[LAB/'scripts'/s for s in ('current_oracle.py','decoder_comparison.py','biased_bp_kernel.py','run_mechanism.py')]
    source_files += [ROOT/'src/herald_decoder/lattice_model.py',ROOT/'labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py',
                     ROOT/'labs/lab-006-sun-bp-theory/scripts/sun_fusion_bp.py']
    hashes={str(f.relative_to(ROOT)):sha(f) for f in source_files}
    frozen_manifest={k:v for k,v in manifest.items() if k not in ('status','completed_at','analysis')}
    design_hash=hashlib.sha256(json.dumps(frozen_manifest,sort_keys=True).encode()).hexdigest()
    cache={};start=monotonic()
    for cell in manifest['cells']:
        name=cell['id'];path=result_dir/(name+'.json')
        if path.exists():
            out=json.loads(path.read_text())
            assert out['source_sha256']==hashes and out['design_sha256']==design_hash
            if out['status']=='complete':print('REUSE',name,flush=True);continue
        else:out={'status':'running','cell':cell,'source_sha256':hashes,'design_sha256':design_hash,
                  'manifest':str(manifest_path.relative_to(ROOT)),
                  'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pymatching':pymatching.__version__},
                  'records':[],'compute_seconds':0.}
        key=(cell['lattice'],cell['L'],cell.get('arrows','stored'),cell['q']==1)
        if key not in cache:
            # Keep only this size/alphabet's oracle; construction is cheap relative to acquisition.
            cache={}
            g=make_model(key[0],key[1],key[2])
            cache[key]=(g,CurrentOracle(g,directed=key[3],cap=manifest.get('max_topology_candidates',12_000_000)))
        g,oracle=cache[key];decoder=DecoderAdapter(g,cell['p'],cell['q'],cell.get('bp_iterations',300))
        out['oracle_profile']=oracle.profile
        rng=np.random.default_rng(cell['seed'])
        # Separate arrays keep samples coupled across q and arrow pattern.
        activity=rng.random((cell['shots'],len(g.edges)))<cell['p']
        orientation=rng.random((cell['shots'],len(g.edges)))<cell['q']
        currents=activity*np.where(orientation,1,-1)
        sample_start=monotonic()
        for i in range(len(out['records']),cell['shots']):
            row=compare_record(g,oracle,decoder,currents[i])
            row['sample_index']=i;row['current']=currents[i].tolist()
            out['records'].append(row)
            if (i+1)%32==0 or i+1==cell['shots']:
                out['compute_seconds']+=monotonic()-sample_start
                out['status']='complete' if i+1==cell['shots'] else 'running'
                tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n');tmp.replace(path)
                sample_start=monotonic()
                print(name,i+1,'/',cell['shots'],'risk',round(float(np.mean([r['bayes_risk'] for r in out['records']])),5),
                      'seconds',round(out['compute_seconds'],1),flush=True)
        risks={k:float(np.mean([r[k] for r in out['records']])) for k in ('bayes_risk','exact_mwpm_risk','bp_mwpm_risk')}
        print('CELL_COMPLETE',name,json.dumps(risks),flush=True)
    print('ALL_COMPLETE',len(manifest['cells']),'seconds',monotonic()-start,flush=True)


if __name__=='__main__':main()
