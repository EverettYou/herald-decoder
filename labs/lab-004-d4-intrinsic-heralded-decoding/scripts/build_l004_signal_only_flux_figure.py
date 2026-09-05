#!/usr/bin/env python3
"""Render the current R6AE paper-unconditional signal-only flux curves."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "results/r6ae-signal-only-bp-threshold-analysis-2026-09-01.json"
OUT = LAB / "figures/l004-1-signal-only-flux-ler-2026-09-01.png"
DATA = LAB / "results/l004-1-signal-only-flux-ler-2026-09-01.json"
POLICIES = {"Published O2 herald-MWPM": "O2_published_herald_weight_MWPM",
            "Signal-only BeliefMatching (BP→MWPM)": "R6D_local_BP_posterior_LLR_MWPM"}

def wilson90(k, n):
    z=1.6448536269514722; p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; r=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-r,c+r

def main():
    d=json.loads(SOURCE.read_text()); rows=[]
    for cell in d["cells"]:
        for label,key in POLICIES.items():
            s=cell[key]["all_final_iterates"]
            n=int(cell["attempted_histories"])
            k=int(cell["terminal_physical_winding"])+int(s["failures"])
            lo,hi=wilson90(k,n)
            rows.append({"policy":label,"size":int(cell["size"]),"p_X":float(cell["p_X"]),"failures":k,"attempts":n,"LER":k/n,"wilson90":[lo,hi]})
    DATA.write_text(json.dumps({"scope":"paper-unconditional first-stage D4 flux LER; X-only p_Z=0; signal-only public e_B/e_G record", "source":SOURCE.name,"records":rows},indent=2)+"\n")
    sizes=sorted({x["size"] for x in rows}); colors=plt.cm.viridis(np.linspace(.08,.92,len(sizes)))
    fig,axes=plt.subplots(1,2,figsize=(12.5,4.8),sharex=True,sharey=True,constrained_layout=True)
    for ax,(label,key) in zip(axes,POLICIES.items()):
        for L,color in zip(sizes,colors):
            vals=sorted((x for x in rows if x["policy"]==label and x["size"]==L),key=lambda x:x["p_X"])
            x=np.array([v["p_X"] for v in vals]); y=np.array([v["LER"] for v in vals]); lo=np.array([v["wilson90"][0] for v in vals]); hi=np.array([v["wilson90"][1] for v in vals])
            ax.errorbar(x,y,yerr=np.vstack((y-lo,hi-y)),marker="o",ms=4,capsize=2,lw=1.5,color=color,label=f"L={L}")
        ax.set_title(label); ax.set_xlabel(r"physical X-error rate $p_X$"); ax.set_xlim(.188,.222); ax.set_ylim(0,.55); ax.grid(alpha=.25)
    axes[0].set_ylabel("unconditional first-stage flux LER")
    axes[1].legend(title="paper-normalized L",frameon=False,ncols=2)
    fig.suptitle("D4 flux recovery with public signal-only heralds",fontsize=14)
    OUT.parent.mkdir(exist_ok=True); fig.savefig(OUT,dpi=220,bbox_inches="tight")
    print(json.dumps({"figure":str(OUT),"data":str(DATA),"records":len(rows)}))
if __name__=="__main__": main()
