---
title: 'R6J multi-observation mini-bucket exact-reference validation'
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

# R6J multi-observation mini-bucket exact-reference validation

## Complete matched-cohort summary

The 128 deterministic rows cover four registered observation strata, `p=0.10,0.30`, both exact factorizations, global/auxiliary-first orders, and `i=10,14,18,20`. No row is selected after seeing its error.

| representation | order | i | useful / 8 | cancellation / 8 | median max error | worst max error | median evidence ratio | max evidence ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| r6d_unclustered | global_min_fill | 10 | 0/8 | 0/8 | 3.054e-01 | 4.955e-01 | 1.8519e+05 | 4.1521e+05 |
| r6d_unclustered | global_min_fill | 14 | 0/8 | 0/8 | 2.758e-01 | 5.479e-01 | 63.986 | 123.86 |
| r6d_unclustered | global_min_fill | 18 | 8/8 | 0/8 | 1.388e-16 | 2.220e-16 | 1 | 1 |
| r6d_unclustered | global_min_fill | 20 | 8/8 | 0/8 | 1.388e-16 | 2.220e-16 | 1 | 1 |
| r6d_unclustered | auxiliary_first_min_fill | 10 | 4/8 | 4/8 | 8.410e-02 | 3.333e-01 | 256 | 384 |
| r6d_unclustered | auxiliary_first_min_fill | 14 | 6/8 | 6/8 | 1.110e-16 | 2.159e-01 | 16 | 24 |
| r6d_unclustered | auxiliary_first_min_fill | 18 | 8/8 | 0/8 | 1.110e-16 | 2.220e-16 | 1 | 1 |
| r6d_unclustered | auxiliary_first_min_fill | 20 | 8/8 | 0/8 | 1.110e-16 | 2.220e-16 | 1 | 1 |
| r6f_bounded_superfactor | global_min_fill | 10 | 0/8 | 0/8 | 3.517e-01 | 5.392e-01 | 1937.7 | 3441.8 |
| r6f_bounded_superfactor | global_min_fill | 14 | 0/8 | 0/8 | 2.936e-01 | 5.806e-01 | 1881 | 15874 |
| r6f_bounded_superfactor | global_min_fill | 18 | 8/8 | 0/8 | 1.388e-16 | 2.220e-16 | 1 | 1 |
| r6f_bounded_superfactor | global_min_fill | 20 | 8/8 | 0/8 | 1.388e-16 | 2.220e-16 | 1 | 1 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 6/8 | 6/8 | 1.110e-16 | 2.120e-01 | 65536 | 65536 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 4/8 | 4/8 | 8.410e-02 | 3.333e-01 | 4096 | 6144 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 6/8 | 6/8 | 1.110e-16 | 9.508e-02 | 64 | 64 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 8/8 | 0/8 | 1.110e-16 | 2.220e-16 | 1 | 1 |

## Validity and hypotheses

All `56` exact-ceiling rows pass, with maximum evidence-ratio error `1.998e-15` and maximum marginal error `2.220e-16`.

Across 32 observation/prior/representation/order sequences, evidence monotonicity violations: `3`; marginal-error monotonicity violations: `14`. Auxiliary-first low-`i` cancellation occurs in `20/32` rows. Branches achieving the prospective 0.01 error gate on all eight conditions at `i<=14`: `0`.

H1 supported; H2 rejected or unresolved; H3 supported.

## Interpretation

This cohort determines whether the favorable single-observation cancellation in R6I is reproducible. Evidence bounds and normalized clamped pseudo-marginals are kept separate: monotone improvement of the former does not certify the latter. If no low-`i` branch is uniformly useful, the result licenses a richer approximation comparison, not correction or LER sampling.

## Claim boundary

Deterministic 12-edge primitive posterior validation only; no paper-L2 accuracy, scalable correction, LER, threshold, runtime-scaling, or fault-tolerance claim.

## Primary method source

- Rina Dechter and Irina Rish, [Mini-buckets: A general scheme for bounded inference](https://doi.org/10.1145/636865.636866), JACM 50 (2003).

