#!/usr/bin/env python3
"""Six-panel hidden-orientation LER, BP diagnostics and paired effects."""
import hashlib,json,os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from scipy.stats import beta
LAB=Path(__file__).resolve().parents[1]
COLORS=['#fca082','#ef6548','#cb181d','#7f0000'];SIZES=(5,7,9,11)

def paired_interval(row):
    n=row['shots'];a=row['joint_failures_directed_by_hidden'][0][1];b=row['joint_failures_directed_by_hidden'][1][0]
    def cp(k):return (0. if k==0 else float(beta.ppf(.0125,k,n-k+1)),1. if k==n else float(beta.ppf(.9875,k+1,n-k)))
    la,ha=cp(a);lb,hb=cp(b)
    return (a-b)/n,(la-hb,ha-lb)

def render():
    payloads={};input_hashes={}
    for lattice in ('square','honeycomb'):
        for group in ('U1','SU2','SU3'):
            path=LAB/f'results/a9-hidden-{lattice}-{group}.json'
            if path.exists():
                raw=path.read_bytes();payloads[lattice,group]=json.loads(raw)['rows'];input_hashes[str(path.relative_to(LAB))]=hashlib.sha256(raw).hexdigest()
            else:payloads[lattice,group]=[]
    total=sum(map(len,payloads.values()));qualifier='complete' if total==600 else f'partial: {total}/600 cells'
    outputs=[]
    for mode in ('ler','nonconvergence','paired-effect'):
        fig,axes=plt.subplots(3,2,figsize=(12,12.5),sharex=True,sharey=False)
        fig.subplots_adjust(left=.105,right=.975,top=.865,bottom=.18,hspace=.30,wspace=.24)
        for row,(group,label) in enumerate((('U1','U(1)'),('SU2','SU(2)'),('SU3','SU(3)'))):
            for col,lattice in enumerate(('square','honeycomb')):
                ax=axes[row,col];rows=payloads[lattice,group];high=[];low=[]
                for L,color in zip(SIZES,COLORS):
                    curve=sorted((r for r in rows if r['L']==L),key=lambda r:r['p'])
                    if not curve:continue
                    x=[r['p'] for r in curve]
                    if mode=='nonconvergence':
                        y=[r['arms']['hidden_orientation']['bp_nonconverged']/r['shots'] for r in curve];ax.plot(x,y,'o-',color=color,markersize=3);high+=y
                    else:
                        if mode=='ler':
                            y=[r['arms']['hidden_orientation']['ler'] for r in curve];interval=[r['arms']['hidden_orientation']['wilson95'] for r in curve]
                        else:
                            pairs=[paired_interval(r) for r in curve];y=[q[0] for q in pairs];interval=[q[1] for q in pairs]
                        interval=np.array(interval);y=np.array(y);ax.errorbar(x,y,yerr=np.maximum(0,np.array([y-interval[:,0],interval[:,1]-y])),fmt='o-',markersize=3,capsize=2,elinewidth=.8,color=color)
                        high+=interval[:,1].tolist();low+=interval[:,0].tolist()
                if mode=='paired-effect':
                    extent=max(.001,1.1*max([abs(v) for v in high+low] or [.001]));ax.set_ylim(-extent,extent);ax.axhline(0,color='#888888',linewidth=.8,linestyle='--')
                else:ax.set_ylim(0,min(1,max(.001,1.12*max(high or [.001]))))
                ax.set_xlim(0,.5);ax.set_xticks(np.linspace(0,.5,6));ax.grid(alpha=.2)
                ax.set_title(f'({chr(97+row*2+col)}) {label} · {len(rows)}/100 cells',loc='left',fontsize=12)
                if not rows:ax.text(.5,.5,'Awaiting sampled cells',transform=ax.transAxes,ha='center',color='#666666')
        title={'ler':'Hidden-orientation heralded logical error rate','nonconvergence':'Hidden-orientation BP nonconvergence','paired-effect':'Orientation effect: hidden minus directed LER'}[mode]
        fig.suptitle(f'{title}\n{qualifier}',y=.99,fontsize=17)
        fig.text(.5,.935,'Fresh fair orientation per pair, hidden from decoder · full interior (m,R) · rough-boundary record unmeasured',ha='center',fontsize=10)
        for col,name in enumerate(('Square lattice','Honeycomb lattice')):
            pos=axes[0,col].get_position();fig.text((pos.x0+pos.x1)/2,.900,name,ha='center',fontsize=15)
        ylabel={'ler':'Logical error rate','nonconvergence':'BP nonconvergence fraction','paired-effect':'LER difference (hidden − directed)'}[mode]
        fig.supylabel(ylabel,x=.015,y=.52,fontsize=13);fig.supxlabel('Physical edge-error probability p',y=.13,fontsize=13)
        fig.legend(handles=[Line2D([],[],color=c,marker='o',markersize=5,label=f'L = {L}') for L,c in zip(SIZES,COLORS)],loc='lower center',bbox_to_anchor=(.5,.077),ncol=4,frameon=False,fontsize=12)
        intervals='Wilson 95% intervals' if mode=='ler' else ('Conservative paired 95% intervals' if mode=='paired-effect' else 'Numerical diagnostic; does not gate LER')
        fig.text(.5,.029,f'20,000 paired shots per cell · {intervals} · independent vertical scales\nSU(2): exact orientation quotient. Lines guide the eye; no threshold fit.',ha='center',fontsize=10,linespacing=1.7)
        path=LAB/f'figures/a9-hidden-orientation-{mode}.png';temp=path.with_suffix(f'.{os.getpid()}.tmp.png');fig.savefig(temp,dpi=180);plt.close(fig);temp.replace(path)
        outputs.append({'path':str(path.relative_to(LAB)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mode':mode})
    data={'status':'complete' if total==600 else 'partial','completed_cells':total,'inputs':input_hashes,'figures':outputs,'layout':{'rows':['U1','SU2','SU3'],'columns':['square','honeycomb'],'colors':dict(zip(map(str,SIZES),COLORS)),'shared_x':True,'shared_y':False,'legend':'four sizes below panels; no p=0 marker'}}
    path=LAB/'results/a9-figure-inputs.json';temp=path.with_suffix(f'.{os.getpid()}.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)

if __name__=='__main__':render()
