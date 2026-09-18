#!/usr/bin/env python3
import json, math
from pathlib import Path
import matplotlib.pyplot as plt
LAB=Path(__file__).resolve().parents[1]; SOURCE=LAB/"results/r6al-dense-crossing-scan-2026-09-09.json"; OUT=LAB/"figures/l004-1-current-herald-aware-flux-curves.png"; Z=1.6448536269514722
def wilson(x,n):
 p=x/n; d=1+Z*Z/n; c=(p+Z*Z/(2*n))/d; r=Z*math.sqrt(p*(1-p)/n+Z*Z/(4*n*n))/d; return p,c-r,c+r
def main():
 d=json.loads(SOURCE.read_text()); cells=d["cells"]; sizes=sorted({c["size"] for c in cells}); fig,ax=plt.subplots(2,2,figsize=(15,10),sharex=True,gridspec_kw={"height_ratios":[2.1,1.0],"hspace":.16,"wspace":.18}); colours=plt.cm.viridis([.05,.28,.5,.72,.95])
 for j,(key,label) in enumerate([("O2_failures","Herald-weight MWPM"),("BP_failures","Signal-only BeliefMatching")]):
  for colour,size in zip(colours,sizes):
   rows=sorted([c for c in cells if c["size"]==size],key=lambda c:c["p_X"]); vals=[wilson(c[key],c["attempted"]) for c in rows]; ax[0,j].errorbar([c["p_X"] for c in rows],[v[0] for v in vals],yerr=([v[0]-v[1] for v in vals],[v[2]-v[0] for v in vals]),marker="o",lw=1.8,capsize=3,color=colour,label=f"L={size}")
  ax[0,j].set_title(label); ax[0,j].grid(alpha=.25); ax[1,j].set_xlabel(r"physical X-error probability $p_X$"); ax[0,j].set_ylim(.10,.42); ax[0,j].axvline(.20842,color="#b23a48",ls="--",lw=1.5,label=r"paper $p_c=0.20842$"); ax[0,j].legend(frameon=False,ncol=2,fontsize=9)
  for pair,(lo,hi) in enumerate([(5,7),(7,9),(9,11),(11,13)]):
   left={c["p_X"]:c for c in cells if c["size"]==lo}; right={c["p_X"]:c for c in cells if c["size"]==hi}; xs=sorted(left); ys=[]; es=[]
   for x in xs:
    pl=left[x][key]/left[x]["attempted"]; pr=right[x][key]/right[x]["attempted"]; ys.append(pr-pl); es.append(1.645*math.sqrt(pl*(1-pl)/left[x]["attempted"]+pr*(1-pr)/right[x]["attempted"]))
   ax[1,j].errorbar(xs,ys,yerr=es,marker="o",lw=1.2,capsize=2,label=f"L={hi} minus {lo}")
  ax[1,j].axhline(0,color="black",lw=1); ax[1,j].axvline(.20842,color="#b23a48",ls="--",lw=1.2); ax[1,j].grid(alpha=.25); ax[1,j].legend(frameon=False,ncol=2,fontsize=8)
 ax[0,0].set_ylabel("unconditional first-stage flux LER"); ax[1,0].set_ylabel("adjacent-size LER difference"); fig.suptitle("D4 dense matched scan: herald-aware decoder comparison",fontsize=17); fig.text(.5,.015,"55 cells x 10,000 matched histories; upper: 90% Wilson intervals; lower: independent binomial error approximation from counts. No thermodynamic threshold fit.",ha="center",fontsize=11); fig.tight_layout(rect=(0,.05,1,.94)); OUT.parent.mkdir(exist_ok=True); fig.savefig(OUT,dpi=200,facecolor="white"); plt.close(fig); print(json.dumps({"source":str(SOURCE),"output":str(OUT),"cells":len(cells),"histories":sum(c["attempted"] for c in cells)}))
if __name__=="__main__": main()
