---
title: 'R6F exact-preserving structural inference matrix'
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

# R6F exact-preserving structural inference matrix

## Registered question

R6E verified exact factor messages but rejected ordinary loopy BP on the unclustered R6D graph as an exact posterior solver. R6F asks whether exact-preserving local clustering removes that pathology. It compares the frozen R6E baseline, a bounded nonnegative superfactor graph, and a deliberately non-scalable exact physical-factor ceiling on the same primitive controls.

## Identity gate

The maximum local product-table error for the bounded clustering is `0.000e+00`. The maximum entrywise error of the exact global physical likelihood table is `0.000e+00`. Thus both representations preserve the registered R6D finite likelihood exactly before BP is compared.

## Matched marginal result

| representation | converged | exact within 1e-8 | hard-message failures | median error (converged) | maximum error (converged) |
|---|---:|---:|---:|---:|---:|
| r6e_unclustered | 10/32 | 0/32 | 6 | 0.5 | 0.5 |
| bounded_superfactor | 8/32 | 0/32 | 2 | 0.00914568 | 0.00959843 |
| global_physical_ceiling | 32/32 | 32/32 | 0 | 9.92778e-12 | 2.61934e-10 |

## Interpretation

The global physical factor is a tree ceiling: exact agreement there confirms that the R6D likelihood and sum-product engine can recover the primitive posterior when all auxiliary-flow loops are removed. The bounded superfactor result is the discriminating arm. Any improvement is evidence that redundant local factor splitting mattered; residual bias or nonconvergence still rejects this particular bounded representation as an exact posterior solver.

The bounded graph uses 36 binary variables, 20 local factors, and maximum local arity nine. It converges on 8/32 rows and is exact within 1e-8 on 0/32. These finite controls do not authorize correction or logical-error sampling.

## Claim boundary

Exact primitive structural discrimination only. No correction, LER, threshold, scalable convergence, runtime scaling, or fault-tolerance claim.

