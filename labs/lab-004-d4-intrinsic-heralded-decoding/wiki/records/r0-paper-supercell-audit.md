---
title: 'R0 paper-normalized periodic-supercell audit'
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

# R0 paper-normalized periodic-supercell audit

Date: 2026-08-28

## Acceptance target

Replace the ambiguous primitive-cell finite-size convention before any paper-L experiment.  The accepted topology must contain `6L^2` affected blue/green vertices and `9L^2` red-qubit edges, preserve degree three, expose two independent torus periods, and recover the published forcing scale through the invariant rule `K=3E=27L^2`.

## Construction

The implementation keeps primitive honeycomb coordinates but quotients them by the determinant-three macro basis with column vectors `(1,1)` and `(-1,2)`.  The three cosets are represented by `(0,0)`, `(1,0)`, and `(2,0)`.  An `L x L` repetition therefore contains exactly `3L^2` primitive cells, hence:

- `6L^2` blue/green vertices;
- `9L^2` red-qubit edges;
- three incident edges at every vertex; and
- torus area `det(P)=3L^2` in primitive coordinates.

Coordinate reduction is integer-exact.  Lift discrepancies are converted to winding coordinates by solving against the full period matrix, rather than by dividing both primitive coordinates by `L`.  The old primitive constructor remains available only for exhaustive tiny semantic fixtures and is explicitly not paper-L normalized.

## Verification

For `L=2,3`, focused tests verify the source counts, degree three, absence of parallel edges, exact periodicity under both period columns, and complete/unique vertex coverage.  Selecting the full graph yields winding vectors of matrix rank two, verifying that the generalized lifted traversal detects both torus directions.  On the paper-normalized `L=2` graph, `E=36` and the production weight function gives `K=3E=108=27L^2`.

The full Lab 004 suite passes: **46 tests**.  This includes the existing 384 exact negative-weight matching comparisons on the primitive enumerable fixture; those tests retain their structural purpose and do not become paper-L data.

## Boundary of the result

This transition verifies topology normalization, periodic coordinate semantics, and the matching forcing scale.  It does not yet map Appendix A's top/bottom-left/bottom-right arms to actual periodic edges, construct the effective post-flux blue/green Pauli-Z strings, or produce LER data.  The periodic charge-geometry adapter is therefore the next dependency.

