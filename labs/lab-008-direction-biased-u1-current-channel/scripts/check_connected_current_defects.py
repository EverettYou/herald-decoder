"""Connected unit-current witnesses and rigorous path-partition LER bounds."""
from collections import Counter, deque
from fractions import Fraction
from itertools import product
from math import comb, lcm, sqrt, log
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from current_oracle import LAB, ROOT, square_graph, honeycomb_graph, charge_matrix
from herald_decoder.lattice_model import LatticeGraph, Vertex


def enumerate_paths(g, retain=False):
    adjacency = [[] for _ in g.vertices]
    for e, (u, v) in enumerate(g.edges):
        adjacency[u].append((v, e, 1)); adjacency[v].append((u, e, -1))
    left = [v for v in g.boundary_vertices if g.vertices[v].boundary_side == 'left']
    counts, paths = Counter(), []
    calls = 0; start = time.monotonic()
    def visit(v, seen, forward, backward, route):
        nonlocal calls
        calls += 1
        if calls % 10000 == 0 and (calls > 10_000_000 or time.monotonic()-start > 60):
            raise RuntimeError('registered path enumeration cap')
        if g.vertices[v].boundary_side == 'right':
            counts[forward, backward] += 1
            if retain:
                delta = np.zeros(len(g.edges), dtype=np.int8)
                for e, sign in route: delta[e] = sign
                paths.append(delta)
            return
        for u, e, sign in adjacency[v]:
            if seen & (1 << u) or g.vertices[u].boundary_side == 'left': continue
            visit(u, seen | (1 << u), forward+(sign == 1), backward+(sign == -1), route+[(e, sign)])
    for v in left: visit(v, 1 << v, 0, 0, [])
    return counts, paths, {'dfs_calls': calls, 'paths': sum(counts.values()), 'seconds': time.monotonic()-start}


def path_probability(F, B, p, q):
    """Physical probability that the specified unit shift is allowed and wins."""
    a, b, c = 1-p, p*q, p*(1-q)
    if q == 1:
        return a**F*b**B if (F-B)*log(b/a) >= -1e-12 else 0.
    if q == 0:
        return path_probability(B, F, p, 1.)
    eta = log(a*a/(b*c))
    base = F*log(b/a)+B*log(c/a)
    value = 0.
    for u in range(F+1):
        for v in range(B+1):
            if base+(u+v)*eta >= -1e-12:
                value += comb(F, u)*comb(B, v)*c**u*b**v*a**(F+B-u-v)
    return value


def path_partition(counts, p, q, directed_square=False):
    if directed_square:
        assert q == 1 and p <= .5
        return sum(n*(1-p)**B*p**F for (F, B), n in counts.items())
    return sum(n*(path_probability(F, B, p, q)+path_probability(B, F, p, q))
               for (F, B), n in counts.items())


