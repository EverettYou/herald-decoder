---
title: 'J3 absorber geometry and neutrality-measurement preflight'
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

# J3 absorber geometry and neutrality-measurement preflight

## Result

The Lyons–Brown schedule now receives its nearest-absorber distance from an
explicit causal geometry instead of a fixture scalar. Absorbers are inclusive
integer spacetime boxes, distances use the minimum box-to-box
\(L_\infty\) metric, and only regions active at the queried round participate.
Opening and termination are separately logged; a cluster-owned absorbing
region can be excluded when querying the nearest external absorber.

The direct-link layer enforces the three restrictions stated in Theorem 4:
a cluster cannot link directly to the same or a smaller level, a smaller
cluster has only one direct larger parent, and an absorber has at most one
direct child at each level. This verifies the admissible linked-forest shape;
it does not rediscover clusters from detector data or re-prove the paper's
\(Q\ge 60\) bound.

Neutrality is now a measured interface rather than an arbitrary schedule
label. A record carries current-round binary \(e\) and \(m\) parities and is
accepted only for an active ungauging wall owned by a schedule cluster already
in D(Z3). `(0,0)` is recorded as neutral and any nonzero parity as non-neutral.
The interface then updates the abstract schedule, without reading simulation
truth.

## Verification

Seven focused fixtures cover the metric and schedule binding, absorber
termination, self-region exclusion, all three link restrictions, neutral and
non-neutral readouts, and rejection of terminated, future, or wrong-owner
measurements. All 40 current Lab 005 tests pass.

Contract and hashes:
[`manifests/j3-absorber-neutrality-manifest-2026-08-29.json`](../../manifests/j3-absorber-neutrality-manifest-2026-08-29.json).

## Claim boundary

This is a deterministic source-level preflight. It does not implement a
microscopic D(S3) gauging/ungauging circuit, derive parity outcomes from
circuit noise, discover linked clusters, reproduce the \(Q\ge60\) proof,
connect a noisy D4 channel, compare schedules, or establish a numerical
threshold or fault tolerance. The next bounded gate is the lifecycle adapter
which creates the ungauged region, preserves a supplied fusion outcome, and
terminates it on re-gauging.

