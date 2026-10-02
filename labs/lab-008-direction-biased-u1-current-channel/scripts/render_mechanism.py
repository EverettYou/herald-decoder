"""Publication-style finite-study figures from analyzed machine-readable data."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from current_oracle import LAB

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.grid':True,'grid.alpha':.18,'figure.facecolor':'white',
                     'savefig.facecolor':'white','font.family':'DejaVu Sans'})
COLORS=['#197e82','#d28c26','#b74664']
LABELS=['Bayes sector','Exact marginals + MWPM','Parent BP + MWPM']


def errors(rows,k):
    mean=np.array([r['risk']['mean'][k] for r in rows])
    ci=np.array([r['risk']['interval'][k] for r in rows])
    return mean,np.maximum(0,np.array([mean-ci[:,0],ci[:,1]-mean]))


def main():
    figdir=LAB/'figures';figdir.mkdir(exist_ok=True)
    data=json.loads((LAB/'results/square-mechanism-2026-09-18-analysis.json').read_text())
    fig,axes=plt.subplots(2,3,figsize=(12.8,7.2),sharex=True,sharey=True)
    for i,L in enumerate((5,7)):
        for j,q in enumerate((.5,.75,1.)):
            ax=axes[i,j];rows=sorted([r for r in data['rows'] if r['L']==L and r['q']==q],key=lambda r:r['p'])
            for k,(color,label) in enumerate(zip(COLORS,LABELS)):
                y,e=errors(rows,k);ax.errorbar([r['p'] for r in rows],y,yerr=e,color=color,
                    marker=['o','s','^'][k],markersize=4,capsize=3,lw=1.4,label=label)
            ax.set_title(f'L={L} · '+('fair q=0.5' if q==.5 else 'directed q=1' if q==1 else 'q=0.75'))
            ax.set_xticks([.1,.3,.46]);ax.set_ylim(-.015,.53)
            if i==1:ax.set_xlabel('Physical jump probability p')
            if j==0:ax.set_ylabel('Expected logical failure probability')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.925),ncol=3,frameon=False)
    fig.suptitle('Square U(1): intrinsic risk and decoder loss',fontsize=17,y=.98)
    fig.text(.5,.01,'Physical-record averages of exact conditional risks · pointwise bootstrap 95% · n=512 at p=0.30, otherwise 192 per cell\nLines connect three sampled p values; no threshold fit. Open rough boundaries and binary logical score match Lab 006.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.065,1,.88))
    fig.savefig(figdir/'square-sector-decoder-risk.png',dpi=180);plt.close(fig)
    honey=LAB/'results/honeycomb-arrow-control-2026-09-18-analysis.json'
    if honey.exists():
        data=json.loads(honey.read_text());fig,axes=plt.subplots(1,2,figsize=(11,4.7),sharey=True)
        for ax,L in zip(axes,(3,5)):
            for pattern,color in [('stored','#197e82'),('bipartite','#b74664')]:
                rows=sorted([r for r in data['rows'] if r['L']==L and r['arrows']==pattern],key=lambda r:r['q'])
                for k,style in [(0,'-'),(2,'--')]:
                    y,e=errors(rows,k);ax.errorbar([r['q'] for r in rows],y,yerr=e,color=color,
                        ls=style,marker='o' if k==0 else '^',ms=4,capsize=3,label=f'{pattern} · '+('Bayes' if k==0 else 'BP + MWPM'))
            ax.set_title(f'Honeycomb L={L}, p=0.30');ax.set_xlabel('Forward direction probability q')
            ax.set_xticks([.5,.75,1]);ax.set_ylim(-.012,.5)
        axes[0].set_ylabel('Expected logical failure probability')
        handles,labels=axes[0].get_legend_handles_labels()
        fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.91),ncol=2,frameon=False,fontsize=9)
        fig.suptitle('Preferred arrow pattern changes the biased channel',fontsize=16)
        fig.text(.5,.015,'Same graph, observation and score; bulk AND boundary arrows change · n=256 per cell · pointwise bootstrap 95%\nFair noise is invariant in law. These are finite-sample mechanism controls, not a flux-only causal isolation.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.09,1,.78));fig.savefig(figdir/'honeycomb-arrow-control-risk.png',dpi=180);plt.close(fig)
    print('Rendered',str(figdir))


if __name__=='__main__':main()
