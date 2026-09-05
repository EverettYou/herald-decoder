---
title: 'R6AE signal-only BP threshold scan — Stage 5 registered cap'
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

# R6AE signal-only BP threshold scan — Stage 5 registered cap

## Completed gate

All 20 cells reached the registered cap of 5,000 matched attempted histories,
for 100,000 total trajectories. Deterministic trajectory indices 4000–4999
were appended to the preserved Stage-4 records under the unchanged paper
X-only channel, public binary herald record, three decoders, and Boolean-union
flux score. The completed raw result contains exactly 5,000 records in every
registered cell.

## Finite-size result

For signal-only BP at $p_X=0.19$, all four adjacent-size differences exclude
zero on the negative side at 90%. At $p_X=0.20$, the $L=5\to7$ and
$L=9\to11$ differences resolve negative, while $L=7\to9$ and $L=11\to13$
remain unresolved. Every BP adjacent-size interval at $p_X=0.21$ and $0.22$
contains zero. In total, six of sixteen BP differences resolve negative and
ten remain unresolved; none resolves positive.

The frozen union-plus-neighbor rule would still select 19 cells, but the
registered 5,000-history/cell cap has been reached and authorizes no further
increment. The curves do not provide a stable multi-size crossing bracket.
All BP runs reach the 40-iteration cap, so fixed-final-iterate behavior—not
fixed-point convergence—is the reported primary result.

## Evidence

- Resumable counts (raw trajectories removed after validation): `results/r6ae-signal-only-bp-threshold-sufficient-statistics-2026-09-05.json`
- Frozen analysis: `results/r6ae-signal-only-bp-threshold-stage5-analysis-2026-09-01.json`
- Figure: `figures/r6ae-signal-only-bp-threshold-stage5-2026-09-01.png`
- Contract: `manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json`

## Decision

R6AE closes at its registered sampling cap without a threshold estimate. It
supports a corrected signal-only, first-stage finite-size comparison and a
clear low-$p_X$ direction for BP, but not the paper's full two-stage D4
threshold. The withdrawn support-revealing BP campaign remains excluded from
performance evidence.
