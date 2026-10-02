# Herald decoder core

The package owns the canonical square/honeycomb simulator, the existing BP plus posterior-LLR matching decoder, and reusable configuration/sector inference. Experiment plans, figures and numerical evidence remain in `labs/`.

## Select a decoder

```python
import numpy as np
from herald_decoder import honeycomb_graph, sample_observation, make_decoder

graph = honeycomb_graph(5)
obs = sample_observation(graph, np.random.default_rng(7), p=.24, q=.5)
decoder = make_decoder(graph, "planar_ml", p=.24, q=.5)
result = decoder.decode(obs.syndrome, obs.herald)
assert np.array_equal(graph.true_syndrome(result.correction), obs.syndrome)
print(result.sector_probabilities, result.conditional_risk)
```

Only syndrome and herald enter decoding. The sampled error is for evaluation: failure is `graph.logical_parity(obs.error ^ result.correction)`. A valid sector representative need not reproduce the herald or the sampled error.

| Factory method | Class | Objective and supported geometry |
| --- | --- | --- |
| `bp_matching` | `HeraldBeliefMatchingDecoder` | Existing approximate BP marginals plus LLR matching; square/honeycomb |
| `configuration_map` | `HeraldConfigurationMAPDecoder` | Exact maximum-posterior configuration on the canonical honeycomb/channel, integer reduction below half; literal floating log-posterior weights above half |
| `planar_ml` | `HeraldPlanarMLDecoder` | Algebraically exact logical-sector posterior; canonical trivalent planar honeycomb |
| `transfer_ml` | `HeraldTransferMLDecoder` | Exact binary frontier contraction; square/honeycomb under width and memory caps |
| `mps_ml` | `HeraldMPSDecoder` | Approximate column contraction on honeycomb; finite bond dimension |

`DECODER_METHODS` supplies labels/objectives/geometry for selectors. Unknown names raise. Options are forwarded to the selected class: for example `chi=32` for MPS, `max_width=14, max_array_bytes=64*1024**2` for transfer, or `update_schedule="residual_priority", max_iterations=80` for BP. Unsupported options raise rather than being ignored.

New methods accept finite `0 <= p <= 1`, `0 <= q <= 1`, exact parity and binary heralds with no false positives. They are not noisy-measurement decoders. MAP/planar/MPS assume the package's canonical honeycomb geometry and boundary convention. Transfer is exponential in its actual frontier width (default cap 18). Its 256 MiB array cap limits its principal state array, not all temporary memory. MPS defaults to `chi=16`; increase it and compare against an exact method before interpreting risk or threshold. Existing BP retains its original parameter domain (`0 < p < 1`) and defaults (synchronous damping, 40 iterations); selecting it does not change an established experiment's settings. Use the research launcher for the pinned accelerated BP runtime.

## Results, posteriors and batches

All `.decode(s, h)` methods return an object with `.correction`. The four new methods return `SectorResult`, with `.method`, `.diagnostics` and `.sector_probabilities`. MAP sets probabilities/risk to `None`, since it does not sum sectors. Sector methods also expose `.posterior(s, h) -> (probabilities, diagnostics)`, where entries are absolute `P(ell(x)=0/1 | s,h)`, not parity relative to an arbitrary reference. `conditional_risk` is the minimum probability; for MPS it is approximate. BP keeps its existing `DecodeResult` and BP convergence diagnostics.

The four new methods expose `.decode_batch(S, H)` for `(shots, detectors)` arrays and return `(shots, edges)` corrections. Transfer/MPS also provide `.probabilities_batch(S,H)` with a `(shots,2)` array and diagnostics; planar/MAP batches currently loop. Empty batches are supported. Sector ties are deterministic by default; an explicit `rng` randomizes probabilities equal within `1e-12` and shares one generator across a batch. Configuration-MAP ties follow the matching backend. These tie conventions can affect finite-sample counts and MAP risk.

Input validation rejects malformed, nonbinary and zero-probability endpoint records. Numerical failures raise `NumericalInferenceError`; callers must count them in denominators rather than omit records. Sparse planar inference checks solve residual and probability range. The herald planar/MPS wrappers use exact transfer for `0 < p < 1e-12` or `1-1e-12 < p < 1`, subject to its caps; they raise when that fallback is too wide. Algebraic exactness is not an all-size floating-point guarantee. Approximate MPS diagnostics report summed relative discarded weight, not a certified posterior/risk bound.

## General local binary factors

`PlanarParitySolver(graph, p=p).posterior_from_factors(s, factors, reference=None)` accepts one nonnegative finite tensor of shape `(2,)*degree` per detector, in `graph.incident_edges[v]` order. Parity is imposed separately. Edge priors remain IID Bernoulli. Rough tips carry no tensor. This supports a different factorized observation record, including appropriate full-irrep likelihoods on binary variables, without assuming it is the classical herald channel. The generic solver has the same honeycomb/matchgate restrictions and does not offer the herald wrapper's specialized extreme-prior fallback. Optional references must be binary and syndrome-compatible; absolute posteriors are invariant under reference changes.

## Validation and research evidence

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s src/herald_decoder/tests -v
.venv/bin/python labs/lab-009-planar-herald-decoder-survey/scripts/validate_decoders.py
```

The regression oracle enumerates literal complete-error weights, independent of the planar/transfer implementation. Tests cover hard zeros/endpoints, generic factors, an SU(2) full-irrep fixture, reference invariance, batches, numerical resource caps and BP factory compatibility. [Lab 009](../../labs/lab-009-planar-herald-decoder-survey/REPORT.md) contains matched performance/efficiency results, vector data and the [theory wiki](../../labs/lab-009-planar-herald-decoder-survey/wiki/index.md). Finite-penalty Kac–Ward is a lab research comparison and is not a factory method.

## Full-prior scientific contract

For incomplete binary heralds (0<q<1), do not complement sampled errors or replace p by min(p,1−p) while keeping the same herald record/likelihood. The visible experiment lacks that symmetry. All four sector/configuration methods support p in [0,1], including deterministic endpoints; BP supports the interior with its existing contract. High-p MAP uses signed literal log-posterior weights and support penalties, not the low-p integer surrogate. At p=0.5 the prior is uniform, but there is no symmetry-enforced boundary tangent. Historical half-domain benchmarks are not full-domain evidence. See the project [full-prior correction](../../wiki/methods/binary-herald-full-prior-domain.md).
