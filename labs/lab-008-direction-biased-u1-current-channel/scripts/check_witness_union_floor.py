"""Exact floors on the full witness-event union, NOT on Bayes LER."""
from collections import Counter
from fractions import Fraction
from math import lcm
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from check_connected_current_defects import enumerate_paths, path_probability
from current_oracle import LAB, ROOT, square_graph
from herald_decoder.lattice_model import LatticeGraph

CELLS = [(Fraction(str(p)), Fraction(str(q)))
         for p in (.05, .08, .30) for q in (.5, .75)]


def strip(parent, rows):
    selected = [i for i, v in enumerate(parent.vertices) if v.y in rows]
    mapping = {v: i for i, v in enumerate(selected)}
    ids = [e for e, (u, v) in enumerate(parent.edges) if u in mapping and v in mapping]
    g = LatticeGraph('square-horizontal-strip', parent.size,
                     tuple(parent.vertices[v] for v in selected),
                     tuple((mapping[parent.edges[e][0]], mapping[parent.edges[e][1]]) for e in ids),
                     frozenset(i for i, e in enumerate(ids) if e in parent.logical_edges), ())
    return g, ids


def analyze(g):
    E = len(g.edges)
    assert 3**E <= 200000
    codes = np.arange(3**E, dtype=np.int64)
    states = np.array([0, 1, -1], dtype=np.int8)[(codes[:, None] // (3**np.arange(E))) % 3]
    plus, minus = (states == 1).sum(axis=1), (states == -1).sum(axis=1)
    state_codes = plus*(E+1)+minus
    _, paths, profile = enumerate_paths(g, retain=True)
    event_tables = []
    for delta in paths + [-x for x in paths]:
        shifted = states + delta
        allowed = np.all(np.abs(shifted) <= 1, axis=1)
        new_codes = (shifted == 1).sum(axis=1)*(E+1)+(shifted == -1).sum(axis=1)
        event_tables.append((allowed, new_codes))
    counts = np.bincount(state_codes, minlength=(E+1)**2)
    rows = []
    for p, q in CELLS:
        raw = (1-p, p*q, p*(1-q))
        den = lcm(*(x.denominator for x in raw))
        A, B, C = [int(x*den) for x in raw]
        weights = np.array([A**(E-u-v)*B**u*C**v if u+v <= E else 0
                            for u in range(E+1) for v in range(E+1)], dtype=object)
        assert sum(int(n)*int(w) for n, w in zip(counts, weights)) == den**E
        mass = weights[state_codes]
        ge = np.zeros(len(states), dtype=bool)
        gt = np.zeros(len(states), dtype=bool)
        for allowed, new_codes in event_tables:
            new = weights[new_codes]
            ge |= allowed & (new >= mass)
            gt |= allowed & (new > mass)
        def probability(mask):
            c = np.bincount(state_codes[mask], minlength=(E+1)**2)
            return Fraction(sum(int(n)*int(w) for n, w in zip(c, weights)), den**E)
        union, strict = probability(ge), probability(gt)
        # Transform both the prior and the event for q -> 1-q.
        reflected_weights = weights.reshape(E+1,E+1).T.reshape(-1)
        reflected_ge = np.zeros(len(states), dtype=bool)
        for allowed,new_codes in event_tables:
            reflected_ge |= allowed & (reflected_weights[new_codes] >= reflected_weights[state_codes])
        reflected_ids = np.where(states == 1, 2, np.where(states == -1, 1, 0)) @ (3**np.arange(E))
        assert np.array_equal(reflected_ge, ge[reflected_ids])
        reflected_counts = np.bincount(state_codes[reflected_ge], minlength=(E+1)**2)
        reflected_mass = sum(int(n)*int(w) for n,w in zip(reflected_counts,reflected_weights))
        assert Fraction(reflected_mass, den**E) == union
        rows.append({'p':float(p), 'q':float(q), 'union':float(union), 'union_exact':str(union),
                     'strict_union':float(strict), 'strict_union_exact':str(strict),
                     'equal_only_union':float(union-strict),
                     'union_state_counts':[[int(i//(E+1)),int(i%(E+1)),int(n)]
                                          for i,n in enumerate(np.bincount(state_codes[ge], minlength=(E+1)**2)) if n]})
    return {'edges':E, 'states':len(states), 'geometric_paths':len(paths), 'cells':rows}


def main():
    start = time.monotonic()
    old = json.loads((LAB/'results/connected-current-defects-2026-09-19.json').read_text())
    baseline = json.loads((LAB/'results/connected-defect-overlap-2026-09-19.json').read_text())
    full = analyze(square_graph(3))
    old_rows = {(c['p'],c['q']):c for c in old['exact_gates'][0]['cells']}
    for c in full['cells']:
        previous = old_rows[c['p'],c['q']]
        assert abs(c['union']-previous['witness_union_probability']) < 5e-14
        c['Bayes_LER'] = previous['Bayes_LER']
        c['current_MAP_LER'] = previous['current_MAP_LER']
        c['union_over_Bayes'] = c['union']/c['Bayes_LER']
    parent = square_graph(5)
    groups = [strip(parent, rows) for rows in ((0.,1.),(2.,3.),(4.,))]
    assert all(set(a[1]).isdisjoint(b[1]) for i,a in enumerate(groups) for b in groups[i+1:])
    # Each strip path remains a full-square charge-preserving logical shift.
    for g, ids in groups:
        _, paths, _ = enumerate_paths(g, retain=True)
        for delta in paths:
            full_delta = np.zeros(len(parent.edges), dtype=int); full_delta[ids] = delta
            divergence = Counter()
            for e,(u,v) in enumerate(parent.edges):
                divergence[u] -= int(full_delta[e]); divergence[v] += int(full_delta[e])
            assert all(divergence[v] == 0 for v in parent.detector_vertices)
            assert int(full_delta[list(parent.logical_edges)].sum()) % 2 == 1
    two, one = analyze(groups[0][0]), analyze(groups[2][0])
    assert groups[0][0].edges == groups[1][0].edges
    strongest = {(c['p'],c['q']):c['new_strongest_upper'] for c in baseline['L5']['cells']}
    rows = []
    for c2,c1 in zip(two['cells'],one['cells']):
        U2,U1 = Fraction(c2['union_exact']),Fraction(c1['union_exact'])
        # At these cells the two one-row shift events are disjoint: the only
        # common supported current is the vacuum, which is not improving.
        p,q=c1['p'],c1['q']
        direct = path_probability(4,0,p,q)+path_probability(0,4,p,q)
        assert abs(direct-float(U1)) < 5e-14
        lower = 1-(1-U2)**2*(1-U1)
        upper = strongest.get((p,q), .5)
        rows.append({'p':p,'q':q,'witness_union_floor':float(lower), 'floor_exact':str(lower),
                     'previous_Bayes_upper':upper,'floor_minus_previous_upper':float(lower)-upper,
                     'excludes_improvement_from_unchanged_union':float(lower)>upper+1e-12,
                     'primary':p in (.05,.08)})
    elapsed=time.monotonic()-start
    assert elapsed < 120
    files=['scripts/check_witness_union_floor.py','scripts/check_connected_current_defects.py',
           'results/connected-current-defects-2026-09-19.json','results/connected-defect-overlap-2026-09-19.json']
    out={'status':'passed','scope':'Exact lower bounds on a witness envelope; never Bayes lower bounds.',
         'L3_full':full,'two_row_strip':two,'one_row_strip':one,'L5':rows,
         'strip_parent_edge_ids':[x[1] for x in groups], 'new_record_samples':0,
         'elapsed_seconds':elapsed,
         'source_sha256':{str((LAB/f).relative_to(ROOT)):hashlib.sha256((LAB/f).read_bytes()).hexdigest() for f in files}}
    path=LAB/'results/witness-union-floor-2026-09-19.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'L5':rows,'seconds':elapsed},indent=2))


if __name__ == '__main__':
    main()
