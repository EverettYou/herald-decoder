"""Small, literal check of vertex factors -> dimer weights -> Pfaffian.

The closed four-vertex planar K4 is an explanatory fixture, not an extension
of the production honeycomb geometry API. No Monte Carlo data are acquired.
"""
import itertools
import json
import hashlib
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from herald_decoder._planar import pfaffian_orientation


def matching_sum(nodes, edges):
    @lru_cache(None)
    def visit(remaining):
        if not remaining:
            return 1.0
        i, *others = remaining
        return sum(edges.get(tuple(sorted((i, j))), 0.0)
                   * visit(tuple(k for k in others if k != j)) for j in others)
    return visit(tuple(nodes))


def pfaffian(matrix):
    @lru_cache(None)
    def visit(remaining):
        if not remaining:
            return 1.0
        i, *others = remaining
        return sum((-1)**position * matrix[i, j]
                   * visit(tuple(k for k in others if k != j))
                   for position, j in enumerate(others))
    return visit(tuple(range(len(matrix))))


def local_fixture(signature):
    g0, g1, g2, g3 = signature
    spokes = [g1, g2, g3]
    if any(spokes):
        selected = next(i for i, value in enumerate(spokes) if value > 0)
        edges = {(i, 3): float(value) for i, value in enumerate(spokes)}
        opposite = [(1, 2), (0, 2), (0, 1)]
        edges[opposite[selected]] = g0 / spokes[selected]
        private = [3]
    else:
        edges = {(0, 3): float(g0), (1, 4): 1.0, (2, 5): 1.0}
        private = [3, 4, 5]
    values = {}
    for bits in itertools.product((0, 1), repeat=3):
        nodes = [i for i in range(3) if not bits[i]] + private
        got = matching_sum(nodes, edges)
        expected = dict(zip([(0,0,0),(0,1,1),(1,0,1),(1,1,0)], signature)).get(bits, 0)
        assert np.isclose(got, expected, rtol=0, atol=1e-12)
        values[''.join(map(str, bits))] = got
    return {'site_weights': signature, 'matching_signatures': values}


def global_fixture(rng):
    xy = np.array([(0,0),(2,0),(1,np.sqrt(3)),(1,np.sqrt(3)/3)])
    physical_edges = list(itertools.combinations(range(4), 2))
    incident = [[e for e, uv in enumerate(physical_edges) if v in uv] for v in range(4)]
    edge_factors = rng.uniform(.2, 1.7, size=(6,2))
    site_factors = [rng.uniform(.2, 2.0, size=(2,2,2)) for _ in range(4)]
    reference = rng.integers(0, 2, size=6)
    syndrome = np.array([reference[inc].sum()%2 for inc in incident])
    x = np.array(list(itertools.product((0,1), repeat=6)))
    weight = np.prod(edge_factors[np.arange(6), x], axis=1)
    for v, inc in enumerate(incident):
        weight *= site_factors[v][tuple(x[:,inc].T)]
    weight[np.any(np.stack([x[:,inc].sum(1)%2 for inc in incident],axis=1)!=syndrome,axis=1)] = 0
    literal_z = float(weight.sum())
    relative_edge_probability = float(weight[(x[:,0]^reference[0])==1].sum()/literal_z)

    positions, ports, centers, ordering = [], {}, {}, {}
    for v in range(4):
        ordering[v] = sorted(incident[v], key=lambda e: np.arctan2(*(xy[sum(physical_edges[e])-v]-xy[v])[::-1]))
        for e in ordering[v]:
            neighbor = sum(physical_edges[e])-v
            direction = xy[neighbor]-xy[v]
            ports[v,e] = len(positions)
            positions.append(xy[v]+.12*direction/np.linalg.norm(direction))
        centers[v] = len(positions)
        positions.append(np.mean([positions[ports[v,e]] for e in ordering[v]],axis=0))
    edges, weights = [], []
    def add(u,v,w):
        edges.append((u,v)); weights.append(float(w))
    for e,(u,v) in enumerate(physical_edges):
        add(ports[u,e],ports[v,e],edge_factors[e,1-reference[e]]/edge_factors[e,reference[e]])
    patterns = np.array([[0,0,0],[0,1,1],[1,0,1],[1,1,0]])
    for v in range(4):
        order = ordering[v]
        physical = patterns ^ reference[order]
        axes = [order.index(e) for e in incident[v]]
        g = site_factors[v][tuple(physical[:,axes].T)]
        legs = [ports[v,e] for e in order]
        for i in range(3): add(legs[i],centers[v],g[i+1])
        add(legs[1],legs[2],g[0]/g[1])
        add(legs[0],legs[2],0)
        add(legs[0],legs[1],0)
    edges = np.array(edges)
    signs = pfaffian_orientation(np.array(positions),edges)
    matrix = np.zeros((16,16))
    for (i,j),w,sign in zip(edges,weights,signs):
        matrix[i,j] += sign*w;matrix[j,i] -= sign*w
    pf = pfaffian(matrix)
    dimers = matching_sum(range(16),dict(zip(map(lambda uv:tuple(sorted(uv)),edges),weights)))
    constant = float(np.prod(edge_factors[np.arange(6),reference]))
    i,j = edges[0]
    solve = np.linalg.solve(matrix,np.eye(16)[:,i])
    occupancy = float(matrix[i,j]*solve[j])
    assert np.isclose(abs(pf),dimers,rtol=1e-11,atol=1e-11)
    assert np.isclose(constant*abs(pf),literal_z,rtol=1e-11,atol=1e-11)
    assert np.isclose(occupancy,relative_edge_probability,rtol=1e-11,atol=1e-11)
    return {'physical_edges':6,'auxiliary_nodes':16,'literal_partition':literal_z,
            'reference_prior_constant':constant,'dimer_partition':dimers,'pfaffian':pf,
            'partition_relative_error':abs(constant*abs(pf)/literal_z-1),
            'literal_relative_edge_probability':relative_edge_probability,
            'inverse_matrix_occupancy':occupancy,
            'occupancy_absolute_error':abs(occupancy-relative_edge_probability)}


if __name__ == '__main__':
    rng = np.random.default_rng(100901)
    local = [local_fixture(g) for g in [(2,3,5,7),(2,0,5,7),(0,3,0,7),(2,0,0,0)]]
    whole = [global_fixture(rng) for _ in range(8)]
    result = {'status':'passed','seed':100901,'local_cases':local,'global_cases':whole,
              'validator_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'orientation_source_sha256':hashlib.sha256((ROOT/'src/herald_decoder/_planar.py').read_bytes()).hexdigest(),
              'scope':'Literal local matching sums and eight closed planar K4 fixtures; no production geometry or numerical-stability extension.'}
    target = Path(__file__).resolve().parents[1]/'results/site-gadget-partition-review.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'passed','local_cases':len(local),'global_cases':len(whole),
                      'maximum_partition_relative_error':max(c['partition_relative_error'] for c in whole),
                      'maximum_occupancy_absolute_error':max(c['occupancy_absolute_error'] for c in whole)}))