def exact_gate(g, cells, directed_square=False):
    E = len(g.edges); D = charge_matrix(g)
    states = np.array(list(product((0, 1, -1), repeat=E)), dtype=np.int8)
    _, inverse = np.unique(states @ D.T, axis=0, return_inverse=True)
    parity = (states[:, list(g.logical_edges)].sum(axis=1) % 2).astype(int)
    FR = states[:, list(g.logical_edges)].sum(axis=1)
    counts, paths, profile = enumerate_paths(g, retain=True)
    # Each candidate shift is constrained to a simple logical path.
    shifts = np.array(paths+[-x for x in paths])
    shifted = states[:, None, :]+shifts[None, :, :]
    supported = np.all(np.abs(shifted) <= 1, axis=2)
    nplus, nminus = (states == 1).sum(axis=1), (states == -1).sum(axis=1)
    shifted_plus = (shifted == 1).sum(axis=2)
    shifted_minus = (shifted == -1).sum(axis=2)
    results = []
    for p, q in cells:
        pf, qf = Fraction(str(p)), Fraction(str(q))
        w = [1-pf, pf*qf, pf*(1-qf)]
        denominator = lcm(*(x.denominator for x in w))
        A, B, C = [int(x*denominator) for x in w]
        # Integer arithmetic makes every MAP comparison and tie exact.
        weights = {(u, v): A**(E-u-v)*B**u*C**v for u in range(E+1) for v in range(E+1-u)}
        integer_mass = [weights[int(u), int(v)] for u, v in zip(nplus, nminus)]
        mass = np.array([float(Fraction(x, denominator**E)) for x in integer_mass])
        assert abs(mass.sum()-1) < 1e-12
        chosen = {}
        for i, weight in enumerate(integer_mass):
            if weight == 0: continue
            Q = int(inverse[i]); old = chosen.get(Q)
            if old is None or (weight, -int(FR[i]), -i) > (integer_mass[old], -int(FR[old]), -old):
                chosen[Q] = i
        wrong = np.array([x > 0 and parity[i] != parity[chosen[int(inverse[i])]]
                          for i, x in enumerate(integer_mass)])
        witness = np.zeros(len(states), dtype=bool)
        right_to_left = np.zeros(len(states), dtype=bool)
        for i, weight in enumerate(integer_mass):
            if weight == 0: continue
            for s in range(len(shifts)):
                if not supported[i, s]: continue
                shifted_weight = weights[int(shifted_plus[i, s]), int(shifted_minus[i, s])]
                if shifted_weight >= weight:
                    witness[i] = True
                    if s >= len(paths): right_to_left[i] = True
        assert not np.any(wrong & ~witness)
        if directed_square and q == 1 and p <= .5:
            assert not np.any(wrong & ~right_to_left)
        joint = np.zeros((int(inverse.max())+1, 2))
        np.add.at(joint, (inverse, parity), mass)
        bayes = float(np.min(joint, axis=1).sum())
        map_risk = float(mass[wrong].sum())
        union_probability = float(mass[witness].sum())
        upper = path_partition(counts, p, q, directed_square=directed_square and q == 1 and p <= .5)
        assert bayes <= map_risk+1e-12 <= union_probability+2e-12
        assert map_risk <= upper+1e-12
        results.append({'p': p, 'q': q, 'supported_states': int((mass > 0).sum()),
                        'wrong_MAP_states': int(wrong.sum()), 'missing_witnesses': 0,
                        'Bayes_LER': bayes, 'current_MAP_LER': map_risk,
                        'witness_union_probability': union_probability, 'path_sum_upper': float(upper)})
    return {'graph': g.name, 'L': g.size, 'edges': E, 'path_profile': profile, 'cells': results}


def trivalent_motif():
    vertices = tuple([Vertex(float(i), 0.) for i in range(6)] +
                     [Vertex(-1., 0., False, 'left'), Vertex(7., 0., False, 'right')])
    edges = tuple([(i, (i+1) % 6) for i in range(6)] + [(6, 0), (3, 7)])
    return LatticeGraph('trivalent-cycle-control', 0, vertices, edges, frozenset({7}), ())


def honeycomb_geometry(L):
    g = honeycomb_graph(L)
    adjacency = [[] for _ in g.vertices]
    for u, v in g.edges: adjacency[u].append(v); adjacency[v].append(u)
    left = [v for v in g.boundary_vertices if g.vertices[v].boundary_side == 'left']
    right = [v for v in g.boundary_vertices if g.vertices[v].boundary_side == 'right']
    dist = {v: 0 for v in left}; queue = deque(left)
    while queue:
        v = queue.popleft()
        for u in adjacency[v]:
            if u not in dist: dist[u] = dist[v]+1; queue.append(u)
    reachable_right = [v for v in right if v in dist]
    assert reachable_right
    distance = min(dist[v] for v in reachable_right)
    gap = min(g.vertices[v].x for v in right)-max(g.vertices[v].x for v in left)
    max_dx = max(abs(g.vertices[u].x-g.vertices[v].x) for u, v in g.edges)
    assert max(map(len, adjacency)) <= 3 and distance >= gap/max_dx-1e-8
    right_region = [v.x > 1.5*(L-1) for v in g.vertices]
    geometric_cut = {e for e, (u, v) in enumerate(g.edges) if right_region[u] != right_region[v]}
    assert geometric_cut == set(g.logical_edges)
    assert all(not right_region[v] for v in left) and all(right_region[v] for v in right)
    return {'L': L, 'boundary_vertices': len(left)+len(right), 'distance': distance,
            'horizontal_gap': gap, 'max_edge_horizontal_span': max_dx, 'max_degree': max(map(len, adjacency)),
            'unreachable_right_vertices': len(right)-len(reachable_right),
            'isolated_boundary_vertices': sum(not adjacency[v] for v in left+right),
            'logical_cut_separates_rough_boundaries': True}


