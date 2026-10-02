---
title: Temporal-boundary ledger reconciliation prerequisite
status: current
updated: 2026-09-23
---

## Summary

The integrated Lab 005 caller now treats a causal odd-snapshot handoff as a
no-physics deferral. A later even full-snapshot action may supersede that
ledger; a terminal unresolved handoff or conflicting same-round request
remains an unconditional failed-closed row. This repairs a deterministic
handoff-to-scoring gap exposed before J6B pilot registration.

## Evidence

The [registered prerequisite](../../manifests/j6b-r0-temporal-ledger-reconciliation-2026-09-23.json)
and [machine-readable result](../../results/j6b-r0-temporal-ledger-reconciliation-2026-09-23.json)
record four fixed fixtures, 158 passing Lab 005 regressions, pinned runtime
versions, source hashes, and unchanged frozen J6 raw/analysis SHA-256 values.
The four new fixtures expand to 22 deterministic arm evaluations, below their
registered 32-arm cap; the existing Lab regression suite is a separate
source-compatibility check under the same 120-second runtime cap.
The decisive counterexample before correction was a public odd round-1
snapshot followed by an even round-2 snapshot: the E1 callback emitted
`defer_temporal_boundary` then `action`, but the integrated caller marked the
whole history failed solely because a prior defer existed. The corrected
deterministic zero-physical case scores with one real commit at round 2 and
one post-action second record; no second record or correction is generated at
the deferred round.

Persistent odd, same-round duplicate, conflicting request, eight-row
unconditional replay, and existing future/private invariance regressions
remain guarded. No stochastic replacement history or production arm was run.

## Status

This is an interface correctness gate, not an estimate of how often later
records resolve odd snapshots. J6 remains closed censored and unpooled. The
next operation is a separate immutable J6B replacement-pilot registration,
including fresh cohort, event and resolved-action gates, compute budget and
stop rule, before any sampling.

## Related pages

[[spatial-policy-boundary|Spatial-policy boundary]] · [[schedule-state|Schedule state]]
