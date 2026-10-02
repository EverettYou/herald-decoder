"""Bounded visible-record workbench using the standard package factory."""
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
from herald_decoder import DECODER_METHODS, honeycomb_graph, make_decoder, sample_observation


def artifact_payload(body):
    L = int(body.get('L', 5))
    p, q = float(body.get('p', .24)), float(body.get('q', .5))
    seed = int(body.get('seed', 7))
    if not 2 <= L <= 9 or not 0 <= p <= 1 or not 0 <= q <= 1 or seed < 0:
        raise ValueError('require 2 <= L <= 9, 0 <= p <= 1, 0 <= q <= 1, seed >= 0')
    methods = body.get('methods', list(DECODER_METHODS))
    if not isinstance(methods, list) or not methods or len(methods) > 5 or any(k not in DECODER_METHODS for k in methods):
        raise ValueError('select one to five registered methods')
    g = honeycomb_graph(L)
    obs = sample_observation(g, np.random.default_rng(seed), p=p, q=q)
    rows = []
    for method in methods:
        try:
            start = time.perf_counter()
            d = make_decoder(g, method, p=p, q=q)
            setup_ms = (time.perf_counter()-start)*1000
            start = time.perf_counter()
            # Only the permitted record is passed to each decoder.
            result = d.decode(obs.syndrome, obs.herald)
            ms = (time.perf_counter()-start)*1000
            probabilities = getattr(result, 'sector_probabilities', None)
            valid = np.array_equal(g.true_syndrome(result.correction), obs.syndrome)
            rows.append(dict(method=method, label=DECODER_METHODS[method]['label'],
                             syndrome_valid=bool(valid), sector=g.logical_parity(result.correction),
                             failure=bool(g.logical_parity(result.correction ^ obs.error)),
                             posterior=None if probabilities is None else probabilities.tolist(),
                             setup_ms=setup_ms, decode_ms=ms, correction=result.correction.tolist(),
                             converged=bool(result.bp.converged) if hasattr(result, 'bp') else None))
        except (ValueError, RuntimeError) as exc:
            rows.append(dict(method=method, label=DECODER_METHODS[method]['label'], error=str(exc)))
    return dict(L=L, p=p, q=q, seed=seed, methods=rows,
                vertices=[dict(x=v.x, y=v.y, detector=v.detector) for v in g.vertices],
                edges=g.edges, error=obs.error.tolist(), syndrome=obs.syndrome.tolist(),
                herald=obs.herald.tolist(), detector_vertices=g.detector_vertices,
                logical_edges=sorted(g.logical_edges), scope='One shared observation. Times include first-call effects; use the report for warmed benchmark timings.')
