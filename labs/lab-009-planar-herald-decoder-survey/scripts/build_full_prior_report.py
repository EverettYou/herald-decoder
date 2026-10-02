"""Deliver the bounded full-prior correction; survey completion is a separate gate."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
LAB=Path(__file__).resolve().parents[1]

def main():
    if (LAB/'results/survey-summary.json').exists():
        raise RuntimeError('The bounded checkpoint is superseded by the survey; use build_survey_figures.py. Do not overwrite the final REPORT.md.')
    bench=json.loads((LAB/'results/benchmark.json').read_text());validation=json.loads((LAB/'results/validation.json').read_text());audit=json.loads((LAB/'results/full-prior-symmetry-audit.json').read_text())
    assert bench['status']=='complete' and validation['status']=='passed' and audit['status']=='passed'
    high=[r for r in bench['rows']if r['p']>.5]
    assert len(high)==40 and all(r['invalid']==0 for r in high) and not bench['exceptions']
    assert sum(r['shots']for r in high if r['method']=='planar_ml')==1600
    fig,axs=plt.subplots(1,3,figsize=(13,4.2),layout='constrained',sharey=True)
    styles={'bp_matching':('#666','o'),'configuration_map':('#c66a20','s'),'planar_ml':('#245ab5','D')}
    for ax,q in zip(axs,[.5,.8,1]):
        for method,(color,marker) in styles.items():
            for L in [5,9]:
                rows=sorted([r for r in bench['rows']if r['q']==q and r['L']==L and r['method']==method],key=lambda r:r['p'])
                p=np.array([r['p']for r in rows]);ler=np.array([r['ler']for r in rows]);lo=np.array([r['ci95'][0]for r in rows]);hi=np.array([r['ci95'][1]for r in rows])
                ax.errorbar(p,ler,yerr=[np.maximum(ler-lo,0),np.maximum(hi-ler,0)],ls='none',marker=marker,color=color,mfc=color if L==9 else 'white',markersize=5,alpha=.8,capsize=2,label=f'{method.replace("_matching", "").replace("configuration_map","MAP").replace("planar_ml","ML")}, L={L}')
        ax.set(xlim=(0,1),ylim=(0,.66),xlabel='Physical error probability p',title=f'q={q:g}');ax.axvline(.5,color='#aaa',ls=':',lw=.8);ax.grid(alpha=.15)
    axs[0].set_ylabel('Logical failure fraction');axs[-1].legend(fontsize=8,ncol=2,loc='upper right')
    fig.suptitle('Independent full-prior diagnostics: 200 common trials per sampled cell',fontsize=13)
    for ext in ['png','svg','pdf']:fig.savefig(LAB/'figures'/f'full-prior-matched-diagnostics.{ext}',dpi=180)
    posterior=max(max(r['max_posterior_error'].values())for r in validation['small_oracle'])
    lines=['# Lab 009 — Planar herald decoder survey and integration','','## Full-prior correction — completed bounded verification','','The binary-herald research domain is **p,q in [0,1]**. Interior-q complement symmetry is false. The uniform prior at p=0.5 remains special, but does not justify a half-domain scan or a forced horizontal boundary tangent. See [model correction](/wiki?page=methods/binary-herald-full-prior-domain.md). No single-valued threshold curve or monotonicity in p is assumed.','','Independent complete L=2 joint-record enumeration gives optimal risks 0.231775342400 at (p,q)=(0.2,0.5), versus 0.304423178240 at (0.8,0.5). Endpoint q=0/1 complement symmetries and zero risks at deterministic p=0/1 pass. The audit enumerates 2048 errors and all 64 herald records per error, independently of candidate decoders.','','## Implementation and checks','',f'Configuration MAP, planar ML, exact transfer and MPS now accept p in [0,1]. High-p MAP uses literal signed log-posterior weights; the low-p integer objective is not reused above half. Impossible deterministic-prior records are rejected. Independent L=2 weighted checks (13 parameter pairs) include actual maximizing MAP configurations; 27 L=3/4/5 cross-check cells cover both sides of half. Maximum checked small-system exact posterior error is {posterior:.3g}; this is a checked-record result, not an all-size stability theorem. BP retains its established interior-p API.','','## Fresh measured evidence','','![Full-prior common-record diagnostic](figures/full-prior-matched-diagnostics.png)','','Each point uses 200 independent trials shared by all five methods. Error bars are 95% Wilson intervals; filled markers denote L=9, open markers L=5. Points are discrete measurements, not interpolated phase boundaries. Low-p pilot cohorts are retained; high-p cells are newly sampled, not reflected. Transfer and MPS are also recorded in the downloadable data.','','| L | p | q | BP failures | MAP failures | Exact sector ML failures | Trials |','| --- | --- | --- | --- | --- | --- | --- |']
    for L,p,q in sorted({(r['L'],r['p'],r['q'])for r in high}):
        selected={r['method']:r for r in high if (r['L'],r['p'],r['q'])==(L,p,q)}
        lines.append(f'| {L} | {p:g} | {q:g} | {selected["bp_matching"]["failures"]} | {selected["configuration_map"]["failures"]} | {selected["planar_ml"]["failures"]} | 200 |')
    lines+=['','All 1600 new high-p trials were scored by five methods: 8000 decoder evaluations, zero invalid corrections and zero runtime exceptions. Nonconverged BP trials remain in denominators. At p=0.95,q=0.8 all methods had zero failures in both sizes; zero of 200 has a Wilson upper limit about 0.0188, so this does not establish zero thermodynamic risk. At p=0.8,q=0.5 ML failures are 58/200 and 56/200; two sizes and this uncertainty do not establish a transition.','','## Remaining survey and phase-diagram work','','The bounded full-prior correction and diagnostics are complete. The broader registered decoder survey, theory pages, inherited-data comparisons and remaining delivery gates stay active in PLAN.md. A converged two-dimensional thermodynamic phase diagram has not been produced by this diagnostic. Independent high-p sampling and justified finite-size analysis are required before claiming its topology or thresholds. Historical restricted-domain SciCode2 runs retain their original evaluation scope.']
    (LAB/'REPORT.md').write_text('\n'.join(lines)+'\n')
    result={'status':'passed_bounded_full_prior_update','domain':{'p':[0,1],'q':[0,1]},'high_p_cells':8,'new_independent_trials':1600,'decoder_evaluations':8000,'invalid_corrections':0,'runtime_exceptions':0,'max_checked_small_posterior_error':posterior,'thermodynamic_diagram_complete':False,'source_sha256':{name:hashlib.sha256((LAB/'results'/name).read_bytes()).hexdigest()for name in ['benchmark.json','validation.json','full-prior-symmetry-audit.json']}}
    (LAB/'results/full-prior-update.json').write_text(json.dumps(result,indent=2)+'\n')
    p=LAB/'lab.json';meta=json.loads(p.read_text());ids={r['id']for r in meta['results']}
    for id,kind,format,title,path in [('full-prior-diagnostics','figure','image','Independent full-prior matched diagnostics','figures/full-prior-matched-diagnostics.png'),('full-prior-update','data','json','Bounded full-prior update and provenance','results/full-prior-update.json'),('full-prior-symmetry-audit','data','json','Complete L=2 complement-symmetry audit','results/full-prior-symmetry-audit.json'),('full-prior-validation','data','json','Decoder verification across the full prior domain','results/validation.json'),('full-prior-matched-data','data','json','Matched pilot including independent high-p cells','results/benchmark.json')]:
        if id not in ids:meta['results'].append({'id':id,'kind':kind,'format':format,'title':title,'path':path,'presentation':'page'if kind=='figure'else'result','summary':'Bounded full-domain check; no thermodynamic threshold claim.'})
    meta['current_focus']='Full-prior correction and independent high-p diagnostic passed; remaining survey integration active.'
    p.write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__':main()
