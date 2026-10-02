"""Replace withdrawn B18 guide with measured coverage on the physical full domain."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
LAB=Path(__file__).resolve().parents[1]
NAME='phase-b19-full-prior-evidence-coverage-2026-10-01'

def main():
    source=LAB/'results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json'
    evidence=json.loads(source.read_text());P=np.array(evidence['p_values']);Q=np.array(evidence['q_values'])
    Z=np.full((len(Q),len(P)),np.nan)
    for cell in evidence['cells']:Z[list(Q).index(cell['q']),list(P).index(cell['p'])]=cell['display_log_odds']
    pe=np.r_[P[0]-(P[1]-P[0])/2,(P[:-1]+P[1:])/2,.5]
    qe=np.r_[0,(Q[:-1]+Q[1:])/2,1]
    fig,ax=plt.subplots(figsize=(10,5.2),layout='constrained');ax.set_facecolor('#f0f0f0')
    mesh=ax.pcolormesh(pe,qe,Z,cmap='coolwarm',vmin=-6,vmax=6,rasterized=True)
    ax.axvline(.5,color='#555',ls=':',lw=1)
    ax.text(.75,.58,'No joint-grid measurements\nin this half of the domain',ha='center',va='center',color='#444',fontsize=12)
    ax.text(.75,.40,'Do not infer values by reflection.\nBoundary topology remains open.',ha='center',va='center',color='#555',fontsize=10)
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Physical error probability p',ylabel='Herald detection probability q',title='Honeycomb: measured finite-window evidence over the full prior domain')
    cb=fig.colorbar(mesh,ax=ax);cb.set_label('Log odds of upward vs downward finite-window LER trend\n(display clipped to ±6; inherited BP protocol)')
    fig.text(.5,-.025,'B14 measured cohorts retained. No fitted boundary, mirror symmetry, or thermodynamic phase inference.',ha='center',fontsize=10)
    for ext in ['png','svg','pdf']:fig.savefig(LAB/'figures'/f'{NAME}.{ext}',dpi=180,bbox_inches='tight')
    result={'status':'current_corrected_coverage','domain':{'p':[0,1],'q':[0,1]},'measured_p_centers':P.tolist(),'measured_q_centers':Q.tolist(),'cells':len(evidence['cells']),'source':{'path':str(source.relative_to(LAB)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},'unmeasured_joint_grid_p_above_half':True,'fabricated_or_mirrored_cells':0,'boundary_curve':None,'withdrawn_guide':'B18','interpretation':'Finite-window trend evidence for the inherited BP protocol; high-p joint grid unmeasured; no thermodynamic threshold inferred.'}
    (LAB/'results'/f'{NAME}.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
