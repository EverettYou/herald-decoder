"""Size and posterior ambiguity plot; finite data only."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from current_oracle import LAB
from render_mechanism import errors

d=json.loads((LAB/'results/size-bias-distributions-2026-09-18.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(13.8,5.2))
colors=['#5265a7','#247f8c','#658d36','#b27824','#b74664']
for q,color in zip((.5,.75,.9,.97,1.),colors):
    rows=sorted([r for r in d['square_grid'] if r['q']==q],key=lambda r:r['L'])
    sizes=[r['L'] for r in rows]
    for k,ax in [(0,axes[0]),(2,axes[1])]:
        y,e=errors(rows,k);ax.errorbar(sizes,y,yerr=e,color=color,marker='o',ms=4,capsize=3,label=f'q={q:g}')
    y=np.array([r['gap_cdf_intervals'][2]['fraction'] for r in rows])
    ci=np.array([r['gap_cdf_intervals'][2]['wilson95'] for r in rows])
    axes[2].errorbar(sizes,y,yerr=np.array([y-ci[:,0],ci[:,1]-y]),color=color,marker='o',ms=4,capsize=3)
for ax in axes:
    ax.set_xlabel('Canonical square size L');ax.set_xticks([5,7,9]);ax.set_xlim(4.65,9.35)
for ax in axes[:2]:
    ax.set_ylim(0,.46);ax.set_ylabel('Expected logical failure probability')
axes[2].set_ylim(0,1);axes[2].set_ylabel(r'Fraction with $|\Delta F|\leq 1$')
axes[0].set_title('Optimal sector inference')
axes[1].set_title('Parent BP + MWPM')
axes[2].set_title('Ambiguous physical records')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.90),ncol=5,frameon=False)
fig.suptitle('Square at p=0.30: bias changes sector ambiguity',fontsize=17,y=.98)
fig.text(.5,.015,'Pointwise 95%: bootstrap for risk, Wilson for record fractions · n=512 at L=5,7 and q=0.5,0.75; 256 at higher q; 192 at L=9\nL=9 was held out from the initial mechanism decision. Lines guide the eye; no thermodynamic extrapolation.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.10,1,.80))
fig.savefig(LAB/'figures/square-size-bias-ambiguity.png',dpi=180)
plt.close(fig)
