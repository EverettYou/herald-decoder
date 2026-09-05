---
title: 'R6I mini-bucket bounded-approximation gate'
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

# R6I mini-bucket bounded-approximation gate

## Method

Mini-bucket elimination is the lowest-cost controlled approximation implied by R6G/R6H: it retains the exact nonnegative factors and registered elimination orders, but partitions a bucket whenever its joint scope would exceed `i`. Its evidence output is an upper bound. The reported physical pseudo-marginal normalizes two separately clamped upper bounds and is therefore a diagnostic, not a marginal bound.

## Primitive exact-reference matrix

| representation | order | i | exact cluster | split buckets | evidence ratio | max marginal error | mean marginal error |
|---|---|---:|---:|---:|---:|---:|---:|
| r6d_unclustered | global_min_fill | 10 | 18 | 12 | 116356 | 2.431e-01 | 8.289e-02 |
| r6d_unclustered | global_min_fill | 14 | 18 | 8 | 102.912 | 1.651e-01 | 7.475e-02 |
| r6d_unclustered | global_min_fill | 18 | 18 | 0 | 1 | 1.110e-16 | 5.551e-17 |
| r6d_unclustered | global_min_fill | 20 | 18 | 0 | 1 | 1.110e-16 | 5.551e-17 |
| r6d_unclustered | auxiliary_first_min_fill | 10 | 16 | 9 | 256 | 1.110e-16 | 6.014e-17 |
| r6d_unclustered | auxiliary_first_min_fill | 14 | 16 | 4 | 16 | 1.110e-16 | 5.089e-17 |
| r6d_unclustered | auxiliary_first_min_fill | 18 | 16 | 0 | 1 | 1.110e-16 | 5.089e-17 |
| r6d_unclustered | auxiliary_first_min_fill | 20 | 16 | 0 | 1 | 1.110e-16 | 5.089e-17 |
| r6f_bounded_superfactor | global_min_fill | 10 | 18 | 12 | 1829.49 | 9.035e-02 | 4.770e-02 |
| r6f_bounded_superfactor | global_min_fill | 14 | 18 | 12 | 1746.34 | 1.260e-01 | 6.582e-02 |
| r6f_bounded_superfactor | global_min_fill | 18 | 18 | 0 | 1 | 1.110e-16 | 5.551e-17 |
| r6f_bounded_superfactor | global_min_fill | 20 | 18 | 0 | 1 | 1.110e-16 | 5.551e-17 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 20 | 17 | 65536 | 1.110e-16 | 8.789e-17 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 20 | 12 | 4096 | 1.110e-16 | 5.089e-17 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 20 | 6 | 64 | 1.110e-16 | 5.089e-17 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 20 | 0 | 1 | 1.110e-16 | 5.089e-17 |

## Paper-L2 bounded evidence diagnostic

| representation | order | i | exact cluster | split buckets | log10 adjusted evidence upper bound |
|---|---|---:|---:|---:|---:|
| r6d_unclustered | global_min_fill | 10 | 36 | 57 | 12.795816 |
| r6d_unclustered | global_min_fill | 14 | 36 | 39 | 4.674360 |
| r6d_unclustered | global_min_fill | 18 | 36 | 31 | 2.868180 |
| r6d_unclustered | global_min_fill | 20 | 36 | 35 | 2.567150 |
| r6d_unclustered | auxiliary_first_min_fill | 10 | 44 | 50 | 10.995990 |
| r6d_unclustered | auxiliary_first_min_fill | 14 | 44 | 42 | 9.417054 |
| r6d_unclustered | auxiliary_first_min_fill | 18 | 44 | 37 | 8.161781 |
| r6d_unclustered | auxiliary_first_min_fill | 20 | 44 | 34 | 7.985690 |
| r6f_bounded_superfactor | global_min_fill | 10 | 36 | 40 | 5.577450 |
| r6f_bounded_superfactor | global_min_fill | 14 | 36 | 51 | 4.674360 |
| r6f_bounded_superfactor | global_min_fill | 18 | 36 | 31 | 2.868180 |
| r6f_bounded_superfactor | global_min_fill | 20 | 36 | 35 | 2.567150 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 52 | 61 | 14.307320 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 52 | 55 | 13.404230 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 52 | 41 | 8.888780 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 52 | 41 | 9.189810 |

## Analysis

Exact-ceiling controls: `7` rows, maximum evidence-ratio error `1.998e-15`, maximum physical-marginal error `1.110e-16`.

H1: mixed: evidence monotonic in every branch=True; maximum marginal error monotonic in every branch=False. H2: supported on 7 exact-ceiling rows.

- At `i=10`, the four paper-L2 branches span `8.730` decades in adjusted evidence upper bound.
- At `i=14`, the four paper-L2 branches span `8.730` decades in adjusted evidence upper bound.
- At `i=18`, the four paper-L2 branches span `6.021` decades in adjusted evidence upper bound.
- At `i=20`, the four paper-L2 branches span `6.623` decades in adjusted evidence upper bound.

Paper-L2 branch spread is a sensitivity diagnostic only. Without an exact paper-L2 reference, a smaller upper bound is tighter but does not validate the normalized clamped pseudo-marginals. A richer GBP/tensor branch is warranted only where this baseline leaves material primitive error at the affordable `i` values.

## Claim boundary

Deterministic primitive approximation error and paper-L2 evidence-bound sensitivity only; normalized clamped bounds are not marginal bounds, paper-L2 has no exact accuracy reference, and no correction/LER/threshold/runtime-scaling/fault-tolerance claim is made.

## Primary sources

- Rina Dechter and Irina Rish, [Mini-buckets: A general scheme for bounded inference](https://doi.org/10.1145/636865.636866), JACM 50 (2003).
- Eduardo Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://ojs.aaai.org/index.php/AAAI/article/view/7761), AAAI 2010.

