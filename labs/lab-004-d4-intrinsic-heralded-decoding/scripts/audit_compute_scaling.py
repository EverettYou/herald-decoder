#!/usr/bin/env python3
"""Matched, process-batched D4 throughput and iteration-sensitivity audit.

Workers cache their own mutable BP templates. No decoder recurrence, observation
law, matching weight or scoring rule is changed. Timing repetitions replay the
same histories and are never counted as independent science samples.
"""
from __future__ import annotations
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import platform
import statistics
import time
import numpy as np
from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_dense_template, run_r6d_dense_template, require_r6d_dense_backend
from d4_matching import edge_chain_boundary, published_herald_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import trajectory_seeds, llr_weights

LAB = Path(__file__).resolve().parents[1]
MANIFEST = LAB / 'manifests/compute-scaling-2026-09-09.json'
_CACHE = {}

def fingerprint(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()

def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)

def simulate(size, rate, index, salt, caps):
    timing = {}
    started = time.perf_counter()
    key = (size, rate)
    if key not in _CACHE:
        lattice = paper_periodic_honeycomb(size)
        _CACHE[key] = lattice, build_r6d_dense_template(lattice, error_rate=rate)
    lattice, template = _CACHE[key]
    timing['setup'] = time.perf_counter()-started
    t = time.perf_counter()
    ps, obs = trajectory_seeds(salt, size, rate, index)
    physical = (np.random.default_rng(ps).random(lattice.edge_count)<rate).astype(np.uint8)
    observation = observation_from_error_edges(lattice, physical, seed=obs)
    timing['sample'] = time.perf_counter()-t
    row = dict(size=size,p_X=rate,index=index,physical_seed=int(ps),observation_seed=int(obs),physical_hash=fingerprint(physical),status=observation.status)
    if observation.status == 'logical_failure':
        row.update(terminal=True,herald_failure=True,bp={})
        return row,timing
    if observation.status != 'sampled':
        raise RuntimeError(observation.status)
    charge = np.asarray(observation.charge_outcomes, dtype=np.int64)
    if not set(charge.tolist()) <= {0,1}:
        raise RuntimeError('Public signal boundary violated')
    public = PublicD4Observation(tuple(map(int,edge_chain_boundary(lattice,physical))),tuple(map(int,charge)))
    row.update(terminal=False,public_hash=fingerprint(np.array([public.flux_syndrome,public.charge_outcomes],dtype=np.int64)))
    t=time.perf_counter()
    o2=decode_and_score_flux_recovery(lattice,physical,published_herald_weights(lattice,charge))
    timing['herald_matching_and_score']=time.perf_counter()-t
    row.update(herald_failure=bool(o2.logical_error),herald_correction=fingerprint(o2.correction),bp={})
    previous = None
    for cap in caps:
        t=time.perf_counter()
        bp=run_r6d_dense_template(template,public,old_message_weight=.25,max_iterations=cap,tolerance=1e-8)
        timing[f'bp_{cap}']=time.perf_counter()-t
        t=time.perf_counter()
        recovery=decode_and_score_flux_recovery(lattice,physical,llr_weights(bp.marginals[:lattice.edge_count,1]))
        timing[f'bp_matching_and_score_{cap}']=time.perf_counter()-t
        marginal=bp.marginals[:lattice.edge_count,1]
        row['bp'][str(cap)]={'failure':bool(recovery.logical_error),'correction':fingerprint(recovery.correction),'marginals':fingerprint(marginal),'converged':bool(bp.converged),'iterations':int(bp.iterations),'message_delta':float(bp.max_message_delta),'max_marginal_change_from_previous':None if previous is None else float(np.max(np.abs(marginal-previous)))}
        previous=marginal.copy()
    return row,timing

def batch(job):
    size,rate,indices,salt,caps=job
    return [simulate(size,rate,i,salt,caps) for i in indices]

def flatten(chunks):
    return [item for chunk in chunks for item in chunk]

