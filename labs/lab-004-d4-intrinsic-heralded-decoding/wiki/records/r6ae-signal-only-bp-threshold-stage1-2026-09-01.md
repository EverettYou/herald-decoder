---
title: 'R6AE signal-only BP threshold scan — Stage 1'
status: current
updated: 2026-09-01
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

# R6AE signal-only BP threshold scan — Stage 1

## Completed gate

The registered 20-cell scan completed all 20,000 matched trajectories: five
paper lattice sizes, four values of $p_X$, and 1,000 attempted histories per
cell. O0, published O2, and signal-only D4-local BP-to-MWPM consumed the same
physical histories and the same public binary charge record.

The primary accounting is the paper-unconditional flux logical error rate.
Every BP run reached the registered 40-iteration cap, so the converged-only
sensitivity set is empty; the finite final iterate remains the preregistered
primary BP output and is reported as such.

## Finite-size result

The BP curves decrease with size at $p_X=0.20$ from $0.208$ at $L=5$ to
$0.140$ at $L=13$, while at $p_X=0.21$ they are non-monotone
($0.249,0.245,0.253,0.229,0.255$). At $p_X=0.22$, the $L=5\to7$ change is
positive but later pairs oscillate. These data place the finite-size change of
direction near the published region but do not define a stable crossing.

The preregistered 90% adjacent-size difference rule selects all 20 cells for
the next 1,000-history increment because at least one decoder/size-pair
interval is unresolved at every grid point after neighbor expansion. This is
an allocation decision, not a threshold estimate.

## Evidence

- Resumable counts (raw trajectories removed after validation): `results/r6ae-signal-only-bp-threshold-sufficient-statistics-2026-09-05.json`
- Frozen analysis: `results/r6ae-signal-only-bp-threshold-analysis-2026-09-01.json`
- Figure: `figures/r6ae-signal-only-bp-threshold-stage1-2026-09-01.png`
- Contract: `manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json`

## Claim boundary

This is an X-only, first-stage flux-decoder finite-size diagnostic. It neither
reproduces the paper's full two-stage decoder nor supports a thermodynamic
threshold claim. The source-compatibility and signal-only observation gates
remain part of every subsequent interpretation.
