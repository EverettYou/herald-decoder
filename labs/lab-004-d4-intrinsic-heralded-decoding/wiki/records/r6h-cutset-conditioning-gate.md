---
title: 'R6H cutset-conditioning exact time-space gate'
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

# R6H cutset-conditioning exact time-space gate

## Result

R6G's paper-L2 dense-memory barrier is not treated as permission to guess a larger-region decoder. Following Dechter, R6H first measures the exact conditioning/elimination trade: conditioning `k` variables creates `2^k` residual branches but can reduce the largest dense table.

| representation | cutset policy | first k with cluster <=20 | cluster | k+cluster at crossing | minimum k+cluster | location (k, cluster) |
|---|---|---:|---:|---:|---:|---|
| r6d_unclustered | physical_only_core | 24 | 20 | 44 | 30 | (4, 26) |
| r6d_unclustered | auxiliary_only_core | 12 | 20 | 32 | 30 | (4, 26) |
| r6d_unclustered | unrestricted_core | 18 | 20 | 38 | 30 | (4, 26) |
| r6f_bounded_superfactor | physical_only_core | not reached | — | — | 30 | (4, 26) |
| r6f_bounded_superfactor | auxiliary_only_core | 13 | 20 | 33 | 30 | (4, 26) |
| r6f_bounded_superfactor | unrestricted_core | 13 | 20 | 33 | 30 | (4, 26) |

## Validity gate

All 18 registered primitive reconstructions (two representations × three policies × `k=0,2,4`) enumerate every cutset assignment and recover the independent 4,096-mask evidence. Maximum relative error is `1.780e-15`. The frontier is therefore an exact space/time decomposition, not an approximation.

## Interpretation

The color of the result is deliberately resource-theoretic: a lower residual cluster means lower peak dense memory, whereas `k+cluster` exposes whether that saving merely moves exponential cost into branching. Physical-only, auxiliary-only, and unrestricted policies are all shown, so the comparison diagnoses which variable class carries the core without elevating one heuristic into a scientific assumption.

These are deterministic upper bounds for one registered cutset-selection and residual min-fill rule. They do not prove an optimal cutset or treewidth, and the exponent proxy is not measured runtime.

## Claim boundary

Exact registered-cutset resource frontier and primitive evidence reconstruction only; no optimal cutset/treewidth, approximation, correction, LER, threshold, runtime-scaling, or fault-tolerance claim.

## Primary sources

- Rina Dechter, [Bucket elimination: A unifying framework for reasoning](https://doi.org/10.1016/S0004-3702(99)00059-4), *Artificial Intelligence* 113 (1999).
- Rina Dechter and Yousri El Fattah, [Topological parameters for time-space tradeoff](https://arxiv.org/abs/1302.3573), *Artificial Intelligence* 125 (2001).

