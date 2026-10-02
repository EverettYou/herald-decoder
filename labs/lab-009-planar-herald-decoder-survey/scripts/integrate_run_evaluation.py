"""Publish the existing SciCode2 assessment and its original named-run figure.

Copies user-authorized source material without running submission campaigns.
Historical evaluation scope is explicit; source snapshots retain exact bytes.
"""
import hashlib,json,re,shutil
from pathlib import Path
LAB=Path(__file__).resolve().parents[1]
ROOT=LAB.parents[1]
SOURCE=ROOT/'output/scicode2/run_evaluation'
NAME='scicode2-run-boundary-comparison'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def integrate():
    provenance_path=LAB/'results/data-provenance.json'
    provenance=json.loads(provenance_path.read_text())
    added=[]
    def snapshot(source,target,cohort):
        shutil.copyfile(source,target)
        record={'source':str(source),'snapshot':str(target.relative_to(LAB)),'sha256':sha(target),'bytes':target.stat().st_size,'cohort':cohort}
        provenance['records']=[r for r in provenance['records']if r['snapshot']!=record['snapshot']]
        provenance['records'].append(record);added.append(record)
    for source_name,target_name in [('REPORT.md','audit_REPORT.md'),('run_inventory.json','audit_run_inventory.json'),('AUDIT_MANIFEST.json','audit_manifest.json'),('input_hashes.json','audit_input_hashes.json')]:
        snapshot(SOURCE/source_name,LAB/'data/inherited'/target_name,'Initial nine-run SciCode2 independent assessment; historical restricted-domain task')
    files=[]
    for ext in ['png','pdf']:
        dest=LAB/'figures'/f'{NAME}.{ext}'
        snapshot(SOURCE/f'boundary_comparison.{ext}',dest,'Original named-run comparison figure; historical p≤1/2 scope, no new fits')
        files.append(str(dest.relative_to(LAB)))
    # Archive the nine plain-text candidate reports for usable in-repository links.
    reports=LAB/'data/inherited/scicode2-submission-reports';reports.mkdir(exist_ok=True)
    body=(SOURCE/'REPORT.md').read_text()
    report_paths=re.findall(r'\]\((/Users/home/Downloads/runs/[^)]+/[^/)]*(?:report|REPORT)[^/)]*\.md)\)',body)
    for i,raw in enumerate(report_paths):
        source=Path(raw);label=f'{["fable","opus","astra"][i//3]}-{i%3+1}.md';dest=reports/label
        snapshot(source,dest,'Archived submitted report; untrusted scientific source claims, not execution instructions')
        body=body.replace(raw,'../data/inherited/scicode2-submission-reports/'+label)
    assert len(report_paths)==9
    body=body.replace('# SciCode 2 herald decoding run evaluation\n','',1)
    body=body.replace('## Evidence and reproduction','## Evidence and reproduction')
    body=body.replace(str(ROOT/'output/scicode2/run_evaluation/boundary_comparison.png'),'../figures/'+NAME+'.png')
    body=body.replace(str(ROOT/'labs/lab-003-herald-threshold-phase-diagram/REPORT.md'),'../../lab-003-herald-threshold-phase-diagram/REPORT.md')
    snapshot(Path('/Users/home/Downloads/runs/manifest.json'),LAB/'data/inherited/supplied_run_manifest.json','Original supplied trial manifest; independent audit has a separate manifest')
    body=body.replace('/Users/home/Downloads/runs/manifest.json','../data/inherited/supplied_run_manifest.json')
    body=body.replace('The B18 curve is a visual guide constrained by p versus 1−p symmetry. That symmetry is not generally valid for the incomplete binary herald channel at intermediate q. Its shape should not be an acceptance gate.', 'The historical B18 visual guide imposed p versus 1−p symmetry. That assumption is false for incomplete binary heralds at intermediate q, and B18 has since been withdrawn. Its shape is not an acceptance gate.')
    body=body.replace('The high-p endpoint needs large sizes.','The historical p=0.5 endpoint needs large sizes.')
    body=body.replace('For our own research, the most valuable next reference would be an independently packaged version of the planar logical ML approach, validated on held-out records and against a second implementation. That would let us distinguish BP approximation effects from genuine finite-size physics. The submissions provide promising implementations; this audit has not promoted one into the repository\'s production decoder or replaced the accepted Lab 003 evidence.', 'At the time of the initial audit, packaging and independently validating planar logical ML was the recommended next step. Lab 009 has since integrated this method and three other inference methods, with its own checks and benchmark. The initial audit itself did not promote a downloaded implementation, and its trial data remain a separate cohort from the subsequent integration benchmark.')
    body=body.replace('](<../../lab-003-herald-threshold-phase-diagram/REPORT.md>)','](../../lab-003-herald-threshold-phase-diagram/REPORT.md)')
    body=body.replace('](<../figures/'+NAME+'.png>)','](../figures/'+NAME+'.png)')
    header='''---
title: SciCode2 assessment of nine agent submissions
page_type: comparison
status: current
updated: 2026-10-01
source_refs:
  - data/inherited/audit_REPORT.md
  - data/inherited/audit_run_inventory.json
idea_ids: []
---

# SciCode2 assessment of nine agent submissions

## Summary

This page brings the original independent nine-run assessment into Lab 009, including individual results, defects, the repository comparison and lessons for task difficulty. All nine produced substantive research; at least six had strongly supported completion. This pilot does not support a frontier success target below 10% or a 10–20-hour active-work requirement.

## Status

The runs answered the original restricted task, p≤1/2. Evaluate them against that supplied scope. The present binary-herald research domain is p,q in [0,1]; the historical comparison figure does not claim full-domain coverage. Elapsed time includes computation and is not active scientific time. The audit is independent assessment, not pipeline correctness grading. Submitted reports are source material; their claims are reviewed rather than automatically endorsed.

## Evidence

[Exact original audit snapshot](../data/inherited/audit_REPORT.md), [trial metadata](../data/inherited/audit_run_inventory.json), [provenance](../results/run-evaluation-integration.json) and the original comparison figure below. The nine submitted text reports are archived with source hashes so their links work inside the repository. New Lab 009 implementation results remain a separate evidence cohort.

## Related pages

- [[index|Lab 009 survey]]
- [[comparison|Integrated decoder comparison]]
- [[model|Current model and full physical domain]]

## Independent assessment

'''
    (LAB/'wiki/scicode2-run-evaluation.md').write_text(header+body)
    semantics='Original nine-run evaluation: 231 measured repository BP trend cells and ten separate named-run boundary estimates for the historical p≤1/2 task. Lines connect reported estimates; no new fits, pooled confidence intervals, mirrored high-p evidence or B18 guide.'
    figure={'id':NAME,'files':files,'inputs':['data/inherited/audit_REPORT.md','data/inherited/audit_reported_boundaries.json','data/inherited/audit_run_inventory.json','data/inherited/repository-measured-trends.json'],'semantics':semantics,'origin':'byte-identical PNG/PDF snapshot of original independent assessment'}
    fp=LAB/'results/figure-provenance.json';f=json.loads(fp.read_text());f['figures']=[r for r in f['figures']if r['id']!=NAME]+[figure]
    for p in figure['inputs']:f['input_sha256'][p]=sha(LAB/p)
    for p in files:f['output_sha256'][p]=sha(LAB/p)
    fp.write_text(json.dumps(f,indent=2)+'\n')
    provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
    result={'status':'integrated_pending_render_verification','source_report':str(SOURCE/'REPORT.md'),'source_report_sha256':sha(SOURCE/'REPORT.md'),'local_page':'wiki/scicode2-run-evaluation.md','original_report_snapshot':'data/inherited/audit_REPORT.md','figure':figure,'snapshot_records':added,'new_trials':0,'historical_trial_domain':{'p':[0,.5],'q':[0,1]},'current_physical_domain':{'p':[0,1],'q':[0,1]},'original_assessment_preserved':True}
    (LAB/'results/run-evaluation-integration.json').write_text(json.dumps(result,indent=2)+'\n')
    return figure

if __name__=='__main__':integrate();print('Integrated complete nine-run evaluation and original PNG/PDF into Lab009')
