#!/usr/bin/env python3
"""Concurrent whole-cell acquisition; preserve the registered per-cell RNG stream."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import time

for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[name] = '1'
HERE = Path(__file__).resolve().parent
LAB = HERE.parent
RESULTS = LAB / 'results'
GROUPS = ('U1','SU2','SU3')
LATTICES = ('square','honeycomb')
SIZES = (5,7,9,11)
RATES = [round(.02*i,2) for i in range(1,26)]

def now():
    return datetime.now(timezone.utc).isoformat()

def atomic(path, data):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n')
    temporary.replace(path)

def hashes():
    paths = [HERE/n for n in ('run_a7_ler.py','artifact_backend.py','numba_fusion_decoder.py','sun_fusion_bp.py','dispatch_a8_ler.py')]
    paths += [LAB.parents[1]/'src/herald_decoder/lattice_model.py']
    return {str(p.relative_to(LAB.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def cell(job):
    import run_a7_ler as runner
    lattice,group,size,rate_index,shots = job
    runner.GROUPS=(group,)
    runner.ARMS=('representation_herald',)
    seed=950000+100*size+rate_index
    start=time.monotonic()
    rows=runner.run_cell(lattice,size,RATES[rate_index],shots,seed,256,optimized=True)
    row=rows[0]
    row.update(seed=seed,batch_size=256,elapsed_seconds=time.monotonic()-start,completed_at=now())
    return row

def render(payload):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=payload['rows']; scope=payload['scope']
    colors={5:'#1665a8',7:'#d36a16',9:'#16836e',11:'#854db3'}
    sampled=[r for r in rows if not r.get('exact_endpoint')]
    qualifier='complete' if len(sampled)==100 else f'partial: {len(sampled)}/100 sampled cells'
    for diagnostic in (False,True):
        fig,axis=plt.subplots(figsize=(9,6))
        for size in SIZES:
            curve=sorted([r for r in sampled if r['L']==size],key=lambda r:r['p'])
            if not curve: continue
            x=[r['p'] for r in curve]
            if diagnostic:
                axis.plot(x,[r['bp_nonconverged']/r['shots'] for r in curve],'.-',color=colors[size],label=f'L={size}')
            else:
                y=[r['ler'] for r in curve]
                axis.errorbar(x,y,yerr=[[max(0,r['ler']-r['wilson95'][0]) for r in curve],[max(0,r['wilson95'][1]-r['ler']) for r in curve]],fmt='o-',markersize=3,capsize=2,color=colors[size],label=f'L={size}')
        axis.plot([0],[0],'k*',markersize=8,label='p=0 exact')
        group={'U1':'U(1)','SU2':'SU(2)','SU3':'SU(3)'}[scope['group']]
        axis.set_title(f"{scope['lattice'].capitalize()} · {group} · {qualifier}\nFull interior (m,R), directed channel; rough-boundary m,R unmeasured")
        axis.set(xlabel='Physical edge-error probability p',ylabel='BP nonconvergence fraction' if diagnostic else 'Logical error rate',xlim=(0,.5),ylim=(0,1))
        axis.grid(alpha=.2); axis.legend(loc='upper left')
        fig.text(.5,.015,'20,000 independent shots per sampled cell; LER: Wilson 95% intervals.\nBP nonconvergence is diagnostic only. Missing cells are not zero; lines guide the eye.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.065,1,1))
        suffix='nonconvergence' if diagnostic else 'ler'
        path=LAB/'figures'/f"a8-{scope['lattice']}-{scope['group']}-{suffix}.png"
        temp=path.with_suffix('.tmp.png'); fig.savefig(temp,dpi=160); plt.close(fig); temp.replace(path)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--workers',type=int,default=48); parser.add_argument('--render-only',action='store_true'); args=parser.parse_args()
    import run_a7_ler as runner
    import run_a8_fullrecord_ler as a8
    payloads={}; jobs=[]; source=hashes()
    backup=RESULTS/'pre-resume-2026-09-07'; backup.mkdir(exist_ok=True)
    for lattice in LATTICES:
        for group in GROUPS:
            path=RESULTS/f'a8-fullrecord-{lattice}-{group}-final-v2.json'
            data=json.loads(path.read_text())
            expected={'lattice':lattice,'group':group,'shots_per_cell':20000,'scoring_rule':runner.SCORING_RULE}
            assert all(data['scope'].get(k)==v for k,v in expected.items()),path
            seen=set()
            for row in data['rows']:
                key=(row['L'],row['p']); assert key not in seen; seen.add(key)
                assert row['group']==group and row['lattice']==lattice and row['arm']=='representation_herald'
                assert row['shots']==20000 and row['L'] in SIZES
                assert row['logical_failures']==row['logical_parity_failures'] and row['invalid_correction']==0
                assert row['ler']==row['logical_failures']/row['shots']
            if not (backup/path.name).exists(): (backup/path.name).write_bytes(path.read_bytes())
            data['scope'].update(expected,measure_boundary_representation=False,orientation='directed',damping=.5,max_iterations=300,tolerance=1e-10,batch_size=256)
            data.setdefault('provenance',{'resumed_at':now(),'inherited_cells':len([r for r in data['rows'] if not r.get('exact_endpoint')]),'inherited_checkpoint':str((backup/path.name).relative_to(LAB)),'compatibility_evidence':'results/a7-runner-optimization-ab.json','note':'Inherited final-correction-v2 counts retained; historical source hashes were not recorded.'})
            data['provenance']['current_source_sha256']=source
            payloads[lattice,group]=data
            render(data)
    if args.render_only: return
    # Round-robin lattice/group and size at each p: every requested curve progresses.
    for rate_index,p in enumerate(RATES):
        for size in SIZES:
            for lattice in LATTICES:
                for group in GROUPS:
                    if not any(r['L']==size and r['p']==p for r in payloads[lattice,group]['rows']):
                        jobs.append((lattice,group,size,rate_index,20000))
    progress=RESULTS/'a8-acquisition-progress.json'
    atomic(progress,{'status':'running','pid':os.getpid(),'started_at':now(),'workers':args.workers,'remaining_cells':len(jobs),'source_sha256':source})
    print(f'{now()} starting {len(jobs)} cells with {args.workers} workers',flush=True)
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(cell,job):job for job in jobs}
        for future in as_completed(pending):
            row=future.result(); lattice,group=row['lattice'],row['group']; data=payloads[lattice,group]
            assert hashes()==source,'Frozen scientific sources changed during acquisition'
            data['rows'].append(row); data['rows'].sort(key=lambda r:(r['L'],r['p']))
            count=sum(not r.get('exact_endpoint',False) for r in data['rows'])
            data['status']='complete' if count==100 else 'running'; data['updated']=now()
            atomic(RESULTS/f'a8-fullrecord-{lattice}-{group}-final-v2.json',data)
            render(data)
            done=sum(sum(not r.get('exact_endpoint',False) for r in d['rows']) for d in payloads.values())
            atomic(progress,{'status':'complete' if done==600 else 'running','pid':os.getpid(),'updated':now(),'workers':args.workers,'completed_cells':done,'total_cells':600,'source_sha256':source})
            print(f'{now()} {done}/600 {lattice}/{group} L={row["L"]} p={row["p"]} LER={row["ler"]} seconds={row["elapsed_seconds"]:.1f}',flush=True)

if __name__=='__main__': main()
