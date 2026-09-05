---
title: 'J1/J2 shared-history baseline readiness audit'
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

# J1/J2 shared-history baseline readiness audit

## Outcome

The project is ready to build a deterministic four-branch scheduling harness,
but it is not ready to run a noisy schedule comparison.

| Dependency | Current evidence | Readiness |
|---|---|---|
| J1 causal record | `SpacetimeRecord` separates truth, readout faults, visible readouts, adjacent-round syndrome detectors, expected known motion, and causal prefixes | Ready for supplied deterministic fixtures; no registered stochastic noisy-history generator |
| J2 immediate baseline | No implementation | Missing |
| J2 fixed-delay baseline | No implementation | Missing |
| J2 offline baseline | No implementation | Missing; future access must be explicit |
| J3 JIT state | Persistent clusters, deferred-record propagation, absorber geometry, neutrality handoff, and deterministic phase lifecycle pass | Ready as an abstract timing branch |
| J5 inner decoder | D4 has a verified observation-only spatial adapter, but no source-neutral callback shared by all schedule branches | Missing common harness protocol; the D4 adapter cannot silently stand in for D(S3) |
| J6 noisy pilot | Requires matched branches, a common decoder, and a registered physical history generator | Blocked by J2/J5 and noise-model registration |

## Smallest discriminating preflight

The four branches are independent, reversible, and inexpensive on tiny
deterministic histories, so there is no human ranking decision. The registered
matrix covers all of them:

1. immediate invocation at first visibility;
2. fixed delay of one readout round;
3. the verified abstract Lyons–Brown JIT age/absorber path;
4. full-history offline invocation, explicitly labelled noncausal.

Every branch must bind to one immutable trial/history digest and use the same
versioned inner-decoder callback. Causal requests contain only their prefix;
offline access is separately declared. Truth faults and logical scoring remain
in a private sidecar unavailable to schedules and the callback. The preflight
callback may return a canonical deterministic token solely to verify timing,
identity, and anti-leakage; it is not a physical decoder.

Contract:
[`manifests/j2-shared-history-baseline-manifest-2026-08-29.json`](../../manifests/j2-shared-history-baseline-manifest-2026-08-29.json).

## Claim boundary

This audit and registration contain no replacement data and no schedule
comparison. They do not show that JIT outperforms immediate or fixed delay,
do not validate noisy syndrome/herald physics, and do not connect D4 to D(S3).
The next bounded transition is implementation and anti-leakage verification of
the deterministic shared-history runner. Only after it passes may a noisy
history generator or pilot matrix be registered.

