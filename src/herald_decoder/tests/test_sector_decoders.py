"""Regression tests using literal posterior sums independent of the new solvers."""
import unittest
from dataclasses import replace

import numpy as np
from herald_decoder import (
    DECODER_METHODS, HeraldBeliefMatchingDecoder, HeraldMPSDecoder,
    HeraldTransferMLDecoder, PlanarParitySolver, honeycomb_graph, square_graph,
    make_decoder, sample_observation,
)

METHODS = ('configuration_map', 'planar_ml', 'transfer_ml', 'mps_ml')


def enumerate_record(g, p, s, factors):
    E = len(g.edges)
    X = ((np.arange(2**E)[:, None] >> np.arange(E)) & 1).astype(np.uint8)
    N = X.astype(int) @ g.check_matrix.toarray().T
    logw = X.sum(1)*np.log(p) + (E-X.sum(1))*np.log1p(-p)
    with np.errstate(divide='ignore'):
        for v, f in zip(g.detector_vertices, factors):
            logw += np.log(f[tuple(X[:, list(g.incident_edges[v])].T)])
    logw[np.any(N % 2 != s, axis=1)] = -np.inf
    weights = np.exp(logw-logw.max())
    ell = X[:, list(g.logical_edges)].sum(1) % 2
    probs = np.bincount(ell.astype(int), weights=weights, minlength=2)
    return probs/probs.sum(), set(ell[np.isclose(logw, logw.max(), atol=1e-9, rtol=0)].astype(int))


