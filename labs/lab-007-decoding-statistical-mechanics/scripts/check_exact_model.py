#!/usr/bin/env python3
"""Finite, exhaustive rational checks for the Lab 007 classical instrument."""
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from math import prod
from pathlib import Path
import hashlib
import json
import sys
import time

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
MANIFEST = LAB / 'manifests/exact-model-checks-2026-09-14.json'
sys.path.insert(0, str(ROOT/'labs/lab-006-sun-bp-theory/scripts'))
from numba_fusion_decoder import group_fusion_distribution

NAMES = {(0,0):'1',(1,0):'3',(0,1):'3bar',(2,0):'6',(0,2):'6bar',
         (1,1):'8',(3,0):'10',(0,3):'10bar',(2,1):'15',(1,2):'15bar',
         (4,0):'15prime',(0,4):'15primebar',(3,1):'24',(1,3):'24bar',(2,2):'27'}

@lru_cache(None)
def fusion(group, plus, minus):
    k = plus + minus
    if group == 'U1': return {str(plus-minus):F(1)}
    mult = {(0,0):1} if group == 'SU3' else {0:1}
    for sign in [1]*plus + [-1]*minus:
        new = defaultdict(int)
        for r,n in mult.items():
            if group == 'SU2':
                new[r+1] += n
                if r: new[r-1] += n
            else:
                a,b = r
                options = [(a+1,b)] + ([(a-1,b+1)] if a else []) + ([(a,b-1)] if b else [])
                if sign == -1:
                    options = [(a,b+1)] + ([(a+1,b-1)] if b else []) + ([(a-1,b)] if a else [])
                for t in options: new[t] += n
        mult = new
    if group == 'SU2': out = {str(r+1):F(n*(r+1),2**k) for r,n in mult.items()}
    else: out = {NAMES[r]:F(n*(r[0]+1)*(r[1]+1)*(sum(r)+2),2*3**k) for r,n in mult.items()}
    assert sum(out.values()) == 1
    return out


def bits(mask,n): return tuple((mask>>a)&1 for a in range(n))
def incidence(g):
    return [[(a,1 if v==head else -1) for a,(tail,head) in enumerate(g['edges']) if v in (tail,head)] for v in g['measured']]
def parity(mask,indices): return sum((mask>>a)&1 for a in indices)%2
def logical(g,mask): return parity(mask,g['logical_edges'])
def syndrome(g,mask): return tuple(parity(mask,[a for a,_ in row]) for row in incidence(g))

def kernel_basis(g):
    n=len(g['edges']);rows=[sum(1<<a for a,_ in row) for row in incidence(g)];pivots=[];r=0
    for c in range(n):
        pivot=next((k for k in range(r,len(rows)) if rows[k]>>c&1),None)
        if pivot is None: continue
        rows[r],rows[pivot]=rows[pivot],rows[r]
        for k in range(len(rows)):
            if k!=r and rows[k]>>c&1: rows[k]^=rows[r]
        pivots.append(c);r+=1
    basis=[]
    for c in range(n):
        if c not in pivots:
            vec=1<<c
            for row,pivot in zip(rows,pivots):
                if row>>c&1: vec|=1<<pivot
            basis.append(vec)
    return basis

def span(basis):
    out=[0]
    for x in basis:out += [y^x for y in out]
    return out


def joint_likelihoods(g,group,hidden):
    """Sum physical states and local record outcomes before adding activity priors."""
    n=len(g['edges']);inc=incidence(g);joint=defaultdict(lambda:defaultdict(F));states=0;branches=0
    for x in product((0,1,-1) if hidden else (0,1),repeat=n):
        states+=1;mask=sum((v!=0)<<a for a,v in enumerate(x));orient=F(1,2**mask.bit_count()) if hidden else F(1)
        choices=[]
        for row in inc:
            leaves=[s*x[a] for a,s in row if x[a]]
            choices.append(list(fusion(group,leaves.count(1),leaves.count(-1)).items()))
        m=syndrome(g,mask)
        for outcomes in product(*choices):
            record=tuple(zip(m,[r for r,w in outcomes]));weight=orient*prod(w for r,w in outcomes)
            joint[record][mask]+=weight;branches+=1
    for mask in range(1<<n): assert sum(d.get(mask,F(0)) for d in joint.values())==1
    return joint,states,branches


