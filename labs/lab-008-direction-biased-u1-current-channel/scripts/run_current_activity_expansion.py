"""Registered deterministic current-activity expansion with a rigorous tail."""
from itertools import combinations, product
from math import comb
from pathlib import Path
import hashlib
import json

import numpy as np

from current_oracle import LAB, ROOT, square_graph, charge_matrix


def binomial_tail(E, p, k):
    return 1.0 - sum(comb(E, j) * p**j * (1-p)**(E-j) for j in range(k+1))


def enumerate_prefix(L, cells, kmax):
    model = square_graph(L)
    D = charge_matrix(model)
    E = len(model.edges)
    logical = set(model.logical_edges)
    table = {}
    checkpoints = []
    states = 0
    for k in range(kmax + 1):
        for support in combinations(range(E), k):
            h = sum(e in logical for e in support) % 2
            columns = D[:, support]
            for signs in product((1, -1), repeat=k):
                signs_array = np.asarray(signs, dtype=np.int8)
                key = (columns @ signs_array).tobytes()
                row = table.setdefault(key, np.zeros((len(cells), 2)))
                plus = sum(s == 1 for s in signs)
                minus = k - plus
                weights = np.array([
                    (1-p)**(E-k) * (p*q)**plus * (p*(1-q))**minus
                    for p, q in cells
                ])
                row[:, h] += weights
                states += 1
        stacked = np.stack(list(table.values()))
        cumulative_mass = stacked.sum(axis=(0, 2))
        lower = np.minimum(stacked[:, :, 0], stacked[:, :, 1]).sum(axis=0)
        rows = []
        for i, (p, q) in enumerate(cells):
            tail = binomial_tail(E, p, k)
            expected_mass = 1-tail
            assert abs(cumulative_mass[i]-expected_mass) < 1e-10
            rows.append({
                'p': p, 'q': q, 'k': k,
                'lower': float(lower[i]),
                'upper': float(min(0.5, lower[i] + tail)),
                'certified_width': float(min(0.5, lower[i] + tail)-lower[i]),
                'omitted_mass_bound': float(tail),
                'cumulative_mass': float(cumulative_mass[i])
            })
        checkpoints.append({'k': k, 'enumerated_states': states, 'records': len(table), 'cells': rows})
    for i in range(len(cells)):
        lowers = [x['cells'][i]['lower'] for x in checkpoints]
        assert all(a <= b+1e-14 for a, b in zip(lowers, lowers[1:]))
    return {'L': L, 'edges': E, 'kmax': kmax, 'checkpoints': checkpoints}


def leading_prediction(L, p, q):
    d = L-1
    if q == 1:
        return comb(2*d, d) * p**d
    if d % 2:
        return None
    coefficient = L * comb(d, d//2) * min(q, 1-q)**(d//2)
    return coefficient * p**(d//2)


def main():
    manifest = LAB/'manifests/current-activity-expansion-2026-09-18.json'
    prior_path = LAB/'results/replica-boundary-theory-2026-09-18.json'
    prior = json.loads(prior_path.read_text())
    reference = {(r['p'], r['q']): r['LER'] for r in prior['square_sector_checks']}
    replay_cells = [(0.1,0.5),(0.1,1.0),(0.3,0.75),(0.46,0.97)]
    replay = enumerate_prefix(3, replay_cells, 12)
    replay_checks = []
    for row in replay['checkpoints'][-1]['cells']:
        expected = reference[(row['p'], row['q'])]
        error = abs(row['lower']-expected)
        assert error < 1e-12 and row['omitted_mass_bound'] < 1e-12
        replay_checks.append({**row, 'reference_LER': expected, 'error': error})

    pilot_cells = [(p,q) for p in (0.02,0.05,0.08) for q in (0.5,0.75,0.97,1.0)]
    pilot = enumerate_prefix(5, pilot_cells, 4)
    final = pilot['checkpoints'][-1]['cells']
    for row in final:
        row['leading_dilute_prediction'] = leading_prediction(5,row['p'],row['q'])
        pred = row['leading_dilute_prediction']
        row['leading_prediction_in_interval'] = bool(pred is not None and row['lower']-1e-14 <= pred <= row['upper']+1e-14)
    max_width = {str(p): max(r['certified_width'] for r in final if r['p']==p) for p in (0.02,0.05,0.08)}
    assert max_width['0.02'] <= 0.002
    assert max_width['0.05'] <= 0.05
    reject_raw_at_008 = max_width['0.08'] > 0.10
    assert reject_raw_at_008

    files = [Path(__file__), manifest, prior_path, LAB/'scripts/current_oracle.py', ROOT/'src/herald_decoder/lattice_model.py']
    out = {
        'status': 'passed_bounded_range_raw_extension_rejected',
        'scope': 'Deterministic positive-current activity truncation; no sampling, decoder, threshold or phase claim.',
        'replay': {'L': 3, 'checks': replay_checks, 'enumerated_states': replay['checkpoints'][-1]['enumerated_states']},
        'pilot': pilot,
        'final_width_by_p': max_width,
        'decision': {
            'accepted_range': 'For L5,k=4 the absolute certified remainder is <=0.000411 at p=.02 and <=0.020354 at p=.05.',
            'rejected_range': 'At p=.08 the raw support-order interval remains wider than .10 (tail .108489), so increasing p by blind enumeration is rejected.',
            'next_method': 'Connected-polymer resummation or a positive transfer calculation that controls repeated local activity more efficiently than a global support cutoff.'
        },
        'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    }
    target = LAB/'results/current-activity-expansion-2026-09-18.json'
    target.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'status':out['status'],'replay_max_error':max(r['error'] for r in replay_checks),'final_width_by_p':max_width},indent=2))


if __name__ == '__main__':
    main()
