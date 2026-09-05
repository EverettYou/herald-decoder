---
title: 'R0 lattice-normalization remediation'
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

# R0 lattice-normalization remediation

## Source-count audit

Appendix A states that the affected blue and green stars form the bipartite honeycomb lattice. Appendix C defines the paper's `L x L` three-colour kagome lattice with nine stars per unit cell. Three stars per cell are red, so the blue/green honeycomb contains `6 L^2` vertices and `9 L^2` red-qubit edges. The published forcing constant is `K=27 L^2`, explicitly three times those `9 L^2` edges.

The existing `periodic_honeycomb(size)` uses the primitive two-vertex honeycomb cell: it has `2 size^2` vertices and `3 size^2` edges. Therefore its `size` is not the paper's `L`. The former default `K=27 size^2` was nine times the actual edge count, not the source invariant `K=3E`.

## Immediate correction

`published_herald_weights` now computes the default forcing scale as `K=3 * edge_count`. This equals `27 L^2` on a source-normalized graph and remains correct on bounded primitive-cell fixtures. The L=2 fixture now has 12 edges and `K=36`, replacing the invalid value 108. The exhaustive 384-case PyMatching comparison was rerun under the corrected weights and still agrees with the exact binary optimum. All 41 Lab 004 tests pass.

## Evidence status and impact

- The negative-weight semantic conclusion remains verified after rerun; its former literal L=2 weight values are superseded.
- Existing topology, likelihood, homology, and DSU tests remain valid as structural primitive-honeycomb evidence.
- They do not establish the paper's finite-size `L` convention or its exact coloured supercell geometry.
- No Lab 004 LER or threshold data exist, so no experimental data require regeneration.
- Any quantitative comparison using the paper's `L`, and the periodic post-flux geometry adapter, is frozen until the determinant-three coloured kagome/honeycomb supercell in Appendix C Eq. C1 is implemented and checked to have `6 L^2` vertices and `9 L^2` edges.

This remediation prevents the abstract primitive torus from being silently presented as the published finite-size lattice.

