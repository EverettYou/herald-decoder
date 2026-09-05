---
title: 'R2 published matching graph and negative-weight semantics audit'
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

# R2 published matching graph and negative-weight semantics audit

## Implemented source rule

The non-winding R2 primitive uses the periodic honeycomb vertex-edge incidence matrix as the PyMatching check matrix.  The two practical objectives are kept distinct:

- unheralded baseline: unit edge weight;
- intrinsically heralded decoder: `w_e = 1 - n_e K`, with invariant `K=3E` and `n_e` equal to the number (zero, one, or two) of charge-one intermediate outcomes adjacent to edge `e`. On the paper's source-normalized graph `E=9L^2`, this is `K=27L^2`.

The charge record uses `-1` for unmeasured, `0` for measured vacuum, and `1` for a measured Abelian charge.  Only value `1` contributes to `n_e`.  The source's weights are passed directly as matching objective weights; they are not reinterpreted as probabilities or as the posterior LLR convention used in Lab 002.

## Exhaustive bounded comparison

The primitive-cell L=2 periodic honeycomb has 8 vertices, 12 edges, `K=36`, 4096 binary edge subsets, and 128 even detector syndromes. For each of three source-rule weight cases—no measured charge, one measured charge, and two charges adjacent to one edge—the test enumerates every binary correction subset and compares PyMatching 2.4.0 against the exact minimum of `sum_e w_e x_e` subject to the GF(2) boundary constraint. The former literal value `K=108` on this fixture is invalid and superseded by the source invariant `K=3E`.

All 384 syndrome/weight comparisons agree with the global binary minimum.  This explicitly includes zero-syndrome cases where the optimal correction is a nonempty negative closed cycle.  Unit-weight ties are bitwise deterministic across four independently rebuilt PyMatching objects for every even L=2 syndrome.

Six R2 tests also verify the graph incidence convention, exact `n_e` weights, and fail-closed handling of invalid charge records and odd periodic syndromes.  Together with R1, the Lab 004 suite passes 28 tests under the verified accelerated research runtime.

## Claim boundary

This audit establishes PyMatching's exact bounded negative-weight behavior and the corrected invariant forcing rule on the primitive graph. It does not establish the paper's finite-size lattice normalization, which requires a three-primitive-cell coloured supercell, nor does it run a logical-error-rate experiment. Discussion thread 008 is resolved separately by the ground-state-relative contract.

