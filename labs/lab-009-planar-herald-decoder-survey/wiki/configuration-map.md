---
title: Configuration MAP by signed matching
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Configuration MAP by signed matching

## Summary

Configuration MAP selects a highest-weight physical error, which can differ from the most probable logical sector.

## Evidence

The [small-record validation](../results/validation.json) checks maximizing configurations on sampled records; its mathematical reduction is detailed below.

## Status

Current as a configuration baseline on the supported honeycomb channel; no universal advantage over BP is claimed.

## Related pages

- [[model|Model and logical loss]]
- [[comparison|Decoder comparison]]

## Literal posterior objective

At measured degree at most three and fixed parity, $n_v\in\{s_v,s_v+2\}$ when allowed by the degree. Positive heralds impose $n_v=s_v+2$. For $0<q<1$, a zero herald contributes $(1-q)^{(n_v-s_v)/2}$. On hard-valid configurations, minimizing minus log posterior is equivalent to

$$
A N+B\sum_{v:h_v=0}n_v,
$$

where $N=\sum_e x_e$, $A=\log((1-p)/p)$ and $B=-\tfrac12\log(1-q)$. If $d_j(e)$ counts detector endpoints carrying herald $j$, literal signed weights are $A+B d_0(e)-M d_1(e)$. A violated positive constraint loses at least two counts. Taking $M$ greater than the sum of absolute finite edge costs dominates every possible soft improvement, provided a feasible configuration exists. The code checks feasibility of its returned optimum. A fixed finite herald penalty has no such continuous-domain guarantee, especially as $p\to0$.

## Geometry-specific integer simplification

Let $T$ be the number of occupied terminal edges at either rough side. Since $\sum_{v\in D}n_v=2N-T$ and positive-herald counts are constant on the feasible set, the soft objective reduces to

$$
(A+2B)N-BT=(A+2B)(N-\theta T),\qquad \theta=B/(A+2B).
$$

For $0<p<1/2,0<q<1$, $0<\theta<1/2$. The symmetric difference of two feasible configurations has degree zero or two at each detector, hence consists of cycles and terminal paths. Flipping any one component preserves the positive constraints. Cycles and same-side paths have even length; opposite-side paths have odd length, because the canonical left and right terminals lie on opposite bipartite sublattices. For a path, $\Delta T\in\{-2,0,2\}$. If $\Delta N$ is a nonzero even integer, its sign dominates $\theta\Delta T$; if it is odd, $|\Delta N|\ge1>2\theta$; if zero, the sign is fixed by $-\Delta T$. Each component's cost ordering is constant throughout the open interval. Componentwise optimality therefore preserves the full minimizing set.

Choose $\theta=1/4$: soft integer costs are four on bulk edges and three on terminals. With $d(e)$ measured endpoints and $d_1(e)$ positive endpoints, the implementation uses

$$
w_e=2+d(e)-M d_1(e),\qquad M=1+\sum_e(2+d(e)).
$$

The reduction preserves the maximizing set, not the actual likelihood values or posterior sector sums. It requires this geometry and boundary coloring; it must not be applied solely because a graph is planar.

## Endpoints and solver

Within the low-prior branch $0\le p\le1/2$: at $p=1/2,0<q<1$, $A=0$, and extra ties occur: use $d(e)-d_1(e)$ as the finite cost before adding the dominating hard penalty. At $q=0$, use unit weights for $p<1/2$ and zero weights at $p=1/2$. At $q=1$, the record fixes every count; weights are $1\{p<1/2\}+M(d_0-d_1)$, with $M$ above the total soft cost. At $p=0$, return zero for the only possible record. Endpoints are treated exactly, not approximated by nearby parameters.

PyMatching minimizes these signed costs subject to $Hx=s$. Negative-edge complementation is part of the signed T-join reduction: choose negative edges in a base configuration, toggle their induced syndrome, then solve the residual nonnegative problem. PyMatching performs this internally. The implementation checks its exact integer range $2^{24}-1$, syndrome and likelihood support; it raises outside the backend range. No fixed syndrome-defect cap is imposed. [Sparse Blossom](https://quantum-journal.org/papers/q-2025-01-20-1600/) describes the backend.

## Advantages and limitations

Below half this gives configuration MAP without BP iteration, with no continuous weight rounding in the supported integer range. Above half it uses the literal floating objective, subject to matching-backend numerical precision. Its returned correction is itself hard-valid. It also supplies a useful visible-record reference for planar ML. It is not logical ML: equal-weight configurations can populate the sectors unequally, and MAP ties can change the logical risk. MAP is not guaranteed to beat marginal-based BP matching. This lab's Python wrapper rebuilds the matching graph per record; published native timings from other implementations do not describe this wrapper. See [measurements](comparison.md) and [source](../../../src/herald_decoder/configuration_map.py).

## Full-prior implementation

For $1/2<p<1$, $A<0$ and the geometry-specific low-prior integer objective is not equivalent to the posterior. The implementation uses $w_e=A+B d_0(e)-M d_1(e)$ for interior q, with $M>\sum_e|A+B d_0(e)|$. A common positive scaling puts weights in backend range without changing minimizers. At q=0 it uses signed prior log odds. At q=1 it uses $A+M(d_0-d_1)$ with a dominating absolute-cost penalty. At p=1 it validates the record and returns the all-edge vector. Both deterministic prior endpoints have zero logical risk. Independent maximizing-configuration checks cover high-p records; they do not certify all floating-point near-ties.
