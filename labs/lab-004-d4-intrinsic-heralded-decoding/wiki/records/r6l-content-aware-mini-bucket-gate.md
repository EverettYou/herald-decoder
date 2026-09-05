---
title: 'R6L factor-content-aware mini-bucket partition gate'
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

# R6L factor-content-aware mini-bucket partition gate

## Question and method

R6L changes one variable in the R6J exact-reference cohort: scope-first-fit partitioning is replaced by a bottom-up factor-content-aware traversal. Each legal merge is scored by its normalized local absolute reduction between separately and jointly eliminated nonnegative factor products. This is a zero-safe project adaptation of Rollon and Dechter's content-based framework because the D4 factors contain exact zeros; it is not their logarithmic heuristic verbatim.

## Matched aggregate comparison

| representation | order | i | scope useful / 8 | content useful / 8 | improved | worsened | median scope error | median content error | worst content error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| r6d_unclustered | global_min_fill | 10 | 0/8 | 0/8 | 2 | 6 | 3.054e-01 | 4.913e-01 | 7.746e-01 |
| r6d_unclustered | global_min_fill | 14 | 0/8 | 0/8 | 4 | 4 | 2.758e-01 | 2.613e-01 | 4.266e-01 |
| r6d_unclustered | global_min_fill | 18 | 8/8 | 8/8 | 0 | 0 | 1.388e-16 | 1.388e-16 | 2.776e-16 |
| r6d_unclustered | global_min_fill | 20 | 8/8 | 8/8 | 0 | 0 | 1.388e-16 | 1.388e-16 | 2.776e-16 |
| r6d_unclustered | auxiliary_first_min_fill | 10 | 4/8 | 4/8 | 0 | 2 | 8.410e-02 | 1.257e-01 | 3.333e-01 |
| r6d_unclustered | auxiliary_first_min_fill | 14 | 6/8 | 6/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 2.159e-01 |
| r6d_unclustered | auxiliary_first_min_fill | 18 | 8/8 | 8/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 2.220e-16 |
| r6d_unclustered | auxiliary_first_min_fill | 20 | 8/8 | 8/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 2.220e-16 |
| r6f_bounded_superfactor | global_min_fill | 10 | 0/8 | 0/8 | 6 | 2 | 3.517e-01 | 2.444e-01 | 4.437e-01 |
| r6f_bounded_superfactor | global_min_fill | 14 | 0/8 | 0/8 | 5 | 3 | 2.936e-01 | 3.379e-01 | 4.948e-01 |
| r6f_bounded_superfactor | global_min_fill | 18 | 8/8 | 8/8 | 0 | 0 | 1.388e-16 | 1.388e-16 | 2.776e-16 |
| r6f_bounded_superfactor | global_min_fill | 20 | 8/8 | 8/8 | 0 | 0 | 1.388e-16 | 1.388e-16 | 2.776e-16 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 10 | 6/8 | 6/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 2.120e-01 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 14 | 4/8 | 4/8 | 0 | 0 | 8.410e-02 | 8.410e-02 | 3.333e-01 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 18 | 6/8 | 6/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 9.508e-02 |
| r6f_bounded_superfactor | auxiliary_first_min_fill | 20 | 8/8 | 8/8 | 0 | 0 | 1.110e-16 | 1.110e-16 | 2.220e-16 |

## Validity and discrimination

All `56` content exact-ceiling rows pass, with maximum evidence-ratio error `1.998e-15` and maximum marginal error `2.776e-16`. Candidate runtime is `149.92` seconds. An independent replay reproduces every scientific field exactly after excluding timestamp and runtime.

The content traversal changes `38` matched rows and selects at least one positive local-tightening merge in `128` candidate rows. At `i<=14`, it improves `17` marginal rows, worsens `17`, and ties `30`. Useful low-`i` rows change from `20` to `20`; uniformly useful branches change from `0` to `0`. Evidence bounds become tighter on `25` low-`i` rows and looser on `10`.

H1 supported; H2 rejected or mixed; H3 rejected.

## Interpretation rule

If factor contents change bounds but do not improve uniform pseudo-marginal accuracy, further mini-bucket packing optimization stops: the next comparison must change the approximation family (explicit regions/join graph versus a bounded tensor contraction). Evidence-bound tightness alone never promotes a decoder.

## Claim boundary

Deterministic primitive posterior method comparison only; no paper-L2 accuracy, decoder correction, LER, threshold, runtime scaling, or fault-tolerance claim.

## Primary source

- Emma Rollon and Rina Dechter, [New Mini-Bucket Partitioning Heuristics for Bounding the Probability of Evidence](https://doi.org/10.1609/aaai.v24i1.7761), AAAI 2010.