def direct_weight(g,group,hidden,mask,record,p):
    n=len(g['edges']);on=[a for a in range(n) if mask>>a&1]
    if syndrome(g,mask)!=tuple(m for m,r in record):return F(0)
    answer=F(0)
    for signs in product((1,-1) if hidden else (1,),repeat=len(on)):
        x=dict(zip(on,signs));w=F(1,2**len(on)) if hidden else F(1)
        for row,(m,r) in zip(incidence(g),record):
            leaves=[s*x[a] for a,s in row if a in x]
            w*=fusion(group,leaves.count(1),leaves.count(-1)).get(r,F(0))
        answer+=w
    return answer*p**len(on)*(1-p)**(n-len(on))


def current_joint(g,hidden,p):
    out=defaultdict(lambda:defaultdict(F));inc=incidence(g);n=len(g['edges'])
    for j in product((0,1,-1) if hidden else (0,1),repeat=n):
        q=tuple(sum(sign*j[a] for a,sign in row) for row in inc)
        mask=sum((v!=0)<<a for a,v in enumerate(j))
        record=tuple((v%2,str(v)) for v in q)
        w=prod((p/2 if hidden else p) if v else 1-p for v in j)
        out[record][mask]+=w
    return out


def analyze(g,group,hidden,joint,p):
    n=len(g['edges']);prior={m:p**m.bit_count()*(1-p)**(n-m.bit_count()) for m in range(1<<n)}
    by_syndrome=defaultdict(list)
    for mask in range(1<<n):by_syndrome[syndrome(g,mask)].append(mask)
    kernel=span(kernel_basis(g));assert set(kernel)==set(by_syndrome[(0,)*len(g['measured'])])
    total=F(0);risk=F(0);marg_risk=F(0);gaps=[];ties=0;checks=0
    current=current_joint(g,hidden,p) if group=='U1' else None
    # Records selected lexicographically before evaluating any transformation.
    selected=set(sorted(joint)[:12])
    for record,lik in joint.items():
        weights={m:w*prior[m] for m,w in lik.items()};z=sum(weights.values());total+=z
        m=tuple(v for v,r in record);feasible=by_syndrome[m];c0=feasible[0]
        assert set(c0^b for b in kernel)==set(feasible)
        sectors=[sum(w for mask,w in weights.items() if logical(g,mask^c0)==h) for h in (0,1)]
        assert sum(sectors)==z and sum(w/z for w in weights.values())==1
        # Change the reference to the last feasible correction, not to the hidden error.
        c1=feasible[-1];permutation=logical(g,c0^c1)
        assert all(sum(w for mask,w in weights.items() if logical(g,mask^c1)==h)==sectors[h^permutation] for h in (0,1))
        if record in selected:
            spin=[F(0),F(0)]
            for b in kernel:
                mask=c0^b;spin[logical(g,b)]+=direct_weight(g,group,hidden,mask,record,p)
            assert spin==sectors;checks+=1
        if current is not None:assert dict(current[record])==weights
        risk+=z-max(sectors)
        marg=[sum(w for mask,w in weights.items() if mask>>a&1)/z for a in range(n)]
        surrogate={mask:prod(marg[a] if mask>>a&1 else 1-marg[a] for a in range(n)) for mask in feasible}
        best=max(surrogate.values());minimizers=[mask for mask,w in surrogate.items() if w==best]
        tied_sectors=sorted({logical(g,mask^c0) for mask in minimizers});ties+=len(tied_sectors)>1
        c=min(minimizers);chosen=logical(g,c^c0);marg_risk+=z-sectors[chosen]
        if len(tied_sectors)==1 and sectors[chosen]<max(sectors):
            gaps.append({'record':record,'reference_mask':c0,'sector_probability':[str(w/z) for w in sectors],
                         'edge_marginals':[str(r) for r in marg],'surrogate_maximizer_masks':minimizers,
                         'chosen_sector':chosen,'conditional_excess_risk':str((max(sectors)-sectors[chosen])/z),
                         'posterior_masks':{str(mask):str(w/z) for mask,w in weights.items()},'evidence_probability':str(z)})
    assert total==1 and marg_risk>=risk
    # Matched information hierarchy, full R versus only m.
    m_sectors=defaultdict(lambda:[F(0),F(0)])
    for record,lik in joint.items():
        m=tuple(v for v,r in record);c0=by_syndrome[m][0]
        for mask,w in lik.items():m_sectors[m][logical(g,mask^c0)]+=w*prior[mask]
    m_risk=sum(sum(s)-max(s) for s in m_sectors.values());assert risk<=m_risk
    return {'fixture':g['id'],'group':group,'orientation':'shared-hidden-fair' if hidden else 'directed','p':str(p),
            'records':len(joint),'joint_normalization':'1','kernel_dimension':len(kernel_basis(g)),
            'spin_sector_checks':checks,'all_record_reference_checks':len(joint),
            'u1_all_record_current_checks':len(joint) if current is not None else 0,
            'bayes_risk':str(risk),'m_only_bayes_risk':str(m_risk),'exact_marginal_matching_risk':str(marg_risk),
            'strict_hardening_gap_records':len(gaps),'cross_sector_ties':ties,
            'first_strict_counterexample':gaps[0] if gaps else None}


