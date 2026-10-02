"""Audit registered production provenance and replay one record per cell."""
from pathlib import Path
import hashlib
import json
import numpy as np
from current_oracle import LAB, ROOT, CurrentOracle, exact_enumeration, square_graph
from decoder_comparison import DecoderAdapter, compare_record
from run_mechanism import make_model
from analyze_mechanism import METRICS


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    inputs={};cell_checks=[];total=0;maximum=0.
    def read(p):
        inputs[str(p.relative_to(ROOT))]=sha(p)
        return json.loads(p.read_text())
    valid=read(LAB/'results/response-oracle-validation-2026-09-18.json')
    assert valid['status']=='passed'
    for path,h in valid['source_sha256'].items():assert sha(ROOT/path)==h,path
    for study in ('square-mechanism','honeycomb-arrow-control','size-bias-extension'):
        m=read(LAB/f'manifests/{study}-2026-09-18.json');assert m['status']=='complete'
        frozen={k:v for k,v in m.items() if k not in ('status','completed_at','analysis')}
        dh=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
        a=read(LAB/f'results/{study}-2026-09-18-analysis.json')
        assert sha(LAB/'scripts/analyze_mechanism.py')==a['analysis_source_sha256']
        for path,h in a['input_sha256'].items():assert sha(LAB/path)==h,path
        rows={r['id']:r for r in a['rows']}
        for cell in m['cells']:
            d=read(LAB/m['result_directory']/(cell['id']+'.json'))
            assert d['status']=='complete' and d['cell']==cell and len(d['records'])==cell['shots']
            assert d['design_sha256']==dh
            for path,h in d['source_sha256'].items():assert sha(ROOT/path)==h,path
            model=make_model(cell['lattice'],cell['L'],cell.get('arrows','stored'))
            dec=DecoderAdapter(model,cell['p'],cell['q'])
            rng=np.random.default_rng(cell['seed'])
            activity=rng.random((cell['shots'],len(model.edges)))<cell['p']
            direction=rng.random(activity.shape)<cell['q'];j=activity*np.where(direction,1,-1)
            risk=[]
            for i,r in enumerate(d['records']):
                assert r['sample_index']==i and r['current']==j[i].tolist()
                assert r['Q']==(dec.D@j[i]).tolist()
                assert r['true_sector']==model.logical_parity((j[i]!=0).astype(np.uint8))
                s=np.array(r['sector_probabilities']);assert abs(s.sum()-1)<1e-12 and np.all(s>=0)
                assert abs(r['bayes_risk']-s.min())<1e-12
                for k,h in enumerate(r['chosen_sectors']):
                    assert abs(r[METRICS[k+1]]-s[1-h])<1e-12
                    assert r['actual_failures'][k]==int(h!=r['true_sector'])
                risk.append([r[k] for k in METRICS])
            assert np.max(abs(np.mean(risk,axis=0)-rows[cell['id']]['risk']['mean']))<1e-12
            oracle=CurrentOracle(model,directed=cell['q']==1)
            i=cell['seed']%cell['shots'];replay=compare_record(model,oracle,dec,j[i]);stored=d['records'][i]
            err=max(abs(replay[k]-stored[k]) for k in METRICS)
            maximum=max(maximum,err);assert err<1e-12
            assert replay['chosen_sectors']==stored['chosen_sectors'] and replay['bp_converged']==stored['bp_converged']
            cell_checks.append({'id':cell['id'],'records':cell['shots'],'replayed_sample':i,'maximum_risk_error':err})
            total+=cell['shots']
    extra=read(LAB/'results/size-bias-distributions-2026-09-18.json')
    assert extra['analysis_source_sha256']==sha(LAB/'scripts/analyze_extension.py')
    for path,h in extra['input_sha256'].items():assert sha(LAB/path)==h,path
    # Independent finite-state check of the derived Bayes continuity bound.
    continuity=[];g=square_graph(3);E=len(g.edges)
    for p in (.1,.3,.46):
        directed=exact_enumeration(g,p,1.);risk1=sum(min(x[0]) for x in directed.values())
        for q in (.5,.75,.9,.97,1.):
            table=exact_enumeration(g,p,q);risk=sum(min(x[0]) for x in table.values())
            TV=.5*sum(np.abs(table.get(Q,[np.zeros(2)])[0]-directed.get(Q,[np.zeros(2)])[0]).sum()
                      for Q in table.keys()|directed.keys())
            bound=1-(1-p*(1-q))**E
            assert abs(risk-risk1)<=TV+1e-12 and TV<=bound+1e-12
            continuity.append({'p':p,'q':q,'risk_difference':risk-risk1,'joint_total_variation':float(TV),'coupling_bound':bound})
    out={'status':'passed','production_cells':len(cell_checks),'production_records':total,
         'replay_maximum_error':maximum,'cells':cell_checks,'finite_continuity_checks':continuity,
         'source_sha256':{str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},'input_sha256':inputs,
         'limits':['Validation verifies the finite model and provenance; it does not establish an asymptotic phase.']}
    assert total==10944 and len(cell_checks)==41
    (LAB/'results/scientific-integrity-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':'passed','records':total,'cells':len(cell_checks),'replay_maximum_error':maximum,'continuity_checks':len(continuity)}))


if __name__=='__main__':main()
