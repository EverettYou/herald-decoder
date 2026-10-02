"""Finite-size risk maps and every resolved fixed-q crossing; no symmetry fit."""
import json,csv,hashlib,argparse
from pathlib import Path
import numpy as np
LAB=Path(__file__).resolve().parents[1]

def read_rows():return [json.loads(p.read_text())for p in sorted((LAB/'data/phase-sweep').glob('*.json'))]

def crossing_risk(row):return row.get('risk_confirmation',row['risk'])

def crossings(rows,a,b,confirmed=False):
    table={(r['L'],r['p'],r['q']):r for r in rows if r['status']in ['passed','analytic_deterministic_prior']}
    roots=[]
    for q in sorted({r['q']for r in rows}):
        pp=sorted({p for L,p,q0 in table if L==a and q0==q and (b,p,q)in table and (not confirmed or (table[a,p,q]['n']>256 and table[b,p,q]['n']>256))})
        for p0,p1 in zip(pp[:-1],pp[1:]):
            small0,big0,small1,big1=[table[k]for k in [(a,p0,q),(b,p0,q),(a,p1,q),(b,p1,q)]]
            d0=crossing_risk(big0)-crossing_risk(small0);d1=crossing_risk(big1)-crossing_risk(small1)
            if d0*d1>=0 or (d0==d1) or max(abs(d0),abs(d1))<1e-3:continue
            risk0=(crossing_risk(big0)+crossing_risk(small0))/2;risk1=(crossing_risk(big1)+crossing_risk(small1))/2
            if max(risk0,risk1)<.025:continue # Numerical/rare-event near-zero coincidences are not transition roots.
            x=p0-d0*(p1-p0)/(d1-d0)
            roots.append({'q':q,'L_small':a,'L_large':b,'p_bracket':[p0,p1],'p_crossing':x,'orientation':'low-p entry'if d0<d1 else'high-p exit','risk_bracket':[risk0,risk1],'difference_bracket':[d0,d1]})
    return roots

def bootstrap_root(root,table,B=1000):
    a,b,q=root['L_small'],root['L_large'],root['q'];p0,p1=root['p_bracket'];center=root['p_crossing']
    # Bootstrap every measured p in a predeclared local window, permitting
    # the crossing to leave its selected adjacent bracket. Report conditioning
    # and absence rather than clipping its uncertainty to that bracket.
    pp=sorted(p for L,p,q0 in table if L==a and q0==q and (b,p,q)in table and p0-.050001<=p<=p1+.050001 and table[a,p,q]['n']>256 and table[b,p,q]['n']>256)
    rng=np.random.default_rng([81002,a,b,int(q*1e6),int(p0*1e6),int(p1*1e6)])
    diffs=[]
    for p in pp:
        draws=[]
        for L in [a,b]:
            r=table[L,p,q]
            if r['n']==0:draws.append(np.zeros(B));continue
            with np.load(LAB/r['vector'],allow_pickle=False)as z:values=z['risk'][r.get('confirmation_start',0):]
            draws.append(values[rng.integers(len(values),size=(B,len(values)))].mean(1))
        diffs.append(draws[1]-draws[0])
    diffs=np.array(diffs).T;xs=[]
    direction=1 if root['orientation']=='low-p entry'else -1
    for delta in diffs:
        candidates=[]
        for i in range(len(pp)-1):
            if delta[i]*delta[i+1]<0 and (delta[i+1]-delta[i])*direction>0:
                candidates.append(pp[i]-delta[i]*(pp[i+1]-pp[i])/(delta[i+1]-delta[i]))
        if candidates:xs.append(min(candidates,key=lambda x:abs(x-center)))
    ci=np.quantile(xs,[.025,.975]).tolist()if xs else None
    fraction=len(xs)/B
    root.update(bootstrap_crossing_fraction=fraction,bootstrap_ci95=ci,bootstrap_p_window=[pp[0],pp[-1]],bootstrap_replicates=B,uncertainty_scope='pointwise iid confirmation-record bootstrap conditional on this local p window and observed root orientation; no thermodynamic or simultaneous confidence claim',status='window_stable'if fraction>=.95 else'window_unresolved')
    return root

def crossing_bands(roots):
    bands=[]
    for key in sorted({(r['L_small'],r['L_large'],r['q'])for r in roots}):
        candidates=sorted([r for r in roots if(r['L_small'],r['L_large'],r['q'])==key],key=lambda r:(r['bootstrap_ci95']or r['p_bracket'])[0])
        groups=[]
        for r in candidates:
            lo,hi=r['bootstrap_ci95']or r['p_bracket']
            if groups and lo<=groups[-1]['hi']:
                groups[-1]['hi']=max(groups[-1]['hi'],hi);groups[-1]['roots'].append(r)
            else:groups.append({'lo':lo,'hi':hi,'roots':[r]})
        for g in groups:
            rr=g['roots'];single=len(rr)==1 and rr[0]['status']=='window_stable'
            bands.append({'L_small':key[0],'L_large':key[1],'q':key[2],'interval':[g['lo'],g['hi']],'candidate_values':[r['p_crossing']for r in rr],'candidate_count':len(rr),'orientations':sorted({r['orientation']for r in rr}),'status':'single_bootstrap_interval'if single else'unresolved_candidate_envelope','interval_scope':'Single candidate: local-window bootstrap95. Multiple/unstable candidates: interval union, not a pooled confidence interval or evidence for multiple physical transitions.'})
    assert sum(b['candidate_count']for b in bands)==len(roots)
    return bands

