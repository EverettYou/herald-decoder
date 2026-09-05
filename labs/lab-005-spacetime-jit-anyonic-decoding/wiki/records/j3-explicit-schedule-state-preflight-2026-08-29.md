---
title: 'J3 explicit schedule-state preflight'
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

# J3 explicit schedule-state preflight

## Result

The missing abstract state transition is implemented without merging the two
source branches.

- The **Jing ILP branch** retains unresolved defects while the bounding-cube
  age condition fails and commits when the youngest cluster element reaches
  age (Q). It does not alter the measurement record.
- The **Lyons–Brown branch** reverses only the latest decoder-side syndrome
  readout at detector-bearing vertices. This removes the current detector and,
  when the raw readout persists, creates the corresponding event on the next
  transition. It separately logs D(S3), boundary, and ungauged D(Z3) states.

A D(S3) or boundary cluster that passes the age gate first emits `ungauge`.
Age is then measured relative to that ungauging boundary. A supplied neutral
outcome emits `correct_regauge`; a supplied non-neutral outcome remains
deferred. Every transition and every readout reversal has a deterministic log.

## Verification

Six focused fixtures cover readout propagation, invalid past/absent events,
Jing retain/commit behavior, D(S3) defer→ungauge→neutral correction, boundary
ungauging, non-neutral deferral, and future/record mismatch rejection. All
33 current Lab 005 tests pass.

Contract and hashes:
[`manifests/j3-explicit-schedule-state-manifest-2026-08-29.json`](../../manifests/j3-explicit-schedule-state-manifest-2026-08-29.json).

## Claim boundary

This is an abstract causal-state preflight. Nearest-absorber distances,
cluster geometry, and neutrality are still supplied by the fixture. There is
no microscopic ungauging circuit, D(S3) fusion inference, linked-cluster
engine, noisy D4 channel, schedule comparison, threshold, or fault-tolerance
result. The next gate is to make absorber geometry and the neutrality
measurement interface explicit on tiny D(S3)-labelled fixtures.