def benchmark(manifest):
    c=manifest['engineering']; n=c['histories']; bs=c['batch_size']
    jobs=[(c['size'],c['p_X'],list(range(i,min(i+bs,n))),c['seed_salt'],[40]) for i in range(0,n,bs)]
    result={'status':'running','manifest':MANIFEST.name,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'backend':require_r6d_dense_backend(),'platform':platform.platform(),'cpu_affinity':sorted(os.sched_getaffinity(0)),'rows':[],'claim_boundary':manifest['claim_boundary']}
    baseline=None
    for workers in c['workers']:
        start=time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn')) as pool:
            warm=flatten(pool.map(batch,jobs))
            cold=time.perf_counter()-start
            samples=[]
            for repeat in range(c['timed_rounds']):
                t=time.perf_counter(); outputs=flatten(pool.map(batch,jobs)); samples.append(time.perf_counter()-t)
                science=[r for r,_ in outputs]
                if baseline is None: baseline=science
                if science!=baseline or [r for r,_ in warm]!=baseline:
                    raise AssertionError(f'Parallel scientific equivalence failed for {workers}')
            parts={k:sum(t.get(k,0) for _,t in outputs)/n for k in outputs[0][1]}
        row={'workers':workers,'histories_per_repeat':n,'cold_start_and_first_batch_seconds':cold,'warm_seconds':samples,'warm_histories_per_second':n/statistics.median(samples),'mean_component_seconds_per_history':parts,'exact_scientific_equality':True}
        result['rows'].append(row);write(LAB/'results/compute-scaling-2026-09-09.json',result)
        print(json.dumps(row),flush=True)
    fastest=max(r['warm_histories_per_second'] for r in result['rows'])
    chosen=min(r['workers'] for r in result['rows'] if r['warm_histories_per_second']>=.9*fastest)
    serial=result['rows'][0]['warm_histories_per_second']
    result.update(status='complete',selected_workers=chosen if fastest/serial>=1.2 else 1,maximum_speedup=fastest/serial,unique_engineering_histories=n,baseline_science=baseline)
    write(LAB/'results/compute-scaling-2026-09-09.json',result)
    return result

def pilot(manifest, workers):
    c=manifest['sensitivity_pilot']; n=c['histories_per_cell'];bs=4
    jobs=[(size,p,list(range(i,min(i+bs,n))),c['seed_salt'],c['iteration_caps']) for size in c['sizes'] for p in c['p_X'] for i in range(0,n,bs)]
    result={'status':'running','manifest':MANIFEST.name,'rows':[],'elapsed_seconds':None,'workers':workers,'claim_boundary':'Bounded iteration sensitivity, not a threshold fit.'}
    started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn')) as pool:
        for outputs in pool.map(batch,jobs):
            result['rows'].extend(r for r,_ in outputs)
            result['elapsed_seconds']=time.perf_counter()-started
            write(LAB/'results/iteration-sensitivity-2026-09-09.json',result)
            print(json.dumps({'pilot_histories':len(result['rows']),'seconds':result['elapsed_seconds']}),flush=True)
    summaries=[]
    for size in c['sizes']:
        for p in c['p_X']:
            rows=[r for r in result['rows'] if r['size']==size and r['p_X']==p]
            cell={'size':size,'p_X':p,'attempted':len(rows),'terminal':sum(r['terminal'] for r in rows),'herald_failures':sum(r['herald_failure'] for r in rows),'caps':{},'comparisons':{}}
            for cap in c['iteration_caps']:
                cell['caps'][str(cap)]={'failures':sum(r['terminal'] or r['bp'][str(cap)]['failure'] for r in rows),'converged':sum(not r['terminal'] and r['bp'][str(cap)]['converged'] for r in rows)}
            for ca,cb in zip(c['iteration_caps'][:-1],c['iteration_caps'][1:]):
                pairs=[(r['bp'][str(ca)],r['bp'][str(cb)]) for r in rows if not r['terminal']]
                cell['comparisons'][f'{ca}_to_{cb}']={'correction_changes':sum(a['correction']!=b['correction'] for a,b in pairs),'failure_improvements':sum(a['failure'] and not b['failure'] for a,b in pairs),'failure_regressions':sum(not a['failure'] and b['failure'] for a,b in pairs),'max_marginal_change':max((b['max_marginal_change_from_previous'] for a,b in pairs),default=0)}
            summaries.append(cell)
    replays=[]
    for size in c['sizes']:
        for p in c['p_X']:
            row=next(r for r in result['rows'] if r['size']==size and r['p_X']==p and r['index']==0)
            replay,_=simulate(size,p,0,c['seed_salt'],c['iteration_caps'])
            assert replay==row,'Pilot deterministic replay failed'
            replays.append({'size':size,'p_X':p,'index':0,'exact':True})
    result.update(status='complete',summaries=summaries,deterministic_replays=replays)
    write(LAB/'results/iteration-sensitivity-2026-09-09.json',result)
    print(json.dumps({'pilot_summaries':summaries}),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['benchmark','pilot','all'],default='all');args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text())
    for path,digest in manifest['source_hashes'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f'Registered source changed: {path}')
    if args.phase in ('benchmark','all'): result=benchmark(manifest)
    else: result=json.loads((LAB/'results/compute-scaling-2026-09-09.json').read_text())
    if args.phase in ('pilot','all'):
        if result['status']!='complete': raise RuntimeError('Benchmark incomplete')
        pilot(manifest,result['selected_workers'])

if __name__=='__main__':main()
