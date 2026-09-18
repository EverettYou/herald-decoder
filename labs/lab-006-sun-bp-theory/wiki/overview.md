---
title: SU(N) full-irrep BP
status: current
updated: 2026-09-09
---

# SU(N) full-irrep BP

## Summary

Lab 006 makes the anyon labels explicit: a directed active bond carries
\(\bar{\mathbf N}\) to \(\mathbf N\), and the site instrument measures the
binary topological boundary syndrome and the complete total fused irrep. The
irrep itself is the symmetry-resolved heralding signal; there is no auxiliary
binary field. The Global Wiki method page owns the detailed likelihood,
Bayesian posterior, sum-product derivation, and proof. The report records only
the frozen configuration, final algorithm, measured results, and evidence map.
Exactness is established for factor trees only; loops require direct comparison
with exact enumeration.

The public artifact uses Lab 002's square and honeycomb lattices with rough
left/right and smooth transverse boundaries. The degree-two ring is retained
only as an exact-enumeration and throughput fixture. In the fixed A5b schedule,
full-\((m,R)\) BP failed to converge by 80 iterations in 22/128 two-dimensional
observations, with the clearest failure direction at \(L=7\) honeycomb SU(2).


## Evidence

The [exact posterior fixtures](../results/small-graph-exact-vs-bp.json),
[accelerated matching checks](../results/a1-numba-belief-matching.json), and
[convergence scan](../results/a5b-two-dimensional-convergence-scan.json)
support the established implementation claims above.

## Status

Current method and implementation evidence. Logical-rate acquisition uses a
separately frozen 300-iteration, damping-0.5 schedule. Older logical-rate
aggregates that counted BP nonconvergence as failure are invalid; current
curves are owned by [logical-rate evidence](ler-curves.md).

## Related pages

- [Logical-rate curves](ler-curves.md)
- [Scoring correction](a8-ler-scoring-correction-2026-09-05.md)

- [Final group/orientation interpretation](interpretation.md)