def main():
    start=time.monotonic();manifest=json.loads(MANIFEST.read_text());rows=[];quotients=[];source_errors=[]
    for group in manifest['groups']:
        for plus in range(5):
            for minus in range(5-plus):
                exact=fusion(group,plus,minus)
                parent=group_fusion_distribution(group,('fund',)*plus+('anti',)*minus)
                parent={str(int(r)) if group=='U1' else r:w for r,w in parent.items()}
                err=max(abs(float(exact.get(r,F(0)))-parent.get(r,0.)) for r in set(exact)|set(parent))
                assert err<=1e-14;source_errors.append(err)
    for g in manifest['fixtures']:
        for group in manifest['groups']:
            tables={}
            for hidden in (False,True):
                joint,states,branches=joint_likelihoods(g,group,hidden);tables[hidden]=joint
                for p in map(F,manifest['priors']):
                    row=analyze(g,group,hidden,joint,p);row.update(edge_states=states,outcome_branches=branches);rows.append(row)
                print(g['id'],group,'hidden' if hidden else 'directed',states,len(joint),flush=True)
            if group=='SU2':assert tables[False]==tables[True];quotients.append(g['id'])
    # Shared-edge endpoint obstruction: opposite endpoint charges are correlated.
    # At two measured degree-one endpoints, P(-,+ | active)=1/2, not 1/4.
    obstructions={'shared_orientation':{'correct_opposite_endpoint_probability':'1/2','independent_endpoint_probability':'1/4','same_sign_probability':'0'},
        'SU3_baryon':{'m':1,'R':'1','three_fundamental_singlet':str(fusion('SU3',3,0)['1']),
                       'three_antifundamental_singlet':str(fusion('SU3',0,3)['1']),'possible_signed_divergences':[-3,3]},
        'SU2_degree_four_singlet':str(fusion('SU2',2,2)['1']),
        'SU3_degree_four_balanced_singlet':str(fusion('SU3',2,2)['1'])}
    # On a cycle with all singlet records the active/full-loop likelihood is explicit.
    g=manifest['fixtures'][1];rec=tuple((0,'1') for _ in g['measured']);loop={}
    for group in ('SU2','SU3'):
        actual=direct_weight(g,group,True,15,rec,F(1,3))/F(1,3)**4
        expected=F(1,4)**4 if group=='SU2' else F(2,2**4*3**8)
        assert actual==expected;loop[group]=str(actual)
    relevant=[r for r in rows if r['first_strict_counterexample']]
    out={'status':'passed','manifest':str(MANIFEST.relative_to(ROOT)),
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'parent_source_sha256':{name:hashlib.sha256((ROOT/'labs/lab-006-sun-bp-theory/scripts'/name).read_bytes()).hexdigest() for name in ('sun_fusion_bp.py','numba_fusion_decoder.py')},
         'arithmetic':'fractions.Fraction; no sampling uncertainty','rows':rows,
         'summary':{'matrix_rows':len(rows),'local_distribution_comparisons':len(source_errors),'max_parent_float_error':max(source_errors),
                    'SU2_joint_quotient_fixtures':quotients,'spin_sector_checks':sum(r['spin_sector_checks'] for r in rows),
                    'reference_checks':sum(r['all_record_reference_checks'] for r in rows),
                    'U1_current_checks':sum(r['u1_all_record_current_checks'] for r in rows),
                    'rows_with_strict_hardening_counterexample':len(relevant)},
         'obstructions':obstructions,'singlet_cycle_full_activity_likelihood':loop,
         'wall_seconds':time.monotonic()-start,'limits':['finite motifs, not full lattice sizes','no transition or BKT fit','no new BP performance estimate']}
    (LAB/'results/exact-model-checks-2026-09-14.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out['summary'],indent=2));print('seconds',out['wall_seconds'])

if __name__=='__main__':main()
