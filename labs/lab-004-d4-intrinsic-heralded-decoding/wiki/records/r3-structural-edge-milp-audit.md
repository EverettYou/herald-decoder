---
title: 'R3.2 structural edge-MILP audit'
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

# R3.2 structural edge-MILP audit

## What changed

The complete-explanation selector variables from R3.1 are removed. The solver now acts directly on 12 binary physical-edge variables plus one parity auxiliary per vertex. Incidence equalities encode the observed flux boundary and exact degree-two measurement support:

- measured vertex: degree 2;
- unmeasured vacuum-flux vertex: degree 0;
- unmeasured flux vertex: degree 1 or 3.

Fusion-incompatible structurally feasible chains are excluded with exact bounded no-good cuts. This keeps the candidate-dependent parity condition fail-closed without pretending that it is already a scalable local formulation.

## Discriminating fixture matrix

On the four-explanation MAP fixture, the direct-edge MILP reproduces the R3.0/R3.1 complete optimizer sets at `p=0.1` and `p=0.6`, along with all relative-sector optima. No fusion cut is required for that observation.

A separate trivial-loop fixture (mask 238) exercises the fusion branch. Its sampled charge record has one supported structural solution. Flipping one measured blue charge violates the generated loop parity and leaves no supported explanation; the implementation fails closed.

Three new tests raise the complete Lab suite to 81 passing tests.

## Remaining boundary

This is structural for boundary and measurement support, but not yet fully structural for the candidate-dependent fusion likelihood. The no-good cuts are compiled by bounded enumeration, and the objective currently requires all compatible explanations to share the same Appendix-A conditional log-likelihood. If candidate constraint counts vary, the solver rejects the instance. The next gate is an auxiliary-variable encoding of fusion components/constraint count that reproduces R3.0–R3.2 without truth-table cuts. No graph-size increase is authorized before that equality check.

