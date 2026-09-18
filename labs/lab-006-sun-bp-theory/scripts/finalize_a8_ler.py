#!/usr/bin/env python3
"""Audit completed registered counts and render the canonical LER overview and companion diagnostics."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import numba, scipy, pymatching
from run_a7_ler import SCORING_RULE, wilson

LAB=Path(__file__).resolve().parents[1]
ROOT=LAB.parents[1]

def main():
    audits=[]; sample_total=0
    for lattice in ('square','honeycomb'):
        for group in ('U1','SU2','SU3'):
            path=LAB/'results'/f'a8-fullrecord-{lattice}-{group}-final-v2.json'
            payload=json.loads(path.read_text()); scope=payload['scope']
            assert payload['status']=='complete'
            assert scope['scoring_rule']==SCORING_RULE and scope['measure_boundary_representation'] is False
            assert scope['orientation']=='directed' and scope['damping']==.5 and scope['max_iterations']==300 and scope['tolerance']==1e-10
            rows=payload['rows']; sampled=[r for r in rows if not r.get('exact_endpoint')]
            assert len(rows)==104 and len(sampled)==100
            endpoints=[r for r in rows if r.get('exact_endpoint')]
            assert {r['L'] for r in endpoints}=={5,7,9,11}
            assert all(r['p']==0 and r['ler']==0 and r['logical_failures']==0 and r['wilson95']==[0,0] for r in endpoints)
            assert {(r['L'],r['p']) for r in sampled}=={(L,round(.02*i,2)) for L in (5,7,9,11) for i in range(1,26)}
            for r in sampled:
                assert r['shots']==20000 and r['arm']=='representation_herald'
                assert r['lattice']==lattice and r['group']==group
                assert 0<=r['bp_nonconverged']<=r['shots'] and r['invalid_correction']==0
                assert r['logical_failures']==r['logical_parity_failures']
                assert r['ler']==r['logical_failures']/r['shots']
                assert np.allclose(r['wilson95'],wilson(r['logical_failures'],r['shots']),atol=1e-15,rtol=0)
                if 'seed' in r:
                    assert r['seed']==950000+100*r['L']+round(r['p']/.02)-1 and r['batch_size']==256
            for source,digest in payload['provenance']['current_source_sha256'].items():
                assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==digest,source
            original=json.loads((LAB/payload['provenance']['inherited_checkpoint']).read_text())
            indexed={(r['L'],r['p']):r for r in rows}
            assert all(all(indexed[r['L'],r['p']][k]==v for k,v in r.items()) for r in original['rows'])
            sample_total+=sum(r['shots'] for r in sampled)
            label={'U1':'U(1)','SU2':'SU(2)','SU3':'SU(3)'}[group]
            figure_checks=[]
            for diagnostic in (True,):
                fig,ax=plt.subplots(figsize=(9,6));colors=['#1665a8','#d36a16','#16836e','#854db3']
                for L,color in zip((5,7,9,11),colors):
                    curve=sorted([r for r in sampled if r['L']==L],key=lambda r:r['p'])
                    x=[r['p'] for r in curve]
                    if diagnostic:
                        ax.plot(x,[r['bp_nonconverged']/r['shots'] for r in curve],'o-',markersize=3,color=color,label=f'L={L}')
                    else:
                        ax.errorbar(x,[r['ler'] for r in curve],yerr=[[max(0,r['ler']-r['wilson95'][0]) for r in curve],[max(0,r['wilson95'][1]-r['ler']) for r in curve]],fmt='o-',markersize=3,capsize=2,color=color,label=f'L={L}')
                upper=max(r['bp_nonconverged']/r['shots'] if diagnostic else r['wilson95'][1] for r in sampled)
                ax.plot([0],[0],'k*',markersize=8,label='p=0 exact')
                ax.set(xlim=(0,.5),ylim=(0,min(1,max(.001,1.12*upper))),xlabel='Physical edge-error probability p',ylabel='BP nonconvergence fraction' if diagnostic else 'Logical error rate')
                ax.set_title(f'{lattice.capitalize()} · {label} · complete: 100/100 sampled cells\nFull interior (m,R), directed channel; rough-boundary m,R unmeasured')
                ax.grid(alpha=.2);ax.legend(loc='best')
                fig.text(.5,.015,'20,000 independent shots per sampled cell; LER: Wilson 95% intervals.\nBP nonconvergence is diagnostic only; lines guide the eye. No threshold fit.',ha='center',fontsize=9)
                fig.tight_layout(rect=(0,.065,1,1))
                suffix='nonconvergence' if diagnostic else 'ler';figure=LAB/'figures'/f'a8-{lattice}-{group}-{suffix}.png'
                temp=figure.with_suffix('.tmp.png');fig.savefig(temp,dpi=180);plt.close(fig);temp.replace(figure)
                figure_checks.append({'path':str(figure.relative_to(LAB)),'sha256':hashlib.sha256(figure.read_bytes()).hexdigest(),'y_max':min(1,max(.001,1.12*upper))})
            audits.append({'lattice':lattice,'group':group,'sampled_cells':100,'shots':2000000,'input':str(path.relative_to(LAB)),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'inherited_cells':payload['provenance']['inherited_cells'],'source_stability':'passed','wilson_intervals':'passed','seed_schedule':'passed','inherited_counts_preserved':'passed','invalid_corrections':0,'figures':figure_checks})
    assert sample_total==12000000
    result={'status':'passed','updated':datetime.now(timezone.utc).isoformat(),'sampled_cells':600,'shots':sample_total,'scope':'U1, SU2, SU3; square and honeycomb; rough-boundary charge unmeasured; None deferred','panels':audits,'claim_boundary':'Finite-size curves only; no threshold estimate. Forty inherited corrected cells lack historical source hashes.','runtime':{'Python':sys.version.split()[0],'NumPy':np.__version__,'Numba':numba.__version__,'SciPy':scipy.__version__,'PyMatching':pymatching.__version__},'exact_endpoints_excluded_from_shot_total':True,'rendered_delivery':'pending separate browser audit'}
    (LAB/'results/a8-completion-audit-2026-09-07.json').write_text(json.dumps(result,indent=2)+'\n')
    from render_a8_ler_overview import main as render_overview
    render_overview()
    print(json.dumps({'status':'passed','sampled_cells':600,'shots':sample_total}))

if __name__=='__main__':main()
