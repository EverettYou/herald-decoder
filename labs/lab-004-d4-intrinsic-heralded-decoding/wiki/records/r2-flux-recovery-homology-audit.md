---
title: 'R2 flux-recovery and union-homology remediation audit'
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

# R2 flux-recovery and union-homology remediation audit

## Implemented prerequisite

The first stage of the published practical decoder can now be scored against a simulated physical X-error string. The decoder receives only the measured flux syndrome and matching weights. The physical string is retained outside the decoder and used after recovery to form the residual Pauli operator.

Two distinct source objects are now retained explicitly:

- Pauli-X operator composition is the symmetric difference (bitwise XOR). Its boundary must vanish; this remains the algebraic recovery residual.
- Appendix A's post-flux history and first logical-error criterion use the Boolean union of physical and correction strings. An edge acted on in both rounds remains in this union because both operations contribute to the measured stabilizer-entanglement component.

The earlier implementation incorrectly used XOR-residual homology for the first logical decision. Integration exposed the error: if the physical and correction strings are the same winding loop, the Pauli residual is empty but their Boolean union is homologically nontrivial. Appendix A declares this branch a logical error before charge recovery. The public scorer now records both analyses and bases `logical_error` on union-component homology.

## Bounded verification

The algebraic tests still verify double-action cancellation, rejection of open XOR residuals, and exhaustive L=2 syndrome preservation. A new discriminating regression uses identical physical and negative-weight-selected correction winding loops: it verifies an empty XOR residual, a nontrivial Boolean union, and a logical failure from the union criterion.

The remediated complete Lab 004 suite passes 64 tests.

## Claim boundary

This repairs the upstream first-stage decision before end-to-end integration. The matched physical-error-to-final-decision record and post-flux charge sampling remain pending; no LER data exist or are authorized.

