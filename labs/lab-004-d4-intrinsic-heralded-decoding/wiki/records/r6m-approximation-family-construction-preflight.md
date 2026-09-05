---
title: 'R6M approximation-family construction preflight'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# R6M approximation-family construction preflight

## Purpose

R6M checks the earliest common gate for two independent bounded-inference families. It does not compare decoder quality. The region branch constructs the arc-labeled bounded join graph required before IJGP-style iteration; the tensor branch removes hyperedges with explicit COPY tensors, verifies exact contraction, and checks deterministic finite compressed contractions.

## Region/join-graph construction

| representation | order | i | nodes | arcs | cycle rank | max cluster | max separator | assignment | cap | labels | running intersection |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| r6d_unclustered | global_min_fill | 10 | 56 | 74 | 19 | 10 | 9 | True | True | True | True |
| r6d_unclustered | global_min_fill | 14 | 44 | 51 | 8 | 14 | 13 | True | True | True | True |
| r6d_unclustered | auxiliary_first_min_fill | 10 | 45 | 53 | 9 | 10 | 9 | True | True | True | True |
| r6d_unclustered | auxiliary_first_min_fill | 14 | 40 | 43 | 4 | 14 | 13 | True | True | True | True |
| r6f_bounded_superfactor | global_min_fill | 10 | 48 | 58 | 11 | 9 | 8 | True | True | True | True |
| r6f_bounded_superfactor | global_min_fill | 14 | 48 | 59 | 12 | 14 | 13 | True | True | True | True |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 53 | 69 | 17 | 10 | 9 | True | True | True | True |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 48 | 59 | 12 | 14 | 13 | True | True | True | True |

## COPY-tensor contraction smoke

| representation | tensors | bonds | exact relative error | max bond | compressed relative error | finite | deterministic | seconds |
|---|---:|---:|---:|---:|---:|---|---|---:|
| r6d_unclustered | 120 | 204 | 2.738e-16 | 2 | 5.482e-01 | True | True | 0.285 |
| r6d_unclustered | 120 | 204 | 2.738e-16 | 4 | failed | False | False | 0.026 |
| r6d_unclustered | 120 | 204 | 2.738e-16 | 8 | failed | False | False | 0.451 |
| r6f_bounded_superfactor | 92 | 144 | 9.583e-16 | 2 | 1.688e-01 | True | True | 0.235 |
| r6f_bounded_superfactor | 92 | 144 | 9.583e-16 | 4 | 3.251e-01 | True | True | 0.084 |
| r6f_bounded_superfactor | 92 | 144 | 9.583e-16 | 8 | 4.107e-15 | True | True | 0.037 |

Compressed-contraction failures were retained as results:
- `LinAlgError: Array must not contain infs or NaNs.`

## Gate decision

Region validity: `8/8`. Tensor exact ceilings: `2/2`. Compressed finite and deterministic rows: `4/6` and `4/6`. Total runtime: `10.44` seconds.

H1 supported; H2 rejected; H3 rejected.

Next gate: remediate the failed construction before any approximation-family selection.

## Claim boundary

Construction feasibility on one primitive partition-function target only; compressed scalar error does not select a decoder and no posterior-accuracy, correction, paper-L2, LER, threshold, scaling, or fault-tolerance claim is made.

## Primary sources

- Mateescu, Kask, Gogate, and Dechter, [Join-Graph Propagation Algorithms](https://doi.org/10.1613/jair.2842), JAIR 37 (2010).
- Yedidia, Freeman, and Weiss, [Constructing Free Energy Approximations and Generalized Belief Propagation Algorithms](https://www.merl.com/publications/TR2002-35).
- Bravyi, Suchara, and Vargo, [Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code](https://doi.org/10.1103/PhysRevA.90.032326), PRA 90 (2014).
- Gray and Chan, [Hyperoptimized Approximate Contraction of Tensor Networks with Arbitrary Geometry](https://doi.org/10.1103/PhysRevX.14.011009), PRX 14 (2024).

