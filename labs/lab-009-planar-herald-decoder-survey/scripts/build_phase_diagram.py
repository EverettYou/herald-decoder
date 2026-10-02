"""Render measured full-domain finite-size evidence with explicit uncertainty."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.tri import Triangulation,LinearTriInterpolator
LAB=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})

def main():
    data=json.loads((LAB/'results/phase-analysis.json').read_text());assert data['status']=='passed_finite_size_analysis'
    fig,axes=plt.subplots(1,3,figsize=(16,5.8),layout='constrained',sharey=True)
    rows=[r for r in data['rows']if r['L']==24];x=np.array([r['p']for r in rows]);y=np.array([r['q']for r in rows]);risk=np.array([r['risk']for r in rows]);tri=Triangulation(x,y)
    cmap=plt.get_cmap('magma').copy()
    levels=np.linspace(0,.5,21);plot=axes[0].tricontourf(tri,risk,levels=levels,cmap=cmap)
    axes[0].scatter(x,y,s=3,color='#d2d8df',alpha=.6,zorder=3)
    fig.colorbar(plot,ax=axes[0],location='bottom',shrink=.88,pad=.10,ticks=np.arange(0,.51,.1),label='Exact conditional Bayes risk, mean over records')
    axes[0].set_title('Logical ML risk: L=24\nIndependent full-square observations')
    trends=data['trends'];x=np.array([r['p']for r in trends]);y=np.array([r['q']for r in trends]);z=np.clip(np.array([r['display_score']for r in trends]),-6,6);tri=Triangulation(x,y)
    px,qy=np.meshgrid(np.linspace(0,1,501),np.linspace(0,1,501));zi=LinearTriInterpolator(tri,z)(px,qy)
    phase=np.ones(px.shape);phase[zi < -1.96]=0;phase[zi > 1.96]=2
    mu=np.sqrt(2+np.sqrt(2));rho=mu*np.sqrt(px*(1-px))*(1+np.sqrt(1-qy));phase[rho<1]=0
    colors=['#d4e8e2','#e5e4e0','#edc6bd']
    axes[1].pcolormesh(px,qy,phase,cmap=ListedColormap(colors),vmin=0,vmax=2,shading='auto',rasterized=True)
    axes[1].contour(px,qy,rho,levels=[1],colors=['#58716a'],linewidths=.9,linestyles=':')
    # Pointwise statistical labels at measured nodes, with a light interpolation
    # only for display. The legend explicitly distinguishes evidence and limit.
    axes[1].scatter(x,y,c=[0 if r['evidence']in ['sufficient recovery bound','risk decreases with size']else 2 if r['evidence']in ['risk increases with size','uniform syndrome-only nonrecovery','near-maximal finite-size risk plateau']else 1 for r in trends],cmap=ListedColormap(colors),vmin=0,vmax=2,s=9,edgecolors='#777',linewidths=.25)
    from matplotlib.patches import Patch
    axes[1].legend(handles=[Patch(color=colors[0],label='Recovery evidence / sufficient bound'),Patch(color=colors[2],label='Nonrecovery evidence'),Patch(color=colors[1],label='Unresolved size trend')],fontsize=8,loc='lower center',bbox_to_anchor=(.5,-.31),frameon=False)
    axes[1].set_title('Decoding-phase evidence\nSize trends and near-maximal-risk plateau')
    labels={(8,16):('8 / 16','#89919a','o'),(16,24):('16 / 24','#346b98','s'),(24,32):('24 / 32','#a3572d','D')}
    for (a,b),(label,color,marker)in labels.items():
        bands=[r for r in data['crossing_bands']if(r['L_small'],r['L_large'])==(a,b)]
        for j,band in enumerate(bands):
            lo,hi=band['interval'];center=band['candidate_values'][0]if band['status']=='single_bootstrap_interval'else(lo+hi)/2
            axes[2].hlines(band['q'],lo,hi,color=color,linewidth=1.3)
            axes[2].plot([lo,hi],[band['q'],band['q']],linestyle='none',marker='|',ms=5,color=color)
            axes[2].plot(center,band['q'],marker=marker if band['status']=='single_bootstrap_interval'else'x',linestyle='none',ms=4,color=color,label=f'L={label}'if j==0 else None)
    axes[2].legend(fontsize=8,loc='lower center',bbox_to_anchor=(.5,-.26),ncol=3,frameon=False)
    axes[2].set_title('Crossing windows and lattice-size drift\nBootstrap 95%; ×: unresolved candidate envelope')
    for ax in axes:ax.set(xlim=(0,1),ylim=(-.015,1.015),xlabel='Physical error probability p');ax.grid(alpha=.10)
    axes[0].set_ylabel('Herald availability q')
    axes[1].text(.5,.97,'q=1: sufficient recovery for every p',transform=axes[1].transAxes,ha='center',va='top',fontsize=8,color='#35584c')
    fig.suptitle('Honeycomb decoding transition — exact planar logical-sector inference',fontsize=15)
    fig.text(.5,-.015,f"{data['new_independent_trials']:,} independent records; L=8,16,24,32. Finite-size estimates, not a certified thermodynamic boundary. No p↔1−p folding.",ha='center',fontsize=10)
    paths=[]
    for ext in ['png','svg','pdf']:
        p=LAB/'figures'/f'exact-planar-phase-diagram.{ext}';fig.savefig(p,dpi=180,bbox_inches='tight');paths.append(str(p.relative_to(LAB)))
    plt.close(fig)
    inputs=['results/phase-analysis.json','results/phase-method-validation.json','data/phase-risk-cells.csv','manifests/phase-diagram.json']
    semantics='Fresh full-domain exact logical-ML evidence. Left: L24 mean conditional Bayes risk, linear display interpolation; dots sampled cells. Middle: L24−L8 pointwise 95% size-trend evidence plus near-maximal finite-size risk plateaus and exact uniform syndrome-only nonrecovery point (gray unresolved), dotted analytic sufficient-recovery bound; between-node coloring interpolates the display score clipped at ±6. Right: crossing intervals for L8/16, L16/24, L24/32. Single stable candidates use local-window bootstrap95; overlapping or unstable candidate intervals are merged into envelopes marked ×, not pooled confidence intervals or distinct physical transitions. All raw crossing candidates remain in the analysis. Statistical uncertainty does not include lattice-size drift or interpolation bias. No complement folding or forced single threshold.'
    receipt={'status':'generated','id':'exact-planar-phase-diagram','files':paths,'inputs':inputs,'semantics':semantics,'input_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for s in inputs},'output_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for s in paths},'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (LAB/'results/phase-figure-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('generated exact-planar-phase-diagram PNG/SVG/PDF')
if __name__=='__main__':main()
