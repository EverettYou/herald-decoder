"""Exact controls for the residual-graph route to a decoding threshold.

The only physical graph is the registered E=8 square L3. The percolation
control shares that graph but is not substituted for the Bayes target.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
import hashlib
import json
import time
import numpy as np
from current_oracle import LAB, ROOT, square_graph, charge_matrix


def reachable(adjacency, seeds):
    seen=set(seeds); todo=list(seeds)
    while todo:
        for v in adjacency[todo.pop()]:
            if v not in seen:
                seen.add(v); todo.append(v)
    return tuple(sorted(seen))


def main():
    start=time.monotonic(); g=square_graph(3); E=len(g.edges)
    assert E==8
    D=charge_matrix(g)
    left={i for i,v in enumerate(g.vertices) if v.boundary_side=='left'}
    right={i for i,v in enumerate(g.vertices) if v.boundary_side=='right'}
    joint=defaultdict(lambda:[0,0]); states=[]
    oriented_clusters=Counter(); bond_clusters=Counter(); crossings=Counter()
    for bits in product((0,1),repeat=E):
        j=np.array(bits,dtype=int); Q=tuple(map(int,D@j))
        sector=int(sum(bits[e] for e in g.logical_edges)%2)
        joint[Q][sector]+=1
        directed=[[] for _ in g.vertices]; bond=[[] for _ in g.vertices]
        for bit,(u,v) in zip(bits,g.edges):
            tail,head=(v,u) if bit else (u,v)
            directed[tail].append(head)
            if bit:
                bond[u].append(v); bond[v].append(u)
        cluster=reachable(directed,left); reverse=reachable(directed,right)
        oriented_clusters[cluster]+=1
        bond_clusters[reachable(bond,left)]+=1
        lr=bool(right.intersection(cluster)); rl=bool(left.intersection(reverse))
        crossings['left_to_right']+=lr; crossings['right_to_left']+=rl
        crossings['either_direction']+=lr or rl; crossings['both_directions']+=lr and rl
        states.append((Q,sector,lr or rl))
    assert oriented_clusters==bond_clusters
    missing=sum(bool(min(joint[Q]))!=cross for Q,sector,cross in states)
    assert missing==0
    rows=[]
    for Q,(a,b) in sorted(joint.items()):
        rows.append({'Q':list(Q),'sector_counts':[a,b],
                     'record_probability':str(Fraction(a+b,2**E)),
                     'conditional_Bayes_risk':str(Fraction(min(a,b),a+b))})
    ambiguous=[r for r in rows if min(r['sector_counts'])>0]
    asymmetric=[r for r in ambiguous if len(set(r['sector_counts']))>1]
    risks=[Fraction(r['conditional_Bayes_risk']) for r in ambiguous]
    bayes=Fraction(sum(min(pair) for pair in joint.values()),2**E)
    union=Fraction(crossings['either_direction'],2**E)
    single=Fraction(crossings['left_to_right'],2**E)
    assert sum(sum(pair) for pair in joint.values())==2**E
    assert bayes<=union/2<=single
    duration=time.monotonic()-start; assert duration<120
    files=[LAB/'scripts/check_square_midpoint.py',LAB/'scripts/current_oracle.py',
           ROOT/'src/herald_decoder/lattice_model.py']
    result={'status':'passed','physical_parameters':{'L':3,'p':'1/2','q':'1'},
            'current_states':2**E,'bond_control_states':2**E,
            'records':len(rows),'ambiguous_records':len(ambiguous),
            'asymmetric_ambiguous_records':len(asymmetric),
            'Bayes_LER_exact':str(bayes),'ambiguous_record_probability_exact':str(union),
            'single_direction_crossing_probability_exact':str(single),
            'min_ambiguous_posterior_risk_exact':str(min(risks)),
            'max_ambiguous_posterior_risk_exact':str(max(risks)),
            'crossing_counts':dict(crossings),'support_equivalence_failures':missing,
            'seed_set_cluster_laws_equal':True,
            'seed_set_cluster_distribution':[{'vertices':list(s),'count':n} for s,n in sorted(oriented_clusters.items())],
            'most_imbalanced_example':min(ambiguous,key=lambda r:Fraction(r['conditional_Bayes_risk'])),
            'record_sector_table':rows,'new_physical_record_samples':0,'decoder_runs':0,
            'elapsed_seconds':duration,
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'inference':'Residual support and the seed-set percolation law are exact. The control does not establish a size-uniform posterior balance or a decoding threshold.'}
    target=LAB/'results/square-midpoint-thermodynamics-2026-09-20.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in
          ('record_sector_table','seed_set_cluster_distribution','source_sha256')},indent=2))


if __name__=='__main__':main()
