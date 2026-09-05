---
title: 'R3 finite-support MILP compilation audit'
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

# R3 finite-support MILP compilation audit

## Formulation

The R3.0 compatible explanation set is compiled into a bounded integer program with one binary selector per explanation and one explicit binary variable per physical edge. One-hot selection and 12 edge-linking equalities force the edge variables to reproduce the selected fusion-compatible explanation. The linear objective is the exact negative `log2[P(s|E)P(E)]` stored by R3.0.

Four additional solves restrict the selectors to one relative homology sector at a time. This makes sector comparison explicit rather than allowing a solver's deterministic tie break to silently choose one topology.

## Exact comparison

At `p=0.1`, the MILP and exhaustive reference return the identical complete global optimizer set `{73,82,268}` and objective `11.3338121257`. The trivial, horizontal, and vertical sectors tie globally; the diagonal sector represented by mask 279 has objective `17.6736621286`.

At `p=0.6`, both methods return the unique mask 279 with objective `12.9383246350`. The other three sector optima share the worse objective `14.1082496365`.

Three new tests verify complete optimizer-set equality at both priors and all four sector-restricted optima. The full Lab suite passes 78 tests.

## Claim boundary

This closes finite solver-plumbing validation only. Fusion compatibility is pre-enumerated into selector variables, so the formulation cannot be presented as the scalable structural MILP sought by R3. It remains a useful exact checkpoint: any structural formulation must reproduce these objectives, ties, edge sets, and sector optima before it is run on a larger graph. It is not R4 posterior-sector summation.

