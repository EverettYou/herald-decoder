"""Single-use exact validation of the frozen row-boundary approximation."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import json
import math
from pathlib import Path
import time
import numpy as np
from run_boundary_mps_validation import (
    LAB, ROOT, sha_file, sha_bytes, peak_gib, load_cell, absolute_gap, risk_share,
    square_graph, BoundaryMPSPosterior,
)

MANIFEST=LAB/'manifests/row-boundary-mps-fresh-validation-2026-09-22.json'
COHORT=LAB/'results/row-boundary-mps-fresh-validation-cohort-2026-09-22.json'
RESULT=LAB/'results/row-boundary-mps-fresh-validation-2026-09-22.json'


def dump(path, value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temp.replace(path)


def prereqs(contract):
    base=MANIFEST.parent; basis=contract['research_basis']
    for source in contract['immutable_exact_sources']:
        assert sha_file(base/source['path'])==source['sha256'],source['path']
    for key in ('prior_frozen_cohort','throughput_result','implementation'):
        assert sha_file(base/basis[key])==basis[key+'_sha256'],key
    prior=json.loads((base/basis['prior_frozen_cohort']).read_text())
    excluded={r['record_key'] for c in prior['cells'] for r in c['selected']}
    assert len(excluded)==96
    throughput=json.loads((base/basis['throughput_result']).read_text())
    projected=throughput['minimum_matrix_projected_four_worker_wall_seconds']
    assert projected==basis['observed_projected_four_worker_seconds'] and projected<=7200
    return excluded,projected


def freeze(contract, excluded):
    cells=[]; keys=set()
    for source in contract['immutable_exact_sources']:
        L,q=source['L'],source['q']; path,_,records=load_cell(L,q)
        assert path.resolve()==(MANIFEST.parent/source['path']).resolve()
        def key(item):
            r=item['record']; return r.get('record_key',f"{path.stem}:index{r['sample_index']}")
        available=[r for r in records if key(r) not in excluded]
        ordered=sorted(available,key=lambda r:(absolute_gap(r['record']),int(r['record']['sample_index'])))
        selected=[]
        for stratum,indices in enumerate(np.array_split(np.arange(len(ordered)),8)):
            assert len(indices)>0
            item=min((ordered[int(i)] for i in indices),key=lambda r:(sha_bytes(('row-boundary-fresh-v1|'+key(r)).encode()),key(r)))
            r=item['record']; k=key(item); Q=np.asarray(item['Q'],dtype=np.int16)
            assert k not in keys and k not in excluded; keys.add(k)
            charge_hash=sha_bytes(Q.tobytes())
            if 'charge_sha256' in r: assert charge_hash==r['charge_sha256'],k
            sectors=np.asarray(r['sector_probabilities'],dtype=float)
            assert np.isfinite(sectors).all() and min(sectors)>=0 and abs(sum(sectors)-1)<1e-10
            gap=absolute_gap(r); risk=float(min(sectors)); e=math.exp(-gap)
            assert abs(risk-e/(1+e))<=1e-10
            selected.append({'record_key':k,'sample_index':int(r['sample_index']),'stratum':stratum,
                             'charge':Q.astype(int).tolist(),'charge_sha256':charge_hash,
                             'exact_sectors':sectors.tolist(),'exact_gap':gap if math.isfinite(gap) else None,
                             'exact_risk':risk})
        cells.append({'L':L,'q':q,'source':str(path.relative_to(ROOT)),
                      'source_sha256':sha_file(path),'available_after_exclusion':len(available),'selected':selected})
    assert len(keys)==48
    cohort={'status':'frozen','contract':str(MANIFEST.relative_to(ROOT)),
            'selection':contract['fresh_cohort']['selection_rule'],'records':48,
            'excluded_prior_records':96,'reuse_of_prior_selected_records':0,
            'new_physical_records':0,'infinite_gap_encoding':'null','cells':cells}
    if COHORT.exists(): assert json.loads(COHORT.read_text())==cohort,'frozen cohort changed'
    else: dump(COHORT,cohort)
    return cohort


def evaluate(task):
    # No true current, true sector, exact posterior or sampling uniforms enter
    # this evaluator. Charge and all other arguments are decoder-public.
    L,q,direction,Qvalues,chis=task
    model=square_graph(L); order=list(model.detector_vertices)
    if direction=='right-to-left': order.reverse()
    engine=BoundaryMPSPosterior(model,order=order)
    Q=np.asarray(Qvalues,dtype=np.int16); out=[]
    for chi in chis:
        start=time.monotonic()
        r=engine.infer(Q,.30,q,chi=chi,truncation_schedule='row')
        z=np.asarray(r.sectors); g=abs(r.signed_gap); e=math.exp(-g)
        valid=bool(np.isfinite(z).all() and min(z)>=0 and abs(sum(z)-1)<=1e-10
                   and not math.isnan(g) and abs(r.bayes_risk-min(z))<=1e-10
                   and abs(r.bayes_risk-e/(1+e))<=1e-10)
        if not valid: raise RuntimeError('candidate identity/nonfinite failure')
        out.append({'chi':chi,'candidate_sectors':z.tolist(),
                    'candidate_gap':g if math.isfinite(g) else None,
                    'candidate_risk':r.bayes_risk,'identity_passed':valid,
                    'seconds':time.monotonic()-start,'worker_peak_gib':peak_gib()})
    return out


def gap(x): return math.inf if x is None else float(x)


def analyze(rows):
    metrics=[]
    for L in (9,11):
      for q in (.90,.94,.97):
       for direction in ('left-to-right','right-to-left'):
        for chi in (16,32):
            block=[r for r in rows if (r['L'],r['q'],r['direction'],r['chi'])==(L,q,direction,chi)]
            assert len(block)==8
            eg=np.array([gap(r['exact_gap']) for r in block]); cg=np.array([gap(r['candidate_gap']) for r in block])
            er=np.array([r['exact_risk'] for r in block]); cr=np.array([r['candidate_risk'] for r in block])
            ge=np.array([0. if a==b else abs(a-b) for a,b in zip(eg,cg)])
            finite=bool(np.isfinite(ge).all())
            med=float(np.median(ge)) if finite else None
            pg=float(np.quantile(ge,.95)) if finite else None
            pr=float(np.quantile(abs(er-cr),.95))
            cdf={str(a):abs(float(np.mean(eg<=a)-np.mean(cg<=a))) for a in (.5,1.,2.,4.)}
            share={str(a):abs(risk_share(eg,er,a)-risk_share(cg,cr,a)) for a in (.5,1.,2.,4.)}
            gates={'gap_finite_or_matched_infinite':finite,'median_gap':finite and med<=.02,
                   'p95_gap':finite and pg<=.05,'p95_risk':pr<=.005,
                   'cutoffs':max(cdf.values())<=.02,'risk_share':max(share.values())<=.02,
                   'identities':all(r['identity_passed'] for r in block)}
            metrics.append({'L':L,'q':q,'direction':direction,'chi':chi,'records':8,
                            'median_gap_error':med,'p95_gap_error':pg,'p95_risk_error':pr,
                            'cdf_errors':cdf,'risk_share_errors':share,'gates':gates,
                            'all_gates_pass':all(gates.values())})
    return metrics


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-only',action='store_true');args=parser.parse_args()
    started=time.monotonic(); contract=json.loads(MANIFEST.read_text())
    excluded,projected=prereqs(contract); cohort=freeze(contract,excluded)
    print('FROZEN: 48 unused records; prior 96 excluded; all source and charge hashes passed.',flush=True)
    if args.freeze_only:return
    if RESULT.exists(): raise RuntimeError('single-use result already exists; inspect without rerunning')
    tasks=[]
    for c in cohort['cells']:
        for r in c['selected']:
            for direction in ('left-to-right','right-to-left'):
                tasks.append((c['L'],c['q'],direction,r))
    rows=[]; result={'status':'running','contract':str(MANIFEST.relative_to(ROOT)),
        'cohort_sha256':sha_file(COHORT),'runner_sha256':sha_file(Path(__file__)),
        'implementation_sha256':contract['research_basis']['implementation_sha256'],
        'new_physical_records':0,'bootstrap_replicates':0,'l13_histories':0,
        'source_replay_anti_leak_passed':True,'projected_four_worker_seconds':projected,
        'rows':rows,'rows_completed':0,'rows_budget':192}
    dump(RESULT,result); pool=ProcessPoolExecutor(max_workers=4); pending={}
    def checkpoint():
        result['rows_completed']=len(rows);result['runtime_seconds']=time.monotonic()-started
        result['conservative_peak_gib']=peak_gib()+4*max((r['worker_peak_gib'] for r in rows),default=0)
        dump(RESULT,result)
    try:
        for L,q,direction,r in tasks:
            f=pool.submit(evaluate,(L,q,direction,r['charge'],(16,32)))
            pending[f]=(L,q,direction,r)
        while pending:
            remaining=1200-(time.monotonic()-started)
            if remaining<=0: raise TimeoutError('1200-second cap')
            done,_=wait(pending,timeout=min(10,remaining),return_when=FIRST_COMPLETED)
            for f in done:
                L,q,direction,r=pending.pop(f)
                for candidate in f.result():
                    rows.append({**candidate,'L':L,'q':q,'direction':direction,
                        **{k:r[k] for k in ('record_key','stratum','charge_sha256','exact_sectors','exact_gap','exact_risk')}})
            checkpoint()
            if result['conservative_peak_gib']>8: raise MemoryError('8-GiB conservative cap')
            if done and len(rows)%32==0:print(f'EVALUATIONS {len(rows)}/192',flush=True)
        pool.shutdown(wait=True)
        assert len(rows)==192 and len({(r['record_key'],r['direction'],r['chi']) for r in rows})==192
        prereqs(contract)
        metrics=analyze(rows);result['metrics']=metrics
        result['status']='passed' if all(m['all_gates_pass'] for m in metrics) else 'rejected_accuracy'
        result['decision']='promote_registered_row_approximation_only' if result['status']=='passed' else 'close_candidate_without_tuning'
        checkpoint()
    except Exception as error:
        result['status']='censored';result['error']=repr(error);checkpoint()
        for proc in getattr(pool,'_processes',{}).values():proc.terminate()
        pool.shutdown(wait=True,cancel_futures=True)
        raise
    print(json.dumps({k:result[k] for k in ('status','decision','rows_completed','runtime_seconds','conservative_peak_gib')},indent=2),flush=True)


if __name__=='__main__':main()
