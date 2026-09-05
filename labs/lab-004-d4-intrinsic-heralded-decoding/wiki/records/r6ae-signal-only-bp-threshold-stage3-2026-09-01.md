---
title: 'R6AE signal-only BP threshold scan — Stage 3'
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

# R6AE signal-only BP threshold scan — Stage 3

## Completed gate

All 20 cells reached 3,000 matched attempted histories, for 60,000 total
trajectories. Deterministic trajectory indices 2000–2999 were appended to the
preserved Stage-2 records under the unchanged paper X-only channel, public
binary herald record, decoders, and Boolean-union flux score.

## Finite-size result

For signal-only BP at $p_X=0.19$, the three larger adjacent-size differences
exclude zero on the negative side at 90%; $L=5\to7$ remains unresolved. At
$p_X=0.20$ and $0.21$, the $L=5\to7$ differences are resolved negative, while
larger-size differences remain unresolved. Every adjacent-size interval at
$p_X=0.22$ still contains zero.

The preregistered decoder-union plus immediate-neighbor rule again selects all
20 cells for the next 1,000-history increment, to 4,000/cell. Precision has
improved, but the larger-size behavior still does not define a stable crossing.
All BP runs reach the 40-iteration cap, so fixed-point convergence remains an
explicit sensitivity limitation.

## Evidence

- Resumable counts (raw trajectories removed after validation): `results/r6ae-signal-only-bp-threshold-sufficient-statistics-2026-09-05.json`
- Frozen analysis: `results/r6ae-signal-only-bp-threshold-stage3-analysis-2026-09-01.json`
- Figure: `figures/r6ae-signal-only-bp-threshold-stage3-2026-09-01.png`
- Contract: `manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json`

## Claim boundary

This remains an X-only first-stage finite-size diagnostic. It is not the
paper's full two-stage decoder and supports neither a crossing fit nor a
thermodynamic threshold claim.
