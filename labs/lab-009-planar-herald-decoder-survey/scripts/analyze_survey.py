"""Audit saved vectors and quantify scoped objective/runtime comparisons."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from herald_decoder import honeycomb_graph, make_decoder


def main():
    b=json.loads((LAB/'results/benchmark.json').read_text())
    assert b['status']=='complete' and len(b['rows'])==80 and not b['exceptions']
    receipt=[];replay=[]
    with np.load(LAB/'data/fresh-matched-vectors.npz',allow_pickle=False)as archive:
        for L,p,q in sorted({(r['L'],r['p'],r['q'])for r in b['rows']}):
            g=honeycomb_graph(L);key=f'L{L}_p{p}_q{q}'
            X,S,H=[archive[key+'_'+n]for n in ['errors','syndrome','herald']]
            flags,invalid,pred,prob=[archive[key+'_'+n]for n in ['failure_flags','invalid_flags','predicted_sectors','posterior']]
            n=X.astype(int)@g.check_matrix.toarray().T
            assert np.array_equal(n%2,S) and np.all(n[H==1]>=2)
            if q==0:assert not H.any()
            if q==1:assert np.array_equal(H,n>=2)
            true_sector=X[:,list(g.logical_edges)].sum(1)%2
            assert not invalid.any()
            assert np.array_equal(flags,pred^true_sector[:,None])
            # Exact backend roundoff can select different equal-risk sectors.
            changed = pred[:,2] != pred[:,3]
            assert np.all(abs(prob[changed,2,0]-prob[changed,2,1]) < 1e-9)
            exact=prob[:,2];bayes=exact.min(1)
            for j,method in enumerate(b['methods']):
                row=next(r for r in b['rows']if(r['L'],r['p'],r['q'],r['method'])==(L,p,q,method))
                assert int(flags[:,j].sum())==row['failures']
                regret=1-exact[np.arange(len(X)),pred[:,j]]-bayes
                assert abs(float(regret.mean())-row['conditional_regret_mean'])<1e-12
                d=make_decoder(g,method,p=p,q=q,**({'use_numba':True}if method=='bp_matching'else{}))
                for i in [0,73,199]:
                    result=d.decode(S[i],H[i]);c=result.correction
                    assert np.array_equal(g.true_syndrome(c),S[i])
                    k=g.logical_parity(c)
                    # Different ties are loss equivalent. Non-ties must reproduce sector.
                    if abs(exact[i,0]-exact[i,1])>1e-9:assert k==int(pred[i,j])
                    if hasattr(result,'sector_probabilities') and result.sector_probabilities is not None:
                        assert np.max(abs(result.sector_probabilities-prob[i,j]))<1e-9
                replay.append({'L':L,'p':p,'q':q,'method':method,'records':3,'status':'passed'})
            receipt.append({'L':L,'p':p,'q':q,'shots':len(X),
                            'transfer_posterior_max_error':float(np.max(abs(prob[:,2]-prob[:,3]))),
                            'mps_posterior_max_error':float(np.max(abs(prob[:,2]-prob[:,4]))),
                            'transfer_sector_disagreements':int(changed.sum()),
                            'mps_sector_disagreements':int(np.sum(pred[:,2]!=pred[:,4])),
                            'mean_exact_conditional_risk':float(bayes.mean()),
                            'bayes_risk_se':float(bayes.std(ddof=1)/np.sqrt(len(bayes)))})
    validation=json.loads((LAB/'results/validation.json').read_text())
    sources=list((ROOT/'src/herald_decoder').glob('*.py'))
    result={'status':'passed','new_independent_trials':sum(r['shots']for r in receipt),
            'decoder_evaluations':sum(r['shots']for r in receipt)*len(b['methods']),
            'invalid_corrections':sum(r['invalid']for r in b['rows']),
            'bp_nonconverged':sum(r['nonconverged']for r in b['rows']),
            'weighted_small_records':sum(r['cases']for r in validation['small_oracle']),
            'larger_cross_backend_records':sum(r['shots']for r in validation['larger']),
            'checked_vector_cells':receipt,'current_source_replay':replay,
            'current_source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},
            'input_sha256':{s:hashlib.sha256((LAB/s).read_bytes()).hexdigest()for s in ['results/benchmark.json','results/validation.json','data/fresh-matched-vectors.npz']},
            'scope':'Current-source replay of3 records/cell/method; other fresh records audited from retained inputs/outputs. No heavy acquisition or threshold fitting.'}
    (LAB/'results/survey-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items()if not isinstance(v,(list,dict))})


if __name__=='__main__':main()
