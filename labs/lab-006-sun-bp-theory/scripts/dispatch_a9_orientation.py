#!/usr/bin/env python3
"""Resume whole paired cells without reseeding or splitting the registered RNG stream."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import time
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[name]='1'
HERE=Path(__file__).resolve().parent;LAB=HERE.parent;ROOT=LAB.parents[1]
LATTICES=('square','honeycomb');GROUPS=('U1','SU2','SU3');SIZES=(5,7,9,11);RATES=[round(.02*i,2) for i in range(1,26)]

def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)
def source_hashes():
    paths=[HERE/name for name in ('run_a9_hidden_orientation.py','dispatch_a9_orientation.py','validate_a9_hidden_orientation.py','run_a7_ler.py','artifact_backend.py','numba_fusion_decoder.py','sun_fusion_bp.py')]+[ROOT/'src/herald_decoder/lattice_model.py']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def job_cell(job):
    from run_a9_hidden_orientation import run_cell
    lattice,group,L,p,shots,pilot=job
    index=round(p/.02)-1;seed=950000+100*L+index
    path=None if pilot else LAB/'results/a9-paired-shots'/f'{lattice}-{group}-L{L}-p{p:.2f}.npz'
    result=run_cell(lattice,group,L,p,shots,seed,256,path)
    if not pilot:
        baseline=json.loads((LAB/f'results/a8-fullrecord-{lattice}-{group}-final-v2.json').read_text())
        old=next(r for r in baseline['rows'] if r['L']==L and r['p']==p)
        for key in ('logical_failures','bp_nonconverged','invalid_correction'):
            assert result['arms']['directed'][key]==old[key],f'directed replay mismatch: {lattice}/{group}/L{L}/p{p}/{key}'
        result['directed_replay_matches_A8']=True
    result['completed_at']=now()
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=48);parser.add_argument('--pilot',action='store_true');args=parser.parse_args()
    validation=json.loads((LAB/'results/a9-validation.json').read_text())
    assert validation['status']=='passed' and validation['source_sha256']==source_hashes(), 'Validation is stale or failed'
    if not args.pilot:
        pilot=json.loads((LAB/'results/a9-pilot.json').read_text())
        assert pilot['status']=='passed' and pilot['source_sha256']==source_hashes(), 'Pilot is stale or failed'
    source=source_hashes();count=0;rows=[];payloads={}
    results=LAB/'results';checkpoint=results/('a9-pilot.json' if args.pilot else 'a9-acquisition-progress.json')
    if args.pilot:
        jobs=[(lat,g,L,p,32,True) for p in (.1,.3,.5) for L in (5,9) for lat in LATTICES for g in GROUPS]
    else:
        baselines={f'{lat}/{g}':hashlib.sha256((results/f'a8-fullrecord-{lat}-{g}-final-v2.json').read_bytes()).hexdigest() for lat in LATTICES for g in GROUPS}
        for lat in LATTICES:
            for g in GROUPS:
                path=results/f'a9-hidden-{lat}-{g}.json'
                if path.exists():
                    data=json.loads(path.read_text());assert data['source_sha256']==source and data['baseline_sha256']==baselines[f'{lat}/{g}']
                else:data={'status':'running','scope':{'lattice':lat,'group':g,'orientation':'hidden independent fair pair orientation','measure_boundary_representation':False,'shots_per_cell':20000,'batch_size':256,'damping':.5,'max_iterations':300,'tolerance':1e-10,'SU2_inference':'exact binary quotient'},'rows':[],'source_sha256':source,'baseline_sha256':baselines[f'{lat}/{g}']}
                payloads[lat,g]=data;count+=len(data['rows']);atomic(path,data)
        jobs=[(lat,g,L,p,20000,False) for p in RATES for L in SIZES for lat in LATTICES for g in GROUPS if not any(r['L']==L and r['p']==p for r in payloads[lat,g]['rows'])]
    atomic(checkpoint,{'status':'running','started_at':now(),'pid':os.getpid(),'workers':args.workers,'completed_cells':count,'remaining_cells':len(jobs),'source_sha256':source})
    print(f'{now()} starting {len(jobs)} paired cells, pilot={args.pilot}, workers={args.workers}',flush=True)
    try:
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            futures={pool.submit(job_cell,job):job for job in jobs}
            for future in as_completed(futures):
                row=future.result();assert source_hashes()==source,'Scientific source drift'
                count+=1
                if args.pilot:
                    rows.append(row);atomic(checkpoint,{'status':'running','rows':rows,'completed_cells':count,'source_sha256':source})
                else:
                    data=payloads[row['lattice'],row['group']];data['rows'].append(row);data['rows'].sort(key=lambda r:(r['L'],r['p']))
                    data['status']='complete' if len(data['rows'])==100 else 'running';data['updated']=now()
                    atomic(results/f"a9-hidden-{row['lattice']}-{row['group']}.json",data)
                    atomic(checkpoint,{'status':'running','pid':os.getpid(),'updated':now(),'completed_cells':count,'total_cells':600,'source_sha256':source})
                    if count%6==0:
                        from render_a9_orientation import render
                        render()
                print(f"{now()} {count}/{'36' if args.pilot else '600'} {row['lattice']}/{row['group']} L{row['L']} p={row['p']} directed={row['arms']['directed']['ler']:.5g} hidden={row['arms']['hidden_orientation']['ler']:.5g} seconds={row['elapsed_seconds']:.1f}",flush=True)
        if args.pilot:atomic(checkpoint,{'status':'passed','rows':rows,'completed_cells':count,'source_sha256':source,'updated':now()})
        else:
            from render_a9_orientation import render
            render();atomic(checkpoint,{'status':'complete','completed_cells':600,'total_cells':600,'source_sha256':source,'updated':now()})
    except Exception as error:
        atomic(checkpoint,{'status':'failed','completed_cells':count,'error':repr(error),'source_sha256':source,'updated':now()});raise

if __name__=='__main__':main()
