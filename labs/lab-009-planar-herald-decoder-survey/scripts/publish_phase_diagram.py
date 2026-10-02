"""Connect the measured diagram to the report, wiki and active registry."""
from pathlib import Path
import json,re
LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parents[1]
def dump(p,o):p.write_text(json.dumps(o,indent=2)+'\n')

def main():
    a=json.loads((LAB/'results/phase-analysis.json').read_text());f=json.loads((LAB/'results/phase-figure-provenance.json').read_text());v=json.loads((LAB/'results/phase-vector-audit.json').read_text());assert v['status']=='passed'
    n=a['new_independent_trials'];rows=a['rows'];roots=a['crossings'];stable=[r for r in roots if r['status']=='window_stable'];validation=json.loads((LAB/'results/phase-method-validation.json').read_text())
    table=['| Fixed q | L24 / L32 crossing p (bootstrap 95%) |','| --- | --- |']
    for q in [0,.5,.8,.85,.86,.875,.89]:
        rr=[r for r in a['crossing_bands']if r['q']==q and r['L_small']==24 and r['L_large']==32]
        values=[]
        for r in sorted(rr,key=lambda r:r['interval'][0]):
            lo,hi=r['interval']
            if r['status']=='single_bootstrap_interval':values.append(f"{r['candidate_values'][0]:.3f} [{lo:.3f}, {hi:.3f}]")
            else:values.append(f"{lo:.3f}–{hi:.3f} (unresolved candidate envelope)")
        table.append(f"| {q:g} | {'; '.join(values) if values else 'No resolved crossing in the sampled confirmation window'} |")
    methods=f"Exact planar sector inference was selected for reliability and measured efficiency. The cached/vectorized sweep changes geometry reuse and weight assembly, preserving the source solver's posterior algebra and numerical gates. On {validation['records']} matched records, including independent transfer comparisons through L=12, the maximum discrepancy was {validation['max_posterior_error']:.3g}. The median profiled sweep time was about 14 ms at L=24 and 29 ms at L=32; these are single-process timings, not whole-campaign throughput."
    scope=f"The fresh sweep contains **{n:,} independent records**, with a full 21×13 pilot grid at L=8,16,24, transition-neighborhood refinement and L=32 confirmation. Here L is the linear patch parameter, with 3L²−1 retained edges, 2L²−2 detectors and shortest logical-path length 2L−1. Both sides of p=1/2 are sampled independently. Deterministic p=0/1 risks are analytic endpoints. The risk estimator is the unconditional mean of min(P₀,P₁), the exact conditional logical Bayes risk. All retained observations, score vectors and numerical gates pass; source replays and an independent L=2 whole-error oracle provide separate checks."
    interpretation="A decodable phase has logical Bayes risk tending to zero as L grows; a non-decodable phase retains positive limiting risk. A fixed-q finite-size threshold estimate is a sign-changing crossing of R_L(p,q) curves. The diagram uses all retained crossing estimates and does not assume p monotonicity, p↔1−p symmetry, a unique crossing or an endpoint at p=1/2. Decreasing/increasing risk across sampled sizes is evidence for the phases, not a proof of the infinite-size limit."
    uncertainty="The pilot chooses refinement windows. Primary crossing means and bootstraps exclude the initial 256 pilot records in refined original cells; new parameter cells and size-32 records have independent streams. Bars give pointwise local-window bootstrap intervals, conditional on finding the observed root orientation. Overlapping or unstable candidate intervals are merged into unresolved envelopes marked ×; an envelope is an interval union, not a pooled confidence interval or evidence for multiple physical transitions. All raw candidates remain in the analysis. Different lattice-size pairs expose systematic drift, which is not included in those bars. Between-node coloring is linear display interpolation; gray denotes an unresolved trend. The dotted line is a conservative analytical sufficient-recovery bound, not a fitted transition. Near-zero coincidences are filtered and cannot exclude undetected transitions."
    caption="*Figure L009.1. Fresh exact logical-ML decoding-phase evidence over the full p,q square. Left: mean conditional Bayes risk at L=24; dots are sampled cells. Middle: approximate pointwise 95% L24−L8 risk-trend evidence and near-maximal risk plateaus (both means ≥0.49), with unresolved regions in gray and the dotted sufficient-recovery bound; the syndrome-only uniform point has exact nonrecovery. Right: confirmation-record crossings for three size pairs, with local-window bootstrap 95% intervals; × marks overlapping/unstable candidate envelopes (not pooled confidence intervals). Finite-size drift and interpolation bias remain separate. Data: [cell vectors](data/phase-risk-cells.csv), [analysis](results/phase-analysis.json), [figure provenance](results/phase-figure-provenance.json).*"
    block='\n'.join(['### L009.5 Full-domain decoding-phase diagram','',methods,'',scope,'','![Exact planar full-domain decoding-phase diagram](figures/exact-planar-phase-diagram.png)',caption,'',interpretation,'']+table+['',uncertainty,'','The independently measured branches show substantial interior-q asymmetry. Perfect heralding has a sufficient recovery guarantee for every p; the diagram does not reflect low-p measurements into high-p values. A larger-size campaign could tighten thermodynamic estimates, particularly near the closing region. [Complete phase analysis and definitions](wiki/phase-diagram.md).',''])
    p=LAB/'REPORT.md';s=p.read_text()
    if '<!-- phase-diagram-start -->'in s:
        start=s.index('<!-- phase-diagram-start -->');end=s.index('<!-- phase-diagram-end -->',start)+len('<!-- phase-diagram-end -->');s=s[:start]+s[end:]
        # Existing section numbers are normalized below after replacement.
    else:s=re.sub(r'Figure L009\.(\d+)',lambda m:'Figure L009.'+str(int(m[1])+1),s)
    pos=s.index('## Evidence')+len('## Evidence');s=s[:pos]+'\n\n<!-- phase-diagram-start -->\n'+block+'<!-- phase-diagram-end -->\n'+s[pos:]
    i=iter(range(1,50));s=re.sub(r'### L009\.\d+',lambda m:'### L009.'+str(next(i)),s)
    s=s.replace('The survey/integration deliverable ends here; neither a new phase sweep nor a physical-channel extension is required to reuse these standard methods.','The phase sweep provides measured finite-size transition evidence; a physical-channel extension remains a separately scoped research task.')
    p.write_text(s)
    definitions=r'''
## Risk and transition definitions

For the same open honeycomb geometry at every linear size,

$$
R_L(p,q)=\mathbb{E}_{s,h}\!\left[\min_{a\in\{0,1\}} P_L(\ell(x)=a\mid s,h;p,q)\right].
$$

Recovery means $\lim_{L\to\infty}R_L(p,q)=0$. Nonrecovery means $\liminf_{L\to\infty}R_L(p,q)>0$. Finite measurements need not decide either limit. A candidate threshold on a fixed-q cut is a sign-changing root

$$
R_L(p,q)-R_{L'}(p,q)=0.
$$

All roots passing the declared diagnostic filters are retained; a root or plateau by itself is not a thermodynamic transition. The registered analysis excludes near-zero coincidences (risk scale below 0.025 or size-difference amplitude below 0.001); those filters and finite grid spacing cannot exclude additional undetected transitions. The conservative recovery condition is

$$
\sqrt{2+\sqrt{2}}\sqrt{p(1-p)}\left(1+\sqrt{1-q}\right)<1.
$$

Its symmetric shape is a sufficient bound, not a complement symmetry of the measured boundary.
'''
    wiki='''---
title: Full-domain exact-planar decoding-phase diagram
page_type: comparison
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/phase-analysis.json
idea_ids: []
---

# Full-domain exact-planar decoding-phase diagram

## Summary

'''+interpretation+definitions+'\n\n## Evidence\n\n'+methods+'\n\n'+scope+'\n\n![Full-domain decoding-phase evidence](../figures/exact-planar-phase-diagram.png)\n\n'+f['semantics']+'\n\n'+'\n'.join(table)+'\n\n'+uncertainty+r'''

## Status

Measured finite-size transition evidence over p,q in [0,1], with explicit unresolved regions. It is not a certified thermodynamic boundary or a universality result. The sufficient recovery region and the perfect-herald edge follow the assumptions in [[statistical-mechanics|Statistical mechanics and recovery bounds]].

The sufficient-bound input is the honeycomb walk-growth constant $\mu=\sqrt{2+\sqrt{2}}$ proved by [Duminil-Copin and Smirnov](https://annals.math.princeton.edu/2012/175-3/p14). The decoding bound is derived separately in [[statistical-mechanics|the local model analysis]], under its stated assumptions.

## Data and reproduction

- [Registered design](../manifests/phase-diagram.json)
- [Per-cell risk and standard errors](../data/phase-risk-cells.csv)
- [All crossings, bootstrap diagnostics and size trends](../results/phase-analysis.json)
- [Matched method reliability and speed](../results/phase-method-validation.json)
- [Whole-error oracle and every retained observation vector](../results/phase-vector-audit.json)
- [Figure inputs, outputs and hashes](../results/phase-figure-provenance.json)

Run the registered scripts in `scripts/README.md`. The packed numeric arrays retain sampled errors for scoring only, exact detector parity, heralds, posterior risk, realized failure bits, timings and solve residuals; errors are never passed to the decoder.

## Related pages

- [[model|Observation law and logical loss]]
- [[planar-ml|Exact planar inference]]
- [[comparison|Decoder objectives and the matched pilot]]
'''
    (LAB/'wiki/phase-diagram.md').write_text(wiki)
    p=LAB/'wiki/statistical-mechanics.md';s=p.read_text()
    if 'phase-diagram.md'not in s:s+='\n## Measured full-domain transition\n\nThe [exact-planar phase diagram](phase-diagram.md) samples the complete p,q square, with confirmation-record crossings, successive lattice-size comparisons, statistical uncertainty and unresolved regions. The sufficient bound above is plotted separately from measured transition estimates.\n'
    p.write_text(s)
    p=LAB/'wiki/index.md';s=p.read_text()
    if 'phase-diagram.md'not in s:s+='\n- [Full-domain decoding-phase diagram](phase-diagram.md): independent full-square sampling, confirmation-record crossings, size drift and unresolved regions.\n'
    p.write_text(s)
    p=LAB/'lab.json';o=json.loads(p.read_text());o['results']=[r for r in o['results']if r['id']not in ['exact-planar-phase-diagram','phase-analysis','phase-vector-audit']]
    o['results'].insert(0,{'id':f['id'],'kind':'figure','format':'image','title':'Exact planar full-domain decoding-phase diagram','summary':f['semantics'],'path':f['files'][0],'presentation':'page'})
    for id,title,file in [('phase-analysis','Finite-size crossing analysis and uncertainty','phase-analysis.json'),('phase-vector-audit','Independent phase data and posterior audit','phase-vector-audit.json')]:o['results'].append({'id':id,'kind':'data','format':'json','title':title,'summary':'Fresh exact-sector full-domain measurements; finite-size interpretation and declared scope.','path':'results/'+file,'presentation':'download'})
    o['current_focus']='Full-domain exact-planar phase diagram measured; final rendered delivery verification active.';o['next_action']='Verify report, diagram, vector exports, analysis links and method wiki in the actual dashboard.';dump(p,o)
    p=ROOT/'labs/labs.json';o=json.loads(p.read_text());m=json.loads((LAB/'lab.json').read_text())
    for e in o['labs']:
        if e['id']==LAB.name:
            for k in list(e):
                if k in m:e[k]=m[k]
    dump(p,o)
    p=LAB/'data/README.md';s=p.read_text()
    if 'phase-risk-cells.csv'not in s:s+='\n## Full-domain phase sweep\n\n`phase-risk-cells.csv` contains independently measured risk/SE for each lattice size and p,q cell. `phase-sweep/*.npz` retains packed errors, syndromes, heralds, exact risk, absolute sector probability, realized failure bits, solve residuals and seconds; use `allow_pickle=False` and unpack only the known graph dimensions. Per-cell JSON gives seeds, record counts, source hashes and confirmation cutoffs. Pilot records used to choose refinement windows are excluded from primary crossing inference at refined original cells.\n\n| Figure | SVG | PDF |\n| --- | --- | --- |\n| Full-domain phase diagram | [SVG](../figures/exact-planar-phase-diagram.svg) | [PDF](../figures/exact-planar-phase-diagram.pdf) |\n'
    p.write_text(s)
    p=LAB/'scripts/README.md';s=p.read_text()
    if 'run_phase_sweep.py'not in s:s+='\n## Full-domain phase diagram\n\n1. `validate_phase_method.py`: matched cached/vectorized planar posterior and speed gate, with independent transfer checks.\n2. `run_phase_sweep.py --workers 6`: resume the registered three-size full-square grid.\n3. `analyze_phase_sweep.py --refine`: freeze selected refinement jobs; archive the broad grid receipt before refinement.\n4. `run_phase_sweep.py --jobs labs/lab-009-planar-herald-decoder-survey/manifests/phase-refinement-jobs.json --workers 6`: acquire independent confirmation records and size-32 checks.\n5. `audit_phase_vectors.py`: verify every retained observation/score vector, whole-error oracle and source replays.\n6. `analyze_phase_sweep.py`: confirmation-only crossing bootstraps, full-domain size-trend evidence and tabular risk data.\n7. `build_phase_diagram.py`, then `publish_phase_diagram.py`: PNG/SVG/PDF, provenance, main report, wiki and active registry.\n8. `verify_delivery.cjs`: verify the complete rendered delivery chain.\n\nThe measurement method is exact planar sector summation with unchanged numerical gates. `phase_runtime.py` caches canonical incidence and vectorizes identical local weights. This support work is frozen after the matched-input promotion gate.\n'
    p.write_text(s)
    print('published phase figure, main report and method wiki')
if __name__=='__main__':main()
