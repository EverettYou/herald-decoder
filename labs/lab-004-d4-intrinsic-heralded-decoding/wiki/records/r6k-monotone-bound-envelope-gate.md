---
title: 'R6K monotone mini-bucket bound-envelope gate'
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

# R6K monotone mini-bucket bound-envelope gate

## Question and construction

R6J's independent greedy partitions are not nested across `i`. R6K isolates that failure without introducing a new partition heuristic: for every total or clamped evidence query, the envelope at `i_j` is the minimum valid mini-bucket upper bound observed at any registered `i<=i_j`. This guarantees monotone evidence bounds. The two clamped envelopes are normalized only as a pseudo-marginal diagnostic.

## Matched aggregate comparison

| branch | representation | order | i | useful / 8 | median max error | worst max error |
|---|---|---|---:|---:|---:|---:|
| independent_greedy | r6d_unclustered | global_min_fill | 10 | 0/8 | 3.054e-01 | 4.955e-01 |
| independent_greedy | r6d_unclustered | global_min_fill | 14 | 0/8 | 2.758e-01 | 5.479e-01 |
| independent_greedy | r6d_unclustered | global_min_fill | 18 | 8/8 | 1.388e-16 | 2.220e-16 |
| independent_greedy | r6d_unclustered | global_min_fill | 20 | 8/8 | 1.388e-16 | 2.220e-16 |
| independent_greedy | r6d_unclustered | auxiliary_first_min_fill | 10 | 4/8 | 8.410e-02 | 3.333e-01 |
| independent_greedy | r6d_unclustered | auxiliary_first_min_fill | 14 | 6/8 | 1.110e-16 | 2.159e-01 |
| independent_greedy | r6d_unclustered | auxiliary_first_min_fill | 18 | 8/8 | 1.110e-16 | 2.220e-16 |
| independent_greedy | r6d_unclustered | auxiliary_first_min_fill | 20 | 8/8 | 1.110e-16 | 2.220e-16 |
| independent_greedy | r6f_bounded_superfactor | global_min_fill | 10 | 0/8 | 3.517e-01 | 5.392e-01 |
| independent_greedy | r6f_bounded_superfactor | global_min_fill | 14 | 0/8 | 2.936e-01 | 5.806e-01 |
| independent_greedy | r6f_bounded_superfactor | global_min_fill | 18 | 8/8 | 1.388e-16 | 2.220e-16 |
| independent_greedy | r6f_bounded_superfactor | global_min_fill | 20 | 8/8 | 1.388e-16 | 2.220e-16 |
| independent_greedy | r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 6/8 | 1.110e-16 | 2.120e-01 |
| independent_greedy | r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 4/8 | 8.410e-02 | 3.333e-01 |
| independent_greedy | r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 6/8 | 1.110e-16 | 9.508e-02 |
| independent_greedy | r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 8/8 | 1.110e-16 | 2.220e-16 |
| cumulative_valid_bound_envelope | r6d_unclustered | global_min_fill | 10 | 0/8 | 3.054e-01 | 4.955e-01 |
| cumulative_valid_bound_envelope | r6d_unclustered | global_min_fill | 14 | 0/8 | 2.758e-01 | 5.479e-01 |
| cumulative_valid_bound_envelope | r6d_unclustered | global_min_fill | 18 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6d_unclustered | global_min_fill | 20 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6d_unclustered | auxiliary_first_min_fill | 10 | 4/8 | 8.410e-02 | 3.333e-01 |
| cumulative_valid_bound_envelope | r6d_unclustered | auxiliary_first_min_fill | 14 | 6/8 | 0.000e+00 | 2.159e-01 |
| cumulative_valid_bound_envelope | r6d_unclustered | auxiliary_first_min_fill | 18 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6d_unclustered | auxiliary_first_min_fill | 20 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | global_min_fill | 10 | 0/8 | 3.517e-01 | 5.392e-01 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | global_min_fill | 14 | 0/8 | 2.534e-01 | 5.806e-01 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | global_min_fill | 18 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | global_min_fill | 20 | 8/8 | 0.000e+00 | 0.000e+00 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 6/8 | 1.110e-16 | 2.120e-01 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 4/8 | 8.333e-02 | 1.862e-01 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 6/8 | 0.000e+00 | 9.508e-02 |
| cumulative_valid_bound_envelope | r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 8/8 | 0.000e+00 | 0.000e+00 |

## Analysis

Evidence monotonicity violations fall from `3` to `0`. Marginal-error monotonicity violations change from `14` to `13`. Total useful low-`i` rows change from `20` to `20`, while uniformly useful low-`i` branches change from `0` to `0`.

On 128 matched envelope rows, error improves in `4`, is unchanged in `124`, and worsens in `0`. Maximum improvement is `1.667e-01` and maximum regression `2.220e-16`.

H1 supported; H2 mixed or rejected; H3 supported.

A monotone valid-bound envelope fixes bound ordering but need not improve normalized clamped pseudo-marginals, because tightening the two state bounds by different factors can move their ratio either way. If uniform low-`i` accuracy remains absent, the next method must change factor content/region coupling rather than merely select among existing bounds.

## Claim boundary

Primitive valid-bound selection diagnostic only; the envelope is not a nested partition algorithm or posterior bound, and no paper-L2 accuracy, correction, LER, threshold, scaling, or fault-tolerance claim is made.

## Primary source

- Emma Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://doi.org/10.1609/aaai.v24i1.7761), AAAI 2010.

