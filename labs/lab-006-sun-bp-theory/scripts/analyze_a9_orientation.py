#!/usr/bin/env python3
"""Audit all paired observations and analyze the preregistered orientation contrast."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
from run_a7_ler import wilson
from render_a9_orientation import paired_interval
from dispatch_a9_orientation import source_hashes
LAB=Path(__file__).resolve().parents[1]

def main():
    cells=[];cohorts={};sources=source_hashes();data_hashes={};shots=0
    for lattice in ('square','honeycomb'):
        for group in ('U1','SU2','SU3'):
            path=LAB/f'results/a9-hidden-{lattice}-{group}.json';raw=path.read_bytes();data=json.loads(raw)
            assert data['status']=='complete' and len(data['rows'])==100
            assert data['source_sha256']==sources
            assert data['scope']['measure_boundary_representation'] is False
            baseline_path=LAB/f'results/a8-fullrecord-{lattice}-{group}-final-v2.json'
            assert hashlib.sha256(baseline_path.read_bytes()).hexdigest()==data['baseline_sha256']
            baseline={(r['L'],r['p']):r for r in json.loads(baseline_path.read_text())['rows']}
            assert {(r['L'],r['p']) for r in data['rows']}=={(L,round(i*.02,2)) for L in (5,7,9,11) for i in range(1,26)}
            data_hashes[str(path.relative_to(LAB))]=hashlib.sha256(raw).hexdigest()
            for r in data['rows']:
                n=r['shots'];assert n==20000 and r['batch_size']==256
                assert r['seed']==950000+100*r['L']+round(r['p']/.02)-1 and r['orientation_seed']==r['seed']+10000000
                assert r['directed_replay_matches_A8']
                indicators=LAB/r['shot_indicators_path'];assert hashlib.sha256(indicators.read_bytes()).hexdigest()==r['shot_indicators_sha256']
                with np.load(indicators) as f:
                    flags=np.unpackbits(f['failures'],axis=1)[:,:n];nonconv=np.unpackbits(f['bp_nonconverged'],axis=1)[:,:n]
                    assert flags.shape==(2,n) and int(f['seed'])==r['seed']
                joint=np.bincount(2*flags[0]+flags[1],minlength=4).reshape(2,2)
                assert joint.tolist()==r['joint_failures_directed_by_hidden'] and int(joint.sum())==n
                for index,name in enumerate(('directed','hidden_orientation')):
                    arm=r['arms'][name];k=int(flags[index].sum())
                    assert arm['logical_failures']==k and arm['ler']==k/n and arm['invalid_correction']==0
                    assert arm['bp_nonconverged']==int(nonconv[index].sum())
                    assert np.allclose(arm['wilson95'],wilson(k,n),rtol=0,atol=1e-15)
                old=baseline[r['L'],r['p']]
                for field in ('logical_failures','invalid_correction','bp_nonconverged'):assert r['arms']['directed'][field]==old[field]
                if group=='SU2':
                    assert np.array_equal(flags[0],flags[1]) and np.array_equal(nonconv[0],nonconv[1])
                    assert r['truth_and_record_sha256']['directed_R']==r['truth_and_record_sha256']['hidden_R']
                key=(lattice,r['L'],r['p']);stream=tuple(r['truth_and_record_sha256'][k] for k in ('activity','m','orientation'))
                if key in cohorts:assert cohorts[key]==stream
                else:cohorts[key]=stream
                a=int(joint[0,1]);b=int(joint[1,0]);delta,interval=paired_interval(r)
                test=1. if a+b==0 else float(binomtest(a,a+b,.5).pvalue)
                cells.append({'lattice':lattice,'group':group,'L':r['L'],'p':r['p'],'shots':n,
                              'directed':r['arms']['directed'],'hidden':r['arms']['hidden_orientation'],
                              'hidden_only_failures':a,'directed_only_failures':b,
                              'delta_hidden_minus_directed':delta,'paired95_conservative':list(interval),
                              'mcnemar_exact_p':test,'holm_adjusted_p':None})
                shots+=n
    tested=sorted([c for c in cells if c['group']!='SU2'],key=lambda c:c['mcnemar_exact_p']);assert len(tested)==400
    previous=0.
    for rank,cell in enumerate(tested):
        previous=max(previous,min(1,(len(tested)-rank)*cell['mcnemar_exact_p']));cell['holm_adjusted_p']=previous
    summaries=[]
    for lattice in ('square','honeycomb'):
        for group in ('U1','SU2','SU3'):
            group_cells=[c for c in cells if c['lattice']==lattice and c['group']==group]
            sig=[c for c in group_cells if c['holm_adjusted_p'] is not None and c['holm_adjusted_p']<.05]
            summaries.append({'lattice':lattice,'group':group,'cells':len(group_cells),'holm_significant_increases':sum(c['delta_hidden_minus_directed']>0 for c in sig),'holm_significant_decreases':sum(c['delta_hidden_minus_directed']<0 for c in sig),'zero_discordance_cells':sum(c['hidden_only_failures']+c['directed_only_failures']==0 for c in group_cells),
                              'max_observed_delta':max(c['delta_hidden_minus_directed'] for c in group_cells),
                              'p030_slice':[c for c in group_cells if c['p']==.3],
                              'finite_size_ordering':[{'p':p,'hidden_LER_L5_L7_L9_L11':[next(c['hidden']['ler'] for c in group_cells if c['p']==p and c['L']==L) for L in (5,7,9,11)]} for p in (round(.02*i,2) for i in range(1,26))]})
    assert shots==12000000
    result={'status':'passed','updated':datetime.now(timezone.utc).isoformat(),'paired_cells':600,'paired_shots':shots,'directed_replay_cells_matching_A8':600,'SU2_identical_shots':4000000,'independent_cross_group_stream_cells':len(cohorts),'inputs':data_hashes,'source_sha256':sources,
            'inference':{'LER_intervals':'pointwise Wilson95','paired_intervals':'two 97.5% Clopper-Pearson discordance intervals, union-bound difference; pointwise conservative95','tests':'exact McNemar, Holm FWER=.05 across 400 U1/SU3 cells','finite_size':'descriptive ordering, not an asymptotic threshold fit'},
            'summaries':summaries,'cells':cells,'claim_boundary':'Physical orientation-law effects on this finite-schedule belief-matching decoder; SU2 exact local-model quotient control. Do not equate crossings with thermodynamic thresholds or absent crossings with absent thresholds. Numerical BP effects remain a competing explanation.'}
    (LAB/'results/a9-orientation-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'passed','paired_cells':600,'paired_shots':shots,'summaries':[{k:v for k,v in s.items() if k not in ('p030_slice','finite_size_ordering')} for s in summaries]}),flush=True)

if __name__=='__main__':main()