class SectorDecoderTests(unittest.TestCase):
    def test_literal_weighted_oracle_and_endpoints(self):
        rng = np.random.default_rng(77)
        g = honeycomb_graph(2)
        for p, q in ((.2, .5), (.4, .9), (.5, 0), (.5, 1), (.7,0), (.8,.5), (.95,.9), (.8,1), (1e-80, .5), (1-1e-14,.5)):
            # Use a deliberately improbable but supported record for the extreme prior.
            obs = sample_observation(g, rng, p=.4, q=q)
            factors = []
            for v, h in zip(g.detector_vertices, obs.herald):
                n = np.indices((2,)*len(g.incident_edges[v])).sum(0)
                factors.append(q*(n >= 2) if h else 1-q*(n >= 2))
            expected, map_sectors = enumerate_record(g, p, obs.syndrome, factors)
            for method in METHODS:
                d = make_decoder(g, method, p=p, q=q)
                result = d.decode(obs.syndrome, obs.herald)
                np.testing.assert_array_equal(g.true_syndrome(result.correction), obs.syndrome)
                if method == 'configuration_map':
                    self.assertIn(g.logical_parity(result.correction), map_sectors)
                else:
                    np.testing.assert_allclose(result.sector_probabilities, expected, atol=1e-9, rtol=0)
        for method in METHODS:
            d = make_decoder(g, method, p=0, q=.5)
            np.testing.assert_array_equal(d.decode(np.zeros(6), np.zeros(6)).correction, np.zeros(11))
            with self.assertRaises(ValueError):
                d.decode(np.ones(6), np.zeros(6))

    def test_deterministic_high_prior_support(self):
        g=honeycomb_graph(2);x=np.ones(len(g.edges),np.uint8)
        s=g.true_syndrome(x)
        for method in METHODS:
            for q in (0,.5,1):
                h=np.full(len(s),int(q==1),np.uint8)
                result=make_decoder(g,method,p=1,q=q).decode(s,h)
                self.assertEqual(g.logical_parity(result.correction),g.logical_parity(x))
                if method!='configuration_map':
                    self.assertEqual(result.sector_probabilities[g.logical_parity(x)],1)
            with self.assertRaises(ValueError):make_decoder(g,method,p=1,q=1).decode(s,np.zeros(len(s)))
            with self.assertRaises(ValueError):make_decoder(g,method,p=1,q=.5).decode(s^1,np.zeros(len(s)))
            for p in (-.01,1.01):
                with self.assertRaises(ValueError):make_decoder(g,method,p=p,q=.5)

    def test_perfect_herald_counts_and_signed_costs(self):
        rng = np.random.default_rng(81)
        for p in (.2, .5, .8):
            g = honeycomb_graph(5)
            d = make_decoder(g, 'configuration_map', p=p, q=1)
            for _ in range(10):
                obs = sample_observation(g, rng, p=p, q=1)
                result = d.decode(obs.syndrome, obs.herald)
                counts = g.degrees(result.correction)[list(g.detector_vertices)]
                np.testing.assert_array_equal(counts, obs.syndrome + 2*obs.herald)
        g = honeycomb_graph(2)
        d = make_decoder(g, 'configuration_map', p=.3, q=.5)
        self.assertTrue(np.any(d.edge_weights(np.ones(6, np.uint8)) < 0))

    def test_generic_factors_and_reference_invariance(self):
        rng = np.random.default_rng(78)
        g = honeycomb_graph(2)
        d = PlanarParitySolver(g, p=.3)
        for _ in range(12):
            s = rng.integers(0, 2, len(g.detector_vertices), dtype=np.uint8)
            factors = [rng.uniform(.01, 1, size=(2,)*len(g.incident_edges[v])) for v in g.detector_vertices]
            expected, _ = enumerate_record(g, .3, s, factors)
            for ref in (d.representative(s, 0), d.representative(s, 1)):
                got, _ = d.posterior_from_factors(s, factors, ref)
                np.testing.assert_allclose(got, expected, atol=1e-9, rtol=0)
        ref = d.representative(s, 0).astype(float); ref[0] = 256
        with self.assertRaises(ValueError):
            d.posterior_from_factors(s, factors, ref)

    def test_su2_full_irrep_local_factor(self):
        # Maximally mixed n spin-1/2 particles: P(J | n) for n <= 3.
        table = {0: {0: 1}, 1: {1: 1}, 2: {0: .25, 2: .75}, 3: {1: .5, 3: .5}}
        g = honeycomb_graph(2); rng = np.random.default_rng(79)
        d = PlanarParitySolver(g, p=.31)
        for _ in range(20):
            x = rng.integers(0, 2, len(g.edges), dtype=np.uint8)
            counts = g.degrees(x)[list(g.detector_vertices)]
            J2 = [rng.choice(list(table[int(n)]), p=list(table[int(n)].values())) for n in counts]
            factors = []
            for v, j in zip(g.detector_vertices, J2):
                n = np.indices((2,)*len(g.incident_edges[v])).sum(0)
                factors.append(np.array([table[int(k)].get(int(j), 0) for k in n.flat]).reshape(n.shape))
            s = g.true_syndrome(x)
            expected, _ = enumerate_record(g, .31, s, factors)
            got, _ = d.posterior_from_factors(s, factors)
            np.testing.assert_allclose(got, expected, atol=1e-9, rtol=0)

    def test_batch_empty_shape_caps_and_random_ties(self):
        g = honeycomb_graph(2)
        for method in METHODS:
            d = make_decoder(g, method, p=.5, q=0)
            empty = np.empty((0, 6), np.uint8)
            self.assertEqual(d.decode_batch(empty, empty).shape, (0, 11))
            with self.assertRaises(ValueError):
                d.decode_batch(np.empty((0, 5)), np.empty((0, 5)))
            with self.assertRaises(ValueError):
                d.decode(np.zeros(6), np.full(6, 2))
            if method != 'configuration_map':
                S = np.zeros((64, 6), np.uint8)
                C = d.decode_batch(S, S, rng=123)
                self.assertEqual(set(g.logical_parity(c) for c in C), {0, 1})
        with self.assertRaises(ValueError):
            HeraldTransferMLDecoder(honeycomb_graph(5), p=.2, q=.5, max_width=1)
        d = HeraldTransferMLDecoder(g, p=.2, q=.5, max_array_bytes=1)
        with self.assertRaises(ValueError):
            d.posterior(np.zeros(6), np.zeros(6))
        with self.assertRaises(ValueError):
            HeraldMPSDecoder(g, p=.2, q=.5, chi=0)
        for method in ('configuration_map', 'planar_ml', 'mps_ml'):
            with self.assertRaises(ValueError):
                make_decoder(square_graph(3), method, p=.2, q=.5)

    def test_square_transfer_and_bp_factory_compatibility(self):
        rng = np.random.default_rng(80)
        g = square_graph(3); obs = sample_observation(g, rng, p=.2, q=.5)
        result = make_decoder(g, 'transfer_ml', p=.2, q=.5).decode(obs.syndrome, obs.herald)
        np.testing.assert_array_equal(g.true_syndrome(result.correction), obs.syndrome)
        kwargs = dict(p=.2, q=.5, use_numba=False)
        direct = HeraldBeliefMatchingDecoder(g, **kwargs).decode(obs.syndrome, obs.herald)
        factory = make_decoder(g, 'bp_matching', **kwargs).decode(obs.syndrome, obs.herald)
        np.testing.assert_array_equal(direct.correction, factory.correction)
        self.assertEqual(len(DECODER_METHODS), 5)

    def test_geometry_label_is_not_a_proof(self):
        g = honeycomb_graph(2)
        wrong = replace(g, logical_edges=frozenset({0}))
        for method in ('configuration_map', 'planar_ml', 'mps_ml'):
            with self.assertRaises(ValueError):
                make_decoder(wrong, method, p=.2, q=.5)


if __name__ == '__main__':
    unittest.main()
