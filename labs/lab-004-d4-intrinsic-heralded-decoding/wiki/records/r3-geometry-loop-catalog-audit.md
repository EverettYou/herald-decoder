---
title: 'R3.4 geometry-derived loop catalog audit'
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

# R3.4 geometry-derived loop catalog audit

## Transition

The R3.3 loop catalog no longer comes from scanning all `2^E` edge subsets. A graph DFS generates simple cycles directly, deduplicates them by edge mask, and retains only one-component, nonbranching, homologically trivial cycles carrying the source's two colour constraints. Maximum cycle length and total cycle count are explicit guards.

## Exact checks

On the primitive 12-edge graph, the geometry generator returns masks 238, 1589, 2947, and 3416—exactly the complete catalog previously obtained from all 4096 edge subsets.

On the paper-normalized `L=2` graph with 36 edges, a length-six run finds 12 source-valid trivial hexagons without an edge-subset scan. This is a local geometry checkpoint, not a complete all-length catalog.

Two tests bring the complete Lab suite to 86 passing tests.

## Winding contract

The existing researcher decision already fixes the relevant interpretation: any nontrivial winding action is a terminal logical error independent of the absolute ground-state sector, and no sector-dependent charge record may be invented. R3 recovery optimization therefore excludes such terminal records; it does not need an assumed winding likelihood. Explicit even/odd/unconstrained policies remain diagnostics only.

## Remaining boundary

Longer trivial components remain length-guarded, and sector-restricted comparison inside the nonwinding recovery problem still uses bounded exclusion cuts. The next gate is to make the terminal winding-failure constraint explicit in the MILP interface and verify it against all primitive winding fixtures before considering a larger optimization instance.

