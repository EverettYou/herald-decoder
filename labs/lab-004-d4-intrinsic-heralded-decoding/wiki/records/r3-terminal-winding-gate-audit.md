---
title: 'R3.5 terminal winding-gate audit'
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

# R3.5 terminal winding-gate audit

## Interface contract

The R3 record interface now implements the resolved thread-008 decision before optimization. Any observation record containing a nontrivial winding component is returned immediately as `terminal_winding_logical_failure`; the component-auxiliary MAP solver is not called, and no absolute-sector charge likelihood is fabricated. Sampled nonwinding records alone enter R3 recovery.

## Exhaustive primitive audit

All 4096 physical edge configurations on the primitive `L=2` graph were sampled through the schema-v3 observation contract. Exactly 123 produce terminal winding records. Every one is routed to logical failure with no recovery object.

The registered nonwinding mask-73 control is routed to `recovered_nonwinding` and invokes the R3.3 component-auxiliary solver.

Two tests bring the complete Lab suite to 88 passing tests.

## Claim boundary

This verifies model routing, not an observable real-device oracle for the hidden physical error. It follows the deliberately incomplete generative convention selected for practical decoding: terminal winding records carry no invented fusion record. A full sector-conditioned generative posterior would be a distinct scientific model and is not silently introduced here.

