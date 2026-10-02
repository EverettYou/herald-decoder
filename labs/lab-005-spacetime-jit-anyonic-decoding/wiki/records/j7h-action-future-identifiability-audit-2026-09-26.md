---
title: Action and future-fault identifiability under red-X support
status: current
updated: 2026-09-26
---

## Summary

In the fixed additive red-X model, a comparison cannot hold the initial
physical error, later physical fault, and final physical support all fixed
while changing only the public correction. This is an exact cancellation
identity, not a statistical limitation. It explains why the earlier
same-final-support complete-public difference is a history contrast rather
than an isolated action effect.

## Evidence

The [registered audit](../../manifests/j7h-action-future-identifiability-audit-2026-09-26.json)
freezes the three-edge initial support and the two corrections and later
faults used by the [positive exact history result](j7g-three-edge-matched-complete-next-law-2026-09-25.md).
For red-edge sets, final support is `S = E xor A xor F`.
Holding `E,F` fixed and cancelling xor on both sides gives
`S(A1)=S(A2) iff A1=A2`. A distinct-action comparison therefore cannot
also match the final physical support under one shared future-fault key.

The [machine audit](../../results/j7h-action-future-identifiability-audit-2026-09-26.json)
reconciles all four frozen action/future cells to the source-pinned periodic
edge and public-flux maps:

| Public correction | Later physical fault | Final red-X support |
| --- | --- | --- |
| edge 0 | edge 0 | edges 0, 3, 4 |
| edge 0 | edge 4 | edge 3 |
| edge 4 | edge 0 | edge 3 |
| edge 4 | edge 4 | edges 0, 3, 4 |

The diagonal cells reproduce the earlier matched-final-support result but
necessarily use different future faults. The same-future-key column
comparisons keep the exogenous later fault fixed but end on different
physical supports. The exhaustive control checks all 32 in-support
correction/no-or-one-future-fault cells and all 112 distinct-action pairs at
the same future key; every pair has different final support. Five immutable
source/caller/result pins, two focused tests and deterministic replay pass;
no Born-law, stochastic history or caller evaluation was run.

## Status

The two questions are different estimands, not interchangeable baselines:
the same-final-support test probes ideal history dependence under different
physical futures, while the same-future-key test could estimate an action's
**total** effect, including any changed final physical state. The latter
fits the project's causal JIT-action objective. Its separately registered
[complete-public comparison](j7i-same-future-total-action-law-2026-09-26.md)
now closes one finite ideal case, with a deterministic next-flux distinction.
This support audit itself proves no causal benefit, noisy schedule risk or
threshold.

## Related pages

- [[schedule-state|Schedule state]]
- [[records/j7g-three-edge-matched-complete-next-law-2026-09-25|Three-edge ideal history contrast]]
- [[records/j7i-same-future-total-action-law-2026-09-26|Same-future total-action public law]]
