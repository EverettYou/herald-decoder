#!/usr/bin/env python3
"""Recover paired aggregates from atomic per-shot files without resampling."""
from __future__ import annotations
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
from datetime import datetime,timezone
import hashlib,json,re,time
from pathlib import Path
import numpy as np
import run_a9_hidden_orientation as a9
import run_a7_ler as directed
from dispatch_a9_orientation import source_hashes
from render_a9_orientation import render
LAB=Path(__file__).resolve().parents[1]

def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
    temp=path.with_suffix(f'.collector-{os.getpid()}.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)
def recover(path,lattice,group,L,p):
    seed=950000+100*L+round(p/.02)-1
    with np.load(path) as f:
        n=int(f['shots']);assert n==20000 and int(f['seed'])==seed and int(f['orientation_seed'])==seed+10000000
        flags=np.unpackbits(f['failures'],axis=1)[:,:n];nonconv=np.unpackbits(f['bp_nonconverged'],axis=1)[:,:n]
    assert flags.shape==nonconv.shape==(2,n)
    baseline=json.loads((LAB/f'results/a8-fullrecord-{lattice}-{group}-final-v2.json').read_text())
    old=next(r for r in baseline['rows'] if r['L']==L and r['p']==p)
    assert int(flags[0].sum())==old['logical_failures'] and int(nonconv[0].sum())==old['bp_nonconverged'] and old['invalid_correction']==0
    if group=='SU2':assert np.array_equal(flags[0],flags[1]) and np.array_equal(nonconv[0],nonconv[1])
    # Reconstruct only the cheap deterministic record streams, never repeat decoding.
    _,graph,_,boundary=directed.context(lattice,L);fixed=directed._record_tables(graph,boundary,group);hidden=a9.record_tables(graph,boundary,group)
    rng=np.random.default_rng(seed);orientation=np.random.default_rng(seed+10000000)
    hashes={k:hashlib.sha256() for k in ('activity','m','directed_R','hidden_R','orientation')};forward=reverse_count=0
    for begin in range(0,n,256):
        count=min(256,n-begin);errors=(rng.random((count,len(graph.edges)))<p).astype(np.uint8);u=rng.random((count,len(graph.vertices)));rev=(orientation.random(errors.shape)<.5).astype(np.uint8)
        m,dr=directed._generate_records_numba(errors,u,*fixed);mh,hr=a9.generate_hidden_records(errors,rev,u,*hidden);assert np.array_equal(m,mh)
        if group=='SU2':assert np.array_equal(dr,hr)
        for k,a in [('activity',errors),('m',m),('directed_R',dr),('hidden_R',hr),('orientation',rev)]:hashes[k].update(a.tobytes())
        reverse_count+=int(np.sum(errors*rev));forward+=int(np.sum(errors*(1-rev)))
    joint=np.bincount(2*flags[0]+flags[1],minlength=4).reshape(2,2)
    result={'lattice':lattice,'group':group,'L':L,'p':p,'shots':n,'seed':seed,'orientation_seed':seed+10000000,'batch_size':256,
            'scoring_rule':directed.SCORING_RULE,'joint_failures_directed_by_hidden':joint.tolist(),
            'truth_and_record_sha256':{k:v.hexdigest() for k,v in hashes.items()},'active_forward':forward,'active_reverse':reverse_count,
            'elapsed_seconds':None,'completed_at':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),
            'aggregation_recovery':'Per-shot failure/convergence bits recovered after collector rendering stalled; RNG hashes reconstructed without decoding. Iteration/time diagnostics unavailable.',
            'shot_indicators_path':str(path.relative_to(LAB)),'shot_indicators_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'directed_replay_matches_A8':True,'arms':{}}
    for i,name in enumerate(('directed','hidden_orientation')):
        k=int(flags[i].sum());result['arms'][name]={'logical_failures':k,'ler':k/n,'wilson95':list(directed.wilson(k,n)),'invalid_correction':0,'bp_nonconverged':int(nonconv[i].sum()),'mean_iterations':None,'max_terminal_delta':None}
    return result

def main():
    checkpoint=LAB/'results/a9-acquisition-progress.json';source=source_hashes();recovered=0
    atomic(LAB/'results/a9-collector-recovery.json',{'status':'active','pid':os.getpid(),'started':now(),'reason':'Original collector stopped publishing after 48 cells while workers continued writing atomic per-shot files. Recover exact failure and convergence aggregates; do not resample or alter the decoder.','source_sha256':source})
    while True:
        assert source_hashes()==source
        payloads={}
        for lat in ('square','honeycomb'):
            for group in ('U1','SU2','SU3'):
                p=LAB/f'results/a9-hidden-{lat}-{group}.json';d=json.loads(p.read_text());assert d['source_sha256']==source;payloads[lat,group]=d
        added=0
        for p in sorted((LAB/'results/a9-paired-shots').glob('*.npz')):
            match=re.fullmatch(r'(square|honeycomb)-(U1|SU2|SU3)-L(5|7|9|11)-p(\d\.\d\d)\.npz',p.name);assert match,p
            lat,group,L,rate=match.groups();L=int(L);rate=float(rate);d=payloads[lat,group]
            if any(r['L']==L and r['p']==rate for r in d['rows']):continue
            row=recover(p,lat,group,L,rate);d['rows'].append(row);d['rows'].sort(key=lambda r:(r['L'],r['p']));d['status']='complete' if len(d['rows'])==100 else 'running';d['updated']=now()
            atomic(LAB/f'results/a9-hidden-{lat}-{group}.json',d);added+=1;recovered+=1
        total=sum(len(d['rows']) for d in payloads.values())
        if added or total==600:
            render()
            atomic(checkpoint,{'status':'complete' if total==600 else 'running','completed_cells':total,'total_cells':600,'collector_pid':os.getpid(),'source_sha256':source,'updated':now()})
            atomic(LAB/'results/a9-collector-recovery.json',{'status':'complete' if total==600 else 'active','pid':os.getpid(),'updated':now(),'recovered_cells':recovered,'total_cells':total,'sampling_or_decoder_changed':False,'missing_recovered_fields':['elapsed_seconds','mean_iterations','max_terminal_delta'],'source_sha256':source})
            print(f'{now()} saved and rendered {total}/600 cells ({added} newly recovered)',flush=True)
        if total==600:break
        time.sleep(10)

if __name__=='__main__':main()
