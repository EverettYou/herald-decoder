---
title: 'R6AE signal-only BP threshold scan — Stage 2'
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

# R6AE signal-only BP threshold scan — Stage 2

## Completed gate

All 20 selected cells reached 2,000 matched attempted histories, for 40,000
total trajectories. The continuation preserved trajectories 0–999 from Stage
1 and added deterministic indices 1000–1999 without changing the physical
channel, public binary $e_B/e_G$ record, decoder-visible information, or
Boolean-union flux score.

## Finite-size result

For signal-only BP, every adjacent-size difference at $p_X=0.19$ is now
negative; three of four exclude zero at 90%, while $L=5\to7$ remains
unresolved. At $p_X=0.20$, $L=5\to7$ is resolved negative but the three larger
size pairs remain unresolved. The $p_X=0.21$ and $0.22$ curves remain
non-monotone with unresolved intervals across most size pairs.

The exact preregistered union rule still selects all 20 cells for the next
1,000-history increment: at least one decoder/adjacent-size interval is
unresolved at every grid point after immediate-neighbor expansion. The added
precision narrows the finite-size transition to the studied $0.19$–$0.22$
window but does not establish a stable multi-size crossing.

All BP runs still reach the registered 40-iteration cap. The finite final
iterate is the preregistered primary output; the empty converged-only subset is
reported as a sensitivity limitation rather than silently filtered.

## Evidence

- Resumable counts (raw trajectories removed after validation): `results/r6ae-signal-only-bp-threshold-sufficient-statistics-2026-09-05.json`
- Frozen analysis: `results/r6ae-signal-only-bp-threshold-stage2-analysis-2026-09-01.json`
- Figure: `figures/r6ae-signal-only-bp-threshold-stage2-2026-09-01.png`
- Contract: `manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json`

## Claim boundary

This remains an X-only, first-stage flux-decoder finite-size diagnostic. It is
not the paper's full two-stage D4 decoder and supports neither a crossing fit
nor a thermodynamic threshold claim.
