---
title: 'R6AE signal-only BP threshold scan — Stage 4'
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

# R6AE signal-only BP threshold scan — Stage 4

## Completed gate

All 20 cells reached 4,000 matched attempted histories, for 80,000 total
trajectories. Deterministic trajectory indices 3000–3999 were appended to the
preserved Stage-3 records under the unchanged paper X-only channel, public
binary herald record, decoders, and Boolean-union flux score. The completed
raw result contains exactly 4,000 records in every registered cell.

## Finite-size result

For signal-only BP at $p_X=0.19$, the $L=5\to7$, $7\to9$, and $9\to11$
differences exclude zero on the negative side at 90%; $L=11\to13$ remains
unresolved. At $p_X=0.20$, $L=5\to7$ and $9\to11$ resolve negative, while the
other two adjacent-size intervals contain zero. Every BP adjacent-size
interval at $p_X=0.21$ and $0.22$ contains zero.

The preregistered decoder-union plus immediate-neighbor rule still selects all
20 cells for the final 1,000-history increment, to the registered cap of
5,000/cell. The finite-size pattern remains inconsistent with a stable
crossing: increasing size lowers risk in much of the low-$p_X$ region, but the
larger-size directions near $p_X=0.21$–$0.22$ are unresolved. All BP runs reach
the 40-iteration cap, so fixed-point convergence remains an explicit
sensitivity limitation.

## Evidence

- Resumable counts (raw trajectories removed after validation): `results/r6ae-signal-only-bp-threshold-sufficient-statistics-2026-09-05.json`
- Frozen analysis: `results/r6ae-signal-only-bp-threshold-stage4-analysis-2026-09-01.json`
- Figure: `figures/r6ae-signal-only-bp-threshold-stage4-2026-09-01.png`
- Contract: `manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json`

## Claim boundary

This remains an X-only first-stage finite-size diagnostic. It is not the
paper's full two-stage decoder and supports neither a crossing fit nor a
thermodynamic threshold claim.