def exact_directed_square_polynomial(tmax=Fraction(1)):
    g = square_graph(3); E = len(g.edges); D = charge_matrix(g)
    table = {}
    for values in product((0, 1), repeat=E):
        j = np.array(values); Q = tuple(D @ j)
        h = int(j[list(g.logical_edges)].sum()) % 2
        table.setdefault(Q, [[0]*(E+1), [0]*(E+1)])[h][sum(values)] += 1
    selected = [0]*(E+1); failed = []; certificates = []
    for Q, sectors in sorted(table.items()):
        difference = [sectors[0][n]-sectors[1][n] for n in range(E+1)]
        bernstein = [sum((Fraction(difference[j]*comb(k, j), comb(E, j))*tmax**j for j in range(k+1)), Fraction(0))
                     for k in range(E+1)]
        if all(x >= 0 for x in bernstein): smaller = 1
        elif all(x <= 0 for x in bernstein): smaller = 0
        else:
            failed.append({'Q': [int(x) for x in Q], 'difference': difference}); continue
        selected = [x+y for x, y in zip(selected, sectors[smaller])]
        certificates.append({'Q': [int(x) for x in Q], 'smaller_sector': smaller,
                             'difference_in_t': difference, 'bernstein': [str(x) for x in bernstein]})
    coefficients = [sum(selected[n]*comb(E-n, k-n)*(-1)**(k-n) for n in range(k+1)) for k in range(E+1)]
    return {'status': 'certified' if not failed else 'sign_certificate_incomplete',
            'L': 3, 'q': 1, 'p_interval': [0., float(tmax/(1+tmax))], 'charge_records': len(table),
            'selected_activity_counts': selected, 'power_coefficients': coefficients if not failed else None,
            'failed': failed, 'certificates': certificates,
            'extension': 'For this directed U(1) q=1 channel only, for p>1/2 replace p by 1-p using j->1-j, which shifts the observed charge and relabels logical parity.'}


