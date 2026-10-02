"""Reproduce figures from frozen numeric cohorts; never fit a new threshold."""
import csv
import hashlib
import json
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'svg.fonttype': 'none', 'pdf.fonttype': 42})
FIGURES = []
COLORS = ['#406b91', '#a46c33', '#295e43', '#9272ab', '#be5054', '#679baf', '#565656']
LABELS = {'bp_matching':'BP + matching', 'configuration_map':'Configuration MAP',
          'planar_ml':'Planar ML', 'transfer_ml':'Exact transfer', 'mps_ml':'MPS χ=16'}
METHOD_COLORS = dict(zip(LABELS, COLORS))


def save(fig, name, sources, semantics):
    paths = []
    for ext in ('png', 'svg', 'pdf'):
        path = LAB/'figures'/f'{name}.{ext}'
        fig.savefig(path, dpi=180)
        paths.append(str(path.relative_to(LAB)))
    plt.close(fig)
    FIGURES.append({'id':name, 'files':paths, 'inputs':sources, 'semantics':semantics})


def load_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    LAB.joinpath('figures').mkdir(exist_ok=True)
    parent = ROOT/'labs/lab-003-herald-threshold-phase-diagram/results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json'
    target = LAB/'data/inherited/repository-measured-trends.json'
    shutil.copyfile(parent, target)
    provenance_path = LAB/'results/data-provenance.json'
    provenance = json.loads(provenance_path.read_text())
    provenance['records'] = [r for r in provenance['records'] if r['snapshot'] != str(target.relative_to(LAB))]
    provenance['records'].append({'source':str(parent),'snapshot':str(target.relative_to(LAB)),
                                  'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                                  'cohort':'inherited Lab 003 measured trends; no B18 symmetry guide'})
    provenance_path.write_text(json.dumps(provenance, indent=2)+'\n')
    curves = json.loads((LAB/'data/inherited/audit_reported_boundaries.json').read_text())
    cells = json.loads(target.read_text())['cells']
    assert len(cells) == 231
    fig, axes = plt.subplots(1,3,figsize=(15,5.1),layout='constrained')
    vals = [c['posterior_log_odds_upward_vs_downward'] if c['posterior_log_odds_upward_vs_downward'] is not None else c['posterior_log_odds_censoring']['bound'] for c in cells]
    sc = axes[0].scatter([c['p']for c in cells],[c['q']for c in cells],c=np.clip(vals,-6,6),
                         s=48,marker='s',cmap='RdBu_r',vmin=-6,vmax=6)
    axes[0].axvspan(.5,1,color='#edf0f2',zorder=-1)
    axes[0].text(.75,.42,'No inherited\nmeasurements here',ha='center',color='#5c6870',fontsize=9)
    fig.colorbar(sc,ax=axes[0],shrink=.66,label='Log odds: increasing / decreasing LER')
    axes[0].set_title('Repository BP: measured trends\nFinite sizes, mainly L=7,9,11')
    counters = {'MAP':0,'ML':0}
    mapping = []
    for c in curves:
        ax = axes[1] if c['family']=='MAP' else axes[2]
        if c['family']=='MAP':
            counters['MAP']+=1; label=f'MAP study {counters["MAP"]}'
        elif c['family']=='ML':
            counters['ML']+=1; label=f'Planar ML study {counters["ML"]}'
        else:
            label='Finite-penalty Kac–Ward' if '1 ML' in c['name'] else 'MPS, finite χ'
        mapping.append({'label':label,'inherited_study':c['name'],'family':c['family']})
        points = np.array(sorted(set(tuple(z)for z in c['points']if 0<=z[0]<=.5 and 0<=z[1]<=1),key=lambda z:z[1]))
        ax.plot(points[:,0],points[:,1],'.--' if 'approximate' in c['family'] else '.-',
                lw=1.3,ms=4,label=label)
    axes[1].set_title('Reported configuration-MAP estimates\nDistinct sizes and tie rules')
    axes[2].set_title('Reported sector-inference estimates\nExact planar or approximate contraction')
    for i, ax in enumerate(axes):
        ax.set(xlim=(0,1 if i==0 else .5),ylim=(0,1),xlabel='Physical error probability p',ylabel='Herald availability q')
        ax.grid(alpha=.15)
    for ax in axes[1:]: ax.legend(fontsize=8,loc='upper left')
    (LAB/'results/boundary-study-labels.json').write_text(json.dumps(mapping,indent=2)+'\n')
    save(fig,'survey-boundaries',['data/reported-boundaries.csv','data/inherited/repository-measured-trends.json'],
         'Measured finite-window trends versus separate reported restricted-domain estimates; no mirrored high-p values, no new fits or pooled CI.')

    rows = load_csv(LAB/'data/inherited-ml-cells.csv')
    numeric = [{k:float(v)for k,v in r.items()}for r in rows]
    fig, axes = plt.subplots(1,4,figsize=(15,4.3),layout='constrained')
    for ax,q,window in zip(axes[:3],[0,.5,.8],[(.15,.178),(.215,.25),(.34,.40)]):
        for j,L in enumerate([8,16,32,48,64]):
            rr=sorted([r for r in numeric if r['L']==L and r['q']==q and window[0]<=r['p']<=window[1]],key=lambda r:r['p'])
            if not rr:continue
            x=np.array([r['p']for r in rr]);y=np.array([r['ler_rb']for r in rr]);se=np.array([r['se_rb']for r in rr])
            ax.errorbar(x,y,yerr=1.96*se,marker='o',lw=1,ms=3,capsize=2,color=COLORS[j],label=f'L={L}')
        ax.set(xlabel='Physical error probability p',ylabel='Mean conditional ML risk',title=f'Inherited planar ML: q={q:g}',xlim=window,ylim=(0,.42));ax.grid(alpha=.15)
    axes[0].legend(fontsize=8)
    ax=axes[3]
    rr=sorted([r for r in numeric if r['p']==.5 and r['q']==1],key=lambda r:r['L'])
    for r in rr:
        L,n,k=r['L'],int(r['n']),int(r['fails'])
        if k:
            ax.plot(L,k/n,'o',color=COLORS[2])
        else:
            upper=1-.05**(1/n)
            ax.plot(L,upper,'v',mfc='white',color=COLORS[2]);ax.annotate(f'0/{n}\n95% upper limit',(L,upper),xytext=(-10,12),textcoords='offset points',fontsize=8,ha='right')
    ax.set(xscale='log',yscale='log',xlabel='Linear size L',ylabel='Direct failure proportion / upper limit',title='Perfect heralding: p=0.5, q=1')
    ax.set_xticks([8,16,32]);ax.set_xticklabels(['8','16','32']);ax.xaxis.set_minor_locator(NullLocator());ax.grid(alpha=.15)
    save(fig,'inherited-ml-curves',['data/inherited-ml-cells.csv'],
         'First three panels: unconditional Rao–Blackwell mean ±1.96 sample SE, not binomial counts. Fourth: direct failure counts; zero counts are 95% one-sided exact upper limits, never plotted as zero risk.')

    thresholds = json.loads((LAB/'data/inherited/anthropic__claude-opus-5-5_run_03_thresholds.json').read_text())
    crossing_rows = []
    for t in thresholds:
        for c in t['crossings']:
            crossing_rows.append({'fixed_axis':t['kind'],'fixed_value':t['value'],**c})
    with (LAB/'data/inherited-crossings.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(crossing_rows[0]));w.writeheader();w.writerows(crossing_rows)
    fig, axes = plt.subplots(1,3,figsize=(12.5,3.8),layout='constrained')
    for ax,kind,value in zip(axes,['q','q','p'],[0,.5,.5]):
        t=next(t for t in thresholds if t['kind']==kind and t['value']==value)
        rr=sorted([c for c in t['crossings']if c['L2']==2*c['L1']],key=lambda r:r['L1'])
        ax.errorbar([r['L1']for r in rr],[r['x']for r in rr],yerr=[r['err']for r in rr],fmt='o-',capsize=3,color=COLORS[0],label='Crossing: L and 2L')
        est=t['estimate'];ax.axhspan(est['lo'],est['hi'],color=COLORS[1],alpha=.13,label='Reported working range')
        ax.axhline(est['xc'],color=COLORS[1],ls='--',lw=1)
        ax.set(xscale='log',xlabel='Smaller linear size L',ylabel='Crossing p' if kind=='q' else 'Crossing q',title=f'Fixed {kind}={value:g}')
        ax.set_xticks([8,12,16,24,32]);ax.set_xticklabels(['8','12','16','24','32']);ax.xaxis.set_minor_locator(NullLocator());ax.grid(alpha=.15)
    axes[0].legend(fontsize=8)
    save(fig,'inherited-crossing-drift',['data/inherited-crossings.csv','data/inherited/anthropic__claude-opus-5-5_run_03_thresholds.json'],
         'Inherited crossing errors use the source convention; shaded working ranges combine fit/size sensitivity and are not rigorous confidence bands.')

    b=json.loads((LAB/'results/benchmark.json').read_text());assert b['status']=='complete' and len(b['rows'])==80
    cells_low=[(.16,0),(.24,.5),(.4,.8),(.49,1)]
    cells_high=[(.6,.5),(.8,.5),(.95,.8),(.8,1)]
    fig, axes=plt.subplots(2,2,figsize=(13,8),layout='constrained',sharey=True)
    selected=['bp_matching','configuration_map','planar_ml','mps_ml']
    for i,L in enumerate([5,9]):
        for j,cells0 in enumerate([cells_low,cells_high]):
            ax=axes[i,j]
            for m,method in enumerate(selected):
                rr=[next(r for r in b['rows']if(r['L'],r['p'],r['q'],r['method'])==(L,p,q,method))for p,q in cells0]
                y=np.array([r['ler']for r in rr]);ci=np.array([r['ci95']for r in rr]);offset=(m-1.5)*.12
                ax.errorbar(np.arange(4)+offset,y,yerr=[np.maximum(y-ci[:,0],0),np.maximum(ci[:,1]-y,0)],fmt='o',capsize=3,ms=5,color=METHOD_COLORS[method],label='Planar / transfer ML'if method=='planar_ml'else LABELS[method])
            ax.set_xticks(range(4));ax.set_xticklabels([f'p={p:g}\nq={q:g}'for p,q in cells0]);ax.set(title=f'L={L}: '+('original range' if j==0 else 'independent high-p cells'),ylabel='Logical failure proportion',ylim=(-.015,.65));ax.grid(axis='y',alpha=.15)
    axes[0,0].legend(fontsize=9,ncol=2)
    save(fig,'fresh-matched-ler',['results/benchmark.json','data/fresh-matched-vectors.npz'],
         'Fresh 200 shared unconditional records per cell, Wilson95 intervals. Planar and transfer failure counts coincide; MPS χ16 approximate. High-p records independently sampled; no reflection or interpolation.')

    fig,axes=plt.subplots(1,2,figsize=(13,4),layout='constrained',sharey=True)
    for ax,L in zip(axes,[5,9]):
        for j,method in enumerate(['bp_matching','configuration_map','mps_ml']):
            rr=[next(r for r in b['rows']if(r['L'],r['p'],r['q'],r['method'])==(L,p,q,method))for p,q in cells_low+cells_high]
            ax.errorbar(np.arange(8)+(j-1)*.15,[r['conditional_regret_mean']for r in rr],yerr=[1.96*r['conditional_regret_se']for r in rr],fmt='o',capsize=2,color=METHOD_COLORS[method],ms=4,label=LABELS[method])
        ax.axhline(0,color='#888',lw=.8);ax.set_xticks(range(8));ax.set_xticklabels([f'{p:g}\n{q:g}'for p,q in cells_low+cells_high],fontsize=9);ax.set(xlabel='Sampled (p, q) cell',ylabel='Mean excess conditional logical risk',title=f'L={L}: posterior-weighted objective gap');ax.grid(axis='y',alpha=.15)
    axes[0].legend(fontsize=8)
    save(fig,'fresh-conditional-regret',['results/benchmark.json','data/fresh-matched-vectors.npz'],
         'Selected sector expected loss minus exact planar conditional Bayes risk, averaged over 200 records. Error bars ±1.96 sample SE. Exact reference zero; MPS posterior agreement is cohort-specific.')

    with np.load(LAB/'data/fresh-matched-vectors.npz',allow_pickle=False)as archive:
        runtime_rows=[]
        for L in [5,9]:
            arrays=[archive[k] for k in archive.files if k.startswith(f'L{L}_')and k.endswith('_timing_seconds')]
            a=np.concatenate(arrays,axis=0)*1000
            for j,method in enumerate(b['methods']):
                runtime_rows.append(dict(L=L,method=method,n=len(a),median_ms=float(np.median(a[:,j])),p95_ms=float(np.quantile(a[:,j],.95))))
    with (LAB/'data/warm-runtime-summary.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(runtime_rows[0]));w.writeheader();w.writerows(runtime_rows)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained',sharey=True)
    for ax,L in zip(axes,[5,9]):
        rr=[r for r in runtime_rows if r['L']==L];x=np.arange(len(rr));med=np.array([r['median_ms']for r in rr]);hi=np.array([r['p95_ms']for r in rr])
        ax.bar(x,med,color=[METHOD_COLORS[r['method']]for r in rr],width=.65,alpha=.85)
        ax.errorbar(x,med,yerr=[np.zeros(len(rr)),np.maximum(hi-med,0)],fmt='none',capsize=4,color='#333')
        for i,(m,h)in enumerate(zip(med,hi)):ax.text(i,h*1.09,f'{m:.2f}',ha='center',fontsize=9)
        ax.set(yscale='log',ylabel='Warmed decode time (ms / shot)',title=f'L={L}: median, upper whisker = p95');ax.set_xticks(x);ax.set_xticklabels(['BP','Config.\nMAP','Planar\nML','Exact\ntransfer','MPS\nχ=16']);ax.grid(axis='y',alpha=.15)
    save(fig,'warm-runtime',['data/warm-runtime-summary.csv','results/benchmark.json'],
         'Pooled equal-size fresh eight-cell mix:1600 timings/method/size, one CPU thread; excludes graph setup and independent first call. Median and p95, no claim of native or asymptotic speed.')

    audit=json.loads((LAB/'data/inherited/audit_matched_comparison.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained',sharey=True)
    for ax,L in zip(axes,[7,11]):
        for j,name in enumerate(['MAP','ML']):
            rr=[next(r for r in audit if(r['L'],r['p'],r['q'])==(L,p,q))for p,q in cells_low]
            val=[r['paired_differences'][name]['candidate_minus_BP']for r in rr];se=[r['paired_differences'][name]['paired_se']for r in rr]
            ax.errorbar(np.arange(4)+(j-.5)*.16,val,yerr=1.96*np.array(se),fmt='o',capsize=3,color=COLORS[j+1],label=f'{name} minus residual-80 BP')
        ax.axhline(0,color='#888',lw=.8);ax.set_xticks(range(4));ax.set_xticklabels([f'p={p:g}\nq={q:g}'for p,q in cells_low]);ax.set(title=f'Inherited audit cohort: L={L}',ylabel='Paired logical failure difference');ax.grid(axis='y',alpha=.15)
    axes[0].legend(fontsize=8)
    save(fig,'inherited-matched-differences',['data/inherited/audit_matched_comparison.json','data/inherited/audit_matched_failure_flags.json'],
         'Separate inherited 500-record cells; residual-priority80 BP and distinct implementations. Error bars ±1.96 paired SE, pointwise only. Not pooled with the fresh synchronous40 cohort.')

    val=json.loads((LAB/'results/validation.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for j,chi in enumerate([4,16]):
        rr=val['mps_sensitivity'];x=[3,4,5];y=[max(r['max_error']for r in rr if r['L']==L and r['chi']==chi)for L in x]
        axes[0].plot(x,np.maximum(y,1e-17),'o-',color=COLORS[j],label=f'MPS χ={chi}')
    axes[0].set(xlabel='Linear size L',ylabel='Maximum checked posterior error',yscale='log',title='MPS versus exact transfer');axes[0].set_xticks([3,4,5]);axes[0].legend(fontsize=9)
    for j,(p,q) in enumerate([(.2,0),(.3,.5),(.4,.9),(.5,1)]):
        rr=sorted([r for r in val['kac_ward_research']if r['p']==p and r['q']==q],key=lambda r:r['penalty'])
        axes[1].plot([r['penalty']for r in rr],np.maximum([r['max_error']for r in rr],1e-17),'o-',color=COLORS[j],label=f'p={p:g}, q={q:g}')
    axes[1].set(xlabel='Finite penalty λ',ylabel='Maximum checked posterior error',yscale='log',title='Kac–Ward softened support: L=3');axes[1].set_xticks([8,12,16]);axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.15)
    save(fig,'approximation-diagnostics',['results/validation.json'],
         'Maximum sampled posterior differences, not rigorous risk bounds. MPS finitechi and KacWard finitepenalty remain approximations. Plot floor1e-17 for zero/roundoff differences; no production threshold inferred.')

    extra=['data/inherited-crossings.csv','data/warm-runtime-summary.csv']
    for name in extra:
        p=LAB/name
        provenance['records']=[r for r in provenance['records']if r['snapshot']!=name]
        provenance['records'].append({'snapshot':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cohort':'derived inherited crossings'if 'crossings'in name else'fresh warmed timing summaries'})
    provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
    inputs=sorted(set(s for r in FIGURES for s in r['inputs']))
    manifest={'status':'generated','figures':FIGURES,'input_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for s in inputs},
              'output_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for r in FIGURES for s in r['files']},'new_threshold_fits':0}
    (LAB/'results/figure-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    from integrate_run_evaluation import integrate
    integrate()
    print('generated',len(FIGURES),'survey figures in PNG/SVG/PDF and integrated the original evaluation PNG/PDF; input and output hashes saved')


if __name__=='__main__':main()
