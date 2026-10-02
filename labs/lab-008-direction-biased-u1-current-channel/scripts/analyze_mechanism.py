"""Registered record-level analysis of matched posterior and decoder risks."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from current_oracle import LAB

METRICS=('bayes_risk','exact_mwpm_risk','bp_mwpm_risk')

def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n
    mid=(p+z*z/(2*n))/d;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(mid-half),float(mid+half)]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest');args=parser.parse_args()
    manifest=json.loads((LAB/args.manifest).read_text());rng=np.random.default_rng(manifest['analysis']['bootstrap_seed'])
    count=manifest['analysis']['bootstrap_replicates'];rows=[];arrays={};inputs={}
    def summarize(values,level=.95):
        values=np.asarray(values)
        idx=rng.integers(0,len(values),size=(count,len(values)))
        means=values[idx].mean(axis=1)
        return {'mean':np.mean(values,axis=0).tolist(),
                'interval':np.quantile(means,[(1-level)/2,(1+level)/2],axis=0).T.tolist(),
                'level':level}
    for cell in manifest['cells']:
        file=LAB/manifest['result_directory']/(cell['id']+'.json')
        d=json.loads(file.read_text());assert d['status']=='complete' and len(d['records'])==cell['shots']
        records=d['records'];risk=np.array([[r[k] for k in METRICS] for r in records])
        assert np.all(risk[:,1:]>=risk[:,0,None]-1e-10)
        arrays[cell['id']]=risk
        inputs[str(file.relative_to(LAB))]=hashlib.sha256(file.read_bytes()).hexdigest()
        failures=np.array([[r['bayes_actual_failure'],*r['actual_failures']] for r in records])
        deviations=(failures-risk).sum(axis=0)/np.sqrt(np.maximum((risk*(1-risk)).sum(axis=0),1e-20))
        # Generative-law guard, not a claim that every nominal interval must cover.
        assert np.max(abs(deviations))<6,('calibration anomaly',cell['id'],deviations.tolist())
        gap=np.array([abs(r['signed_gap']) if r['signed_gap'] is not None else np.inf for r in records])
        bpnon=np.array([not r['bp_converged'] for r in records])
        response=np.array([np.sign(r['signed_gap'])*r['response'] for r in records
                           if r['response'] is not None and r['signed_gap'] is not None])
        row={**cell,'risk':summarize(risk),'excess':summarize(risk[:,1:]-risk[:,0,None]),
             'actual_failures':[{'count':int(k),'rate':float(k/len(records)),'wilson95':wilson(k,len(records))} for k in failures.sum(axis=0)],
             'conditional_calibration_z':deviations.tolist(),
             'ambiguous_abs_gap_below_1':float(np.mean(gap<1)),'infinite_gap_fraction':float(np.mean(np.isinf(gap))),
             'gap_cdf':{str(x):float(np.mean(gap<=x)) for x in (0.1,.5,1.,2.,4.,8.)},
             'bp_nonconvergence':float(bpnon.mean()),
             'marginal_error_mean':float(np.mean([r['marginal_mean_error'] for r in records])),
             'marginal_error_max':float(max(r['marginal_max_error'] for r in records)),
             'gap_response_positive_fraction':float(np.mean(response>1e-8)) if len(response) else None,
             'gap_response_median':float(np.median(response)) if len(response) else None,
             'compute_seconds':d['compute_seconds']}
        rows.append(row)
    contrasts=[]
    groups=sorted({(x['lattice'],x['L'],x['p'],x.get('arrows','stored')) for x in manifest['cells']})
    for lattice,L,p,pattern in groups:
            found={x['q']:x for x in manifest['cells'] if (x['lattice'],x['L'],x['p'],x.get('arrows','stored'))==(lattice,L,p,pattern)}
            if .5 not in found or 1 not in found:continue
            a,b=found[.5],found[1.]
            # Across arrow patterns is handled below, not silently collapsed.
            if a.get('arrows','stored')!=b.get('arrows','stored'):continue
            assert a['seed']==b['seed'] and a['shots']==b['shots']
            diff=arrays[a['id']]-arrays[b['id']]
            contrasts.append({'lattice':lattice,'L':L,'p':p,'arrows':pattern,'contrast':'fair minus directed',
                              'risks':summarize(diff,.975 if p==.3 else .95),
                              'excess':summarize(diff[:,1:]-diff[:,0,None])})
    arrow=[]
    for L in sorted({x['L'] for x in manifest['cells']}):
        for q in sorted({x['q'] for x in manifest['cells']}):
            pair={x.get('arrows','stored'):x for x in manifest['cells'] if x['L']==L and x['q']==q}
            if set(pair)!={'stored','bipartite'}:continue
            a,b=pair['stored'],pair['bipartite']
            assert a['seed']==b['seed'] and a['shots']==b['shots'] and a['p']==b['p']
            arrow.append({'L':L,'p':a['p'],'q':q,'contrast':'bipartite minus stored',
                          'risks':summarize(arrays[b['id']]-arrays[a['id']])})
    primary=[r for r in contrasts if r['p']==.3 and r['arrows']=='stored']
    supported=bool(primary) and all(r['risks']['interval'][0][0]>0 for r in primary)
    out={'status':'complete','manifest':args.manifest,'input_sha256':inputs,'risk_metrics':METRICS,
         'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'rows':rows,'orientation_contrasts':contrasts,'arrow_contrasts':arrow,
         'primary_intrinsic_component_resolved':supported,
         'interpretation':'Intrinsic fair-minus-directed component resolved at every registered primary size.' if supported else 'Primary intrinsic component not resolved at all registered sizes; inspect intervals and algorithmic excess.',
         'uncertainty':'Record-level paired percentile bootstrap; primary p=.30 Bayes contrasts use per-size 97.5% intervals. Realized failures have Wilson95 companions.',
         'limits':['Conditional risks estimate a physical-record mean, not a transition.','Degenerate bootstrap intervals do not prove zero population risk.',
                   'The two MWPM decoders are not assumed ordered.','Fixed-record gap responses do not include the derivative of the physical record law.']}
    output=LAB/'results'/(Path(args.manifest).stem+'-analysis.json')
    output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'result':str(output),'primary':primary,'arrow':arrow,'interpretation':out['interpretation']},indent=2))


if __name__=='__main__':main()
