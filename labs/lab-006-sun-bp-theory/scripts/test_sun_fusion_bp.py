from sun_fusion_bp import bp_marginals, exact_marginals, exact_posterior, fusion_distribution, path_graph, plaquette_graph
from numba_fusion_decoder import FastFusionBeliefMatchingDecoder, GeneralizedSyndrome, NUMBA_AVAILABLE
import numpy as np
import pytest

def test_su3_fusion_channels_normalize():
    for leaves in ((), ("3",), ("3bar",), ("3", "3"), ("3bar", "3bar"), ("3", "3bar")):
        assert abs(sum(fusion_distribution(leaves).values()) - 1) < 1e-14
    assert fusion_distribution(("3", "3bar")) == {"1": 1 / 9, "8": 8 / 9}

def test_bp_equals_exact_on_tree():
    graph = path_graph()
    obs = ((1, "3bar"), (0, "8"), (0, "8"), (1, "3"))
    exact = exact_marginals(exact_posterior(graph, obs, .18), len(graph.edges))
    bp, converged, _ = bp_marginals(graph, obs, .18)
    assert converged
    np.testing.assert_allclose(bp, exact, atol=1e-12)


@pytest.mark.skipif(not NUMBA_AVAILABLE, reason="Numba unavailable")
@pytest.mark.parametrize("graph,obs", [
    (path_graph(), ((1, "3bar"), (0, "8"), (0, "8"), (1, "3"))),
    (plaquette_graph(), ((0, "1"),) * 4),
])
def test_numba_matches_python_recurrence(graph, obs):
    reference, ref_converged, ref_iterations = bp_marginals(
        graph, obs, .18, max_iter=80, tol=1e-10, damping=.25
    )
    observation = GeneralizedSyndrome(
        np.asarray([x[0] for x in obs]),
        tuple(x[1] for x in obs),
    )
    candidate = FastFusionBeliefMatchingDecoder(graph, p=.18).infer(observation)
    np.testing.assert_allclose(candidate.edge_marginals, reference, atol=1e-12, rtol=0)
    assert candidate.converged == ref_converged
    assert candidate.iterations == ref_iterations


@pytest.mark.skipif(not NUMBA_AVAILABLE, reason="Numba unavailable")
def test_belief_matching_correction_is_syndrome_faithful():
    graph = path_graph()
    observation = GeneralizedSyndrome(
        np.asarray([1, 0, 0, 1], dtype=np.uint8),
        ("3bar", "8", "8", "3"),
    )
    decoder = FastFusionBeliefMatchingDecoder(graph, p=.18)
    result = decoder.decode(observation)
    recovered = np.asarray(decoder.matrix @ result.correction, dtype=np.uint8).ravel() & 1
    np.testing.assert_array_equal(recovered, observation.m)