def refinement_jobs(rows):
    roots=crossings(rows,8,16)+crossings(rows,16,24)
    # Expand each observed sign-change bracket by one coarse interval, then
    # add interior points. This avoids treating a noisy selected root as fixed.
    jobs={}
    for r in roots:
        if r['q']>=.95:continue
        lo,hi=r['p_bracket'];mid=round((lo+hi)/2,6)
        for p in [lo,round(lo+(hi-lo)/4,6),mid,round(lo+3*(hi-lo)/4,6),hi]:
            for L in [8,16,24,32]:jobs[L,p,r['q']]=768
    # Explicit higher-q cuts locate closure without assuming its p coordinate.
    for q in [.86,.875,.89]:
        for p in [.35,.4,.45,.5,.55,.6,.65,.7,.75]:
            for L in [8,16,24,32]:jobs[L,p,q]=512
    return [[L,p,q,n]for (L,p,q),n in sorted(jobs.items())]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refine',action='store_true');args=ap.parse_args();rows=read_rows()
    if args.refine:
        frozen=LAB/'manifests/phase-refinement-jobs.json'
        if frozen.exists():
            print('reusing frozen refinement jobs',len(json.loads(frozen.read_text())));return
        jobs=refinement_jobs(rows);(LAB/'manifests/phase-refinement-jobs.json').write_text(json.dumps(jobs,indent=2)+'\n');print('refinement jobs',len(jobs));return
    assert len(rows)>0 and all(r['status']in ['passed','analytic_deterministic_prior']for r in rows),'Numerical failure gate'
    table={(r['L'],r['p'],r['q']):r for r in rows}
    roots=[]
    for a,b in [(8,16),(16,24),(24,32)]:
        roots.extend(bootstrap_root(r,table)for r in crossings(rows,a,b,confirmed=True))
    # A conservative finite-size phase indicator, with pointwise SE, separately
    # from the crossing bootstrap and the analytic sufficient recovery bound.
    trends=[]
    mu=np.sqrt(2+np.sqrt(2))
    for q in sorted({r['q']for r in rows}):
        pp=sorted({p for L,p,q0 in table if L==8 and q0==q and (24,p,q)in table})
        for p in pp:
            a=table[8,p,q];b=table[24,p,q];d=b['risk']-a['risk'];se=np.hypot(a['se'],b['se']);rho=mu*np.sqrt(p*(1-p))*(1+np.sqrt(1-q));z=d/se if se>1e-15 else 0.
            evidence='sufficient recovery bound'if rho<1 else('risk decreases with size'if z < -1.96 else('risk increases with size'if z > 1.96 else'unresolved'))
            display_score=z
            if a['risk']>=.49 and b['risk']>=.49:
                evidence='near-maximal finite-size risk plateau';display_score=4.
            if p==.5 and q==0:
                evidence='uniform syndrome-only nonrecovery';display_score=4.
            trends.append({'p':p,'q':q,'risk_L8':a['risk'],'risk_L24':b['risk'],'difference_L24_minus_L8':d,'se':float(se),'z':float(z),'display_score':float(display_score),'evidence':evidence,'rho_sufficient_bound':float(rho)})
    # Keep direct failure scoring as a secondary Monte Carlo sanity check.
    deltas=[]
    for r in rows:
        if r['n']==0:continue
        with np.load(LAB/r['vector'],allow_pickle=False)as z:
            risk=z['risk'];prob=z['probability_one'];fail=z['failure'];assert np.max(abs(risk-np.minimum(prob,1-prob)))<1e-12
            diff=fail-risk;deltas.append((float(diff.sum()),float(np.sum((diff-diff.mean())**2)),len(diff)))
    delta=sum(t[0]for t in deltas)/sum(t[2]for t in deltas);se=np.sqrt(sum(t[1]for t in deltas))/sum(t[2]for t in deltas)
    compact_fields=['L','p','q','n','risk','se','status','vector','sha256','direct_failures','max_solve_residual','confirmation_start','confirmation_n','risk_confirmation','se_confirmation']
    compact_rows=[{k:r[k]for k in compact_fields if k in r}for r in rows]
    result={'status':'passed_finite_size_analysis','estimator':'unconditional exact conditional Bayes risk, Rao–Blackwell estimator','rows':compact_rows,'crossings':roots,'crossing_bands':crossing_bands(roots),'pilot_crossings':crossings(rows,8,16)+crossings(rows,16,24),'crossing_sample_policy':'Only refined cells used in primary crossings; first 256 pilot records excluded from refined original cells; new cells use their independent streams.','trends':trends,'new_independent_trials':sum(r['n']for r in rows),'numerical_failures':0,'sizes':sorted({r['L']for r in rows}),'domain':{'p':[0,1],'q':[0,1]},'bootstrap_replicates':1000,'direct_failure_minus_conditional_risk':{'mean':delta,'se':float(se)},'interpretation':'Crossings are finite-size transition estimates; lattice-size drift, unresolved brackets and between-cut interpolation are separate limitations. No enforced p symmetry, single transition or exponent.','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (LAB/'results/phase-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    with (LAB/'data/phase-risk-cells.csv').open('w',newline='')as f:
        fields=['L','p','q','n','risk','se','confirmation_start','confirmation_n','risk_confirmation','se_confirmation','status'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    print(json.dumps({'cells':len(rows),'trials':result['new_independent_trials'],'crossings':len(roots),'stable_crossings':sum(r['status']=='window_stable'for r in roots),'direct_minus_RB':result['direct_failure_minus_conditional_risk']}))
if __name__=='__main__':main()
