---
title: 'J3 persistent detector-cluster tracker preflight'
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

# J3 persistent detector-cluster tracker preflight

## Result

The registered causal snapshot components now have persistent state across
successive prefixes. A new component receives a monotone identifier. When a
later event extends one component, that identifier remains stable. When a
bridge event joins multiple prior components, the earliest identifier becomes
the canonical owner and the others remain durable aliases.

Two ownership records are kept deliberately separate. `event_origin` is
immutable and records the persistent component in which an event first
appeared. `current_owner` follows deterministic merges and covers every known
event. Previously seen events must remain present with identical check,
position, and time data; deletion or retrospective change is rejected. Under
the fixed append-only adjacency rule, a prior component may merge but cannot
split.

Snapshot geometry is refreshed at every causal horizon. Nearest absorbers and
link candidates follow absorber opening/termination, and self-exclusion uses
the persistent owner identifier rather than the ephemeral snapshot name. A
current-frontier handoff preserves the persistent identifier through the
public schedule API.

## Verification

Seven focused fixtures cover extension, independent creation, bridge merge,
history mutation rejection, idempotent refresh, absorber lifecycle/self-
exclusion, and persistent-ID schedule handoff. All 60 current Lab 005 tests
pass.

Contract and hashes:
[`manifests/j3-persistent-cluster-tracker-manifest-2026-08-29.json`](../../manifests/j3-persistent-cluster-tracker-manifest-2026-08-29.json).

## Claim boundary

This verifies deterministic state management over the registered radius-one
snapshot rule. It does not support deletion or decoder-side rewriting of the
raw observation history, prove that the adjacency is physically optimal,
infer ILP corrections or fusion channels, or supply microscopic/noisy physics.
It establishes no schedule-performance, threshold, or fault-tolerance result.

The next bounded transition is an audit of remaining J1/J2 prerequisites and
the smallest shared-fault-history baseline matrix. A noisy pilot must not begin
until immediate, fixed-delay, JIT, and offline paths share one explicit record
and inner-decoder contract.

