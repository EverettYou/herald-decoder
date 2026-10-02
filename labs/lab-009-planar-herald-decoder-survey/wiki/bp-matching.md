---
title: BP and posterior-LLR matching
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/benchmark.json
idea_ids: []
---

# BP and posterior-LLR matching

**Summary**: BP estimates edge marginals from local parity/herald factors; matching then constructs a syndrome-compatible correction. This is an approximate inference and projection pipeline, distinct from configuration MAP and exact logical ML.

**Sources**: [Lab 002 method](../../lab-002-herald-belief-matching/wiki/index.md), [core source](../../../src/herald_decoder/herald_bp_decoder.py), [matched benchmark](../results/benchmark.json).

**Last updated**: 2026-10-01

## Summary

BP approximates the local posterior and matching projects it to a valid syndrome correction.

## Evidence

The [matched benchmark](../results/benchmark.json) and inherited audit use explicitly different BP schedules.

## Status

Current as a reusable approximate baseline; nonconverged records are retained.

## Factor messages

Use [the same physical law](model.md): independent edge priors and a detector tensor that combines exact parity with the count-dependent herald likelihood. For edge variable $x_e$, the sum-product messages are

$$
m_{e\to v}(x_e)\propto w_e(x_e)\prod_{u\in\partial e\setminus v}m_{u\to e}(x_e).
$$

$$
m_{v\to e}(x_e)\propto
\sum_{x_{\partial v\setminus e}}T_v(x_{\partial v})
\prod_{f\in\partial v\setminus e}m_{f\to v}(x_f).
$$

Rough endpoints supply no measured factor. At degree two or three these local sums are small. A positive herald is a hard count constraint; a zero herald is a mixture of an ineligible count and a missed eligible event. Treating heralded vertices as independent edge erasures changes this model.

On a tree, converged messages give exact local marginals. This honeycomb graph has loops, so the iterative fixed point need not give exact marginals or converge. Damping, synchronous or residual-priority scheduling, tolerances and iteration caps are part of the decoder definition and must be matched in comparisons. The existing frozen source uses probability-space damping by default, with Numba kernels when enabled.

## Matching projection

From the belief $r_e\approx P(x_e=1\mid s,h)$, use posterior log odds

$$
\lambda_e=\log\frac{1-r_e}{r_e}.
$$

Signed matching minimizes $\sum_e\lambda_e c_e$ under $Hc=s$. Negative weights mean the marginal favors an occupied edge; they are not an error or a reason to erase that edge. The weights are not $-\log r_e$, and a correction's syndrome is explicitly checked.

This projection behaves as if its edge beliefs defined an independent surrogate posterior. They do not generally retain the correlations of the true posterior or the entropy of a logical class. It is neither an exact configuration-MAP solve of the original factor graph nor a sector-sum ML solve. Exact planar inference can quantify both marginal-inference and projection loss, while a MAP baseline quantifies a different objective.

## Benefits, limits and evidence

BP is reusable beyond matchgate-compatible tensors and retains the existing square/honeycomb local model machinery. Its per-record runtime in this implementation is low, but convergence and accuracy depend on schedule and cap. Nonconverged records are still evaluated; dropping them would bias the reported LER. The new survey cohort uses synchronous 40 iterations, while the inherited audit comparator uses residual-priority 80 iterations. Their results and timing are separate.

Syndrome-only matching removes the herald tensor and uses prior log odds. At $q=0$ it is a useful baseline, but even exact minimum-weight configuration recovery differs from logical ML because of class degeneracy. At $p>1/2$, a negative prior log odds is legitimate; incomplete herald data must not be copied from $1-p$.

## Related pages

- [Configuration MAP](configuration-map.md)
- [Planar logical ML](planar-ml.md)
- [Survey and measurements](comparison.md)