def main():
    started = time.monotonic()
    cells = [(p, q) for p in (.01, .03, .05, .08, .10, .30) for q in (.5, .75, .97, 1.)]
    gates = [exact_gate(square_graph(3), cells+[(.5, 1.), (.7, 1.)], directed_square=True),
             exact_gate(trivalent_motif(), [(p, 1.) for p in (.1, .3, .5, .7, .9)])]
    # Direct short-path enumeration independently verifies the binomial formula.
    max_path_error = 0.
    for n in range(1, 7):
        for F in range(n+1):
            B = n-F; shift = np.array([1]*F+[-1]*B)
            for p, q in ((.08, .5), (.10, .75), (.3, .97), (.3, 1.)):
                total = 0.
                for values in product((0, 1, -1), repeat=n):
                    j = np.array(values); k = j+shift
                    if np.any(abs(k) > 1): continue
                    prob = lambda z: np.prod(np.where(z == 0, 1-p, np.where(z == 1, p*q, p*(1-q))))
                    w, v = prob(j), prob(k)
                    if w > 0 and v >= w*(1-1e-12): total += w
                err = abs(total-path_probability(F, B, p, q)); max_path_error = max(max_path_error, err)
                assert err < 1e-12
                assert abs(path_probability(F, B, p, q)-path_probability(B, F, p, 1-q)) < 1e-12
    path_tables, predictions = [], []
    for L in (3, 4, 5):
        counts, _, profile = enumerate_paths(square_graph(L))
        d = L-1
        assert all(F >= d and F >= B for F, B in counts)
        directed_coefficient = sum(n for (F, B), n in counts.items() if F == d)
        assert directed_coefficient == comb(2*d, d)
        path_tables.append({'L': L, 'profile': profile, 'directed_leading_coefficient': directed_coefficient,
                            'counts': [{'forward': F, 'backward': B, 'count': n} for (F, B), n in sorted(counts.items())]})
        for p, q in cells:
            upper = path_partition(counts, p, q, directed_square=q == 1)
            gamma = sqrt(p*(1-p))*(sqrt(q)+sqrt(1-q))
            affinity_sum = sum(n*gamma**(F+B) for (F, B), n in counts.items())*(1 if q == 1 else 2)
            assert upper <= affinity_sum+1e-10
            predictions.append({'L': L, 'p': p, 'q': q, 'connected_path_sum': float(upper),
                                'LER_upper': min(.5, float(upper)), 'half_Chernoff_path_sum': float(affinity_sum),
                                'gamma': gamma, 'square_sufficient_exponential_condition': 3*gamma < 1})
    activity = json.loads((LAB/'results/current-activity-expansion-2026-09-18.json').read_text())
    baseline = {(r['p'], r['q']): r for r in activity['pilot']['checkpoints'][-1]['cells']}
    comparisons = []
    for row in predictions:
        key = row['p'], row['q']
        if row['L'] != 5 or key not in baseline: continue
        old = baseline[key]; upper = min(old['upper'], row['LER_upper'])
        assert upper >= old['lower']-1e-12
        comparisons.append({**row, 'activity_lower': old['lower'], 'activity_upper': old['upper'],
                            'combined_upper': upper, 'combined_width': upper-old['lower'],
                            'width_reduction': 1-(upper-old['lower'])/(old['upper']-old['lower'])})
    threshold = [{'q': q, 'square_sufficient_p_below': (1-sqrt(1-4/(9*(1+2*sqrt(q*(1-q))))))/2}
                 for q in (.5, .75, .97, 1.)]
    full_polynomial_attempt = exact_directed_square_polynomial()
    polynomial = exact_directed_square_polynomial(Fraction(1, 4))
    if polynomial['status'] == 'certified':
        for row in gates[0]['cells']:
            if row['q'] != 1: continue
            p = min(row['p'], 1-row['p'])
            if p > polynomial['p_interval'][1]: continue
            predicted = sum(c*p**k for k, c in enumerate(polynomial['power_coefficients']))
            assert abs(predicted-row['Bayes_LER']) < 1e-12
    files = [Path(__file__), LAB/'scripts/current_oracle.py', ROOT/'src/herald_decoder/lattice_model.py',
             LAB/'results/current-activity-expansion-2026-09-18.json']
    out = {'status': 'passed', 'scope': 'New connected-current theorem and deterministic path-partition bounds; no replica/CFT calibration or physical threshold fit.',
           'exact_gates': gates, 'exact_directed_L3': polynomial,
           'exact_directed_L3_full_interval_attempt': full_polynomial_attempt,
           'short_path_max_error': max_path_error, 'path_tables': path_tables,
           'predictions': predictions, 'frozen_activity_comparisons': comparisons, 'square_sufficient_region': threshold,
           'honeycomb': {'mu': sqrt(2+sqrt(2)), 'max_directed_mu_gamma': sqrt(2+sqrt(2))/2,
                          'geometry_checks': [honeycomb_geometry(L) for L in (3, 5, 7, 9, 11)],
                          'claim': 'Under exact interior charge and binary logical scoring, q=1 honeycomb Bayes LER decays exponentially for every p in [0,1], for any fixed edge arrows. Analytic path bound plus rigorous honeycomb connective constant; no corresponding all-p square claim.'},
           'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
           'elapsed_seconds': time.monotonic()-started}
    (LAB/'results/connected-current-defects-2026-09-19.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'status': out['status'], 'seconds': out['elapsed_seconds'],
                      'path_profiles': [{k: r[k] for k in ('L', 'profile', 'directed_leading_coefficient')} for r in path_tables],
                      'comparisons': comparisons, 'honeycomb': out['honeycomb'], 'sufficient_region': threshold}, indent=2))


if __name__ == '__main__': main()
