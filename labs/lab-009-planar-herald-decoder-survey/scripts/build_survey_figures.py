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
    provenance_path = LAB/'results/data-provenance.json'
    provenance = json.loads(provenance_path.read_text())
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

    extra=['data/warm-runtime-summary.csv']
    for name in extra:
        p=LAB/name
        provenance['records']=[r for r in provenance['records']if r['snapshot']!=name]
        provenance['records'].append({'snapshot':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cohort':'fresh warmed timing summaries'})
    provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
    inputs=sorted(set(s for r in FIGURES for s in r['inputs']))
    manifest={'status':'generated','figures':FIGURES,'input_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for s in inputs},
              'output_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for r in FIGURES for s in r['files']},'new_threshold_fits':0}
    (LAB/'results/figure-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('generated',len(FIGURES),'figures in PNG/SVG/PDF; input and output hashes saved')

if __name__=='__main__':main()
