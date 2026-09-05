---
title: 'R1 versioned D4 observation-sampler audit'
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

# R1 versioned D4 observation-sampler audit

Date: 2026-08-28

## Implemented transition

The R1 sampler now separates the physical error draw from the conditional fusion-record draw with deterministic independent random streams. A schema-versioned record contains lattice size, physical error rate, seed, error-edge indices, red m-flux vertices, intermediate charge outcomes, generated constraint labels, conditional log2 likelihood, and winding metadata.

For records without a nonbranching winding loop, intermediate outcomes are sampled uniformly on the affine parity subspace: unconstrained degree-two outcomes are fair bits, and one disjoint pivot per independent colour/loop constraint is fixed by parity. The sample is then revalidated by the independent local-likelihood evaluator.

Schema version 3 supersedes the pre-decision status described in the original audit. Under the researcher-selected anyon-free, ground-state-relative contract, a nonbranching winding loop is returned with status `logical_failure` and `logical_error=true`; charge outcomes and conditional likelihood are absent. The sampler does not reject or redraw the physical error and therefore does not silently condition the error channel on trivial homology.

## Verification

Five sampler tests plus the eleven existing topology/likelihood tests pass (`16 passed`). The new tests verify:

- fixed-error and full-channel seed reproducibility;
- satisfaction of every generated constraint;
- all 16 allowed charge outcomes of a local constrained hexagon are reached across 512 deterministic seeds;
- winding records are flagged without guessed outcomes;
- the p=0 record is empty and normalized with schema version 1.

## Claim boundary and next gate

This completes the versioned non-winding sampler. It does not define the protected logical sector for winding-loop measurements. The next R1 transition must derive a logical-sector representation and cover every supported winding-parity branch as a bounded matrix rather than selecting a favorable sector after seeing decoder results.

