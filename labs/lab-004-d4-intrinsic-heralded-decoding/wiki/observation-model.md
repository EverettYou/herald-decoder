---
title: D4 observation model
status: current
updated: 2026-09-01
---

## Summary

The paper-normalized D4 model separates physical errors, public fusion signals, and private truth scoring.

## Evidence

[Periodic supercell audit](records/r0-paper-supercell-audit.md), [local likelihood audit](records/r1-local-likelihood-core-audit.md), [sublattice herald audit](records/r6ac-d4-sublattice-herald-model-audit-2026-08-31.md), [Lab 003/D4 channel audit](records/p4-lab003-d4-channel-equivalence-audit-2026-09-01.md), and [two-stage public-charge preflight](records/r6af-two-stage-public-charge-preflight-2026-09-01.md).

## Status

Current. The first public BP record is binary signal-only and explicitly
non-equivalent to Lab 003's independent $q=3/4$ herald field. The second public
charge record must likewise be full binary; inactive-support sentinels and the
hidden relation graph are simulator truth, not decoder-visible information.

R6AJ carries this exact boundary into the registered complete-pipeline
transfer test: matched arms share physical, first-observation, and
second-exogenous keys, but each second full-binary record is generated against
its own realized first action. The public charge decoder consumes only that
record and the known first correction; private relation/support/effective-truth
objects remain generation and scoring data.

## Related pages

[[bp-signal-boundary|BP signal-model boundary]] · [[index|Lab 004 index]]
