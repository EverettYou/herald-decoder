---
title: 'R6G exact elimination-width and junction feasibility gate'
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

# R6G exact elimination-width and junction feasibility gate

## Question and method

R6F showed that exact global auxiliary elimination recovers the primitive posterior, while one bounded clustering remains biased. R6G therefore measures the structural cost of exact elimination before implementing a larger-region algorithm. Following Dechter's bucket-elimination framework, the relevant dense-table cost is exponential in induced width; following Yedidia, Freeman, and Weiss, larger regions are treated as an adjustable accuracy/complexity trade rather than presumed to solve the problem.

Each factor scope is completed to a clique in the primal interaction graph. The reported widths are deterministic upper bounds for three registered min-fill orders, not proofs of optimal treewidth.

## Complete structural matrix

| geometry | representation | order | variables | factors | input max arity | induced width | max cluster vars | log2 peak entries | fill edges |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| primitive | r6d_unclustered | auxiliary_first_min_fill | 36 | 48 | 6 | 15 | 16 | 16 | 154 |
| primitive | r6d_unclustered | physical_first_min_fill | 36 | 48 | 6 | 27 | 28 | 28 | 324 |
| primitive | r6d_unclustered | global_min_fill | 36 | 48 | 6 | 17 | 18 | 18 | 168 |
| primitive | r6f_bounded_superfactor | auxiliary_first_min_fill | 36 | 20 | 9 | 19 | 20 | 20 | 186 |
| primitive | r6f_bounded_superfactor | physical_first_min_fill | 36 | 20 | 9 | 27 | 28 | 28 | 264 |
| primitive | r6f_bounded_superfactor | global_min_fill | 36 | 20 | 9 | 17 | 18 | 18 | 144 |
| paper_L2 | r6d_unclustered | auxiliary_first_min_fill | 108 | 144 | 6 | 43 | 44 | 44 | 1678 |
| paper_L2 | r6d_unclustered | physical_first_min_fill | 108 | 144 | 6 | 79 | 80 | 80 | 3401 |
| paper_L2 | r6d_unclustered | global_min_fill | 108 | 144 | 6 | 35 | 36 | 36 | 1260 |
| paper_L2 | r6f_bounded_superfactor | auxiliary_first_min_fill | 108 | 60 | 9 | 51 | 52 | 52 | 1942 |
| paper_L2 | r6f_bounded_superfactor | physical_first_min_fill | 108 | 60 | 9 | 79 | 80 | 80 | 3220 |
| paper_L2 | r6f_bounded_superfactor | global_min_fill | 108 | 60 | 9 | 35 | 36 | 36 | 1188 |

## Primitive exact-evidence gate

Dense bucket elimination is allowed only through 20 binary variables in one bucket. It computes 4/6 registered primitive branches and censors 2/6 before allocating an oversized table. Every computed branch matches the independent 4,096-mask evidence with maximum relative error `1.780e-15`.

## Interpretation

The best registered primitive order needs 16 binary variables in its largest cluster. On paper-L2 the best registered order needs 36, corresponding to a dense table with `2^36` entries before accounting for multiple buckets or messages. This is the discriminating feasibility result: exact junction inference may be tractable on the semantic fixture while naive dense extension already has exponential structural growth at the first paper-normalized size.

The hypotheses separate cleanly. H1 is rejected for these orders: the bounded superfactor graph never lowers maximum cluster size; it ties the unclustered graph under global and physical-first orders and is worse under auxiliary-first, even though it has fewer factors and sometimes fewer fill edges. Factor-count compression is therefore not treewidth compression. H2 is geometry-dependent: global min-fill is best at paper-L2, but the primitive unclustered auxiliary-first order is smaller (16 versus 18 cluster variables). H3 is supported because every paper-L2 branch exceeds the registered cap of 20.

The next method should therefore expose a controlled region/cutset/tensor approximation and validate it against primitive exact marginals. It should not silently call a min-fill upper bound the optimal treewidth, and this audit does not authorize correction or LER sampling.

## Claim boundary

Registered-order induced-width upper bounds and capped primitive exact-evidence checks only. No optimal-treewidth, generalized-BP, correction, LER, threshold, runtime-scaling, or fault-tolerance claim.

## Primary method sources

- Rina Dechter, [Bucket elimination: A unifying framework for reasoning](https://doi.org/10.1016/S0004-3702(99)00059-4), *Artificial Intelligence* 113 (1999).
- Jonathan Yedidia, William Freeman, and Yair Weiss, [Generalized Belief Propagation](https://proceedings.neurips.cc/paper/2000/hash/61b1fb3f59e28c67f3925f3c79be81a1-Abstract.html), NeurIPS 2000.

