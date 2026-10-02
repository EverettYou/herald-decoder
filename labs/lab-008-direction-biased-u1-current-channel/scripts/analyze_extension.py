"""Exploratory distributional follow-up; no scaling model is fitted."""
from pathlib import Path
import hashlib
import json
import numpy as np
from current_oracle import LAB
from analyze_mechanism import METRICS, wilson


def main():
    rng=np.random.default_rng(909182029);replicates=4000;inputs={};records={};rows=[]
    def read(relative):
        p=LAB/relative;inputs[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
        return json.loads(p.read_text())
    def interval(x):
        x=np.asarray(x);boot=x[rng.integers(0,len(x),size=(replicates,len(x)))].mean(axis=1)
        return {'mean':x.mean(axis=0).tolist(),'interval95':np.quantile(boot,[.025,.975],axis=0).T.tolist()}
    for study in ('square-mechanism','size-bias-extension'):
        analysis=read(f'results/{study}-2026-09-18-analysis.json')
        manifest=read(analysis['manifest'])
        for row in analysis['rows']:
            if row['p']!=.3:continue
            if study=='square-mechanism' and row['q'] not in (.5,.75):continue
            data=read(manifest['result_directory']+'/'+row['id']+'.json')['records']
            records[row['L'],row['q']]=data
            gaps=np.array([abs(r['signed_gap']) if r['signed_gap'] is not None else np.inf for r in data])
            probs=np.array([r['sector_probabilities'] for r in data])
            entropy=-(probs*np.log2(np.maximum(probs,1e-300))).sum(axis=1)
            cdf=[{'threshold':x,'fraction':float((gaps<=x).mean()),'wilson95':wilson(int((gaps<=x).sum()),len(gaps))}
                 for x in (.1,.5,1.,2.,4.,8.)]
            rows.append({**row,'study':study,'gap_cdf_intervals':cdf,'sector_entropy_bits':interval(entropy)})
    near=[]
    for L in (5,7,9):
        baseline=np.array([[r[k] for k in METRICS] for r in records[L,1.]])
        for q in (.9,.97):
            target=np.array([[r[k] for k in METRICS] for r in records[L,q]])
            near.append({'L':L,'q':q,'contrast':'near-directed minus directed','risk':interval(target-baseline)})
    size=[]
    for q in (.5,.75,.9,.97,1.):
        a=np.array([[r[k] for k in METRICS] for r in records[9,q]])
        b=np.array([[r[k] for k in METRICS] for r in records[7,q]])
        aboot=a[rng.integers(0,len(a),size=(replicates,len(a)))].mean(axis=1)
        bboot=b[rng.integers(0,len(b),size=(replicates,len(b)))].mean(axis=1)
        size.append({'q':q,'contrast':'L9 minus L7','mean':(a.mean(axis=0)-b.mean(axis=0)).tolist(),
                     'interval95':np.quantile(aboot-bboot,[.025,.975],axis=0).T.tolist()})
    out={'status':'complete','input_sha256':inputs,'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'bootstrap_seed':909182029,'bootstrap_replicates':replicates,'square_grid':sorted(rows,key=lambda r:(r['q'],r['L'])),
         'near_endpoint_contrasts':near,'size_contrasts':size,
         'selection':'Stage2 L5,L7 q=.5,.75; Stage4 all remaining cells. Earlier q=1 cells are separate replication and are not pooled.',
         'limits':['Exploratory pointwise intervals; no simultaneous discovery claim.','Three sizes at p=.30 cannot establish a thermodynamic class or endpoint singularity.',
                   'CDF intervals measure physical-record ambiguity; no mean-gap extrapolation.','Independent bootstrap across sizes, paired bootstrap within the new q grid.']}
    p=LAB/'results/size-bias-distributions-2026-09-18.json';p.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'near_endpoint':near,'size_contrasts':size},indent=2))


if __name__=='__main__':main()
