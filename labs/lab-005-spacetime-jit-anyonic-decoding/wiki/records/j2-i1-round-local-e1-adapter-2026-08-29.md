---
title: 'J2 I1 round-local E1 adapter'
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

# J2 I1 round-local E1 adapter

I1 is verified for the registered paper \(L=2\) scope. The new adapter accepts one `InnerDecoderRequest`, verifies that its digest binds the supplied causal prefix, and converts only the prefix's final public syndrome/herald row into a typed E1 report over all 24 D4 vertices. Syndrome membership becomes `m_flux`; herald membership becomes `e_charge`; the two bits remain independent, so a site may carry both labels.

The resulting report inherits the callback trial identity and invocation round. Counterfactual tests show that changing private truth/fault decompositions without changing public readouts leaves the record identical, and changing only a later public row leaves an earlier record identical. Mismatched prefix binding, wrong spatial width, and unverified lattice size fail closed.

Six focused tests and all 113 Lab 005 tests pass. No policy mode was invoked and no sample or performance result was produced. I2/I3—the two modes across four schedules plus deterministic negative controls—remain the next gate.

Machine-readable evidence: [manifests/j2-i1-round-local-e1-adapter-2026-08-29.json](../../manifests/j2-i1-round-local-e1-adapter-2026-08-29.json).

