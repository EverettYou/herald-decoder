#!/usr/bin/env python3
"""Bounded exact audit plus canonical-arrow inspection, not a LER sweep."""
from collections import defaultdict, deque
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json
import sys

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from herald_decoder.lattice_model import square_graph, honeycomb_graph


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weight(j, p, q):
    w = F(1)
    for value in j:
        w *= 1-p if value == 0 else p*(q if value == 1 else 1-q)
    return w


def joint(edges, measured, cut, p, q):
    table = defaultdict(lambda: [F(0), F(0)])
    for j in product((-1, 0, 1), repeat=len(edges)):
        charges = tuple(sum(((v == b)-(v == a))*t for (a,b),t in zip(edges,j)) for v in measured)
        table[charges][sum(abs(j[a]) for a in cut) % 2] += weight(j,p,q)
    return {Q: z for Q,z in table.items() if sum(z)}


def geometry_audit(g):
    adjacency = defaultdict(list)
    for a,(u,v) in enumerate(g.edges):
        adjacency[u].append((v,1,a))
        adjacency[v].append((u,-1,a))
    psi, parent = {}, {}
    components = 0
    for root in sorted(adjacency):
        if root in psi:
            continue
        components += 1
        psi[root] = 0
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v,delta,a in adjacency[u]:
                if v not in psi:
                    psi[v] = psi[u] + delta
                    parent[v] = (u,a,delta)
                    queue.append(v)
    residuals = [(a,1-(psi[v]-psi[u])) for a,(u,v) in enumerate(g.edges) if psi[v]-psi[u] != 1]
    witness = None
    if residuals:
        edge,residual = residuals[0]
        u,v = g.edges[edge]
        def ancestry(x):
            chain=[]
            while x in parent:
                par,a,d = parent[x]
                chain.append((x,par,a,d))
                x=par
            return chain
        # Closed walk u->v followed by tree v->root->u; common suffix cancels.
        signed = defaultdict(int)
        signed[edge] += 1
        for x,par,a,d in ancestry(v): signed[a] -= d
        for x,par,a,d in ancestry(u): signed[a] += d
        signed = {a:s for a,s in signed.items() if s}
        divergence=defaultdict(int)
        for a,s in signed.items():
            tail,head=g.edges[a]
            divergence[head] += s
            divergence[tail] -= s
        assert all(x == 0 for x in divergence.values())
        assert sum(signed.values()) == residual
        witness={'signed_edge_cycle': sorted(signed.items()), 'circulation_in_units_of_h': residual}
    return {'lattice':g.name,'L':g.size,'edges':len(g.edges),'incident_vertices':len(adjacency),
            'cycle_rank':len(g.edges)-len(adjacency)+components,
            'pure_gradient':not residuals,'inconsistent_chords_in_this_basis':len(residuals),
            'all_edges_increase_vertex_id':all(u<v for u,v in g.edges),
            'witness':witness,
            'boundary_potential_values_if_gradient':sorted({psi[v] for v in g.boundary_vertices if v in psi}) if not residuals else None}


def main():
    config_path=LAB/'manifests/sector-prediction-audit-2026-09-18.json'
    config=json.loads(config_path.read_text())
    p=F(config['p']); biases=list(map(F,config['bias_q']))
    fixtures=[('rough-path',[(0,1),(1,2)],[1],[0]),
              ('gradient-square',[(0,1),(1,2),(3,2),(0,3)],list(range(4)),[0]),
              ('circulating-square',[(0,1),(1,2),(2,3),(3,0)],list(range(4)),[0])]
    rows=[]; state_checks=0
    for name,edges,measured,cut in fixtures:
        tables={q:joint(edges,measured,cut,p,q) for q in biases}
        for q,table in tables.items():
            assert sum(sum(z) for z in table.values()) == 1
            reflected={tuple(-v for v in Q):z for Q,z in tables[1-q].items()}
            assert table == reflected
            risk=sum(min(z) for z in table.values())
            from_posterior=sum(sum(z)*(1-abs(z[0]-z[1])/sum(z))/2 for z in table.values())
            assert risk == from_posterior
            rows.append({'fixture':name,'p':str(p),'bias_q':str(q),'records':len(table),
                         'binary_sector_bayes_risk':str(risk),'risk_float':float(risk),
                         'Q0_sector_weights':list(map(str,table.get((0,)*len(measured),[F(0),F(0)])))})
        # q=4/5: sqrt(q(1-q))=2/5, C=14/15, p_eff=2/7, exp(h)=2.
        for j in product((-1,0,1),repeat=len(edges)):
            assert weight(j,p,F(4,5)) == F(14,15)**len(edges)*weight(j,F(2,7),F(1,2))*F(2)**sum(j)
            state_checks+=1
        if name=='rough-path':
            for q,table in tables.items():
                assert table[(0,)][0] == (1-p)**2
                assert table[(0,)][1] == p**2*(q*q+(1-q)**2)
    geometry=[geometry_audit(factory(size)) for factory in (square_graph,honeycomb_graph) for size in config['canonical_sizes']]
    inherited_path=ROOT/'labs/lab-006-sun-bp-theory/results/a9-orientation-analysis.json'
    inherited=json.loads(inherited_path.read_text())
    assert digest(ROOT/'src/herald_decoder/lattice_model.py') == inherited['source_sha256']['src/herald_decoder/lattice_model.py']
    slices=[{'lattice':s['lattice'],'cells':s['cells'],'significant_increases':s['holm_significant_increases'],
             'p030_slice':s['p030_slice']} for s in inherited['summaries'] if s['group']=='U1']
    source_paths=[Path(__file__),ROOT/'src/herald_decoder/lattice_model.py',inherited_path,config_path]
    out={'status':'passed','scope':config['scope'],'source_sha256':{str(path.relative_to(ROOT)):digest(path) for path in source_paths},
         'arithmetic':'Fraction for all motif probabilities; integer potential and cycle arithmetic',
         'canonical_lattice_hash_matches_parent_production':True,
         'effective_prior_state_checks':state_checks,'motif_rows':rows,'canonical_arrow_audit':geometry,
         'inherited_U1_p030':slices,
         'limits':['Finite motif parity is not a two-dimensional threshold measurement.',
                   'The chord count depends on the spanning tree; a nonzero witnessed circulation and the pure-gradient verdict do not.',
                   'Inherited production data were read, not reacquired; no intermediate-bias LER points exist in this audit.']}
    (LAB/'results/sector-prediction-audit-2026-09-18.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'effective_prior_state_checks':state_checks,'motif_rows':len(rows),'geometry':geometry,
                     'inherited_slices':[(s['lattice'],len(s['p030_slice'])) for s in slices]},indent=2))


if __name__=='__main__': main()
